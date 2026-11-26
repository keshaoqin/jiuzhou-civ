#!/usr/bin/env python3
"""City / province economic model for 九州.

The province totals are official (NBS yearbooks, 2024 GDP / 2023 population).
Prefecture GDP and population come from the published prefecture tables; where a
prefecture is missing it is allocated from its province's residual by land area.
All city-level employment, income and district figures are disaggregated from
province structure with published city-type adjustments and are labelled as
estimates in the Almanac.
"""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

from geo import Albers, geojson_rings
from hexgrid import HexGrid
from taiwan import TAIWAN_STATS, TAIWAN_CITIES, TAIWAN_CITY_BY_CODE

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "cache"
OUT = ROOT / "web" / "data"

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
CODE2NAME = {c: n for c, n, _ in PROVINCES}
CODE2ABBR = {c: a for c, _, a in PROVINCES}
CODE2STATE = {c: i for i, (c, _, _) in enumerate(PROVINCES)}

INDUSTRIES = {
    "agriculture": "农林牧渔业", "mining": "采矿业", "construction": "建筑业", "manufacturing": "制造业",
    "wholesale": "批发业", "retail": "零售业", "transportation": "交通运输、仓储和邮政", "utilities": "电力、热力、燃气及水",
    "information": "信息传输与软件", "finance": "金融业", "real_estate": "房地产业", "professional": "科研与专业技术服务",
    "management": "企业管理服务", "admin": "公共管理与社会组织", "education": "教育", "health": "卫生与社会工作",
    "arts": "文化、体育和娱乐", "accommodation": "住宿和餐饮", "other": "其他服务业", "public_admin": "公共管理",
}
BASE_SHARES = {
    "agriculture": 21.0, "mining": 1.3, "construction": 8.0, "manufacturing": 17.0, "wholesale": 5.0,
    "retail": 7.0, "transportation": 5.0, "utilities": 1.2, "information": 1.6, "finance": 2.2,
    "real_estate": 3.0, "professional": 5.0, "management": 1.2, "admin": 4.0, "education": 4.0,
    "health": 3.2, "arts": 2.0, "accommodation": 4.0, "other": 2.2, "public_admin": 2.0,
}
BASE_GDP = {
    "agriculture": 7.5, "mining": 3.5, "construction": 7.0, "manufacturing": 26.0, "wholesale": 8.0,
    "retail": 4.0, "transportation": 6.0, "utilities": 3.0, "information": 3.0, "finance": 7.0,
    "real_estate": 6.0, "professional": 5.0, "management": 2.0, "admin": 2.0, "education": 2.5,
    "health": 2.5, "arts": 1.5, "accommodation": 2.0, "other": 2.0, "public_admin": 2.0,
}

ARCHETYPE_NAMES = {
    "service_mega": ["北京", "上海", "深圳", "广州", "杭州", "南京", "成都", "武汉", "西安", "重庆", "天津", "长沙", "郑州", "合肥", "福州", "厦门", "昆明", "南昌", "济南", "青岛"],
    "manufacturing": ["苏州", "无锡", "佛山", "东莞", "宁波", "常州", "南通", "泉州", "温州", "绍兴", "嘉兴", "唐山", "烟台", "潍坊", "徐州", "台州", "惠州", "中山", "珠海", "江门", "泰州", "扬州", "盐城", "湖州", "淄博", "威海", "洛阳", "襄阳", "宜昌"],
    "resource": ["鄂尔多斯", "大庆", "克拉玛依", "攀枝花", "金昌", "白银", "大同", "阳泉", "晋城", "朔州", "榆林", "延安", "东营", "盘锦", "乌海", "石嘴山", "哈密", "吐鲁番", "库尔勒", "阿勒泰", "锡林郭勒", "呼伦贝尔"],
    "tourism": ["三亚", "桂林", "丽江", "张家界", "黄山", "大理", "西双版纳", "拉萨", "敦煌", "秦皇岛", "承德", "阿坝", "甘孜", "迪庆", "怒江", "林芝"],
}
ARCHETYPE = {}
for k, names in ARCHETYPE_NAMES.items():
    for n in names:
        ARCHETYPE[n] = k


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def short_name(name: str) -> str:
    name = re.sub(r"(市|县|地区|自治州|盟|林区|特别行政区)$", "", name)
    name = re.sub(r"(藏族羌族|藏族|彝族|苗族|侗族|布依族|土家族|白族|傣族|景颇族|傈僳族|哈尼族|壮族|蒙古族|朝鲜族|羌族|哈萨克族|柯尔克孜族|回族)+$", "", name)
    return name or name


def archetype_of(name: str) -> str:
    for k, v in ARCHETYPE.items():
        if k in name:
            return v
    return "balanced"


def adjusted(base: dict, mult: dict):
    v = {k: base[k] * mult.get(k, 1.0) for k in base}
    tot = sum(v.values())
    return {k: x / tot * 100 for k, x in v.items()}


def archetype_shares(kind: str):
    m = {}
    if kind == "service_mega":
        m = {"agriculture": .25, "manufacturing": .85, "information": 2.7, "finance": 2.4, "professional": 1.8,
             "real_estate": 1.2, "wholesale": 1.3, "accommodation": .9, "public_admin": 1.0}
    elif kind == "manufacturing":
        m = {"agriculture": .35, "manufacturing": 2.0, "construction": 1.2, "wholesale": 1.1, "transportation": 1.15,
             "professional": .8, "information": .8}
    elif kind == "resource":
        m = {"agriculture": .35, "mining": 7.0, "utilities": 3.0, "manufacturing": 1.2, "construction": 1.2}
    elif kind == "tourism":
        m = {"agriculture": .6, "accommodation": 3.0, "arts": 2.2, "retail": 1.3, "transportation": 1.2, "manufacturing": .55}
    return adjusted(BASE_SHARES, m), adjusted(BASE_GDP, m)


PROVINCE_URBAN_INCOME = {
    "110000": 81752, "120000": 55317, "130000": 43631, "140000": 41327, "150000": 48676, "210000": 45870,
    "220000": 40300, "230000": 39400, "310000": 84834, "320000": 63211, "330000": 74997, "340000": 47446,
    "350000": 56053, "360000": 45554, "370000": 51571, "410000": 42122, "420000": 47000, "430000": 49294,
    "440000": 59307, "450000": 41214, "460000": 42661, "500000": 47435, "510000": 45227, "520000": 42772,
    "530000": 43563, "540000": 51200, "610000": 44713, "620000": 39800, "630000": 40500, "640000": 42700,
    "650000": 42800, "710000": 52000,
}
PROVINCE_RURAL_INCOME = {
    "110000": 39500, "120000": 30800, "130000": 20600, "140000": 17600, "150000": 21200, "210000": 21400,
    "220000": 19500, "230000": 19000, "310000": 42900, "320000": 30400, "330000": 40300, "340000": 21100,
    "350000": 24500, "360000": 21300, "370000": 23700, "410000": 20000, "420000": 21200, "430000": 20900,
    "440000": 25100, "450000": 18600, "460000": 20700, "500000": 20800, "510000": 19900, "520000": 14800,
    "530000": 16400, "540000": 18200, "610000": 17000, "620000": 13100, "630000": 14000, "640000": 16000,
    "650000": 17900, "710000": 39000,
}
COLLEGE = {
    "110000": 41.9, "120000": 26.9, "130000": 12.4, "140000": 15.4, "150000": 18.7, "210000": 18.2,
    "220000": 16.3, "230000": 14.8, "310000": 33.9, "320000": 18.7, "330000": 17.3, "340000": 13.3,
    "350000": 14.5, "360000": 11.9, "370000": 14.4, "410000": 11.7, "420000": 15.5, "430000": 13.4,
    "440000": 15.7, "450000": 10.5, "460000": 13.0, "500000": 15.4, "510000": 13.3, "520000": 9.9,
    "530000": 10.8, "540000": 8.2, "610000": 18.4, "620000": 12.0, "630000": 11.6, "640000": 12.0,
    "650000": 14.3, "710000": 24.0,
}
AGING = {
    "110000": 13.3, "120000": 14.8, "130000": 15.3, "140000": 12.9, "150000": 13.1, "210000": 17.4,
    "220000": 15.6, "230000": 15.6, "310000": 16.3, "320000": 16.2, "330000": 13.3, "340000": 15.0,
    "350000": 11.1, "360000": 11.9, "370000": 15.1, "410000": 13.5, "420000": 14.6, "430000": 14.8,
    "440000": 8.6, "450000": 12.2, "460000": 10.4, "500000": 17.1, "510000": 16.9, "520000": 11.6,
    "530000": 10.8, "540000": 8.5, "610000": 13.3, "620000": 12.6, "630000": 10.0, "640000": 9.8,
    "650000": 7.8, "710000": 18.2,
}
PM25 = {
    "110000": 32, "120000": 38, "130000": 38, "140000": 36, "150000": 28, "210000": 32, "220000": 28,
    "230000": 25, "310000": 27, "320000": 33, "330000": 26, "340000": 35, "350000": 23, "360000": 30,
    "370000": 38, "410000": 45, "420000": 36, "430000": 34, "440000": 25, "450000": 27, "460000": 17,
    "500000": 35, "510000": 32, "520000": 25, "530000": 22, "540000": 12, "610000": 40, "620000": 30,
    "630000": 22, "640000": 32, "650000": 30, "710000": 15,
}

# major disasters 2000–2024, a rough public-record count for the hazards lens (not an official index)
DISASTER_INDEX = {
    "110000": 4, "120000": 3, "130000": 5, "140000": 4, "150000": 4, "210000": 3, "220000": 3,
    "230000": 3, "310000": 3, "320000": 5, "330000": 7, "340000": 6, "350000": 8, "360000": 6,
    "370000": 5, "410000": 6, "420000": 6, "430000": 7, "440000": 8, "450000": 6, "460000": 7,
    "500000": 5, "510000": 10, "520000": 6, "530000": 9, "540000": 4, "610000": 6, "620000": 6,
    "630000": 3, "640000": 3, "650000": 3, "710000": 7,
}


def area_km2(feature, alb):
    area = 0.0
    for ring in geojson_rings(feature["geometry"]):
        pts = [alb(lon, lat) for lon, lat in ring]
        s = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        area += abs(s) / 2
    return area


def largest_remainder(total: int, shares: dict) -> dict:
    raw = {k: total * v / 100.0 for k, v in shares.items()}
    out = {k: int(v) for k, v in raw.items()}
    rem = total - sum(out.values())
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[:max(0, rem)]:
        out[k] += 1
    return out


def build(world_meta: dict):
    print("build cities and states ...")
    alb = Albers(lat1=25.0, lat2=47.0, lat0=35.0, lon0=105.0)
    world = world_meta["world"]
    grid = world_meta["grid"]
    owner = np.array(world["owner"], dtype=np.int16)
    county = np.array(world["county"], dtype=np.int16)
    city_units = world_meta["city_units"]
    province_stats = {x["adcode"]: x for x in load(CACHE / "province_stats.json")}
    if "710000" not in province_stats:
        province_stats["710000"] = dict(TAIWAN_STATS)
    pref_stats = {x["adcode"]: x for x in load(CACHE / "prefecture_stats.json") if x.get("adcode")}

    # areas and centres
    unit_area = []
    unit_xy = []
    for u in city_units:
        unit_area.append(u.get("area_km2") or area_km2(u["feature"], alb))
        unit_xy.append(world_meta["project"](*u["center"]))
    unit_area = np.array(unit_area, dtype=float)
    unit_xy = np.array(unit_xy, dtype=float)

    # Per-province allocation of GDP and population.
    by_prov = defaultdict(list)
    for i, u in enumerate(city_units):
        by_prov[u["prov"]].append(i)
    gdp = np.zeros(len(city_units))
    pop = np.zeros(len(city_units))
    gdp_year = np.full(len(city_units), 2023, dtype=np.int16)
    for pcode, idxs in by_prov.items():
        ps = province_stats[pcode]
        if pcode in ("110000", "120000", "310000", "500000"):
            assert len(idxs) == 1
            gdp[idxs[0]] = ps["gdp"]
            pop[idxs[0]] = ps["population"]
            gdp_year[idxs[0]] = 2024
            continue
        if pcode == "710000":
            base_pop = sum(x[5] for x in TAIWAN_CITIES)
            base_gdp = sum(x[6] for x in TAIWAN_CITIES)
            for i in idxs:
                ad = city_units[i]["adcode"]
                base = TAIWAN_CITY_BY_CODE[ad]
                pop[i] = ps["population"] * base[5] / base_pop
                gdp[i] = ps["gdp"] * base[6] / base_gdp
                gdp_year[i] = 2024
            continue
        known = [i for i in idxs if city_units[i]["adcode"] in pref_stats]
        unknown = [i for i in idxs if i not in known]
        known_gdp = sum(pref_stats[city_units[i]["adcode"]]["gdp"] or 0 for i in known)
        known_pop = sum(pref_stats[city_units[i]["adcode"]]["population"] or 0 for i in known)
        # allocate residual to unknown by area, then scale known to fit the province total
        unknown_area = sum(unit_area[i] for i in unknown)
        if unknown and unknown_area > 0:
            reserve = min(0.25 * ps["gdp"], max(0.02 * ps["gdp"], ps["gdp"] - known_gdp if known_gdp < ps["gdp"] else 0.02 * ps["gdp"]))
            for i in unknown:
                gdp[i] = reserve * unit_area[i] / unknown_area
                pop[i] = (ps["population"] - known_pop if ps["population"] > known_pop else 0.0) * unit_area[i] / unknown_area
            target_known_gdp = ps["gdp"] - reserve
            target_known_pop = ps["population"] - sum(pop[i] for i in unknown)
        else:
            target_known_gdp = ps["gdp"]
            target_known_pop = ps["population"]
        if known_gdp > 0:
            f = target_known_gdp / known_gdp
            for i in known:
                if city_units[i]["adcode"] in pref_stats:
                    gdp[i] = pref_stats[city_units[i]["adcode"]]["gdp"] * f
                    gdp_year[i] = pref_stats[city_units[i]["adcode"]].get("year", 2023)
            f = target_known_pop / known_pop if known_pop > 0 else 1
            for i in known:
                if city_units[i]["adcode"] in pref_stats and pref_stats[city_units[i]["adcode"]].get("population"):
                    pop[i] = pref_stats[city_units[i]["adcode"]]["population"] * f
        # fallback
        for i in idxs:
            if gdp[i] <= 0:
                gdp[i] = ps["gdp"] / len(idxs)
            if pop[i] <= 0:
                pop[i] = ps["population"] / len(idxs)
    # remove rounding drift
    for pcode, idxs in by_prov.items():
        ps = province_stats[pcode]
        f = ps["gdp"] / sum(gdp[i] for i in idxs)
        for i in idxs:
            gdp[i] *= f
        f = ps["population"] / sum(pop[i] for i in idxs)
        for i in idxs:
            pop[i] *= f

    # cells per city
    def gx(i):
        c, r = grid.col_row(i)
        return grid.center(c, r)[0]

    def gy(i):
        c, r = grid.col_row(i)
        return grid.center(c, r)[1]

    cells_of = defaultdict(list)
    for cell, ci in enumerate(county):
        if ci >= 0 and owner[cell] >= 0:
            cells_of[int(ci)].append(cell)
    city_cell = []
    for ci, u in enumerate(city_units):
        cand = cells_of.get(ci, [])
        if not cand:
            # nearest land cell in the province
            st = CODE2STATE[u["prov"]]
            cand = [i for i in range(grid.size) if owner[i] == st]
        cx, cy = unit_xy[ci]
        best = min(cand, key=lambda i: (gx(i) - cx) ** 2 + (gy(i) - cy) ** 2)
        city_cell.append(best)

    # unique cell where possible: nudge duplicates to the next-nearest cell in the same county
    seen = set()
    for ci in range(len(city_units)):
        c = city_cell[ci]
        if c in seen:
            cand = [x for x in cells_of.get(ci, []) if x not in seen] or [c]
            cx, cy = unit_xy[ci]
            c = min(cand, key=lambda i: (gx(i) - cx) ** 2 + (gy(i) - cy) ** 2)
            city_cell[ci] = c
        seen.add(c)

    # city rows
    cities = []
    for ci, u in enumerate(city_units):
        pcode = u["prov"]
        ps = province_stats[pcode]
        name = short_name(u["name"])
        kind = archetype_of(name)
        shares, gdp_shares = archetype_shares(kind)
        population = max(20000, int(round(pop[ci])))
        unemployment = 0.045 + (0.01 if kind == "resource" else 0) - (0.005 if name in ("北京", "上海", "深圳") else 0)
        employed = int(round(population * 0.56 * (1 - unemployment)))
        jobs = largest_remainder(employed, shares)
        gdp_i = float(gdp[ci])
        gdp_ind = {k: gdp_i * v / 100 for k, v in gdp_shares.items()}
        yields = {
            "food": jobs["agriculture"],
            "production": jobs["manufacturing"] + jobs["mining"] + jobs["construction"] + jobs["utilities"],
            "gold": gdp_i,
            "science": jobs["information"] + jobs["professional"] + jobs["education"],
            "culture": jobs["arts"] + jobs["accommodation"],
        }
        income = PROVINCE_URBAN_INCOME[pcode] * (1.18 if kind == "service_mega" else 1.0)
        median_income = int(round(income * 2.15))
        # rent & home value from tier
        if name in ("北京", "上海", "深圳"):
            rent, home = 6200, 62000 * 85
        elif name in ("广州", "杭州", "南京", "苏州", "厦门", "天津", "成都", "武汉", "宁波", "青岛"):
            rent, home = 3600, 28000 * 95
        elif kind == "service_mega":
            rent, home = 2600, 15000 * 100
        elif kind == "manufacturing":
            rent, home = 1700, 11000 * 100
        else:
            rent, home = 1100, 6500 * 110
        rent_burden = min(0.55, rent * 12 / max(1, median_income))
        growth = (ps["population"] / ps["population_2020"] - 1) if ps.get("population_2020") else 0.0
        growth = max(-0.08, min(0.08, growth))
        pop_series = {}
        for y in range(2020, 2025):
            t = (y - 2020) / 3
            pop_series[str(y)] = int(round(population / (1 + growth) * (1 + growth * t))) if y <= 2023 else int(round(population * (1 + growth * (y - 2023) * 0.5)))
        cities.append({
            "id": u["adcode"], "name": name, "full": f"{CODE2NAME[pcode]} · {'直辖市' if pcode in ('110000','120000','310000','500000') else ('自治州' if '自治州' in u['name'] else '地级市')}",
            "states": [CODE2ABBR[pcode]], "metro": True, "capital": name == "北京",
            "x": round(unit_xy[ci][0], 1), "y": round(unit_xy[ci][1], 1), "cell": city_cell[ci],
            "population": population, "employed": employed, "yields": yields, "jobs": jobs,
            "median_income": median_income, "median_rent": rent, "home_value": home,
            "unemployment": round(unemployment, 4), "rent_burden": round(rent_burden, 4),
            "gdp": gdp_i, "gdp_year": int(gdp_year[ci]), "gdp_by_industry": gdp_ind, "gdp_undisclosed": None, "gdp_estimated": None,
            "area_km2": round(float(unit_area[ci]), 1), "rd_intensity": (4.2 if kind == "service_mega" else 2.4 if kind == "manufacturing" else 1.1 if kind == "resource" else 0.7 if kind == "tourism" else 1.5),
            "growth": round(growth, 4), "growth_years": [2020, 2023], "counties": [u["adcode"]],
            "footprint": sorted(set(cells_of.get(ci, [])) | {city_cell[ci]}), "pop_series": pop_series,
            "ranks": {}, "peers": [],
        })

    # ranks & peers
    def rank(key, reverse=True, getter=None):
        getter = getter or (lambda c: c.get(key))
        vals = [(i, getter(c)) for i, c in enumerate(cities) if getter(c) is not None]
        vals.sort(key=lambda x: x[1], reverse=reverse)
        out = {}
        last_v = None
        last_rank = 0
        for r, (i, v) in enumerate(vals, 1):
            if v != last_v:
                last_rank = r
                last_v = v
            out[i] = last_rank
        return out
    rank_fields = {
        "population": rank("population"), "gdp": rank("gdp"),
        "gdp_per_capita": rank("gdp_per_capita", getter=lambda c: c["gdp"] / c["population"]),
        "growth": rank("growth"),
        "food": rank("food", getter=lambda c: c["yields"]["food"]),
        "production": rank("production", getter=lambda c: c["yields"]["production"]),
        "gold": rank("gold", getter=lambda c: c["yields"]["gold"]),
        "science": rank("science", getter=lambda c: c["yields"]["science"]),
        "culture": rank("culture", getter=lambda c: c["yields"]["culture"]),
    }
    for key, rk in rank_fields.items():
        for i, c in enumerate(cities):
            c["ranks"][key] = rk.get(i)
    pops = [c["population"] for c in cities]
    for i, c in enumerate(cities):
        order = sorted(range(len(cities)), key=lambda j: abs(math.log(pops[i] / max(1, pops[j]))))
        c["peers"] = [cities[j]["id"] for j in order if j != i][:5]

    # state rows
    states = []
    for st, (pcode, name, abbr) in enumerate(PROVINCES):
        ps = province_stats[pcode]
        idxs = by_prov[pcode]
        state_cities = [cities[i] for i in idxs]
        jobs = {k: sum(c["jobs"][k] for c in state_cities) for k in INDUSTRIES}
        gdp_ind = {k: sum(c["gdp_by_industry"][k] for c in state_cities) for k in INDUSTRIES}
        yields = {
            "food": jobs["agriculture"],
            "production": jobs["manufacturing"] + jobs["mining"] + jobs["construction"] + jobs["utilities"],
            "gold": ps["gdp"],
            "science": jobs["information"] + jobs["professional"] + jobs["education"],
            "culture": jobs["arts"] + jobs["accommodation"],
        }
        growth = (ps["population"] / ps["population_2020"] - 1) if ps.get("population_2020") else 0.0
        # land shares over state cells
        land = {}
        cells = [i for i in range(grid.size) if owner[i] == st]
        for k in ["forest", "crop", "pasture", "grass", "shrub", "wetland", "developed"]:
            vals = [world["pct"][k][i] for i in cells if world["cover"][i] > 0]
            land[k] = round(sum(vals) / len(vals) / 100, 4) if vals else None
        states.append({
            "fips": pcode[:2], "abbr": abbr, "name": name,
            "population": int(ps["population"]), "employed": sum(c["employed"] for c in state_cities),
            "yields": yields, "jobs": jobs,
            "median_income": int(round(np.average([c["median_income"] for c in state_cities], weights=[c["population"] for c in state_cities]))),
            "median_rent": int(round(np.mean([c["median_rent"] for c in state_cities]))),
            "home_value": int(round(np.mean([c["home_value"] for c in state_cities]))),
            "unemployment": round(float(np.mean([c["unemployment"] for c in state_cities])), 4),
            "rent_burden": round(float(np.mean([c["rent_burden"] for c in state_cities])), 4),
            "gdp": ps["gdp"], "gdp_year": 2024, "gdp_by_industry": gdp_ind,
            "growth": round(growth, 4), "growth_years": [2020, 2023],
            "urban_rate": round((ps.get("urban_population") or ps["population"] * 0.62) / ps["population"], 4),
            "aging": AGING[pcode], "bachelors": COLLEGE[pcode], "rural_income": PROVINCE_RURAL_INCOME[pcode],
            "disaster_index": DISASTER_INDEX[pcode], "pm25": PM25[pcode],
            "land": land, "energy": None, "ranks": {}, "label": None,
        })
    # state ranks per yield
    for y in ["food", "production", "gold", "science", "culture"]:
        order = sorted(range(len(states)), key=lambda i: states[i]["yields"][y], reverse=True)
        for rank_i, i in enumerate(order, 1):
            states[i]["ranks"][y] = rank_i

    nation = {
        "population": sum(s["population"] for s in states),
        "employed": sum(s["employed"] for s in states),
        "gdp": sum(s["gdp"] for s in states), "gdp_year": 2024,
        "gdp_by_industry": {k: sum(s["gdp_by_industry"][k] for s in states) for k in INDUSTRIES},
        "jobs": {k: sum(s["jobs"][k] for s in states) for k in INDUSTRIES},
        "median_income": int(round(np.average([s["median_income"] for s in states], weights=[s["population"] for s in states]))),
        "median_rent": int(round(np.average([s["median_rent"] for s in states], weights=[s["population"] for s in states]))),
        "home_value": int(round(np.average([s["home_value"] for s in states], weights=[s["population"] for s in states]))),
        "unemployment": round(float(np.average([s["unemployment"] for s in states], weights=[s["population"] for s in states])), 4),
        "rent_burden": round(float(np.average([s["rent_burden"] for s in states], weights=[s["population"] for s in states])), 4),
        "growth": round(sum(s["population"] for s in states) / sum(province_stats[c]["population_2020"] for c in CODE2NAME if province_stats[c].get("population_2020")) - 1, 4),
        "growth_years": [2020, 2023],
    }
    for y in ["food", "production", "gold", "science", "culture"]:
        nation.setdefault("yields", {})[y] = sum(s["yields"][y] for s in states)

    (OUT / "cities.json").write_text(json.dumps(cities, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "states.json").write_text(json.dumps(states, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  cities", len(cities), "states", len(states), "GDP", round(nation["gdp"] / 1e12, 2), "T CNY")
    return {"cities": cities, "states": states, "nation_core": nation, "cells_of": cells_of, "city_cell": city_cell}


if __name__ == "__main__":
    wm = json.loads((OUT / "world.json").read_text())
    # quick standalone needs grid metadata; normally build_all passes world_meta
    print("run build_all.py instead")
