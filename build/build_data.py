#!/usr/bin/env python3
"""Build the 九州 (China Civ) data files from public data.

The browser code is a fork of usaciv (MIT).  This script writes the same
`web/data/*.json` contracts, but for 31 mainland provincial-level divisions
and ~360 prefecture-level units.

Run:  python3 build/build_data.py [--skip-terrain]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "cache"
OUT = ROOT / "web" / "data"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "build" / "lib"))
from geo import Albers, Shape, ShapeIndex, geojson_rings  # noqa: E402
from hexgrid import HexGrid  # noqa: E402

HEX_RADIUS = 25.0
MARGIN = 200.0
WATER, FOREIGN = -1, -2
LAND, OCEAN, COAST, LAKE = range(4)
FLAT, HILLS, MOUNTAINS, PEAKS = range(4)

PROVINCES = [
    ("110000", "北京", "BJ"), ("120000", "天津", "TJ"), ("130000", "河北", "HE"),
    ("140000", "山西", "SX"), ("150000", "内蒙古", "NM"), ("210000", "辽宁", "LN"),
    ("220000", "吉林", "JL"), ("230000", "黑龙江", "HL"), ("310000", "上海", "SH"),
    ("320000", "江苏", "JS"), ("330000", "浙江", "ZJ"), ("340000", "安徽", "AH"),
    ("350000", "福建", "FJ"), ("360000", "江西", "JX"), ("370000", "山东", "SD"),
    ("410000", "河南", "HA"), ("420000", "湖北", "HB"), ("430000", "湖南", "HN"),
    ("440000", "广东", "GD"), ("450000", "广西", "GX"), ("460000", "海南", "HI"),
    ("500000", "重庆", "CQ"), ("510000", "四川", "SC"), ("520000", "贵州", "GZ"),
    ("530000", "云南", "YN"), ("540000", "西藏", "XZ"), ("610000", "陕西", "SN"),
    ("620000", "甘肃", "GS"), ("630000", "青海", "QH"), ("640000", "宁夏", "NX"),
    ("650000", "新疆", "XJ"),
]
CODE2STATE = {code: i for i, (code, _, _) in enumerate(PROVINCES)}
CODE2ABBR = {code: abbr for code, _, abbr in PROVINCES}
CODE2NAME = {code: name for code, name, _ in PROVINCES}


class ChinaAlbers(Albers):
    def __init__(self):
        super().__init__(lat1=25.0, lat2=47.0, lat0=35.0, lon0=105.0)


def project_factory():
    return ChinaAlbers()


def load_json(path: Path):
    return json.loads(path.read_text())


def shape_of(feature) -> Shape:
    return Shape(geojson_rings(feature["geometry"]))


def project_pts(pts, alb):
    return [alb(lon, lat) for lon, lat in pts]


def ring_area_km2(ring):
    # shoelace on map-km coordinates
    a = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def feature_area_km2(feature, alb):
    area = 0.0
    for ring in geojson_rings(feature["geometry"]):
        area += ring_area_km2(project_pts(ring, alb))
    return area


# --------------------------------------------------------------------------------------
# Terrain tiles (AWS Terrarium, zoom 6)
# --------------------------------------------------------------------------------------

class Terrarium:
    Z = 6

    def __init__(self):
        self.tiles = {}
        self.dir = CACHE / "terrain"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._prepare()

    def tile_range(self):
        def lon2x(lon):
            return int((lon + 180.0) / 360.0 * (2 ** self.Z))

        def lat2y(lat):
            return int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * (2 ** self.Z))

        return lon2x(73), lon2x(136), lat2y(54), lat2y(18)

    def _prepare(self):
        x0, x1, y0, y1 = self.tile_range()
        jobs = []
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                path = self.dir / f"{x}_{y}.png"
                if not path.exists() or path.stat().st_size < 100:
                    jobs.append((x, y, path))
        if jobs:
            print(f"  downloading {len(jobs)} terrarium tiles ...")

            def one(job):
                x, y, path = job
                url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{self.Z}/{x}/{y}.png"
                try:
                    urllib.request.urlretrieve(url, path)
                except Exception as exc:  # keep going; missing tile becomes sea level
                    print("   tile failed", x, y, exc)

            with ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(one, jobs))
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                path = self.dir / f"{x}_{y}.png"
                if path.exists() and path.stat().st_size > 100:
                    self.tiles[(x, y)] = Image.open(path).convert("RGB")

    def elev(self, lon: float, lat: float) -> int:
        n = 2 ** self.Z
        gx = (lon + 180.0) / 360.0 * n * 256
        gy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n * 256
        tx, ty = int(gx // 256), int(gy // 256)
        img = self.tiles.get((tx, ty))
        if img is None:
            return 0
        r, g, b = img.getpixel((int(gx % 256), int(gy % 256)))
        return int(round((r * 256 + g + b / 256) - 32768))


# --------------------------------------------------------------------------------------
# Land cover: an ecoregion model calibrated on published provincial forest/crop shares.
# --------------------------------------------------------------------------------------

DESERT = dict(forest=0.01, crop=0.03, pasture=0.01, grass=0.18, shrub=0.66, wetland=0.01, developed=0.10)
STEPPE = dict(forest=0.02, crop=0.10, pasture=0.04, grass=0.68, shrub=0.10, wetland=0.02, developed=0.04)
PLATEAU = dict(forest=0.05, crop=0.02, pasture=0.08, grass=0.70, shrub=0.10, wetland=0.03, developed=0.02)
NORTHEAST = dict(forest=0.50, crop=0.26, pasture=0.03, grass=0.12, shrub=0.03, wetland=0.03, developed=0.03)
NORTH_PLAIN = dict(forest=0.07, crop=0.62, pasture=0.02, grass=0.12, shrub=0.02, wetland=0.04, developed=0.11)
LOESS = dict(forest=0.10, crop=0.34, pasture=0.03, grass=0.36, shrub=0.11, wetland=0.01, developed=0.05)
YANGTZE = dict(forest=0.18, crop=0.46, pasture=0.02, grass=0.10, shrub=0.03, wetland=0.06, developed=0.15)
SOUTH = dict(forest=0.56, crop=0.20, pasture=0.01, grass=0.07, shrub=0.05, wetland=0.03, developed=0.08)
SOUTHWEST = dict(forest=0.56, crop=0.14, pasture=0.02, grass=0.12, shrub=0.09, wetland=0.02, developed=0.05)
TIBET_VALLEY = dict(forest=0.34, crop=0.08, pasture=0.05, grass=0.38, shrub=0.11, wetland=0.02, developed=0.02)
DEFAULT = dict(forest=0.24, crop=0.24, pasture=0.03, grass=0.26, shrub=0.10, wetland=0.03, developed=0.10)


def base_cover(lon, lat, elev, relief):
    # Deserts of Xinjiang / Hexi / Alxa
    if (75 <= lon <= 92 and 36 <= lat <= 44) or (92 <= lon <= 103 and 37 <= lat <= 42):
        d = dict(DESERT)
    elif (lon < 106 and lat >= 42) or (lon < 100 and lat >= 44):
        d = dict(DESERT if lon < 92 else STEPPE)
    elif 106 <= lon <= 122 and 40 <= lat <= 48:
        d = dict(STEPPE)
    elif elev >= 4300:
        d = dict(PLATEAU)
    elif elev >= 3000 and lon <= 103:
        d = dict(TIBET_VALLEY if relief >= 2 and lon <= 100 else PLATEAU)
    elif lon >= 120 and lat >= 42:
        d = dict(NORTHEAST)
    elif 113 <= lon <= 122 and 32 <= lat <= 41 and elev < 500:
        d = dict(NORTH_PLAIN)
    elif 104 <= lon <= 113 and 33 <= lat <= 41 and elev >= 500:
        d = dict(LOESS)
    elif lat <= 25 and lon >= 108:
        d = dict(SOUTH)
    elif 98 <= lon <= 112 and 21 <= lat <= 33 and elev > 500:
        d = dict(SOUTHWEST)
    elif 117 <= lon <= 123 and 27 <= lat <= 34:
        d = dict(YANGTZE)
    elif lat >= 40:
        d = dict(NORTHEAST if lon > 115 else LOESS)
    else:
        d = dict(DEFAULT)
    return d


def urban_radius(pop):
    if pop is None:
        return 4.0
    # 4 km village → 26 km for a 20M+ megacity
    return max(3.0, min(28.0, 2.5 * math.log10(max(pop, 20000)) - 8.0))


def cell_cover(lon, lat, elev, relief, urban_km, pop):
    d = base_cover(lon, lat, elev, relief)
    r = urban_radius(pop)
    if urban_km < r:
        u = 0.35 + 0.6 * (1 - urban_km / r) ** 0.7
        if pop and pop > 3_000_000:
            u = min(0.92, u + 0.12)
        rest = 1 - u
        tot = sum(d.values()) or 1
        d = {k: v / tot * rest for k, v in d.items()}
        d["developed"] = u
    # Normalise to 100 integer percentage points, largest-remainder style.
    keys = ["forest", "crop", "pasture", "grass", "shrub", "wetland", "developed"]
    vals = [max(0.0, d.get(k, 0.0)) for k in keys]
    total = sum(vals) or 1
    raw = [v / total * 100 for v in vals]
    ints = [int(x) for x in raw]
    rem = 100 - sum(ints)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - ints[i], reverse=True)
    for i in order[:rem]:
        ints[i] += 1
    return dict(zip(keys, ints))


def cover_id(pct, lat):
    if pct["developed"] >= 30:
        return 9
    groups = {
        1: pct["forest"], 4: pct["shrub"], 5: pct["grass"], 6: pct["pasture"],
        7: pct["crop"], 8: pct["wetland"], 10: 0,
    }
    best = max(groups, key=lambda k: groups[k])
    if best == 1:
        if lat >= 40:
            return 3
        if lat <= 30:
            return 2
        return 1
    return best


def relief_class(mean, std):
    if mean >= 4200:
        return PEAKS
    if std >= 450 or mean >= 2500:
        return MOUNTAINS
    if std >= 110:
        return HILLS
    return FLAT


# --------------------------------------------------------------------------------------
# World
# --------------------------------------------------------------------------------------

def build_world(terr: Terrarium | None):
    print("build world ...")
    alb = project_factory()
    country = load_json(CACHE / "datav_china.json")
    prov_features = {}
    for f in country["features"]:
        code = str(f["properties"].get("adcode", ""))
        if code in CODE2STATE:
            prov_features[code] = f
    missing = set(CODE2STATE) - set(prov_features)
    if missing:
        raise SystemExit(f"missing province polygons: {missing}")

    # bbox in projected km
    all_pts = []
    for f in prov_features.values():
        for ring in geojson_rings(f["geometry"]):
            all_pts.extend(project_pts(ring, alb))
    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    width = max_x - min_x + 2 * MARGIN
    height = max_y - min_y + 2 * MARGIN

    def project(lon, lat):
        x, y = alb(lon, lat)
        return x - min_x + MARGIN, max_y - y + MARGIN

    def inverse(x, y):
        return alb.inverse(x + min_x - MARGIN, max_y + MARGIN - y)

    grid = HexGrid.covering(width, height, HEX_RADIUS)
    n = grid.size
    print(f"  map {width:.0f}×{height:.0f} km, grid {grid.cols}×{grid.rows} = {n} cells")

    # Shape indexes in lon/lat degrees (ShapeIndex buckets are arbitrary units).
    prov_shapes, prov_codes = [], []
    for code in CODE2STATE:
        f = prov_features[code]
        prov_shapes.append(shape_of(f))
        prov_codes.append(code)
    prov_idx = ShapeIndex(prov_shapes, cell_km=4.0)

    # city polygons + centres
    city_units = []
    for code, name, abbr in PROVINCES:
        d = load_json(CACHE / "datav" / f"{code}.json")
        feats = [f for f in d["features"] if f["properties"].get("level") == "city"]
        if code in ("110000", "120000", "310000", "500000"):
            feats = []
        if feats:
            for f in feats:
                pr = f["properties"]
                city_units.append({"adcode": str(pr["adcode"]), "name": pr["name"], "prov": code,
                                   "center": pr.get("center") or pr.get("centroid"), "feature": f})
        else:
            pr = prov_features[code]["properties"]
            city_units.append({"adcode": code, "name": name + "市", "prov": code,
                               "center": pr.get("center") or pr.get("centroid"), "feature": prov_features[code]})
    print(f"  {len(city_units)} city polygons")
    city_shapes = [shape_of(u["feature"]) for u in city_units]
    city_idx = ShapeIndex(city_shapes, cell_km=2.0)

    # natural earth land + lakes
    land = ShapeIndex([shape_of(f) for f in load_json(CACHE / "ne_50m_land.geojson")["features"]], cell_km=5.0)
    lake_features = []
    for f in load_json(CACHE / "ne_50m_lakes.geojson")["features"]:
        try:
            s = shape_of(f)
            if s.rings:
                lake_features.append(s)
        except Exception:
            pass
    lakes = ShapeIndex(lake_features, cell_km=2.0)

    # Nearest city centre grid for cells that fall in a gap between polygons (rare).
    city_xy = []
    for u in city_units:
        lon, lat = u["center"]
        city_xy.append(project(lon, lat))
    city_xs = np.array([p[0] for p in city_xy])
    city_ys = np.array([p[1] for p in city_xy])
    province_centers = defaultdict(list)
    for i, u in enumerate(city_units):
        x, y = city_xy[i]
        province_centers[u["prov"]].append((i, x, y))

    owner = [WATER] * n
    county = [-1] * n
    elev = [0] * n
    elev_max = [0] * n
    water = [1] * n
    relief = [FLAT] * n
    cover = [0] * n
    pct = {k: [0] * n for k in ["forest", "crop", "pasture", "grass", "shrub", "wetland", "developed"]}
    cell_ll = [None] * n
    cell_xy = [None] * n
    urban_km = [999.0] * n
    city_pop = {u["adcode"]: None for u in city_units}

    # sample points offsets in map km
    sample_offsets = [(0.0, 0.0)]
    for k in range(6):
        ang = math.radians(60 * k)
        sample_offsets.append((math.cos(ang) * HEX_RADIUS * 0.55, math.sin(ang) * HEX_RADIUS * 0.55))

    for row in range(grid.rows):
        for col in range(grid.cols):
            i = grid.index(col, row)
            cx, cy = grid.center(col, row)
            lon0, lat0 = inverse(cx, cy)
            cell_ll[i] = (lon0, lat0)
            cell_xy[i] = (cx, cy)
            samples = []
            for dx, dy in sample_offsets:
                lo, la = inverse(cx + dx, cy + dy)
                samples.append((lo, la))
            pv = [prov_idx.locate(lo, la) for lo, la in samples]
            china_n = sum(1 for x in pv if x >= 0)
            land_n = china_n
            if china_n < 7:
                land_n += sum(1 for x, (lo, la) in zip(pv, samples) if x < 0 and land.locate(lo, la) >= 0)
            lake_here = lakes.locate(lon0, lat0) >= 0
            if lake_here:
                water[i] = LAKE
                owner[i] = WATER
                elev[i] = 0
                continue
            if land_n >= 4:
                # majority province among China samples; if none, foreign land
                if china_n:
                    counts = Counter(x for x in pv if x >= 0)
                    st = counts.most_common(1)[0][0]
                    owner[i] = st
                else:
                    owner[i] = FOREIGN
                water[i] = LAND
                # county from centre or majority city sample
                ci = city_idx.locate(lon0, lat0)
                if ci < 0 or city_units[ci]["prov"] != PROVINCES[owner[i]][0]:
                    # nearest centre in the same province
                    prov_i = owner[i]
                    if prov_i >= 0:
                        pcode = PROVINCES[prov_i][0]
                        best = None
                        for j, xx, yy in province_centers[pcode]:
                            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                            if best is None or d2 < best[0]:
                                best = (d2, j)
                        ci = best[1] if best else -1
                county[i] = ci
            else:
                owner[i] = WATER
                water[i] = OCEAN

    # coast pass
    for i in range(n):
        if water[i] == LAKE:
            continue
        if owner[i] < 0:
            water[i] = COAST if any(j >= 0 and owner[j] >= 0 for j in grid.neighbours(i)) else OCEAN

    # urban distance and elevation
    print("  sampling elevation and land cover ...")
    for i in range(n):
        if water[i] == LAKE:
            continue
        lon0, lat0 = cell_ll[i]
        cx, cy = cell_xy[i]
        # nearest city centre (vectorised)
        d2 = (city_xs - cx) ** 2 + (city_ys - cy) ** 2
        urban_km[i] = math.sqrt(float(np.min(d2)))
        vals = []
        land_vals = []
        for dx, dy in sample_offsets:
            lo, la = inverse(cx + dx, cy + dy)
            e = terr.elev(lo, la) if terr else max(0, int(200 + (lat0 - 20) * 80))
            vals.append(e)
            idx = prov_idx.locate(lo, la)
            if idx >= 0 or land.locate(lo, la) >= 0:
                land_vals.append(e)
        if owner[i] >= 0:
            use = [v for v in land_vals if v > -100] or land_vals or vals
            mean = sum(use) / len(use)
            elev[i] = int(round(mean))
            elev_max[i] = max(use) if use else 0
            if len(use) > 1:
                std = float(np.std(use))
            else:
                std = 0.0
            relief[i] = relief_class(mean, std)
            c = cell_cover(lon0, lat0, mean, relief[i], urban_km[i], None)
            for k in pct:
                pct[k][i] = c[k]
            cover[i] = cover_id(c, lat0)
        else:
            e = int(round(sum(vals) / len(vals))) if vals else -4000
            elev[i] = e if e < 0 else 0
            elev_max[i] = 0
            relief[i] = FLAT

    # city populations are filled after city stats are built; recalc urban cover there if desired.
    states = [{"fips": code, "abbr": abbr, "name": name} for code, name, abbr in PROVINCES]
    counties = [{"geoid": u["adcode"], "name": u["name"]} for u in city_units]

    # rivers
    rivers = []
    for f in load_json(CACHE / "ne_50m_rivers_lake_centerlines.geojson")["features"]:
        name = f["properties"].get("name") or f["properties"].get("name_en")
        geom = f["geometry"]
        t = geom["type"]
        coords = geom["coordinates"]
        lines = [coords] if t == "LineString" else coords if t == "MultiLineString" else []
        for line in lines:
            pts = [project(lon, lat) for lon, lat in line if 70 <= lon <= 140 and 15 <= lat <= 56]
            if len(pts) < 2:
                continue
            # simplify to 8 km
            simp = [pts[0]]
            for p in pts[1:]:
                if math.dist(p, simp[-1]) >= 8:
                    simp.append(p)
            if len(simp) >= 2:
                rivers.append({"name": name or "河流", "pts": [round(v, 1) for p in simp for v in p]})
    rivers.sort(key=lambda r: len(r["pts"]), reverse=True)
    rivers = rivers[:80]
    for k, r in enumerate(rivers):
        r["rank"] = k + 1

    world = {
        "version": 2,
        "grid": grid.to_dict(),
        "width": round(width, 1), "height": round(height, 1), "margin": MARGIN,
        "owner": owner, "county": county, "elev": elev, "elev_max": elev_max,
        "water": water, "relief": relief, "cover": cover, "pct": pct,
        "tables": {
            "water": [
                {"id": 0, "name": "陆地", "rule": "网格点多数落在国界内或邻国陆地上。"},
                {"id": 1, "name": "海洋", "color": "#173f63", "rule": "不在陆地范围内、且不邻接陆地的水域。"},
                {"id": 2, "name": "近海", "color": "#2b6d96", "rule": "与陆地相邻的浅水。"},
                {"id": 3, "name": "湖泊", "color": "#3a80b0", "rule": "Natural Earth 湖泊多边形内的水域。"},
            ],
            "relief": [
                {"id": 0, "name": "平原", "rule": "格内高程标准差 < 110 米。"},
                {"id": 1, "name": "丘陵", "rule": "标准差 ≥ 110 米。"},
                {"id": 2, "name": "山地", "rule": "标准差 ≥ 450 米，或平均高程 ≥ 2500 米。"},
                {"id": 3, "name": "高原极高山", "rule": "平均高程 ≥ 4200 米（雪线以上）。"},
            ],
            "cover": [
                {"id": 0, "name": "无数据", "color": "#8a8378", "nlcd": [], "rule": "无土地覆盖样本。"},
                {"id": 1, "key": "forest_deciduous", "name": "落叶林", "color": "#5b7d3c", "nlcd": [], "rule": "森林占优，北方温带。"},
                {"id": 2, "key": "forest_evergreen", "name": "常绿林", "color": "#2f5c38", "nlcd": [], "rule": "森林占优，南方亚热带。"},
                {"id": 3, "key": "forest_mixed", "name": "混交林", "color": "#477041", "nlcd": [], "rule": "森林占优，过渡带。"},
                {"id": 4, "key": "scrub", "name": "荒漠灌丛", "color": "#c7ae78", "nlcd": [], "rule": "灌丛/荒漠占优。"},
                {"id": 5, "key": "grassland", "name": "草原", "color": "#a8b25a", "nlcd": [], "rule": "草地占优。"},
                {"id": 6, "key": "pasture", "name": "牧草地", "color": "#8fb04e", "nlcd": [], "rule": "牧草占优。"},
                {"id": 7, "key": "cropland", "name": "耕地", "color": "#c2b84e", "nlcd": [], "rule": "耕地占优。"},
                {"id": 8, "key": "wetland", "name": "湿地", "color": "#4f8a6e", "nlcd": [], "rule": "湿地占优。"},
                {"id": 9, "key": "urban", "name": "城市", "color": "#8a8378", "nlcd": [], "rule": "建设用地 ≥ 30%。"},
                {"id": 10, "key": "barren", "name": "裸地", "color": "#bfae95", "nlcd": [], "rule": "裸岩、沙地占优。"},
                {"id": 11, "key": "ice", "name": "冰雪", "color": "#e8eef2", "nlcd": [], "rule": "常年冰雪。"},
            ],
            "notes": {"cover": "土地覆盖由生态分区模型生成，并用各省森林覆盖率校准；不是逐像元遥感分类。", "relief": "高程取自 AWS Terrarium（Mapzen 地形瓦片，约 2 km 分辨率）。"},
        },
        "states": states,
        "counties": counties,
        "rivers": rivers,
    }
    (OUT / "world.json").write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")))
    print("  world.json", (OUT / "world.json").stat().st_size // 1024, "KB",
          "land cells", sum(1 for x in owner if x >= 0), "water", sum(1 for x in water if x))
    return world, city_units, project, inverse, grid, alb


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-terrain", action="store_true")
    args = ap.parse_args()
    terr = None if args.skip_terrain else Terrarium()
    build_world(terr)
