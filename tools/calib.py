"""Tiny single-image calibration: fit focal length + pose to 2D-3D correspondences where some 3D
coordinates are unknowns (e.g. a strip height). Pinhole, principal point at image centre, no distortion.
World (cm): X along wall 1 from wall 4 (0) to wall 3 (300); Y from wall 2 (0) to wall 1 (290); Z up.
"""
import numpy as np


def rodrigues(r):
    th = np.linalg.norm(r)
    if th < 1e-12: return np.eye(3)
    k = r / th; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def rot_to_rvec(R):
    th = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if th < 1e-9: return np.zeros(3)
    if th > np.pi - 1e-3:  # near 180 deg: axis from the dominant column of (R + I) / 2
        B = (R + np.eye(3)) / 2; i = np.argmax(np.diag(B)); k = B[:, i] / np.sqrt(B[i, i])
        return th * k / np.linalg.norm(k)
    return th / (2 * np.sin(th)) * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])


class Problem:
    """obs: list of (u, v, (X, Y, Z)) where a coordinate may be a string naming an unknown."""
    def __init__(self, size, obs, unknowns):
        self.cx, self.cy = size[0] / 2, size[1] / 2
        self.obs, self.unk = obs, list(unknowns)

    def pack(self, f, R, C, u0):
        return np.r_[f, rot_to_rvec(R), C, [u0[k] for k in self.unk]]

    def project(self, p, P):
        f, R, C = p[0], rodrigues(p[1:4]), p[4:7]
        q = R @ (np.asarray(P, float) - C)
        return np.array([self.cx + f * q[0] / q[2], self.cy + f * q[1] / q[2]])

    def point(self, p, P):
        vals = dict(zip(self.unk, p[7:]))
        return [vals[c] if isinstance(c, str) else c for c in P]

    def residuals(self, p):
        return np.concatenate([self.project(p, self.point(p, P)) - (u, v) for u, v, P in self.obs])

    def solve(self, p, iters=200, fix_f=None):
        lam = 1e-3
        for _ in range(iters):
            if fix_f: p[0] = fix_f
            r = self.residuals(p)
            J = np.empty((r.size, p.size))
            for i in range(p.size):
                d = np.zeros_like(p); d[i] = 1e-6 * max(1, abs(p[i]))
                J[:, i] = (self.residuals(p + d) - r) / d[i]
            if fix_f: J[:, 0] = 0
            A = J.T @ J; g = J.T @ r
            while True:
                step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
                if np.sum(self.residuals(p + step) ** 2) < np.sum(r ** 2):
                    p = p + step; lam = max(lam / 3, 1e-9); break
                lam *= 5
                if lam > 1e9: return p
            if np.linalg.norm(step) < 1e-8: break
        return p

    def report(self, p):
        r = self.residuals(p).reshape(-1, 2)
        R = rodrigues(p[1:4])
        print(f"f={p[0]:.1f}px  C=({p[4]:.1f},{p[5]:.1f},{p[6]:.1f})  rms={np.sqrt((r**2).sum(1).mean()):.2f}px  max={np.abs(r).max():.1f}")
        for k, v in zip(self.unk, p[7:]): print(f"  {k} = {v:.1f}")
        return R

    def backproject(self, p, uv, plane_axis, plane_val):
        """Intersect pixel ray with plane coord[plane_axis] == plane_val; returns world point."""
        f, R, C = p[0], rodrigues(p[1:4]), p[4:7]
        d = R.T @ np.array([(uv[0] - self.cx) / f, (uv[1] - self.cy) / f, 1.0])
        t = (plane_val - C[plane_axis]) / d[plane_axis]
        return C + t * d


def R_from_vps(vx, vz_down, f, c):
    """World X axis from its VP, world -Z from the downward vertical VP; returns world->camera R."""
    dx = np.array([(vx[0] - c[0]) / f, (vx[1] - c[1]) / f, 1.0]); dx /= np.linalg.norm(dx)
    dz = -np.array([(vz_down[0] - c[0]) / f, (vz_down[1] - c[1]) / f, 1.0]); dz /= np.linalg.norm(dz)
    dz -= dx * (dx @ dz); dz /= np.linalg.norm(dz)
    dy = np.cross(dz, dx)
    return np.column_stack([dx, dy, dz])
