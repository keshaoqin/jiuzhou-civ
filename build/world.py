#!/usr/bin/env python3
"""Vectorised world builder for 九州."""
from __future__ import annotations

import json
import math
import os
from collections import defaultdict

import numpy as np
from matplotlib.path import Path

from geo import Albers, geojson_rings
from hexgrid import HexGrid
from taiwan import TAIWAN_CITIES

ROOT = None


class ChinaAlbers(Albers):
    def __init__(self):
        super().__init__(lat1=25.0, lat2=47.0, lat0=35.0, lon0=105.0)


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
    ("650000", "新疆", "XJ"), ("710000", "台湾", "TW"),
]
CODE2STATE = {code: i for i, (code, _, _) in enumerate(PROVINCES)}


def _load(path):
    return json.loads(open(path, encoding="utf-8").read())


def _paths(feature, min_lat=-90.0):
    out = []
    for ring in geojson_rings(feature["geometry"]):
        if len(ring) >= 3 and sum(p[1] for p in ring) / len(ring) >= min_lat:
            out.append((Path(np.asarray(ring, dtype=float)), np.min(ring, axis=0), np.max(ring, axis=0)))
    return out


def _contains_any(paths, pts, out=None):
    if out is None:
        out = np.zeros(len(pts), dtype=bool)
    for p, lo, hi in paths:
        sel = (pts[:, 0] >= lo[0]) & (pts[:, 0] <= hi[0]) & (pts[:, 1] >= lo[1]) & (pts[:, 1] <= hi[1])
        if not sel.any():
            continue
        idx = np.nonzero(sel)[0]
        out[idx] |= p.contains_points(pts[idx])
    return out


def relief_class(mean, std):
    if mean >= 4200:
        return PEAKS
    if std >= 450 or mean >= 2500:
        return MOUNTAINS
    if std >= 110:
        return HILLS
    return FLAT


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
    if (75 <= lon <= 92 and 36 <= lat <= 44) or (92 <= lon <= 103 and 37 <= lat <= 42):
        return dict(DESERT)
    if (lon < 106 and lat >= 42) or (lon < 100 and lat >= 44):
        return dict(DESERT if lon < 92 else STEPPE)
    if 106 <= lon <= 115 and 40 <= lat <= 48:
        return dict(STEPPE)
    if elev >= 4300:
        return dict(PLATEAU)
    if elev >= 3000 and lon <= 103:
        return dict(TIBET_VALLEY if relief >= 2 and lon <= 100 else PLATEAU)
    if lon >= 120 and lat >= 42:
        return dict(NORTHEAST)
    if 113 <= lon <= 122 and 32 <= lat <= 41 and elev < 500:
        return dict(NORTH_PLAIN)
    if 104 <= lon <= 113 and 33 <= lat <= 41 and elev >= 500:
        return dict(LOESS)
    if lat <= 25 and lon >= 108:
        return dict(SOUTH)
    if 98 <= lon <= 112 and 21 <= lat <= 33 and elev > 500:
        return dict(SOUTHWEST)
    if 117 <= lon <= 123 and 27 <= lat <= 34:
        return dict(YANGTZE)
    if lat >= 40:
        return dict(NORTHEAST if lon > 115 else LOESS)
    return dict(DEFAULT)


def urban_radius(pop):
    if not pop:
        return 4.0
    return max(3.0, min(28.0, 2.5 * math.log10(max(pop, 20000)) - 8.0))


def cover_pct(lon, lat, elev, relief, urban_km, pop):
    d = base_cover(lon, lat, elev, relief)
    r = urban_radius(pop)
    if urban_km < r:
        u = 0.35 + 0.60 * (1 - urban_km / r) ** 0.7
        if pop and pop > 3_000_000:
            u = min(0.93, u + 0.12)
        rest = 1 - u
        tot = sum(d.values()) or 1
        d = {k: v / tot * rest for k, v in d.items()}
        d["developed"] = u
    keys = ["forest", "crop", "pasture", "grass", "shrub", "wetland", "developed"]
    vals = [max(0.0, d.get(k, 0.0)) for k in keys]
    total = sum(vals) or 1
    raw = [v / total * 100 for v in vals]
    ints = [int(x) for x in raw]
    rem = 100 - sum(ints)
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - ints[i], reverse=True)[:rem]:
        ints[i] += 1
    return dict(zip(keys, ints))


def cover_id(p, lat):
    if p["developed"] >= 30:
        return 9
    groups = {1: p["forest"], 4: p["shrub"], 5: p["grass"], 6: p["pasture"], 7: p["crop"], 8: p["wetland"]}
    best = max(groups, key=lambda k: groups[k])
    if best == 1:
        if lat >= 40:
            return 3
        if lat <= 30:
            return 2
        return 1
    return best


def build_world(terr, cache_dir):
    print("build world ...")
    alb = ChinaAlbers()
    country = _load(cache_dir / "datav_china.json")
    prov_features = {str(f["properties"]["adcode"]): f for f in country["features"]
                     if str(f["properties"].get("adcode", "")) in CODE2STATE}

    all_pts = np.array([alb(lon, lat) for f in prov_features.values() for ring in geojson_rings(f["geometry"])
                        if sum(p[1] for p in ring) / len(ring) >= 17.0 for lon, lat in ring])
    min_x, max_x = float(all_pts[:, 0].min()), float(all_pts[:, 0].max())
    min_y, max_y = float(all_pts[:, 1].min()), float(all_pts[:, 1].max())
    width = max_x - min_x + 2 * MARGIN
    height = max_y - min_y + 2 * MARGIN

    def project(lon, lat):
        x, y = alb(lon, lat)
        return x - min_x + MARGIN, max_y - y + MARGIN

    def inverse(x, y):
        return alb.inverse(x + min_x - MARGIN, max_y + MARGIN - y)

    grid = HexGrid.covering(width, height, HEX_RADIUS)
    n = grid.size
    print(f"  map {width:.0f}x{height:.0f} km, grid {grid.cols}x{grid.rows} = {n} cells")

    # all cell centres and 7 sample points
    centers = np.empty((n, 2))
    samples = np.empty((n, 7, 2))
    offsets = [(0.0, 0.0)] + [(math.cos(math.radians(60 * k)) * HEX_RADIUS * 0.55,
                               math.sin(math.radians(60 * k)) * HEX_RADIUS * 0.55) for k in range(6)]
    for row in range(grid.rows):
        for col in range(grid.cols):
            i = grid.index(col, row)
            cx, cy = grid.center(col, row)
            centers[i] = inverse(cx, cy)
            for k, (dx, dy) in enumerate(offsets):
                samples[i, k] = inverse(cx + dx, cy + dy)
    flat = samples.reshape(-1, 2)

    # province masks
    prov_of_sample = np.full(len(flat), -1, dtype=np.int16)
    unassigned = np.ones(len(flat), dtype=bool)
    for code, st in CODE2STATE.items():
        fp = _paths(prov_features[code], 17.0)
        mask = np.zeros(len(flat), dtype=bool)
        for p, lo, hi in fp:
            sel = unassigned & (flat[:, 0] >= lo[0]) & (flat[:, 0] <= hi[0]) & (flat[:, 1] >= lo[1]) & (flat[:, 1] <= hi[1])
            if sel.any():
                idx = np.nonzero(sel)[0]
                mask[idx] = p.contains_points(flat[idx])
        prov_of_sample[mask] = st
        unassigned &= ~mask

    prov_of_sample = prov_of_sample.reshape(n, 7)
    china_n = (prov_of_sample >= 0).sum(axis=1)
    # foreign land: not China, but inside a Natural Earth land polygon
    land_paths = []
    for f in _load(cache_dir / "ne_50m_land.geojson")["features"]:
        land_paths.extend(_paths(f))
    foreign_mask = np.zeros(len(flat), dtype=bool)
    need = prov_of_sample.reshape(-1) < 0
    idx = np.nonzero(need)[0]
    if len(idx):
        sub = flat[idx]
        m = _contains_any(land_paths, sub)
        foreign_mask[idx[m]] = True
    foreign_mask = foreign_mask.reshape(n, 7)
    land_n = china_n + foreign_mask.sum(axis=1)

    # lakes (only test cell centres)
    lake_mask = np.zeros(n, dtype=bool)
    lake_paths = []
    for f in _load(cache_dir / "ne_50m_lakes.geojson")["features"]:
        lake_paths.extend(_paths(f))
    lake_mask = _contains_any(lake_paths, centers)

    owner = np.full(n, WATER, dtype=np.int16)
    county = np.full(n, -1, dtype=np.int16)
    water = np.full(n, OCEAN, dtype=np.int16)
    for i in range(n):
        if lake_mask[i]:
            water[i] = LAKE
            continue
        if land_n[i] >= 4:
            water[i] = LAND
            if china_n[i]:
                counts = np.bincount(prov_of_sample[i][prov_of_sample[i] >= 0], minlength=len(PROVINCES))
                owner[i] = int(np.argmax(counts))
            else:
                owner[i] = FOREIGN

    # city masks on cell centres
    city_units = []
    for code, name, abbr in PROVINCES:
        if code == "710000":
            # No city-level DataV boundary is published for Taiwan; split the island by
            # nearest city centre, using the province polygon only as a fallback shape.
            for adcode, short, full, lon, lat, pop, gdp, area in TAIWAN_CITIES:
                city_units.append({"adcode": adcode, "name": full, "prov": code, "center": [lon, lat],
                                   "feature": prov_features[code], "special": True, "area_km2": area})
            continue
        d = _load(cache_dir / "datav" / f"{code}.json")
        feats = [f for f in d["features"] if f["properties"].get("level") == "city"]
        if code in ("110000", "120000", "310000", "500000"):
            feats = []
        if feats:
            for f in feats:
                pr = f["properties"]
                ctr = pr.get("center") or pr.get("centroid")
                if ctr and ctr[1] < 17.0:
                    continue
                city_units.append({"adcode": str(pr["adcode"]), "name": pr["name"], "prov": code,
                                   "center": ctr, "feature": f})
        else:
            pr = prov_features[code]["properties"]
            city_units.append({"adcode": code, "name": name + "市", "prov": code,
                               "center": pr.get("center") or pr.get("centroid"), "feature": prov_features[code]})
    print(f"  {len(city_units)} city polygons")
    for ci, u in enumerate(city_units):
        if u.get("special"):
            continue
        sel_owner = owner == CODE2STATE[u["prov"]]
        if not sel_owner.any():
            continue
        pts = centers[sel_owner]
        hit = np.zeros(len(pts), dtype=bool)
        for p, lo, hi in _paths(u["feature"], 17.0):
            sel = (pts[:, 0] >= lo[0]) & (pts[:, 0] <= hi[0]) & (pts[:, 1] >= lo[1]) & (pts[:, 1] <= hi[1])
            if sel.any():
                j = np.nonzero(sel)[0]
                hit[j] = p.contains_points(pts[j])
        county[np.nonzero(sel_owner)[0][hit]] = ci

    # nearest city centre fill
    city_xy = np.array([project(*u["center"]) for u in city_units])
    for st, (code, name, abbr) in enumerate(PROVINCES):
        own = np.nonzero((owner == st) & (county < 0))[0]
        if not len(own):
            continue
        cand = [i for i, u in enumerate(city_units) if u["prov"] == code]
        if not cand:
            continue
        cxy = city_xy[cand]
        for i in own:
            cx, cy = grid.center(*grid.col_row(i))
            d2 = (cxy[:, 0] - cx) ** 2 + (cxy[:, 1] - cy) ** 2
            county[i] = cand[int(np.argmin(d2))]

    # coast pass
    for i in range(n):
        if water[i] == LAKE:
            continue
        if owner[i] < 0:
            water[i] = COAST if any(owner[j] >= 0 for j in grid.neighbours(i)) else OCEAN

    # terrain
    print("  sampling elevation ...")
    elev = np.zeros(n, dtype=np.int32)
    elev_max = np.zeros(n, dtype=np.int32)
    relief = np.zeros(n, dtype=np.int8)
    pct = {k: np.zeros(n, dtype=np.int16) for k in ["forest", "crop", "pasture", "grass", "shrub", "wetland", "developed"]}
    cover = np.zeros(n, dtype=np.int8)
    urban_km = np.full(n, 999.0)
    for i in range(n):
        if water[i] == LAKE:
            continue
        lon0, lat0 = centers[i]
        cx, cy = grid.center(*grid.col_row(i))
        d2 = (city_xy[:, 0] - cx) ** 2 + (city_xy[:, 1] - cy) ** 2
        urban_km[i] = math.sqrt(float(d2.min()))
        vals = [terr.elev(*samples[i, k]) if terr else int(300 + max(0, 35 - lat0) * 60) for k in range(7)]
        if owner[i] >= 0:
            land_idx = np.nonzero((prov_of_sample[i] >= 0) | foreign_mask[i])[0]
            use = [vals[k] for k in land_idx if vals[k] > -100] or [vals[k] for k in land_idx] or vals
            mean = sum(use) / len(use)
            elev[i] = int(round(mean))
            elev_max[i] = max(use)
            std = float(np.std(use)) if len(use) > 1 else 0.0
            relief[i] = relief_class(mean, std)
            p = cover_pct(lon0, lat0, mean, int(relief[i]), urban_km[i], None)
            for k in pct:
                pct[k][i] = p[k]
            cover[i] = cover_id(p, lat0)
        else:
            e = int(round(sum(vals) / len(vals)))
            elev[i] = min(0, e)
            elev_max[i] = 0

    # state labels are computed in the browser.  Build the file.
    states = [{"fips": code[:2], "abbr": abbr, "name": name} for code, name, abbr in PROVINCES]
    counties = [{"geoid": u["adcode"], "name": u["name"]} for u in city_units]

    # rivers
    rivers = []
    for f in _load(cache_dir / "ne_50m_rivers_lake_centerlines.geojson")["features"]:
        name = f["properties"].get("name") or f["properties"].get("name_en") or "河流"
        geom = f["geometry"]
        lines = [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"] if geom["type"] == "MultiLineString" else []
        for line in lines:
            pts = [project(lon, lat) for lon, lat in line if 70 <= lon <= 140 and 15 <= lat <= 56]
            if len(pts) < 2:
                continue
            simp = [pts[0]]
            for p in pts[1:]:
                if math.dist(p, simp[-1]) >= 8:
                    simp.append(p)
            if len(simp) >= 2:
                rivers.append({"name": name, "pts": [round(v, 1) for p in simp for v in p]})
    rivers.sort(key=lambda r: len(r["pts"]), reverse=True)
    rivers = rivers[:80]
    for k, r in enumerate(rivers):
        r["rank"] = k + 1

    world = {
        "version": 2, "grid": grid.to_dict(), "width": round(width, 1), "height": round(height, 1), "margin": MARGIN,
        "owner": owner.tolist(), "county": county.tolist(), "elev": elev.tolist(), "elev_max": elev_max.tolist(),
        "water": water.tolist(), "relief": relief.tolist(), "cover": cover.tolist(),
        "pct": {k: v.tolist() for k, v in pct.items()},
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
            "notes": {"cover": "土地覆盖由生态分区模型生成，并用各省森林覆盖率校准；不是逐像元遥感分类。",
                       "relief": "高程取自 AWS Terrarium（Mapzen 地形瓦片，约 2 km 分辨率）。"},
        },
        "states": states, "counties": counties, "rivers": rivers,
    }
    out = cache_dir.parents[1] / "web" / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "world.json").write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  world.json", (out / "world.json").stat().st_size // 1024, "KB · land", int((owner >= 0).sum()), "water", int((water > 0).sum()))
    return {"world": world, "grid": grid, "project": project, "inverse": inverse, "city_units": city_units,
            "owner": owner, "county": county, "center": centers, "samples": samples}
