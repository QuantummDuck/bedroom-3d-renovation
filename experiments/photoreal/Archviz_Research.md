# How professional interior renders are made, and what I applied to your room

Research notes for round 5 (14–15 Oct 2026). Each section gives what the industry does, then what I did in your files. The sources are listed at the end.

## 1. Why renders look "CG"

Studios agree that realism comes from many small, correct choices, not from one setting or engine:
- real scale
- real light levels
- measured material values
- imperfections
- a camera used the way a photographer uses it

The problems I found in my earlier renders, against that checklist:

| Problem in the earlier renders | Industry practice | Fix in round 5 |
|---|---|---|
| 14–18 mm lenses: stretched corners, the room looks huge | Interior photographers use 20–28 mm full-frame equivalent; 35–50 mm for natural-looking views; avoid wider than ~16 mm | Rooms at **24–28 mm**, corners at 35 mm, details at **50 mm** |
| Cameras at 1.2–1.5 m, tilted | Shoot from chest height (about 1.2–1.5 m) with the camera **level**; frame with shift, never tilt (two-point perspective) | Level cameras at **your** eye height (156 cm standing, 118 cm seated), framed with lens shift, so verticals stay vertical |
| Perfect, sharp, clean surfaces | "Even the smallest imperfections, like a crack in the wall or the unevenness of a tile, can make a huge difference"; bevel every edge; never use uniform roughness | Paint relief from your wall photo, tiny paint specks, grime near the floor, tile-to-tile tilt, smudges on the floor glaze, fingerprints and dust on the glass, chrome and MacBook; bevels on all furniture |
| Fabric too smooth | Bedding needs folds and crinkles; simulate it, then add fine detail | Cloth-simulated bedspread, plus fine crinkle creases and quilting dips, a slight hollow where you sleep, and the grey jersey fitted sheet at the sides |
| Generic stand-in props | Use real, specific objects (scanned or photographed) | Your real book spines and shelf objects cut from your photos (45 books), your handwritten notes, your bedspread, rug and puzzle images, your MacBook screen |
| LED scenes 2 stops dark | Expose for the room the way a photographer would; don't dim the lights to protect the highlights | Per-scenario camera exposure and white balance; the AgX view transform handles bright light sources |

## 2. Camera

**Height**
- Archviz "eye level" is 1.5–1.8 m.
- Real-estate photographers go lower, to chest height (about 1.2–1.5 m), so you see the tops of beds and tables without looking down into the room.
- For your renders I used your own eye heights: 156 cm standing and 118 cm seated (from your height of 167 cm).

**Lens (full-frame equivalent)**
- 20–25 mm is what "many professional interior photographers use".
- 24 mm is the professional favourite; 16–35 mm zooms are the workhorse.
- Going wider than ~14 mm becomes hard to manage because of distortion.
- Human central vision is about 55°, which equals a 43 mm lens. That is why 35–50 mm frames feel like "being there".
- Your iPhone's main camera is about 26 mm. Your photos look natural partly because no camera was wider than that.

**Verticals**
- Keep the camera level and use shift (the same idea as a tilt-shift lens) instead of tilting.
- Tilting makes vertical lines converge (keystoning), which immediately looks wrong in architecture.
- All new cameras are level, with automatic shift so the subject sits where a tilted camera would have put it.

**Depth of field**
- Add depth of field only after the composition is right.
- Rooms: f/8, so everything is sharp, as a photographer would shoot it.
- Details: f/2.8–4, for natural background blur.

**Physical exposure as a reference**
- Typical camera settings for interiors:
  - daylight: ISO 200–400, f/5.6–8, 1/30–1/60 s
  - night with lamps on: ISO 800–1600, f/2.8–4, 1/15–1/30 s
- Fix the light levels and expose with the camera. Don't brighten the lights to fix a dark picture.
- I set the exposure separately for each lighting scenario and kept every light at its physical power.

**Lens character**
- Use a little chromatic aberration, vignette, bloom and grain, and keep them subtle; overdoing them looks artificial.
- Mine: a mild barrel distortion and colour fringing, a gentle vignette, bloom only around very bright points, and fine grain.

## 3. Render settings (Cycles, Blender 5.2)

**Why interiors are hard**
- Most light rays fail to find the light source, which shows up as noise.
- Studios use portals in the windows, enough bounces, adaptive sampling, a denoiser, and an indirect clamp against fireflies.

**What I used**
- **Light paths:**
  - light portal in the window (from earlier rounds)
  - light tree for the many LED strips
  - 16 total bounces: 6 diffuse, 6 glossy, 12 transmission
  - indirect clamp 8
  - blur glossy 0.5
- **Sampling and denoising:**
  - up to 1024 samples, adaptive threshold 0.008
  - OpenImageDenoise at high quality with albedo and normal passes, so fine texture survives denoising (plain denoising can turn walls "watercolour")
- **Output:**
  - 16-bit PNG plus a JPG preview
  - AgX view transform with the Medium High Contrast look
  - per-scenario white balance in Kelvin, like a camera

**Colour management**
- AgX replaced Filmic in Blender 4.0.
- Archviz artists prefer it because bright windows and lamps roll off to white the way they do in a camera, instead of collapsing into six hues.
- AgX looks darker at first, so the exposure has to be re-tuned rather than copied from Filmic.

## 4. Materials

**Real-world reference values** (physicallybased.info, a CC0 database of measured values)

| Material | Base colour (linear) | Roughness / metal | Notes |
|---|---|---|---|
| Porcelain | 0.745 | 0 (polished) | your floor tiles: near-mirror glaze, broken up by smudges |
| White paint | 0.5–0.9 (flat white is about sRGB 227) | matte | your wall #E6E1CF is calibrated against your photos |
| Aluminium | 0.916 0.923 0.924 | metal 1 | MacBook, window frames |
| Stainless / chrome | 0.669 0.639 0.598 | metal 1 | stool, wardrobe handles |
| Glass | 1.0, IOR 1.52 | 0 | your window: 5 mm pane, slight green edge tint |
| Office paper | 0.79 0.83 0.88 | 0.8 | notes and books |

**Rules studios follow**
- Keep non-metal colours between about 0.03 and 0.8 linear (Unity's chart is 50–243 sRGB).
- Never use pure black or pure white diffuse; both break the bounce light.
- "Everything has Fresnel."
- Roughness always varies across a surface; uniform gloss is the classic CG tell.
- Model bevels; real edges catch light.
- A subtle bump looks more real than a strong one.

**Texture quality**
- Texel density means texture pixels per centimetre.
- Close-up surfaces need about 20–40 px/cm; distant ones can be much lower.
- Use scanned, real-world-scale PBR sets: colour, roughness, normal, displacement.

**What your scene now uses**

| Surface | Texture | Resolution / scale |
|---|---|---|
| Teak boards (design) | Poly Haven teak_veneer scan | 4K over a 1 m tile (41 px/cm) |
| Oak melamine (current room) | oak_veneer_01 scan | 2K over 1.83 m |
| Wall paint | relief from **your** close-up photo 42 | about 47 px/cm, plus procedural specks and grime |
| Floor | speckle from **your** photo 43 | plus smudge maps (ambientCG) and per-tile tilt |
| Bedspread | **your** photo 50, de-lit and flattened | 10 px/cm over the whole bed |
| Rug | **your** photo 44 | plus a carpet-pile normal scan |
| Puzzle | **your** straight-on photo 45, perspective-corrected and white-balanced | 20 px/cm |
| Books | **your** photos 46–49 | 40 px/cm, one spine texture per book |
| Fingerprints, dust, smudges | ambientCG | glass, chrome, aluminium, floor |
| Desk lamp | Poly Haven desk_lamp_arm_01 | scanned spring-arm lamp, refinished in black satin |
| Plant outside | Poly Haven potted_plant_02 | stand-in for your tomato plant |

## 5. Simulation

- **Bedding:** studios use Marvelous Designer or Blender cloth with pins to direct the folds, then add fine detail.
- **Your bed:**
  - the bedspread is cloth-simulated, pinned along the walls, draping over the open side and the foot
  - fine crinkles and the quilting channels are added in the shader
  - the pillows are pressure-inflated cloth
- **Fan:** the blades spin with real motion blur in the "everyday night" scene. They turn about 55° during a 1/15 s exposure, like your photo 40.

## 6. Light

- **Natural light:** a sun lamp placed for your exact location and window. The window faces 260°.
- **Sun on your window:**

| Day | Sun on the window | Sunset |
|---|---|---|
| Tomorrow (15 Oct) | 12:00 | 18:05 |
| Summer solstice (21 Dec) | 12:05 | 18:45 |
| Equinox (20 Mar) | 12:30 | 18:15 |
| Winter solstice (21 Jun) | 12:40 | 17:25 |

- **Rendered sun times:** 16:00, 17:00 and 17:40 tomorrow, with the sky from a real HDR photo. See `Sun_Path_Diagram.png` and `sun_positions.json`.
- **The neighbouring tower:** it sits at a bearing of about 216° and about 75 m away, so the low sun in the late afternoon comes from the right of it. Its height is unknown, so I assumed it is similar to your building.
- **Artificial light:**
  - every lamp and LED group has a physical power and colour temperature
  - the screen glows
  - lit windows across the street at night
- **Scenarios:** 8 lighting setups, from overcast morning to night, listed in the README.

## Sources

- [D5 Render: camera settings for archviz](https://www.d5render.com/posts/camera-setting-tips-must-known-for-archviz)
- [Columbia GSAPP: technical camera in Blender](https://smorgasbord.cdp.arch.columbia.edu/modules/40-rendering-with-blender/252-technical-camera)
- [Novedge: camera views and 2-point perspective](https://novedge.com/blogs/design-news/revit-tip-enhancing-architectural-visualizations-mastering-camera-views-in-revit)
- [Photography for Real Estate: tilt-shift lenses](https://photographyforrealestate.net/how-to-learn-how-to-use-tilt-shift-lenses/)
- [DPReview: ideal camera height for real estate](https://www.dpreview.com/forums/post/60809976)
- [Improve Photography: lenses for real estate](https://improvephotography.com/?p=45705)
- [Lensrentals: normal lens and human vision](https://www.lensrentals.com/blog/?p=749)
- [Artlist: what is a standard lens](https://artlist.io/blog/normal-lens/)
- [Novedge: V-Ray physical camera exposure](https://novedge.com/blogs/design-news/v-ray-tip-v-ray-physical-camera-match-real-world-exposure-and-optics)
- [Novedge: balanced interior lighting](https://novedge.com/blogs/design-news/v-ray-tip-v-ray-techniques-for-balanced-and-natural-interior-lighting)
- [Corona forum: exposure](https://forum.corona-renderer.com/index.php/topic,9586.0.html)
- [S2 Archviz: Corona quality guide](https://s2archviz.com/high-quality-renders-in-corona-renderer-guide/)
- [Blender manual: reducing noise](https://docs.blender.org/manual/de/5.3/render/cycles/optimizations/reducing_noise.html)
- [Blender Artists: interior noise in Cycles](https://blenderartists.org/t/how-to-easily-render-noisy-interior-lighting-in-cycles/1641294)
- [Super Renders Farm: render settings](https://superrendersfarm.com/es/article/blender-render-settings-optimization-guide)
- [Blender 4.0 colour management notes](https://wiki.blender.org/release_notes/4.0/color_management/)
- [Blender Artists: Filmic vs ACES vs AgX for archviz](https://blenderartists.org/t/filmic-vs-aces-vs-agx-for-architectural-visualization/1459951)
- [physicallybased.info](https://api.physicallybased.info/materials)
- [Unity material validator (albedo ranges)](https://docs.unity3d.com:443/Manual/MaterialValidator.html)
- [Corona forum: reflectance of common materials](https://forum.corona-renderer.com/index.php/topic,2359.msg17366.html)
- [CGarchitect / Chaos: 15 tips for photorealistic rendering](https://cgconnect.chaos.com/features/articles/6ae07fc2-photorealistic-architectural-rendering-15-tips-to-follow?from=cgarchitect)
- [Chaos: 5 lighting tips](https://www.chaos.com/blog/5-lighting-tips-for-photorealistic-renders)
- [Blender 3D Architect: realism tips](https://www.blender3darchitect.com/light-and-rendering/tips-to-improve-realism-in-rendering)
- [DesignBlendz: photorealistic rendering tips](https://www.designblendz.com/blog/10-tips-to-improve-photo-realistic-rendering)
- [The Rookies: creating realistic interior renders](https://discover.therookies.co/2018/12/10/creating-realistic-interior-renders/)
- [Studio Matrx: textures and real-world scale](https://www.studiomatrx.org/students/real-time-vr-for-architecture/textures-uvs-and-real-world-scale)
- [Polycount: texel density reference](https://polycount.com/discussion/217178/texel-density-texture-map-resolutions-reference-sheet)
- [Ronen Bekerman: cloth modelling with Marvelous Designer](https://www.ronenbekerman.com/3d-cloth-modeling-with-marvelous-designer/)
- [Lester Banks: modelling bedding](https://lesterbanks.com/tag/how-to-model-and-render-bedding-with-marvelous-designer/)
- [Digital Photography School: mixed lighting in interiors](https://digital-photography-school.com/photographing-mixed-lighting-interiors/)
- [SLR Lounge: mixing daylight and tungsten](https://www.slrlounge.com/?p=226103)
- Assets: [Poly Haven](https://polyhaven.com) (CC0) and [ambientCG](https://ambientcg.com) (CC0). Your book models from Sketchfab were unpacked but not used: your real spines photographed better.
