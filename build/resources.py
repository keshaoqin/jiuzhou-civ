#!/usr/bin/env python3
"""Resources: power plants, mines, oil & gas fields."""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "cache"
OUT = ROOT / "web" / "data"
PROVINCES = [
    ("110000", "北京", "BJ"), ("120000", "天津", "TJ"), ("130000", "河北", "HE"), ("140000", "山西", "SX"),
    ("150000", "内蒙古", "NM"), ("210000", "辽宁", "LN"), ("220000", "吉林", "JL"), ("230000", "黑龙江", "HL"),
    ("310000", "上海", "SH"), ("320000", "江苏", "JS"), ("330000", "浙江", "ZJ"), ("340000", "安徽", "AH"),
    ("350000", "福建", "FJ"), ("360000", "江西", "JX"), ("370000", "山东", "SD"), ("410000", "河南", "HA"),
    ("420000", "湖北", "HB"), ("430000", "湖南", "HN"), ("440000", "广东", "GD"), ("450000", "广西", "GX"),
    ("460000", "海南", "HI"), ("500000", "重庆", "CQ"), ("510000", "四川", "SC"), ("520000", "贵州", "GZ"),
    ("530000", "云南", "YN"), ("540000", "西藏", "XZ"), ("610000", "陕西", "SN"), ("620000", "甘肃", "GS"),
    ("630000", "青海", "QH"), ("640000", "宁夏", "NX"), ("650000", "新疆", "XJ"), ("710000", "台湾", "TW"),
]
ABBR = [x[2] for x in PROVINCES]

TYPES = [
    dict(id="nuclear", name="核电厂", category="energy", emoji="☢️", icon="r-nuclear", color="#e8d44d", unit="MW",
         description="中国所有在运核电机组，单站装机 ≥ 300 MW。", source="wri_power"),
    dict(id="coal_plant", name="燃煤电厂", category="energy", emoji="🏭", icon="r-coal_plant", color="#6b5545", unit="MW",
         description="单站装机 ≥ 1,000 MW 的燃煤电厂（坑口、沿海大基地为主）。", source="wri_power"),
    dict(id="gas_plant", name="燃气电厂", category="energy", emoji="🔥", icon="r-gas_plant", color="#b06a3a", unit="MW",
         description="单站装机 ≥ 500 MW 的燃气/燃油电厂。", source="wri_power"),
    dict(id="hydro", name="水电站", category="energy", emoji="💧", icon="r-hydro", color="#2b7fb8", unit="MW",
         description="单站装机 ≥ 500 MW 的水电站，含三峡、白鹤滩、溪洛渡等。", source="wri_power"),
    dict(id="wind", name="风电场", category="energy", emoji="🌬️", icon="r-wind", color="#7db6c9", unit="MW",
         description="单场装机 ≥ 300 MW 的陆上/海上风电场。", source="wri_power"),
    dict(id="solar", name="光伏电站", category="energy", emoji="☀️", icon="r-solar", color="#e0a93a", unit="MW",
         description="单场装机 ≥ 300 MW 的光伏电站。", source="wri_power"),
    dict(id="biomass", name="生物质电厂", category="energy", emoji="🌾", icon="r-coal_plant", color="#7d8a3a", unit="MW",
         description="单站装机 ≥ 50 MW 的生物质发电厂。", source="wri_power"),
    dict(id="coal_mine", name="煤矿", category="mineral", emoji="⛏️", icon="r-coal_mine", color="#5a4b3b", unit="万吨/年",
         description="年产 ≥ 1,000 万吨的大型煤矿区（按矿区合并）。", source="curated_mines"),
    dict(id="iron", name="铁矿", category="mineral", emoji="⛏️", icon="r-iron", color="#8b6b52", unit="万吨/年",
         description="鞍本、攀西、冀东等主要铁矿区。", source="curated_mines"),
    dict(id="copper", name="铜矿", category="mineral", emoji="⛏️", icon="r-copper", color="#b06a3a", unit="万吨/年",
         description="德兴、铜陵、大冶、白银等主要铜矿区。", source="curated_mines"),
    dict(id="rare_earths", name="稀土矿", category="mineral", emoji="⛏️", icon="r-rare_earths", color="#9a6ab0", unit="万吨/年",
         description="白云鄂博、赣州离子型稀土等主要稀土矿区。", source="curated_mines"),
    dict(id="gold", name="金矿", category="mineral", emoji="⛏️", icon="r-gold", color="#d4af37", unit="吨/年",
         description="招远、三门峡等主要黄金产区。", source="curated_mines"),
    dict(id="oil", name="油田", category="agri", emoji="🛢️", icon="r-oil", color="#39434b", unit="km² 油田面积",
         description="大庆、胜利、长庆、塔里木等主要油田（面积示意）。", source="curated_mines"),
    dict(id="gas", name="气田", category="agri", emoji="🔥", icon="r-gas", color="#3e6b8a", unit="km² 气田面积",
         description="四川盆地、鄂尔多斯、塔里木等主要气田（面积示意）。", source="curated_mines"),
]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build(world_meta, cities, states):
    world = world_meta["world"]
    grid = world_meta["grid"]
    owner = np.array(world["owner"], dtype=np.int16)
    county = np.array(world["county"], dtype=np.int16)
    project = world_meta["project"]
    land_cells = np.nonzero(owner >= 0)[0]
    land_xy = np.array([grid.center(*grid.col_row(i)) for i in land_cells])
    city_by_index = {i: c for i, c in enumerate(cities)}
    county_to_city = {}
    for c in cities:
        for cell in c["footprint"]:
            county_to_city[cell] = c["id"]

    def point_cell(lon, lat):
        x, y = project(lon, lat)
        d2 = (land_xy[:, 0] - x) ** 2 + (land_xy[:, 1] - y) ** 2
        idx = int(np.argmin(d2))
        return int(land_cells[idx]), x, y

    items = []
    seen = set()

    # --- WRI power plants ---------------------------------------------------------
    csv_path = CACHE / "global_power_plants.csv"
    if csv_path.exists() and csv_path.stat().st_size > 100000:
        fuels = {
            "Coal": ("coal_plant", 1000), "Gas": ("gas_plant", 500), "Hydro": ("hydro", 500),
            "Nuclear": ("nuclear", 300), "Wind": ("wind", 300), "Solar": ("solar", 300),
            "Biomass": ("biomass", 50), "Oil": ("gas_plant", 500), "Geothermal": ("gas_plant", 100),
            "Storage": ("battery", 100), "Petcoke": ("coal_plant", 500), "Waste": ("biomass", 50),
        }
        rows = []
        with open(csv_path, newline="", encoding="utf-8", errors="ignore") as f:
            r = csv.DictReader(f)
            for row in r:
                if row.get("country_long") != "China":
                    continue
                try:
                    cap = float(row.get("capacity_mw") or 0)
                    lon = float(row.get("longitude"))
                    lat = float(row.get("latitude"))
                except Exception:
                    continue
                fuel = row.get("primary_fuel") or ""
                if fuel not in fuels:
                    continue
                typ, threshold = fuels[fuel]
                if cap < threshold:
                    continue
                rows.append((cap, typ, row.get("name") or "电厂", lon, lat, row))
        rows.sort(key=lambda x: -x[0])
        # keep top wind/solar to avoid thousands of dots
        keep = []
        counts = Counter()
        caps = {"coal_plant": 120, "gas_plant": 80, "hydro": 80, "nuclear": 200, "wind": 80, "solar": 80, "biomass": 40}
        for row in rows:
            typ = row[1]
            if counts[typ] >= caps.get(typ, 60):
                continue
            counts[typ] += 1
            keep.append(row)
        for cap, typ, name, lon, lat, row in keep:
            cell, x, y = point_cell(lon, lat)
            if cell in county_to_city and any(it["type"] == typ and it["cell"] == cell and abs(it["value"] - cap) < 1 for it in items):
                continue
            item = {
                "type": typ, "name": name[:48], "x": round(x, 1), "y": round(y, 1), "cell": cell,
                "value": round(cap, 1), "detail": f"{round(cap):,} MW · {row.get('primary_fuel')} · 投产 {row.get('commissioning_year') or '—'}",
                "state": ABBR[owner[cell]], "cbsa": county_to_city.get(cell),
            }
            items.append(item)
    else:
        print("  WRI power plants not found, using curated fallback")
        curated = [
            ("nuclear", "秦山核电", 121.0, 30.4, 656, "秦山一期至三期"), ("nuclear", "大亚湾核电", 114.55, 22.6, 610, "大亚湾/岭澳"),
            ("nuclear", "田湾核电", 119.45, 34.68, 660, "田湾 1-6 号"), ("nuclear", "岭东核电", 114.55, 22.6, 600, "岭东"),
            ("nuclear", "宁德核电", 120.0, 27.0, 435, "宁德 1-4 号"), ("nuclear", "福清核电", 119.45, 25.45, 665, "福清 1-6 号"),
            ("coal_plant", "托克托电厂", 111.1, 40.3, 6720, "大唐托克托"), ("coal_plant", "外高桥第三电厂", 121.6, 31.4, 4600, "上海"),
            ("coal_plant", "北仑电厂", 121.9, 29.9, 5000, "宁波"), ("coal_plant", "海门电厂", 121.2, 28.6, 4000, "台州"),
            ("coal_plant", "绥中电厂", 120.0, 40.3, 3600, "葫芦岛"), ("coal_plant", "灵武电厂", 106.3, 38.1, 3200, "宁夏"),
            ("hydro", "三峡水电站", 111.0, 30.8, 22500, "三峡"), ("hydro", "白鹤滩水电站", 102.9, 27.2, 16000, "金沙江"),
            ("hydro", "溪洛渡水电站", 103.6, 28.2, 13860, "金沙江"), ("hydro", "乌东德水电站", 102.6, 26.3, 10200, "金沙江"),
            ("hydro", "向家坝水电站", 104.4, 28.6, 7750, "金沙江"), ("hydro", "龙滩水电站", 107.0, 25.0, 6300, "红水河"),
            ("wind", "甘肃酒泉风电基地", 97.0, 40.2, 10000, "酒泉"), ("wind", "内蒙古辉腾锡勒", 112.5, 41.2, 3000, "乌兰察布"),
            ("solar", "青海塔拉滩光伏", 100.6, 36.2, 8000, "海南州"), ("solar", "新疆哈密光伏", 93.5, 42.8, 3000, "哈密"),
            ("gas_plant", "北京京西燃气", 116.2, 39.9, 2000, "北京"), ("gas_plant", "上海临港燃气", 121.9, 30.9, 1800, "上海"),
        ]
        for typ, name, lon, lat, cap, detail in curated:
            cell, x, y = point_cell(lon, lat)
            items.append({"type": typ, "name": name, "x": round(x, 1), "y": round(y, 1), "cell": cell,
                          "value": cap, "detail": f"{cap:,} MW · {detail}", "state": ABBR[owner[cell]], "cbsa": county_to_city.get(cell)})

    # --- curated mines & fields ---------------------------------------------------
    curated_sites = [
        ("coal_mine", "鄂尔多斯煤矿区", 109.8, 39.6, 60000, "神东、准格尔等"),
        ("coal_mine", "大同煤矿区", 113.3, 40.1, 20000, "同煤集团"), ("coal_mine", "朔州煤矿区", 112.4, 39.3, 18000, "平朔"),
        ("coal_mine", "榆林煤矿区", 109.7, 38.3, 30000, "陕北"), ("coal_mine", "长治煤矿区", 113.1, 36.2, 12000, "潞安"),
        ("coal_mine", "晋城煤矿区", 112.85, 35.5, 10000, "晋煤"), ("coal_mine", "平顶山煤矿区", 113.3, 33.77, 8000, "平煤"),
        ("coal_mine", "淮南煤矿区", 117.0, 32.6, 9000, "淮河能源"), ("coal_mine", "六盘水煤矿区", 104.8, 26.6, 7000, "盘江"),
        ("coal_mine", "双鸭山煤矿区", 131.2, 46.6, 5000, "龙煤"),
        ("iron", "鞍本铁矿区", 123.0, 41.2, 8000, "鞍山-本溪"), ("iron", "攀西铁矿区", 101.7, 26.6, 5000, "攀枝花"),
        ("iron", "冀东铁矿区", 118.2, 39.8, 4000, "唐山"),
        ("copper", "德兴铜矿", 117.6, 28.9, 20, "江西铜业"), ("copper", "铜陵铜矿", 117.8, 30.9, 15, "铜陵有色"),
        ("copper", "大冶铜矿", 114.9, 30.1, 12, "大冶有色"), ("copper", "白银铜矿", 104.2, 36.5, 10, "白银有色"),
        ("rare_earths", "白云鄂博稀土", 109.9, 41.8, 20, "包钢稀土"), ("rare_earths", "赣州离子型稀土", 114.9, 25.8, 8, "赣州"),
        ("gold", "招远金矿", 120.4, 37.3, 30, "山东黄金"), ("gold", "三门峡金矿", 111.2, 34.8, 15, "灵宝"),
        ("oil", "大庆油田", 125.1, 46.6, 6000, "松辽盆地"), ("oil", "胜利油田", 118.8, 37.5, 4000, "渤海湾盆地"),
        ("oil", "长庆油田", 108.0, 36.0, 5000, "鄂尔多斯盆地"), ("oil", "塔里木油田", 84.0, 41.0, 3000, "塔里木盆地"),
        ("oil", "克拉玛依油田", 84.9, 45.6, 2000, "准噶尔盆地"), ("oil", "渤海油田", 119.0, 38.5, 3000, "渤海湾"),
        ("gas", "四川盆地气田", 105.0, 30.5, 5000, "川渝"), ("gas", "鄂尔多斯气田", 108.5, 38.5, 4000, "苏里格"),
        ("gas", "塔里木气田", 84.0, 40.0, 3000, "塔里木"), ("gas", "莺歌海气田", 109.5, 18.5, 1500, "南海"),
        ("nuclear", "核三厂", 120.85, 21.96, 1900, "屏东"),
        ("coal_plant", "台中电厂", 120.51, 24.21, 5500, "台中港"),
        ("coal_plant", "兴达电厂", 120.16, 22.85, 4320, "高雄"),
        ("gas_plant", "大潭电厂", 121.05, 25.03, 4980, "桃园"),
        ("gas_plant", "通霄电厂", 120.75, 24.49, 3000, "苗栗"),
        ("wind", "彰化外海风场", 120.30, 24.00, 1000, "彰化"),
        ("solar", "台南盐田光伏", 120.10, 23.10, 500, "台南"),
    ]
    for typ, name, lon, lat, val, detail in curated_sites:
        cell, x, y = point_cell(lon, lat)
        items.append({"type": typ, "name": name, "x": round(x, 1), "y": round(y, 1), "cell": cell,
                      "value": val, "detail": detail, "state": ABBR[owner[cell]], "cbsa": county_to_city.get(cell)})

    # old WRI fuel labels: rename `battery` and drop if missing type
    type_ids = {t["id"] for t in TYPES}
    items = [it for it in items if it["type"] in type_ids]

    summary = {"note": "这里只统计地图上标出的规模以上站点，不是全国总装机；煤矿、油田等按规模排序选点。", "national": {}, "states": {}}
    for t in TYPES:
        its = [it for it in items if it["type"] == t["id"]]
        total = None if t["id"] in ("oil", "gas") else sum(it["value"] for it in its if it["value"] is not None)
        summary["national"][t["id"]] = {"count": len(its), "value": round(total, 1) if total is not None else None, "unit": t["unit"]}
    for ab in ABBR:
        its = [it for it in items if it["state"] == ab]
        if not its:
            continue
        summary["states"][ab] = {}
        for t in TYPES:
            sub = [it for it in its if it["type"] == t["id"]]
            if sub:
                total = None if t["id"] in ("oil", "gas") else sum(it["value"] for it in sub if it["value"] is not None)
                summary["states"][ab][t["id"]] = {"count": len(sub), "value": round(total, 1) if total is not None else None, "unit": t["unit"]}

    res = {"types": TYPES, "items": items, "summary": summary}
    (OUT / "resources.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # update state energy blocks
    mw_types = [t for t in TYPES if t["unit"] == "MW"]
    for s in states:
        its = [it for it in items if it["state"] == s["abbr"]]
        by_type = {t["id"]: 0 for t in mw_types}
        sites = {t["id"]: 0 for t in mw_types}
        for it in its:
            if it["type"] in by_type and it["value"]:
                by_type[it["type"]] += it["value"]
                sites[it["type"]] += 1
        s["energy"] = {"unit": "MW", "total": round(sum(by_type.values())), "by_type": by_type, "sites": sites,
                       "note": "只统计地图上标出的规模以上电站，不是全省总装机。"}
    (OUT / "states.json").write_text(json.dumps(states, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  resources {len(items)} sites, {len(TYPES)} types")
    return res
