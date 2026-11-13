#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Krasnoyarsk Map Generator — DayZ 1.30 community map project.

Generates everything Terrain Builder (DayZ Tools) needs for a NEW 12 x 12 km
stylized map of Krasnoyarsk (Yenisey in the middle, Tatyshev island, Stolby
ridge in the south-east, Emelyanovo airport in the north-west):

  source/heightmap.asc      — Esri ASCII Grid (north row first), import into Terrain Builder
  source/heightmap.png      — 16-bit grayscale heightmap (backup / inspection)
  source/satmask.png        — 4096x4096 surface mask (layer colours, see layers.cfg)
  source/satmap.png         — 4096x4096 stylised satellite texture
  source/maplegend.png      — legend of mask colours
  source/layers.cfg         — Terrain Builder layer definitions (template)
  docs/09-coordinates.md    — generated table of POIs (X / Z / elevation)
  previews/relief.png       — shaded relief + contours + labels
  previews/satellite.png    — satmap with labels
  previews/mask.png         — surface mask preview

The generator is deterministic (fixed seeds). Requires: numpy, pillow, matplotlib.

World units are METRES. Local map coordinates: x = east (0..12288),
y = north (0..12288). In-game these become CfgWorld coordinates directly.
Terrain Builder project settings must use easting=200000 / northing=0
(standard for Bohemia tools; the 200000 offset is stripped on export).
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# ----------------------------------------------------------------------------- config
WORLD_M = 12288          # world size, metres (2048 cells * 6 m)
GRID = 2048              # heightmap samples per side
CELL = WORLD_M / GRID    # 6.0 m
MASK_PX = 4096           # satmask / satmap resolution
M2PX = MASK_PX / WORLD_M # mask pixels per metre

ELEV_MIN, ELEV_MAX = -4.0, 235.0   # metres; water plane is at z = 0
WATER_LEVEL = 0.0
SEED = 20260611

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source")
PREV = os.path.join(ROOT, "previews")
DOCS = os.path.join(ROOT, "docs")
for d in (SRC, PREV, DOCS):
    os.makedirs(d, exist_ok=True)

# ----------------------------------------------------------------------------- noise

def value_noise(shape, cell, seed):
    """Smoothed value noise in [0, 1], lattice spacing `cell` samples."""
    rng = np.random.default_rng(seed)
    h, w = shape
    gh, gw = h // cell + 3, w // cell + 3
    lattice = rng.random((gh, gw))
    ys = np.arange(h) / cell
    xs = np.arange(w) / cell
    yi, xi = ys.astype(np.int64), xs.astype(np.int64)
    yf, xf = ys - yi, xs - xi
    sy = yf * yf * (3.0 - 2.0 * yf)
    sx = xf * xf * (3.0 - 2.0 * xf)
    a00 = lattice[np.ix_(yi, xi)]
    a01 = lattice[np.ix_(yi, xi + 1)]
    a10 = lattice[np.ix_(yi + 1, xi)]
    a11 = lattice[np.ix_(yi + 1, xi + 1)]
    top = a00 + (a01 - a00) * sx[np.newaxis, :]
    bot = a10 + (a11 - a10) * sx[np.newaxis, :]
    return top + (bot - top) * sy[:, np.newaxis]

def fbm(shape, seed, octaves=6, base_cell=256):
    total = np.zeros(shape)
    amp, norm, cell = 1.0, 0.0, base_cell
    for i in range(octaves):
        c = max(4, cell >> i)
        total += amp * value_noise(shape, c, seed + 101 * i)
        norm += amp
        amp *= 0.5
    return total / norm

# ----------------------------------------------------------------------------- geometry helpers

def river_center_x(y):
    """Easting of the Yenisey centre line at northing y (metres)."""
    yc = np.asarray(y, dtype=np.float64)
    return (6144.0
            + 700.0 * np.sin(yc * 2 * np.pi / 5200.0 + 0.6)
            + 250.0 * np.sin(yc * 2 * np.pi / 2100.0 + 2.0))

def river_half_width(y):
    yc = np.asarray(y, dtype=np.float64)
    return 300.0 + 120.0 * np.sin(yc * 2 * np.pi / 3400.0 + 1.2) + 40.0 * np.sin(yc * 2 * np.pi / 1300.0 + 0.4)

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def gauss2(X, Y, cx, cy, sigma):
    return np.exp(-(((X - cx) ** 2 + (Y - cy) ** 2) / (2.0 * sigma ** 2)))

def polyline_resample(points, step=10.0):
    pts = np.array(points, dtype=np.float64)
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        seg = b - a
        length = np.hypot(*seg)
        if length < 1e-6:
            continue
        n = max(1, int(length / step))
        for i in range(1, n + 1):
            out.append(a + seg * (i / n))
    return np.array(out)

def dist_to_points(X, Y, pts):
    """Min distance from each (X, Y) to point set pts (Nx2). Chunked over points."""
    d2 = np.full(X.shape, np.inf)
    for p in pts:
        d2 = np.minimum(d2, (X - p[0]) ** 2 + (Y - p[1]) ** 2)
    return np.sqrt(d2)

def rounded_square_dist(X, Y, cx, cy, half, corner):
    qx = np.abs(X - cx) - (half - corner)
    qy = np.abs(Y - cy) - (half - corner)
    ax, ay = np.maximum(qx, 0.0), np.maximum(qy, 0.0)
    return np.hypot(ax, ay) + np.minimum(np.maximum(qx, qy), 0.0) - corner

# ----------------------------------------------------------------------------- layout (world metres, x east / y north)
ROADS = [
    # name, width m, points  (left bank)
    ("pr_Mira",            11, [(5880, 6520), (5100, 6300), (4300, 6050), (3500, 5750), (2600, 5400), (1700, 5050)]),
    ("ul_PartizanaZhel",    9, [(5230, 7650), (5220, 6900), (5200, 6200), (5050, 5400), (4850, 4700), (4600, 4150)]),
    ("ul_Lenina",           9, [(5750, 5760), (4900, 5550), (4100, 5300), (3300, 5100), (2400, 4750)]),
    ("ul_Surikova",         7, [(4650, 6900), (4600, 6100), (4550, 5300), (4500, 4600)]),
    ("trassa_R255",        12, [(4300, 6050), (3300, 6650), (2300, 7350), (1500, 8250), (800, 9300), (120, 10350)]),
    ("severnoe_shosse",     9, [(5400, 8450), (5300, 7550), (5200, 7000)]),
    # bridges & crossings
    ("bridge_oktyabrskiy", 12, [(5410, 8445), (5920, 8485)]),
    ("bridge_kommunalny",  14, [(5700, 6530), (6180, 6545), (6540, 6555), (6720, 6560), (7290, 6565)]),
    ("bridge_tatyshev_w",   8, [(6340, 5510), (6565, 5512)]),
    ("bridge_tatyshev_e",   8, [(7155, 6300), (7400, 6300)]),
    # right bank
    ("pr_KrasnoyarskiyRabochy", 11, [(6650, 7900), (6720, 7000), (6760, 6620), (7410, 6400), (7440, 6050), (7050, 5520), (6920, 4600), (7000, 3800), (7050, 3000)]),
    ("pr_Svobodny",        10, [(6780, 6300), (7700, 6150), (8600, 6000), (9500, 5800)]),
    ("ul_9Maya",           10, [(6900, 4550), (7900, 4350), (8900, 4100), (9900, 3800)]),
    ("pr_Mayakovskogo",     9, [(8300, 7600), (8380, 6500), (8460, 5500), (8530, 4500), (8600, 3300)]),
    ("trassa_R257_se",     12, [(7050, 3000), (7400, 1900), (7900, 900), (8400, 120)]),
    ("severo_vostochnaya",  9, [(6650, 7900), (7300, 8450), (8100, 8950), (9000, 9350), (10100, 9700)]),
    # dirt tracks
    ("track_stolby",        5, [(9900, 3800), (9400, 2800), (8900, 2100), (8400, 1600)]),
    ("track_lake",          5, [(4300, 6050), (4100, 6900), (3900, 7600), (3750, 8030)]),
]
RAIL_LINE = [(0, 3920), (2400, 3905), (4300, 3880), (4600, 3875), (7800, 3830), (9800, 3720), (12288, 3560)]

URBAN = [  # (name, polygon)
    ("levo_centr",   [(4400, 5300), (5800, 5300), (5860, 6250), (5700, 6650), (5450, 6900), (4400, 6800)]),
    ("levo_yug",     [(4300, 4480), (5850, 4480), (5860, 5300), (4350, 5300)]),
    ("levo_sever",   [(4600, 6900), (5550, 6900), (5400, 7950), (4650, 7950)]),
    ("pravo_indust", [(6600, 4870), (7700, 4700), (7750, 5750), (7020, 5630)]),
    ("pravo_sovetsky", [(7480, 5660), (8700, 5550), (9100, 6400), (8500, 7150), (7420, 6980)]),
    ("pravo_sever",  [(6720, 7000), (7620, 7100), (7700, 8000), (6680, 7950)]),
]

BUNKERS = [  # name, x, y, half-size, corner radius, depth
    ("B1_Stolby",      8400, 1600, 13, 4, 4.0),
    ("B2_Zavodskoy",   8080, 2560, 12, 4, 3.5),
    ("B3_Emelyanovo",  3310, 8660, 12, 4, 3.5),
]

PILLARS = [  # Stolby rock pillars: x, y, radius m, extra height m
    (9120, 320, 85, 26),
    (9560, 780, 120, 34),
    (10100, 1150, 95, 22),
    (10650, 1620, 130, 38),
    (11150, 2150, 90, 24),
    (11750, 2680, 105, 30),
    (8810, 150, 60, 18),
]

LAKES = [  # noisy-edge lakes: name, cx, cy, radius
    ("Severnoe", 3750, 8050, 235),
]
KACHA = [(12288, 9120), (11700, 9050), (11150, 8900), (10600, 8780), (10050, 8705), (9550, 8565), (9050, 8520), (8500, 8565), (8000, 8600), (7450, 8585), (6880, 8565), (6300, 8570), (5735, 8562)]

# ----------------------------------------------------------------------------- elevation field
print("[1/7] building elevation grid", flush=True)
N = GRID
yy = (np.arange(N) + 0.5) * CELL          # array row 0 = south
xx = (np.arange(N) + 0.5) * CELL
X, Y = np.meshgrid(xx, yy)                # shapes (N, N)

noise_big = fbm((N, N), SEED, octaves=6, base_cell=256)
noise_mid = fbm((N, N), SEED + 500, octaves=5, base_cell=96)
noise_fin = fbm((N, N), SEED + 900, octaves=4, base_cell=24)

elev = 8.6 + (noise_big - 0.5) * 3.4 + (noise_mid - 0.5) * 1.6 + (noise_fin - 0.5) * 0.5

# Yemelyanovo plateau (NW) and a smaller NE hill
elev += 30.0 * gauss2(X, Y, 2650, 9350, 2050)
elev += 13.0 * gauss2(X, Y, 10150, 8850, 1750)

# south-east steppe shoulder (slightly higher dry ground west of the ridge)
elev += 6.0 * gauss2(X, Y, 7600, 4200, 1600)

# --- Stolby ridge (SE): distance to ridge axis polyline
ridge_axis = polyline_resample([(7900, -200), (9000, 350), (10150, 950), (11350, 1750), (12400, 2550)], 25.0)
d_ridge = dist_to_points(X, Y, ridge_axis)
ridge_noise = fbm((N, N), SEED + 77, octaves=4, base_cell=128)
ridge_profile = np.clip(1.0 - d_ridge / 1950.0, 0.0, 1.0) ** 1.55
elev += ridge_profile * (88.0 + 78.0 * ridge_noise)

# rock pillars on the ridge
for px, py, pr, ph in PILLARS:
    d = np.hypot(X - px, Y - py)
    elev += ph * np.cos(d / pr * np.pi / 2.0) ** 2.0 * (d < pr)

# --- Yenisey carve
cx = river_center_x(Y)
half_w = river_half_width(Y)
d_river = np.abs(X - cx)
t = d_river / half_w
cut = 1.0 - smoothstep(0.60, 1.0, t)                  # 1 deep inside -> 0 at bank
bed = -3.1 + 1.6 * t ** 2
elev = elev * (1.0 - cut) + bed * cut

# Tatyshev island: elongated noisy island on the axis
isl_y0, isl_y1 = 5120.0, 7010.0
isl_phase = (Y - isl_y0) / (isl_y1 - isl_y0)
in_isl_y = (isl_phase > 0.0) & (isl_phase < 1.0)
isl_half = 165.0 * np.sin(np.pi * np.clip(isl_phase, 0, 1)) ** 0.72
isl_d = d_river / np.maximum(isl_half, 1e-6)
isl_mask = (1.0 - smoothstep(0.62, 1.0, isl_d)) * in_isl_y
island_elev = 1.9 + (noise_fin - 0.5) * 1.5 + (noise_mid - 0.5) * 1.0
elev = elev * (1.0 - isl_mask) + island_elev * isl_mask

# --- Kacha river carve (small, from the east edge)
kacha_pts = polyline_resample(KACHA, 10.0)
kregion_rows = np.where((yy > 8400) & (yy < 8950))[0]
if len(kregion_rows):
    subX = X[kregion_rows]
    subY = Y[kregion_rows]
    d_k = dist_to_points(subX, subY, kacha_pts)
    khalf = 44.0
    kt = d_k / khalf
    kcut = 1.0 - smoothstep(0.35, 1.0, kt)
    kbed = -2.6 + 1.0 * kt ** 2
    elev[kregion_rows] = elev[kregion_rows] * (1.0 - kcut) + kbed * kcut

# --- lakes
for lname, lx, ly, lr in LAKES:
    lf = noise_fin  # reuse fine noise for ragged shorelines
    d_l = np.hypot(X - lx, Y - ly) * (1.0 + 0.30 * (lf - 0.5) * 2.0)
    lcut = 1.0 - smoothstep(lr * 0.55, lr * 1.02, d_l)
    lbed = -2.8 + 1.7 * (d_l / lr) ** 2
    elev = elev * (1.0 - lcut) + lbed * lcut

# --- bunker depressions (flat-bottomed pits)
prepit = elev.copy()
for bname, bx, by, half, corner, depth in BUNKERS:
    d = rounded_square_dist(X, Y, bx, by, half, corner)
    inside = 1.0 - smoothstep(-4.0, 3.0, d)          # flat floor inside, smooth apron outside
    floor_h = prepit[int((by) / CELL), int((bx) / CELL)] - depth
    elev = elev * (1.0 - inside) + floor_h * inside

# final clamp
elev = np.clip(elev, ELEV_MIN, ELEV_MAX)
print(f"   min={elev.min():.2f} m  max={elev.max():.2f} m  water cells={(elev < 0).sum()}", flush=True)

# ----------------------------------------------------------------------------- surface mask
print("[2/7] painting surface mask", flush=True)
MASK = {  # name -> RGB
    "grass":    (0, 255, 0),
    "drygrass": (240, 230, 60),
    "dirt":     (150, 75, 0),
    "asphalt":  (60, 60, 60),
    "concrete": (170, 170, 170),
    "sand":     (235, 220, 160),
    "rock":     (128, 100, 90),
    "forest":   (0, 120, 60),
    "gravel":   (110, 110, 130),
}
SCL = M2PX
def W(v):  # world metres -> mask px (y flipped: image row 0 = north)
    return v * SCL
def PY(y):
    return MASK_PX - y * SCL

mask = Image.new("RGB", (MASK_PX, MASK_PX), MASK["grass"])
mdraw = ImageDraw.Draw(mask)
rng = np.random.default_rng(SEED + 3000)

def draw_poly(draw, pts, fill, width=0):
    p = [(W(x), PY(y)) for x, y in pts]
    if width:
        draw.line(p + [p[0]], fill=fill, width=int(width * SCL), joint="curve")
    else:
        draw.polygon(p, fill=fill)

# dry steppe patches (south-east lowlands & scattered)
for _ in range(90):
    cxp = rng.uniform(6800, 12288) if rng.random() < 0.7 else rng.uniform(0, 12288)
    cyp = rng.uniform(0, 5600)
    rx, ry = rng.uniform(180, 700), rng.uniform(120, 480)
    p = [((cxp + rx * math.cos(a)) * SCL, PY(cyp + ry * math.sin(a))) for a in np.linspace(0, 2 * np.pi, 18)]
    mdraw.polygon(p, fill=MASK["drygrass"])

# forest blobs (taiga), avoiding urban polygons & water
urban_polys = [p for _, p in URBAN]
def in_poly(px, py, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def far_from_river(px, py, margin):
    return abs(px - river_center_x(py)) > river_half_width(py) + margin

for _ in range(420):
    px, py = rng.uniform(0, WORLD_M), rng.uniform(0, WORLD_M)
    if not far_from_river(px, py, 120):
        continue
    if any(in_poly(px, py, p) for p in urban_polys):
        continue
    if gauss2(px, py, 2650, 9350, 1500) > 0.55:   # keep airport area open
        continue
    r = rng.uniform(90, 420)
    nverts = 14
    rr = r * (0.65 + 0.7 * rng.random(nverts))
    p = [((px + rr[k] * math.cos(a)) * SCL, PY(py + rr[k] * math.sin(a)))
         for k, a in enumerate(np.linspace(0, 2 * np.pi, nverts, endpoint=False))]
    mdraw.polygon(p, fill=MASK["forest"])

# rock where high / steep
elev_big = np.flipud(np.array(Image.fromarray(elev.astype(np.float32), mode="F").resize((MASK_PX, MASK_PX))))
rock = elev_big > 42.0
rock_img = np.zeros((MASK_PX, MASK_PX, 3), dtype=np.uint8)
rock_img[rock] = MASK["rock"]
rock_layer = Image.fromarray(rock_img)
mask.paste(rock_layer, (0, 0), Image.fromarray((rock * 255).astype(np.uint8)))

# sand near water level (shoreline ring) — apply before roads so roads cross over
shore = (elev_big > 0.0) & (elev_big < 1.35)
sand_img = np.zeros((MASK_PX, MASK_PX, 3), dtype=np.uint8)
sand_img[shore] = MASK["sand"]
mask.paste(Image.fromarray(sand_img), (0, 0), Image.fromarray((shore * 255).astype(np.uint8)))

# urban concrete polygons
for uname, upoly in URBAN:
    draw_poly(mdraw, upoly, MASK["concrete"])

# industrial gravel yards
draw_poly(mdraw, [(7250, 3150), (8450, 3050), (8550, 3950), (7350, 4050)], MASK["gravel"])
draw_poly(mdraw, [(6700, 5050), (7550, 4880), (7620, 5450), (6750, 5550)], MASK["gravel"])

# rail corridor (gravel)
draw_poly(mdraw, RAIL_LINE, MASK["gravel"], width=9)

# roads: dirt tracks first, then asphalt
for rname, rw, rpts in ROADS:
    if rname.startswith("track"):
        draw_poly(mdraw, rpts, MASK["dirt"], width=rw)
for rname, rw, rpts in ROADS:
    if not rname.startswith("track"):
        draw_poly(mdraw, rpts, MASK["asphalt"], width=rw)

# bridges are asphalt already via ROADS (bridge_* entries) — but paint parapet hint lines
for bname in ("bridge_oktyabrskiy", "bridge_kommunalny"):
    pts = next(p for n, _, p in ROADS if n == bname)
    draw_poly(mdraw, pts, MASK["concrete"], width=2)

# airport: runway + taxiway + apron (rotated rectangle, heading ~28 deg)
def rot_rect(cx, cy, length, width, angle_deg):
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    hl, hw = length / 2, width / 2
    return [(cx - ux * hl - vx * hw, cy - uy * hl - vy * hw),
            (cx + ux * hl - vx * hw, cy + uy * hl - vy * hw),
            (cx + ux * hl + vx * hw, cy + uy * hl + vy * hw),
            (cx - ux * hl + vx * hw, cy - uy * hl + vy * hw)]

mdraw.polygon([(W(x), PY(y)) for x, y in rot_rect(2500, 9400, 2400, 65, 28)], fill=MASK["asphalt"])
mdraw.polygon([(W(x), PY(y)) for x, y in rot_rect(2750, 9625, 1350, 18, 28)], fill=MASK["asphalt"])  # taxiway
mdraw.polygon([(W(x), PY(y)) for x, y in rot_rect(3120, 9750, 520, 260, 28)], fill=MASK["concrete"])  # apron

# bunker pit floors
for bname, bx, by, half, corner, depth in BUNKERS:
    mdraw.rectangle([W(bx - half), PY(by + half), W(bx + half), PY(by - half)], fill=MASK["dirt"])

mask.save(os.path.join(SRC, "satmask.png"))
del mask, mdraw, rock_img, rock_layer, sand_img
import gc; gc.collect()

# ----------------------------------------------------------------------------- satellite texture
print("[3/7] painting satmap", flush=True)
rng2 = np.random.default_rng(SEED + 77)
noise_tex_lo = fbm((512, 512), SEED + 1234, octaves=5, base_cell=64)
noise_tex = np.array(Image.fromarray((noise_tex_lo * 255).astype(np.uint8)).resize((MASK_PX, MASK_PX), Image.BICUBIC), dtype=np.float32) / 255.0
noise_tex2_lo = fbm((512, 512), SEED + 4321, octaves=4, base_cell=48)
noise_tex2 = np.array(Image.fromarray((noise_tex2_lo * 255).astype(np.uint8)).resize((MASK_PX, MASK_PX), Image.BICUBIC), dtype=np.float32) / 255.0
steppe_lo = fbm((256, 256), SEED + 999, octaves=3, base_cell=48)
steppe = np.array(Image.fromarray((steppe_lo * 255).astype(np.uint8)).resize((MASK_PX, MASK_PX), Image.BICUBIC), dtype=np.float32) / 255.0

sat = np.zeros((MASK_PX, MASK_PX, 3), dtype=np.float32)
taiga_dark = np.array([44, 68, 43], np.float32)
taiga_light = np.array([63, 88, 55], np.float32)
steppe_col = np.array([82, 88, 54], np.float32)
t = noise_tex[..., None]
sat[:] = taiga_dark * (1 - t) + taiga_light * t
sy1 = (np.arange(MASK_PX, dtype=np.float32) / MASK_PX)[:, None]   # row 0 = north
sx1 = (np.arange(MASK_PX, dtype=np.float32) / MASK_PX)[None, :]
steppe_region = np.clip((0.52 - sy1) * 2.2, 0.15, 1.0) * np.clip((sx1 - 0.30) * 2.0, 0.15, 1.0)
step_mix = (smoothstep(0.60, 0.76, steppe) * steppe_region)[..., None]
del sy1, sx1, steppe_region
sat = sat * (1 - step_mix) + steppe_col * step_mix

# fields (rotated translucent rectangles) outside urban areas
fields = [(6200, 3000, 900, 500, 12, (95, 96, 56)), (2500, 3500, 1100, 620, -8, (106, 108, 62)),
          (9000, 7400, 850, 480, 20, (88, 96, 52)), (11000, 6200, 700, 420, -15, (99, 101, 58)),
          (1500, 6500, 760, 430, 30, (92, 99, 55)), (5200, 9200, 800, 500, -25, (104, 106, 60))]
def blend_rect(img_arr, poly_px, color, alpha):
    lay = Image.new("RGB", img_arr.size, color)
    m = Image.new("L", img_arr.size, 0)
    ImageDraw.Draw(m).polygon(poly_px, fill=int(255 * alpha))
    img_arr.paste(lay, (0, 0), m)

sat_img = Image.fromarray(sat.astype(np.uint8))
for fx, fy, fl, fw, fa, fc in fields:
    blend_rect(sat_img, [(W(x), PY(y)) for x, y in rot_rect(fx, fy, fl, fw, fa)], fc, 0.55)
sat = np.asarray(sat_img, dtype=np.float32)

sat_img = Image.fromarray(np.clip(sat, 0, 255).astype(np.uint8))
sdraw = ImageDraw.Draw(sat_img, "RGBA")

# island park detail
for _ in range(240):
    a = rng2.uniform(0, 2 * np.pi)
    rr = math.sqrt(rng2.uniform(0, 1))
    iy = rng2.uniform(5150, 6970)
    ix = river_center_x(iy) + math.cos(a) * rr * 150
    iy2 = river_center_x(iy) * 0 + iy
    if abs(ix - river_center_x(iy2)) < 135 * np.sin(np.pi * (iy2 - 5120) / (7010 - 5120)) ** 0.72:
        rdot = rng2.uniform(2.5, 6.5)
        sdraw.ellipse([W(ix) - rdot, PY(iy2) - rdot, W(ix) + rdot, PY(iy2) + rdot], fill=(52, 84, 44, 255))

# urban blocks: warm gray base + subtle block mosaic
for uname, upoly in URBAN:
    pts = [(W(x), PY(y)) for x, y in upoly]
    base_c = tuple(int(c) for c in (168, 160, 148))
    sdraw.polygon(pts, fill=base_c + (255,))
    # block grid: jittered internal lines
    xs_ = [p[0] for p in upoly]; ys_ = [p[1] for p in upoly]
    x0, x1, y0, y1 = min(xs_), max(xs_), min(ys_), max(ys_)
    gx = x0 + 60 * SCL
    while gx < x1:
        sdraw.line([(gx, y0), (gx, y1)], fill=(148, 140, 130, 120), width=1)
        gx += 130 * SCL * rng2.uniform(0.8, 1.35)
    gy = y0 + 60 * SCL
    while gy < y1:
        sdraw.line([(x0, gy), (x1, gy)], fill=(148, 140, 130, 120), width=1)
        gy += 130 * SCL * rng2.uniform(0.8, 1.35)

def draw_poly_rgba(draw, pts, fill_rgba, width=0):
    p = [(W(x), PY(y)) for x, y in pts]
    if width:
        draw.line(p, fill=fill_rgba, width=max(1, int(width * SCL)), joint="curve")
    else:
        draw.polygon(p, fill=fill_rgba)

# industrial yards darker
draw_poly_rgba(sdraw, [(7250, 3150), (8450, 3050), (8550, 3950), (7350, 4050)], (128, 124, 116, 255))
draw_poly_rgba(sdraw, [(6700, 5050), (7550, 4880), (7620, 5450), (6750, 5550)], (128, 124, 116, 255))

# water re-painted on top of city/industrial so no land polygon covers the river
sat_arr = np.asarray(sat_img, dtype=np.float32)
water_big = elev_big < 0.0
depth = np.clip(-elev_big, 0, 3) / 3.0
shore_c = np.array([58, 84, 96], np.float32)
deep_c = np.array([36, 57, 68], np.float32)
water_col = shore_c * (1 - depth[..., None]) + deep_c * depth[..., None]
sat_arr[water_big] = water_col[water_big]
sat_arr[shore & ~water_big] = np.array([132, 128, 101], np.float32)
sat_img = Image.fromarray(np.clip(sat_arr, 0, 255).astype(np.uint8))
sdraw = ImageDraw.Draw(sat_img, "RGBA")

# roads on satmap: dark asphalt + faint centre dashes on arterials
for rname, rw, rpts in ROADS:
    if rname.startswith("track"):
        continue
    draw_poly_rgba(sdraw, rpts, (74, 70, 63, 255), width=max(rw - 3, 4))
for rname, rw, rpts in ROADS:
    if rname.startswith("track") or "bridge" in rname:
        continue
    draw_poly_rgba(sdraw, rpts, (196, 191, 176, 160), width=1)

# railway with ties
draw_poly_rgba(sdraw, RAIL_LINE, (104, 102, 98, 255), width=5)
rail_pts = polyline_resample(RAIL_LINE, 26.0)
rail_dir_step = 1
for i in range(0, len(rail_pts) - 1, 1):
    x0, y0 = rail_pts[i]
    x1, y1 = rail_pts[min(i + 1, len(rail_pts) - 1)]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-3:
        continue
    nx, ny = -dy / L, dx / L
    sdraw.line([(W(x0 - nx * 4), PY(y0 - ny * 4)), (W(x0 + nx * 4), PY(y0 + ny * 4))], fill=(40, 40, 40, 200), width=2)

# bridges slightly lighter with parapet lines
for bname in ("bridge_oktyabrskiy", "bridge_kommunalny", "bridge_tatyshev_w", "bridge_tatyshev_e"):
    pts = next(p for n, _, p in ROADS if n == bname)
    draw_poly_rgba(sdraw, pts, (122, 118, 108, 255), width=9)

# Stolby rock texture on high ground
rock_mix = smoothstep(0.45, 0.8, elev_big / 150.0)[..., None]
rock_base = np.array([104, 97, 88], np.float32)
rock_dark = np.array([66, 60, 54], np.float32)
rock_tex = rock_base * (1 - noise_tex[..., None]) + rock_dark * noise_tex[..., None]
sat_arr = np.asarray(sat_img, dtype=np.float32)
sat_arr = sat_arr * (1 - rock_mix) + rock_tex * rock_mix
sat_img = Image.fromarray(np.clip(sat_arr, 0, 255).astype(np.uint8))
sdraw = ImageDraw.Draw(sat_img, "RGBA")

# apron / runway
def poly_px(pts):
    return [(W(x), PY(y)) for x, y in pts]
for poly, col in [(rot_rect(2500, 9400, 2400, 65, 28), (126, 126, 126, 255)),
                  (rot_rect(2750, 9625, 1350, 18, 28), (118, 118, 118, 255)),
                  (rot_rect(3120, 9750, 520, 260, 28), (96, 96, 96, 255))]:
    sdraw.polygon(poly_px(poly), fill=col)
# runway threshold marks
a = math.radians(28); ux, uy = math.cos(a), math.sin(a)
for end in (-1, 1):
    cxx, cyy = 2500 + ux * 1120 * end, 9400 + uy * 1120 * end
    sdraw.line(poly_px([(cxx - uy * 24, cyy + ux * 24), (cxx + uy * 24, cyy - ux * 24)]), fill=(220, 220, 220, 230), width=6)

# bunker pits
for bname, bx, by, half, corner, depth in BUNKERS:
    sdraw.rectangle([W(bx - half), PY(by + half), W(bx + half), PY(by - half)], fill=(88, 70, 44, 255))
    sdraw.rectangle([W(bx - half * 0.55), PY(by + half * 0.55), W(bx + half * 0.55), PY(by - half * 0.55)], fill=(46, 37, 24, 255))

sat_img.save(os.path.join(SRC, "satmap.png"))
del sat_img, sat, noise_tex, noise_tex2, steppe, step_mix, water_big, water_col, shore, rock_mix, rock_tex
print("   satmap saved", flush=True)

# ----------------------------------------------------------------------------- exports: heightmap + asc
print("[4/7] exporting heightmap", flush=True)
np.set_printoptions(suppress=True)

# Esri ASCII Grid, north row first
asc_path = os.path.join(SRC, "heightmap.asc")
with open(asc_path, "w", encoding="ascii") as f:
    f.write("ncols %d\n" % GRID)
    f.write("nrows %d\n" % GRID)
    f.write("xllcorner 200000\n")
    f.write("yllcorner 0\n")
    f.write("cellsize %.6f\n" % CELL)
    f.write("NODATA_value -9999\n")
    for i in range(GRID - 1, -1, -1):       # north first
        f.write(" ".join("%.3f" % v for v in elev[i]))
        f.write("\n")
print("   asc:", os.path.getsize(asc_path) / 1e6, "MB", flush=True)

# 16-bit PNG backup
norm = (np.clip(elev, ELEV_MIN, ELEV_MAX) - ELEV_MIN) / (ELEV_MAX - ELEV_MIN)
hm16 = (np.flipud(norm) * 65535.0 + 0.5).astype(np.uint16)   # row 0 = north
Image.fromarray(hm16).save(os.path.join(SRC, "heightmap.png"))
with open(os.path.join(SRC, "heightmap.legend.txt"), "w", encoding="utf-8") as f:
    f.write(f"elevation range: {ELEV_MIN} .. {ELEV_MAX} m\n")
    f.write("water level (in-game ocean) = 0.0 m\n")
    f.write("PNG pixel value 0 -> %.3f m ; 65535 -> %.3f m\n" % (ELEV_MIN, ELEV_MAX))
    f.write("cell size: %.4f m ; grid: %d x %d ; world: %d x %d m\n" % (CELL, GRID, GRID, WORLD_M, WORLD_M))

# downscaled float grid for reuse in this process
elev_big2 = np.flipud(np.array(Image.fromarray(elev.astype(np.float32), mode="F").resize((MASK_PX, MASK_PX))))

# ----------------------------------------------------------------------------- maplegend.png
print("[5/7] drawing maplegend", flush=True)
try:
    font_path = fm.findfont("DejaVu Sans", fallback_to_default=True)
except Exception:
    font_path = None
font_big = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default()
font_small = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()

legend_rows = [
    ("grass",    "Grass (meadows / lawns)"),
    ("drygrass", "Dry steppe grass"),
    ("dirt",     "Dirt / gravel roads / pit floors"),
    ("asphalt",  "Asphalt (roads, bridges, runway)"),
    ("concrete", "Concrete (city blocks, pads)"),
    ("sand",     "Sand / shoreline"),
    ("rock",     "Rock (Stolby crags)"),
    ("forest",   "Forest floor (taiga)"),
    ("gravel",   "Gravel (industrial, rail bed)"),
]
lw, lh = 980, 90 + len(legend_rows) * 64 + 40
legend = Image.new("RGB", (lw, lh), (28, 28, 28))
ld = ImageDraw.Draw(legend)
ld.text((30, 22), "Krasnoyarsk map — surface mask legend", fill=(235, 235, 235), font=font_big)
y = 90
for name, desc in legend_rows:
    ld.rectangle([30, y, 110, y + 48], fill=MASK[name], outline=(200, 200, 200))
    ld.text((130, y + 4), f"RGB{MASK[name]}  {name}", fill=(235, 235, 235), font=font_small)
    ld.text((130, y + 28), desc, fill=(170, 170, 170), font=font_small)
    y += 64
legend.save(os.path.join(SRC, "maplegend.png"))

# ----------------------------------------------------------------------------- terrain coordinates doc
print("[6/7] writing docs/09-coordinates.md", flush=True)

def elev_at(x, y):
    ix = int(np.clip(x / CELL, 0, GRID - 1))
    iy = int(np.clip(y / CELL, 0, GRID - 1))
    return float(elev[iy, ix])

pois = [
    ("Центр (левый берег, ул. Ленина / пр. Мира)", 4700, 5700),
    ("Стрелка (устье Качи, исторический центр)", 5900, 8600),
    ("Остров Татышев (парк)", river_center_x(6050), 6050),
    ("Коммунальный мост", 6230, 6555),
    ("Октябрьский мост (северный выезд)", 6110, 8465),
    ("Железнодорожный мост (Транссиб)", river_center_x(3860), 3860),
    ("Мост на Татышев (западный)", 5600, 5520),
    ("Мост на Татышев (восточный)", 6660, 6310),
    ("Правый берег — Промзона (Заводской)", 7200, 5200),
    ("Правый берег — Советский район", 7900, 6300),
    ("Аэропорт Емельяново (ВПП)", 2500, 9400),
    ("Столбы — скала Такмак", 9560, 780),
    ("Столбы — скала Крест", 10650, 1620),
    ("Бункер B1 «Столбы»", 8400, 1600),
    ("Бункер B2 «Заводской»", 8080, 2560),
    ("Бункер B3 «Емельяново»", 3310, 8660),
    ("Озеро Северное", 3750, 8050),
    ("Вокзал Красноярск-Главный (левый берег)", 4300, 3880),
]
with open(os.path.join(DOCS, "09-coordinates.md"), "w", encoding="utf-8") as f:
    f.write("# Координаты ключевых точек карты «Krasnoyarsk»\n\n")
    f.write("Локальные координаты мира, метры. В игре совпадают с координатами в DayZ ")
    f.write("(X = восток, Z = север; Y — высота над уровнем воды).\n\n")
    f.write("| Точка | X | Z | Высота, м |\n|---|---|---|---|\n")
    for name, x, y in pois:
        f.write("| %s | %.0f | %.0f | %.1f |\n" % (name, x, y, elev_at(x, y)))
    f.write("\n## Реки\n\n")
    f.write("- Енисей: русло идёт с юга на север, центр русла `x = 6144 + 700*sin(y*2π/5200 + 0.6) + 250*sin(y*2π/2100 + 2.0)`, ширина ~600–840 м, уровень воды 0.0 м.\n")
    f.write("- Кача: приток с востока, впадает у правого берега `x ≈ 5735, z ≈ 8560`.\n")
    f.write("- Озеро Северное: центр `x = 3750, z = 8050`, радиус ~235 м.\n\n")
    f.write("## Мосты\n\n")
    f.write("- Октябрьский (северный объезд): z ≈ 8450–8480\n")
    f.write("- Коммунальный (центр): z ≈ 6530–6580\n")
    f.write("- Татышев западный: z ≈ 5510–5535 ; Татышев восточный: z ≈ 6300–6315\n")
    f.write("- Железнодорожный (Транссиб): z ≈ 3830–3920 (насыпь/мост)\n\n")
    f.write("## Бункерные углубления (выемки в рельефе)\n\n")
    for bname, bx, by, half, corner, depth in BUNKERS:
        f.write("- **%s**: центр `x = %.0f, z = %.0f`, яма %.0f×%.0f м, глубина %.1f м, дно `y ≈ %.1f`\n" % (
            bname, bx, by, half * 2, half * 2, depth, elev_at(bx, by)))
    f.write("\n> Как использовать: в World Editor (или при расположении объектов) вводи эти координаты; "
            "при создании префаба бункера высота пола объекта = высота дна ямы.\n")

# ----------------------------------------------------------------------------- previews
print("[7/7] rendering previews", flush=True)

def hillshade(e, cellsize=CELL, az=315.0, alt=45.0):
    dy, dx = np.gradient(e, cellsize)
    slope = np.pi / 2.0 - np.arctan(np.hypot(dx, dy))
    aspect = np.arctan2(-dx, dy)
    azr = np.radians(360.0 - az + 90.0)
    alr = np.radians(alt)
    hs = np.sin(alr) * np.sin(slope) + np.cos(alr) * np.cos(slope) * np.cos(azr - aspect)
    return np.clip(hs, 0, 1)

hs = hillshade(elev)
extent = [0, WORLD_M / 1000, 0, WORLD_M / 1000]

# relief preview
fig, ax = plt.subplots(figsize=(11, 11), dpi=110)
ax.imshow(hs, cmap="gray", extent=extent, origin="lower")
ax.contour(np.arange(N) * CELL / 1000, np.arange(N) * CELL / 1000, elev,
           levels=[25, 50, 75, 100, 125], colors="#d8b56a", linewidths=0.4, alpha=0.7)
axro = ax
axro.contour(np.arange(N) * CELL / 1000, np.arange(N) * CELL / 1000, elev,
           levels=[0.6], colors="#e8e0c8", linewidths=0.7, alpha=0.9)
ax.contourf(np.arange(N) * CELL / 1000, np.arange(N) * CELL / 1000, (elev < 0).astype(float),
            levels=[0.5, 1.5], colors=["#3a5a6c"], alpha=0.9)
ax.set_title("Krasnoyarsk — relief (hillshade + 25 m contours, water at z = 0)", fontsize=11)
ax.set_xlabel("X, km (east)"); ax.set_ylabel("Z, km (north)")
fig.savefig(os.path.join(PREV, "relief.png"), bbox_inches="tight")
plt.close(fig)

# satellite preview with labels
label_items = [
    ("ЦЕНТР", 4.7, 5.7, "white"),
    ("Татышев остров", river_center_x(6050) / 1000, 6050 / 1000, "white"),
    ("Аэропорт Емельяново", 2500 / 1000, 9400 / 1000, "white"),
    ("СТОЛБЫ", 10100 / 1000, 1000 / 1000, "#ffd9a0"),
    ("Советский р-н", 7900 / 1000, 6300 / 1000, "white"),
    ("Промзона", 7200 / 1000, 5200 / 1000, "white"),
    ("Оз. Северное", 3750 / 1000, 8050 / 1000, "white"),
    ("Бункер B1", 8400 / 1000, 1600 / 1000, "#ffb0b0"),
    ("Бункер B2", 8080 / 1000, 2560 / 1000, "#ffb0b0"),
    ("Бункер B3", 3310 / 1000, 8660 / 1000, "#ffb0b0"),
]
fig, ax = plt.subplots(figsize=(12, 12), dpi=100)
ax.imshow(np.asarray(Image.open(os.path.join(SRC, "satmap.png"))), extent=extent, origin="upper")
for text, lx, ly_km, col in label_items:
    ax.text(lx, ly_km, text, color=col, fontsize=9, fontweight="bold",
            ha="center", va="center",
            bbox=dict(facecolor="black", alpha=0.45, edgecolor="none", pad=2))
ax.set_title("Krasnoyarsk — satmap stylised preview", fontsize=12)
ax.set_xlabel("X, km"); ax.set_ylabel("Z, km (north at top)")
fig.savefig(os.path.join(PREV, "satellite.png"), bbox_inches="tight")
plt.close(fig)

# mask preview
fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
ax.imshow(np.asarray(Image.open(os.path.join(SRC, "satmask.png"))), extent=extent, origin="upper")
ax.set_title("Surface mask (colours → layers.cfg)", fontsize=12)
ax.set_xlabel("X, km"); ax.set_ylabel("Z, km")
fig.savefig(os.path.join(PREV, "mask.png"), bbox_inches="tight")
plt.close(fig)

print("done. Outputs in source/ and previews/", flush=True)

# ----------------------------------------------------------------------------- Central Economy spawn configs
print("[8/8] generating CE spawn configs for the mission folder", flush=True)
MISSION = os.path.join(ROOT, "mission", "dayzOffline.krasnoyarsk")
os.makedirs(MISSION, exist_ok=True)
rng3 = np.random.default_rng(SEED + 555)

def elev_at_m(x, y):
    ix = int(np.clip(x / CELL, 0, GRID - 1)); iy = int(np.clip(y / CELL, 0, GRID - 1))
    return float(elev[iy, ix])

def on_land(x, y, margin=0.4):
    return elev_at_m(x, y) > margin

road_pts = []
for rname, rw, rpts in ROADS:
    if rname.startswith("track"):
        continue
    road_pts += polyline_resample(rpts, 165.0).tolist()
road_pts = [p for p in road_pts if on_land(p[0], p[1])]
rng3.shuffle(road_pts)

def rand_in_poly(poly, tries=40):
    xs_ = [p[0] for p in poly]; ys_ = [p[1] for p in poly]
    for _ in range(tries):
        x, y = rng3.uniform(min(xs_), max(xs_)), rng3.uniform(min(ys_), max(ys_))
        if in_poly(x, y, poly) and on_land(x, y):
            return (x, y)
    return None

urban_polys_l = [p for _, p in URBAN]
loot_pts = []
for poly in urban_polys_l:
    for _ in range(26):
        pt = rand_in_poly(poly)
        if pt:
            loot_pts.append(pt)
industrial_pts = [(7250, 3200), (8000, 3300), (8400, 3500), (7000, 5100), (7300, 5200), (7400, 3800),
                  (2500, 9400), (3200, 9700), (2800, 9050),   # airport area
                  (8400, 1600), (8080, 2560), (3310, 8660)]     # bunkers
truck_pts = road_pts[::4][:26] + industrial_pts
civic_pts = road_pts[1::2][:70]
static_med = industrial_pts[:6] + [(9560, 780), (10100, 1150), (11350, 1750)]
planks = [(7200, 3300), (4500, 3900), (10000, 2600), (2600, 7350), (8400, 120)]

def fmt(x, z):
    return f'x="{x:.3f}" z="{z:.3f}"'

with open(os.path.join(MISSION, "cfgeventspawns.xml"), "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<eventposdef>\n')
    f.write('\t<!-- Auto-generated by tools/generate_terrain.py — positions are on land & on roads. -->\n')
    f.write('\t<!-- Loot: static loot spawns inside urban blocks | Vehicles: on roads/yards | StaticMedDrop: bunkers & industrial -->\n')
    f.write('\t<event name="Loot">\n')
    for x, z in loot_pts:
        f.write(f'\t\t<pos {fmt(x, z)} a="-1.0" />\n')
    f.write('\t</event>\n\t<event name="VehicleCivilianCars">\n')
    for x, z in civic_pts:
        f.write(f'\t\t<pos {fmt(x, z)} a="-1.0" />\n')
    f.write('\t</event>\n\t<event name="VehicleTrucks">\n')
    for x, z in truck_pts:
        if on_land(x, z):
            f.write(f'\t\t<pos {fmt(x, z)} a="-1.0" />\n')
    f.write('\t</event>\n\t<event name="StaticMedDrop">\n')
    for x, z in static_med:
        if on_land(x, z):
            f.write(f'\t\t<pos {fmt(x, z)} a="-1.0" />\n')
    f.write('\t</event>\n\t<event name="ItemWoodenPlanks">\n')
    for x, z in planks:
        if on_land(x, z):
            f.write(f'\t\t<pos {fmt(x, z)} a="-1.0" />\n')
    f.write('\t</event>\n</eventposdef>\n')

# player spawn bubbles: roads + urban edges, kept on land
spawn_candidates = list(road_pts)
for poly in urban_polys_l:
    xs_ = [p[0] for p in poly]; ys_ = [p[1] for p in poly]
    for _ in range(14):
        pt = rand_in_poly(poly)
        if pt:
            spawn_candidates.append(pt)
spawn_candidates += [(3750, 8050), (2500, 9400), (9560, 780), (8060, 2600)]
seen = set()
spawn_pts = []
for p in spawn_candidates:
    key = (round(p[0] / 300), round(p[1] / 300))
    if key in seen:
        continue
    seen.add(key)
    spawn_pts.append(p)
    if len(spawn_pts) >= 120:
        break

with open(os.path.join(MISSION, "cfgplayerspawnpoints.xml"), "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<playerspawnpoints>\n')
    f.write('    <!-- Auto-generated by tools/generate_terrain.py — fresh spawn bubbles on roads/urban/island/loot spots. -->\n')
    f.write('    <fresh>\n        <spawn_params>\n            <min_dist_infected>30.0</min_dist_infected>\n            <max_dist_infected>70.0</max_dist_infected>\n            <min_dist_player>25.0</min_dist_player>\n            <max_dist_player>70.0</max_dist_player>\n            <min_dist_static>0.5</min_dist_static>\n            <max_dist_static>2.0</max_dist_static>\n        </spawn_params>\n')
    f.write('        <generator_params>\n            <grid_density>8</grid_density>\n            <grid_width>40.0</grid_width>\n            <grid_height>40.0</grid_height>\n            <min_dist_static>0.5</min_dist_static>\n            <max_dist_static>2.0</max_dist_static>\n            <min_steepness>-45</min_steepness>\n            <max_steepness>45</max_steepness>\n        </generator_params>\n')
    f.write('        <generator_posbubbles>\n')
    for x, z in spawn_pts:
        f.write(f'            <pos x="{x:.6f}" z="{z:.6f}" />\n')
    f.write('        </generator_posbubbles>\n    </fresh>\n</playerspawnpoints>\n')
print(f"   mission CE files: {len(loot_pts)} loot, {len(civic_pts)} civilian cars, {len(truck_pts)} trucks, {len(spawn_pts)} spawn bubbles", flush=True)
