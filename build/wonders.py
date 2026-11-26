#!/usr/bin/env python3
"""Wonders: national parks, scenic areas, research universities and landmarks."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "data"

PARKS = [
    # name, lon, lat, visits (2024, approx), area km², kind
    ("三江源国家公园", 95.0, 34.0, 0, 190700, "natural"),
    ("大熊猫国家公园", 103.0, 31.0, 0, 27134, "natural"),
    ("东北虎豹国家公园", 131.0, 43.5, 0, 14600, "natural"),
    ("海南热带雨林国家公园", 109.7, 18.9, 0, 4269, "natural"),
    ("武夷山国家公园", 117.7, 27.75, 1200000, 1279, "natural"),
    ("黄山风景区", 118.17, 30.13, 3500000, 160, "natural"),
    ("泰山风景区", 117.1, 36.25, 5600000, 426, "natural"),
    ("杭州西湖", 120.15, 30.25, 28000000, 60, "recreation"),
    ("九寨沟", 103.9, 33.2, 2800000, 651, "natural"),
    ("张家界武陵源", 110.48, 29.12, 3800000, 264, "natural"),
    ("峨眉山—乐山大佛", 103.48, 29.6, 3200000, 154, "monument"),
    ("庐山", 115.98, 29.55, 2500000, 302, "natural"),
    ("桂林漓江", 110.29, 25.27, 4200000, 1159, "natural"),
    ("长白山", 128.06, 42.0, 2600000, 1965, "natural"),
    ("华山", 110.08, 34.48, 3000000, 148, "natural"),
    ("玉龙雪山", 100.18, 27.1, 2400000, 415, "natural"),
    ("青海湖", 100.2, 36.9, 2200000, 4583, "natural"),
    ("喀纳斯", 86.7, 48.8, 1500000, 1000, "natural"),
    ("稻城亚丁", 100.3, 28.4, 1200000, 1457, "natural"),
    ("神农架", 110.5, 31.5, 1800000, 3253, "natural"),
    ("日月潭", 120.91, 23.85, 8000000, 9.3, "natural"),
    ("阿里山", 120.80, 23.51, 4000000, 1400, "natural"),
    ("太鲁阁", 121.62, 24.16, 3000000, 920, "natural"),
]
UNIVERSITIES = [
    ("清华大学", 116.326, 40.003, 4100000, 57000),
    ("北京大学", 116.310, 39.992, 3600000, 46000),
    ("浙江大学", 120.087, 30.294, 3100000, 63000),
    ("上海交通大学", 121.433, 31.025, 2900000, 46000),
    ("复旦大学", 121.503, 31.298, 2500000, 45000),
    ("中山大学", 113.296, 23.097, 2300000, 62000),
    ("华中科技大学", 114.414, 30.512, 2100000, 61000),
    ("南京大学", 118.958, 32.056, 2000000, 40000),
    ("中国科学技术大学", 117.264, 31.835, 1800000, 21000),
    ("哈尔滨工业大学", 126.632, 45.742, 1750000, 46000),
    ("西安交通大学", 116.0, 34.25, 1650000, 44000),
    ("武汉大学", 114.361, 30.536, 1600000, 59000),
    ("同济大学", 121.501, 31.282, 1500000, 41000),
    ("北京航空航天大学", 116.348, 39.981, 1450000, 37000),
    ("东南大学", 118.798, 32.057, 1350000, 40000),
    ("四川大学", 104.083, 30.630, 1300000, 65000),
    ("厦门大学", 118.096, 24.436, 1200000, 42000),
    ("山东大学", 117.057, 36.675, 1150000, 60000),
    ("中南大学", 112.935, 28.155, 1100000, 58000),
    ("吉林大学", 125.288, 43.825, 1050000, 67000),
]
LANDMARKS = [
    ("故宫", 116.397, 39.916, 19000000, "monument"),
    ("八达岭长城", 116.02, 40.36, 10000000, "monument"),
    ("秦始皇兵马俑", 109.27, 34.38, 9000000, "monument"),
    ("布达拉宫", 91.117, 29.657, 2000000, "monument"),
    ("敦煌莫高窟", 94.8, 40.04, 2200000, "monument"),
    ("乐山大佛", 103.77, 29.55, 3800000, "monument"),
    ("都江堰", 103.61, 31.0, 3500000, "monument"),
    ("苏州园林", 120.62, 31.3, 6000000, "monument"),
    ("丽江古城", 100.23, 26.87, 5000000, "monument"),
    ("平遥古城", 112.18, 37.2, 2000000, "monument"),
    ("福建土楼", 117.0, 24.6, 3000000, "monument"),
    ("三星堆遗址", 104.2, 31.0, 2500000, "monument"),
    ("殷墟", 114.35, 36.12, 800000, "monument"),
    ("台北101", 121.564, 25.034, 3000000, "monument"),
]
RULES = [
    {"id": "national_park", "kind": "natural", "kinds": ["natural", "recreation", "coastal", "monument"], "year": 2024,
     "text": "首批 5 个国家公园全部入选；其余按公开的 5A 景区年接待量选取 15 个。"},
    {"id": "park_unit", "kind": "natural", "kinds": ["natural", "recreation", "coastal", "monument"], "year": 2024,
     "text": "按公开年接待游客量排序的 15 个 5A 级景区（含山岳、湖泊、古城）。"},
    {"id": "research_university", "kind": "university", "year": 2024,
     "text": "按 2024 年高校预算经费排序的前 20 所研究型大学（预算为公开决算/预算口径）。"},
    {"id": "landmark", "kind": "landmark", "curated": True, "year": 2024,
     "text": "项目手工选取的世界遗产与国家级地标，不与公园规则重复。"},
]


def build(world_meta, cities):
    grid = world_meta["grid"]
    owner = world_meta["world"]["owner"]
    county = world_meta["world"]["county"]
    project = world_meta["project"]
    land = [i for i, o in enumerate(owner) if o >= 0]

    def cell_of(lon, lat):
        x, y = project(lon, lat)
        return min(land, key=lambda i: (grid.center(*grid.col_row(i))[0] - x) ** 2 + (grid.center(*grid.col_row(i))[1] - y) ** 2)

    def cells_around(cell, rings=2):
        seen = {cell}
        front = {cell}
        for _ in range(rings):
            nxt = set()
            for c in front:
                for j in grid.neighbours(c):
                    if j not in seen and owner[j] >= 0:
                        seen.add(j)
                        nxt.add(j)
            front = nxt
        return sorted(seen)

    wonders = []
    # parks
    all_parks = PARKS[:5] + PARKS[5:]
    for rule, items, base_rank in (("national_park", PARKS[:5], 0), ("park_unit", PARKS[5:], 0)):
        for k, (name, lon, lat, visits, area, kind) in enumerate(items):
            cell = cell_of(lon, lat)
            cells = cells_around(cell, 3 if area > 5000 else 2)
            wonders.append({"id": f"park-{base_rank+k+1}", "name": name, "short": name.replace("风景区", "").replace("国家公园", ""),
                            "kind": kind, "rule": rule, "rank": k + 1,
                            "metrics": {"visits": visits or None, "year": 2024, "area_km2": area, "unit_type": "国家公园" if rule == "national_park" else "5A 景区"},
                            "x": round(project(lon, lat)[0], 1), "y": round(project(lon, lat)[1], 1), "cell": cell, "cells": cells,
                            "county": None, "cbsa": cities[county[cell]]["id"] if county[cell] >= 0 else None,
                            "state": cities[county[cell]]["states"][0] if county[cell] >= 0 else "—", "curated": False})
    for k, (name, lon, lat, budget, enrollment) in enumerate(UNIVERSITIES):
        cell = cell_of(lon, lat)
        wonders.append({"id": f"univ-{k+1}", "name": name, "short": name.replace("大学", ""),
                        "kind": "university", "rule": "research_university", "rank": k + 1,
                        "metrics": {"rd_usd": budget * 10000, "federal_usd": None, "year": 2024, "enrollment": enrollment,
                                    "enrollment_year": 2024, "r1": True, "med_school": False},
                        "x": round(project(lon, lat)[0], 1), "y": round(project(lon, lat)[1], 1), "cell": cell, "cells": None,
                        "county": None, "cbsa": cities[county[cell]]["id"] if county[cell] >= 0 else None,
                        "state": cities[county[cell]]["states"][0] if county[cell] >= 0 else "—", "curated": False})
    for k, (name, lon, lat, visits, kind) in enumerate(LANDMARKS):
        cell = cell_of(lon, lat)
        wonders.append({"id": f"landmark-{k+1}", "name": name, "short": name, "kind": kind, "rule": "landmark", "rank": k + 1,
                        "metrics": {"visits": visits, "year": 2024, "unit_type": "世界遗产/地标"},
                        "x": round(project(lon, lat)[0], 1), "y": round(project(lon, lat)[1], 1), "cell": cell, "cells": None,
                        "county": None, "cbsa": cities[county[cell]]["id"] if county[cell] >= 0 else None,
                        "state": cities[county[cell]]["states"][0] if county[cell] >= 0 else "—", "curated": True})
    data = {"version": 1,
            "vintage": {"parks": "国家公园与 5A 景区公开接待量（2024 前后）", "boundaries": "景区范围示意", "universities": "高校预算公开数据 2024", "landmarks": "世界遗产名录"},
            "sources": ["national_parks", "mct_5a", "moe_universities", "unesco"], "rules": RULES,
            "national": {"park_visits": sum(x[3] for x in PARKS), "park_visits_year": 2024, "r1_universities": 147},
            "wonders": wonders}
    (OUT / "wonders.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  wonders", len(wonders))
    return data
