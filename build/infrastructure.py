#!/usr/bin/env python3
"""Infrastructure: major highways, high-speed rail, ports and airports."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "data"

ROAD_CORRIDORS = [
    ("G2 京沪高速", ["北京", "天津", "济南", "南京", "上海"], 0),
    ("G4 京港澳高速", ["北京", "石家庄", "郑州", "武汉", "长沙", "广州", "深圳"], 0),
    ("G1 京哈高速", ["北京", "沈阳", "长春", "哈尔滨"], 0),
    ("G30 连霍高速", ["连云港", "徐州", "郑州", "西安", "兰州", "乌鲁木齐"], 0),
    ("G60 沪昆高速", ["上海", "杭州", "南昌", "长沙", "贵阳", "昆明"], 0),
    ("G80 广昆高速", ["广州", "南宁", "昆明"], 0),
    ("G5 京昆高速", ["北京", "太原", "西安", "成都", "昆明"], 0),
    ("G75 兰海高速", ["兰州", "重庆", "贵阳", "南宁", "海口"], 0),
    ("G20 青银高速", ["青岛", "济南", "石家庄", "太原", "银川"], 0),
    ("G42 沪蓉高速", ["上海", "南京", "合肥", "武汉", "重庆", "成都"], 0),
    ("G70 福银高速", ["福州", "南昌", "武汉", "西安", "银川"], 0),
    ("G15 沈海高速", ["沈阳", "大连", "烟台", "青岛", "连云港", "上海", "宁波", "温州", "福州", "厦门", "汕头", "深圳", "广州"], 0),
    ("G45 大广高速", ["大庆", "长春", "沈阳", "北京", "石家庄", "郑州", "武汉", "长沙", "广州"], 0),
    ("G55 二广高速", ["二连浩特", "太原", "洛阳", "襄阳", "常德", "广州"], 0),
    ("G65 包茂高速", ["包头", "西安", "重庆", "贵阳", "南宁", "茂名"], 0),
    ("G6 京藏高速", ["北京", "呼和浩特", "银川", "兰州", "西宁", "拉萨"], 0),
    ("G109 青藏公路", ["西宁", "格尔木", "拉萨"], 1),
    ("G219 新藏公路", ["喀什", "和田", "阿里", "拉萨"], 1),
    ("G98 海南环线", ["海口", "三亚", "海口"], 0),
    ("台1线", ["台北", "新竹", "台中", "台南", "高雄"], 1),
    ("台9线", ["台北", "花莲", "台东", "高雄"], 1),
]
RAIL_CORRIDORS = [
    ("京广高铁", ["北京", "石家庄", "郑州", "武汉", "长沙", "广州"], 0),
    ("京沪高铁", ["北京", "天津", "济南", "南京", "上海"], 0),
    ("京哈高铁", ["北京", "沈阳", "长春", "哈尔滨"], 0),
    ("徐兰高铁", ["徐州", "郑州", "西安", "兰州"], 0),
    ("沪昆高铁", ["上海", "杭州", "南昌", "长沙", "贵阳", "昆明"], 0),
    ("广昆高铁", ["广州", "南宁", "昆明"], 0),
    ("成渝高铁", ["成都", "重庆"], 0),
    ("兰新高铁", ["兰州", "西宁", "乌鲁木齐"], 0),
    ("青藏铁路", ["西宁", "格尔木", "拉萨"], 1),
    ("哈大高铁", ["哈尔滨", "长春", "沈阳", "大连"], 0),
    ("厦深铁路", ["厦门", "深圳"], 0),
    ("沪汉蓉客专", ["上海", "南京", "合肥", "武汉", "重庆", "成都"], 0),
    ("贵广高铁", ["贵阳", "桂林", "广州"], 0),
    ("南广铁路", ["南宁", "广州"], 0),
    ("京九铁路", ["北京", "南昌", "深圳"], 1),
    ("陇海铁路", ["连云港", "徐州", "郑州", "西安", "兰州"], 1),
    ("台湾高铁", ["台北", "台中", "高雄"], 0),
    ("台湾铁路", ["台北", "花莲", "台东", "高雄"], 1),
]

PORTS = [
    ("宁波舟山港", "宁波", 121.9, 29.9, 1324000000, "coastal", 1),
    ("上海港", "上海", 121.5, 31.2, 809000000, "coastal", 2),
    ("唐山港", "唐山", 118.2, 39.2, 800000000, "coastal", 3),
    ("青岛港", "青岛", 120.3, 36.1, 685000000, "coastal", 4),
    ("广州港", "广州", 113.6, 23.1, 656000000, "coastal", 5),
    ("日照港", "日照", 119.5, 35.4, 588000000, "coastal", 6),
    ("苏州港", "苏州", 120.6, 31.3, 566000000, "inland", 7),
    ("天津港", "天津", 117.7, 38.9, 559000000, "coastal", 8),
    ("烟台港", "烟台", 121.4, 37.5, 485000000, "coastal", 9),
    ("北部湾港", "钦州", 108.6, 21.7, 450000000, "coastal", 10),
    ("大连港", "大连", 121.6, 38.9, 420000000, "coastal", 11),
    ("泰州港", "泰州", 119.9, 32.5, 400000000, "inland", 12),
    ("江阴港", "江阴", 120.3, 31.9, 380000000, "inland", 13),
    ("南通港", "南通", 120.9, 32.0, 370000000, "inland", 14),
    ("南京港", "南京", 118.8, 32.1, 320000000, "inland", 15),
    ("连云港港", "连云港", 119.2, 34.6, 310000000, "coastal", 16),
    ("厦门港", "厦门", 118.1, 24.5, 280000000, "coastal", 17),
    ("福州港", "福州", 119.3, 26.0, 270000000, "coastal", 18),
    ("泉州港", "泉州", 118.7, 24.9, 250000000, "coastal", 19),
    ("深圳港", "深圳", 114.1, 22.5, 240000000, "coastal", 20),
    ("高雄港", "高雄", 120.28, 22.61, 400000000, "coastal", 21),
    ("基隆港", "基隆", 121.74, 25.15, 150000000, "coastal", 22),
    ("台中港", "台中", 120.51, 24.29, 120000000, "coastal", 23),
    ("台北港", "台北", 121.38, 25.16, 80000000, "coastal", 24),
]

AIRPORTS = [
    ("PEK", "北京首都国际机场", "北京", 116.6, 40.1, 52880000),
    ("PVG", "上海浦东国际机场", "上海", 121.8, 31.1, 54470000),
    ("CAN", "广州白云国际机场", "广州", 113.3, 23.4, 63170000),
    ("SZX", "深圳宝安国际机场", "深圳", 113.8, 22.6, 52730000),
    ("TFU", "成都天府国际机场", "成都", 104.4, 30.3, 44780000),
    ("CKG", "重庆江北国际机场", "重庆", 106.6, 29.7, 44660000),
    ("SHA", "上海虹桥国际机场", "上海", 121.3, 31.2, 42450000),
    ("KMG", "昆明长水国际机场", "昆明", 102.9, 25.1, 42030000),
    ("XIY", "西安咸阳国际机场", "西安", 108.8, 34.4, 41370000),
    ("HGH", "杭州萧山国际机场", "杭州", 120.4, 30.2, 41170000),
    ("PKX", "北京大兴国际机场", "北京", 116.4, 39.5, 39410000),
    ("NKG", "南京禄口国际机场", "南京", 118.9, 31.7, 27360000),
    ("CSX", "长沙黄花国际机场", "长沙", 113.2, 28.2, 27250000),
    ("WUH", "武汉天河国际机场", "武汉", 114.2, 30.8, 25740000),
    ("CGO", "郑州新郑国际机场", "郑州", 113.8, 34.5, 25360000),
    ("XMN", "厦门高崎国际机场", "厦门", 118.1, 24.5, 24100000),
    ("HAK", "海口美兰国际机场", "海口", 110.5, 19.9, 24200000),
    ("SYX", "三亚凤凰国际机场", "三亚", 109.4, 18.3, 21770000),
    ("TAO", "青岛胶东国际机场", "青岛", 120.1, 36.4, 21400000),
    ("URC", "乌鲁木齐地窝堡国际机场", "乌鲁木齐", 87.5, 43.9, 20800000),
    ("HRB", "哈尔滨太平国际机场", "哈尔滨", 126.3, 45.6, 20800000),
    ("SHE", "沈阳桃仙国际机场", "沈阳", 123.5, 41.6, 20500000),
    ("KWE", "贵阳龙洞堡国际机场", "贵阳", 106.8, 26.5, 19470000),
    ("TSN", "天津滨海国际机场", "天津", 117.3, 39.1, 18400000),
    ("TNA", "济南遥墙国际机场", "济南", 117.2, 36.9, 17500000),
    ("DLC", "大连周水子国际机场", "大连", 121.5, 38.9, 16100000),
    ("FOC", "福州长乐国际机场", "福州", 119.7, 25.9, 15000000),
    ("NNG", "南宁吴圩国际机场", "南宁", 108.2, 22.6, 13600000),
    ("NGB", "宁波栎社国际机场", "宁波", 121.5, 29.8, 12900000),
    ("HET", "呼和浩特白塔国际机场", "呼和浩特", 111.8, 40.9, 11000000),
    ("TPE", "台湾桃园国际机场", "桃园", 121.23, 25.08, 30000000),
    ("KHH", "高雄国际机场", "高雄", 120.35, 22.58, 6000000),
    ("TSA", "台北松山机场", "台北", 121.55, 25.06, 5000000),
]


def build(world_meta, cities):
    world = world_meta["world"]
    grid = world_meta["grid"]
    owner = world["owner"]
    county = world["county"]
    project = world_meta["project"]
    by_name = {}
    for c in cities:
        by_name.setdefault(c["name"], c)
    land_cells = [i for i, o in enumerate(owner) if o >= 0]
    land_xy = [grid.center(*grid.col_row(i)) for i in land_cells]

    def cell_of(lon, lat):
        x, y = project(lon, lat)
        best = min(land_cells, key=lambda i: (grid.center(*grid.col_row(i))[0] - x) ** 2 + (grid.center(*grid.col_row(i))[1] - y) ** 2)
        return best

    def trace(a, b):
        x0, y0 = grid.center(*grid.col_row(a))
        x1, y1 = grid.center(*grid.col_row(b))
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(dist / 6))
        out = []
        for k in range(steps + 1):
            t = k / steps
            c = grid.cell_at(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if c >= 0 and (not out or out[-1] != c):
                out.append(c)
        return out

    road_best = {}
    for name, names, cls in ROAD_CORRIDORS:
        cells = [cell_of(*by_name[n]["x"], by_name[n]["y"]) if False else by_name[n]["cell"] for n in names if n in by_name]
        for a, b in zip(cells, cells[1:]):
            path = trace(a, b)
            for u, v in zip(path, path[1:]):
                if v in grid.neighbours(u):
                    key = (min(u, v), max(u, v))
                    if key not in road_best or cls < road_best[key][0]:
                        road_best[key] = (cls, name)
    rail_best = {}
    for name, names, tier in RAIL_CORRIDORS:
        cells = [by_name[n]["cell"] for n in names if n in by_name]
        for a, b in zip(cells, cells[1:]):
            path = trace(a, b)
            for u, v in zip(path, path[1:]):
                if v in grid.neighbours(u):
                    key = (min(u, v), max(u, v))
                    if key not in rail_best or tier < rail_best[key][0]:
                        rail_best[key] = (tier, name)

    ports = []
    for name, city, lon, lat, tons, typ, rank in PORTS:
        cell = cell_of(lon, lat)
        ports.append({"id": str(rank), "name": name, "type": typ, "rank": rank, "tons": tons, "domestic": None,
                      "foreign": None, "imports": None, "exports": None, "year": 2023,
                      "x": round(project(lon, lat)[0], 1), "y": round(project(lon, lat)[1], 1), "cell": cell,
                      "county": None, "cbsa": cities[county[cell]]["id"] if county[cell] >= 0 else None,
                      "state": cities[county[cell]]["states"][0] if county[cell] >= 0 else "—"})
    airports = []
    for code, name, city, lon, lat, pax in AIRPORTS:
        cell = cell_of(lon, lat)
        airports.append({"id": code, "name": name, "city": city, "hub": "L" if pax >= 30000000 else "M" if pax >= 10000000 else "S",
                         "enplanements": pax, "enplanements_prev": None, "cargo_lbs": None, "year": 2023,
                         "x": round(project(lon, lat)[0], 1), "y": round(project(lon, lat)[1], 1), "cell": cell,
                         "county": None, "cbsa": cities[county[cell]]["id"] if county[cell] >= 0 else None,
                         "state": cities[county[cell]]["states"][0] if county[cell] >= 0 else "—"})
    data = {
        "version": 1,
        "vintage": {"roads": "国家高速公路网（示意）", "rail": "八纵八横高铁网（示意）", "ports": "交通运输部港口吞吐量 2023", "airports": "民航局机场旅客吞吐量 2023"},
        "sources": ["natural_earth_roads", "mot_ports", "caac_airports"],
        "rules": {"roads": "选取国家高速公路主干线，按城市节点连线并在六边形网格上栅格化，是走向示意而非精确线位。",
                  "rail": "选取八纵八横高铁与主要普速干线，按城市节点连线，是走向示意。",
                  "ports": "按 2023 年货物吞吐量排序的前 20 个沿海/内河港口。",
                  "airports": "按 2023 年旅客吞吐量排序的前 30 个机场。"},
        "road_classes": [{"id": "national_expressway", "name": "国家高速"}, {"id": "national_road", "name": "国道"}],
        "rail_tiers": [{"id": "high_speed", "name": "高铁"}, {"id": "conventional", "name": "普速"}],
        "hubs": {"L": "大型枢纽", "M": "中型枢纽", "S": "小型枢纽", "N": "支线"},
        "roads": [[a, b, v[0], v[1]] for (a, b), v in sorted(road_best.items())],
        "rail": [[a, b, v[0]] for (a, b), v in sorted(rail_best.items())],
        "ports": ports, "airports": airports,
    }
    (OUT / "infrastructure.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  infrastructure {len(data['roads'])} road links, {len(data['rail'])} rail links, {len(ports)} ports, {len(airports)} airports")
    return data
