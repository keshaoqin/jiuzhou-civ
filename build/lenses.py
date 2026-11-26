#!/usr/bin/env python3
"""Build lenses.json (19 map lenses) for 九州."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "cache"
OUT = ROOT / "web" / "data"

GROUPS = [
    {"id": "people", "name": "人口"},
    {"id": "economy", "name": "经济"},
    {"id": "prosperity", "name": "民生"},
    {"id": "knowledge", "name": "科教"},
    {"id": "land", "name": "土地"},
    {"id": "hazards", "name": "灾害与环境"},
    {"id": "energy", "name": "能源"},
]

P = lambda *c: list(c)


def build(world_meta, cities, states, resources):
    world = world_meta["world"]
    grid = world_meta["grid"]
    n = grid.size
    owner = np.array(world["owner"])
    county = np.array(world["county"])
    pct = world["pct"]
    city_by_idx = {i: c for i, c in enumerate(cities)}
    province_by_abbr = {s["abbr"]: s for s in states}

    def gx(i):
        c, r = grid.col_row(i)
        return grid.center(c, r)[0]

    def gy(i):
        c, r = grid.col_row(i)
        return grid.center(c, r)[1]

    pop_cell = np.zeros(n)
    gdp_cell = np.zeros(n)
    city_of_cell = np.full(n, -1, dtype=np.int16)
    for ci, c in enumerate(cities):
        cells = c.get("footprint") or []
        if not cells:
            continue
        d = np.array([math.hypot(gx(i) - c["x"], gy(i) - c["y"]) for i in cells])
        wp = 1.0 / (1.0 + (d / 9.0) ** 2) ** 1.5
        wg = np.exp(-(d / 14.0) ** 2)
        wp = wp / wp.sum()
        wg = wg / wg.sum()
        for k, i in enumerate(cells):
            pop_cell[i] = c["population"] * wp[k]
            gdp_cell[i] = c["gdp"] * wg[k]
            city_of_cell[i] = ci

    CELL_KM2 = 1.5 * math.sqrt(3) * 25 * 25
    mw_by_city = {c["id"]: 0.0 for c in cities}
    for it in resources.get("items", []):
        if it.get("cbsa") in mw_by_city and it.get("value"):
            mw_by_city[it["cbsa"]] += it["value"]

    # per-cell base values for city metrics
    val = {}
    for key in ["density", "gdp_cell", "gdp_pc", "urban", "aging", "growth", "income", "rural_income", "home", "unemployment",
                "bachelors", "rd", "forest", "crop", "elev", "relief", "disasters", "pm25", "energy"]:
        val[key] = [None] * n
    for i in range(n):
        if owner[i] < 0 or city_of_cell[i] < 0:
            continue
        c = cities[city_of_cell[i]]
        s = province_by_abbr.get(c["states"][0])
        val["density"][i] = round(pop_cell[i] / CELL_KM2, 2)
        val["gdp_cell"][i] = round(gdp_cell[i] / 1e8, 2)
        val["gdp_pc"][i] = round(c["gdp"] / c["population"], 0)
        urban = (s.get("urban_rate") if s else None) or 0.62
        val["urban"][i] = urban
        val["aging"][i] = (s.get("aging") if s else 13.0) / 100
        val["growth"][i] = c["growth"]
        val["income"][i] = c["median_income"]
        val["rural_income"][i] = (s.get("rural_income") if s else 20000)
        val["home"][i] = round(c["home_value"] / 90)
        val["unemployment"][i] = c["unemployment"]
        val["bachelors"][i] = (s.get("bachelors") if s else 13.0) / 100
        val["rd"][i] = c.get("rd_intensity", 1.5) / 100
        val["forest"][i] = pct["forest"][i] / 100
        val["crop"][i] = pct["crop"][i] / 100
        val["elev"][i] = world["elev"][i]
        val["relief"][i] = world["relief"][i]
        val["disasters"][i] = (s.get("disaster_index") if s else 4)
        val["pm25"][i] = (s.get("pm25") if s else 30)
        val["energy"][i] = mw_by_city.get(c["id"], 0)

    def domain(vals, log=False):
        v = [x for x in vals if x is not None and (x > 0 if log else True)]
        if not v:
            return [0, 1]
        lo, hi = np.percentile(v, 2), np.percentile(v, 98)
        if lo == hi:
            hi = lo + 1
        if log:
            lo = max(lo, 0.01)
        return [round(float(lo), 4), round(float(hi), 4)]

    def lens(id, group, name, icon, emoji, unit, fmt, scale, ramp, higher, source, desc, note=None, values=None):
        if values is None:
            values = val.get({"gdp": "gdp_cell"}.get(id, id), [None] * n)
        d = domain(values, scale == "log")
        return {"id": id, "group": group, "name": name, "icon": icon, "emoji": emoji, "unit": unit,
                "format": fmt, "scale": scale, "domain": d, "ramp": ramp, "higher_is": higher,
                "source": source, "description": desc, "values": values, **({"note": note} if note else {})}

    lenses = [
        lens("density", "people", "人口密度", "l-people", "👥", "人 / 平方公里", "float", "log",
             P("#1c1035", "#4b2377", "#9a3b8a", "#e0645e", "#f4b25a"), "neutral", "nbs_prefecture",
             "每一格按所属地级市常住人口与格内人口权重分配：中心城区权重高、外围低。密度 = 人口 ÷ 1,624 平方公里。",
             "地级市内部的人口分布是模型分配，不是逐格普查。"),
        lens("gdp", "economy", "GDP 总量", "y-gold", "💰", "亿元 / 格", "float", "log",
             P("#1b1035", "#4b2377", "#9a3b8a", "#e0645e", "#f4b25a"), "neutral", "nbs_prefecture",
             "每一格按所属地级市 GDP 与距市中心距离分配；中心城区更集中。", "地级市内部产出分布为估算。"),
        lens("gdp_pc", "economy", "人均 GDP", "l-income", "💵", "元 / 人", "int", "log",
             P("#2b1a0e", "#6b4423", "#b07a3d", "#d9b36a", "#f5e2ad"), "good", "nbs_prefecture",
             "地级市 GDP ÷ 常住人口。资源型城市因少数大企业而人均值偏高，不代表居民收入。"),
        lens("urban", "people", "城镇化率", "l-developed", "🏙️", "%", "pct", "linear",
             P("#e7e0cd", "#b9c7b6", "#7fa39a", "#4a7a78", "#1f4f57"), "good", "nbs_province",
             "省级常住人口城镇化率，地级市沿用省值并略作城区调整。"),
        lens("aging", "people", "65岁以上人口", "l-people", "👴", "%", "pct", "linear",
             P("#f5efe0", "#e6cba0", "#d49a65", "#b45a45", "#7d2f35"), "bad", "nbs_province",
             "省级 2020 年人口普查 65 岁及以上人口占比。"),
        lens("growth", "people", "人口增长", "l-people", "📈", "2020–2023 变化", "pct", "linear",
             P("#8b2f35", "#d17a5a", "#e8dcc0", "#7fa27c", "#2f6b4f"), "neutral", "nbs_province",
             "2020 年普查到 2023 年常住人口变化；东北与部分资源型城市为负增长。"),
        lens("income", "prosperity", "城镇居民收入", "l-income", "💵", "元 / 年", "int", "log",
             P("#2b1a0e", "#6b4423", "#b07a3d", "#d9b36a", "#f5e2ad"), "good", "nbs_province",
             "省级城镇居民人均可支配收入（2023）。地级市按城市类型微调。"),
        lens("rural_income", "prosperity", "农村居民收入", "l-income", "🌾", "元 / 年", "int", "log",
             P("#2b1a0e", "#6b4423", "#b07a3d", "#d9b36a", "#f5e2ad"), "good", "nbs_province",
             "省级农村居民人均可支配收入（2023）。"),
        lens("home", "prosperity", "住房单价", "l-home", "🏠", "元 / 平方米", "int", "log",
             P("#2b1a0e", "#6b4423", "#b07a3d", "#d9b36a", "#f5e2ad"), "bad", "nbs_prefecture",
             "城市住房单价估算，用于比较居住成本；不是官方房价指数。"),
        lens("unemployment", "prosperity", "城镇调查失业率", "unemployment", "😐", "%", "pct", "linear",
             P("#e7e0cd", "#d9c5a0", "#cf9d70", "#b85c4a", "#7d2f35"), "bad", "nbs_province",
             "省级城镇调查失业率附近值；不同城市按产业结构微调。"),
        lens("bachelors", "knowledge", "大专以上人口", "l-degrees", "🎓", "%", "pct", "linear",
             P("#1c1035", "#2d4a7a", "#4a7a9a", "#8fc1c9", "#e8f4f2"), "good", "nbs_province",
             "省级 2020 年人口普查大专及以上受教育程度人口占比。"),
        lens("rd", "knowledge", "研发强度", "y-science", "🔬", "R&D / GDP", "pct", "linear",
             P("#1c1035", "#2d4a7a", "#4a7a9a", "#8fc1c9", "#e8f4f2"), "good", "nbs_province",
             "按城市类型估算的 R&D 经费占 GDP 比重；北京、深圳、上海最高。", "城市层面为估算值。"),
        lens("forest", "land", "森林覆盖率", "l-forest", "🌲", "%", "pct", "linear",
             P("#d9c9a3", "#9dbb72", "#5f9a54", "#2f6b3a", "#173f2a"), "good", "landcover_model",
             "每一格的森林占土地样本比例（生态分区模型，按省级森林覆盖率校准）。"),
        lens("crop", "land", "耕地占比", "l-farmland", "🌾", "%", "pct", "linear",
             P("#8a7a5a", "#c2b84e", "#d9c96a", "#a8b25a", "#4f7a35"), "neutral", "landcover_model",
             "每一格的耕地占土地样本比例（生态分区模型）。"),
        lens("elev", "land", "平均海拔", "terrain", "⛰️", "米", "int", "linear",
             P("#2f6b3a", "#8fb04e", "#c9b07a", "#a88a6a", "#e8eef2"), "neutral", "etopo", "每一格 7 个采样点的平均高程。"),
        lens("relief", "land", "地形起伏", "terrain", "🗻", "0–3 级", "int", "linear",
             P("#7fbf5f", "#c9b07a", "#9a8068", "#e8eef2"), "neutral", "etopo",
             "0 平原、1 丘陵、2 山地、3 高原极高山（按格内高程标准差与均值分级）。"),
        lens("disasters", "hazards", "灾害记录", "l-disasters", "🌪️", "2000–2024 重大灾害次数", "int", "linear",
             P("#f5efe0", "#e8c46a", "#d98b45", "#b8503a", "#70232a"), "bad", "disaster_index",
             "按公开重大自然灾害记录整理的省级灾害次数（地震、洪涝、台风、干旱等），为近似指数。",
             "灾害次数不等于损失：一次大灾可能影响多个省。"),
        lens("pm25", "hazards", "PM2.5", "l-amenities", "🌫️", "微克 / 立方米", "int", "linear",
             P("#e8f4f2", "#c9d9b0", "#e0c26a", "#c77a4a", "#7d2f35"), "bad", "nbs_province",
             "省级年均 PM2.5 浓度近似值（2023 前后）。"),
        lens("energy", "energy", "电站装机", "r-coal_plant", "⚡", "MW / 市", "int", "log",
             P("#1c1035", "#2d4a7a", "#4a7a9a", "#e0a93a", "#b8503a"), "good", "wri_power",
             "每市地图上标出的规模以上电站装机合计（核电、煤电、气电、水电、风电、光伏、生物质）。",
             "只含地图标出的站点，不是全市总装机。"),
    ]

    data = {"vintage": "国家统计局 2023–2024 · 地级市数据 2019–2024", "groups": GROUPS, "lenses": lenses}
    (OUT / "lenses.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  lenses", len(lenses))
    return data
