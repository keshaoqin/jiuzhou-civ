#!/usr/bin/env python3
"""Counties.json (here: prefecture-level units) for 九州."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "data"

COLS = [
    ("geoid", "代码", "text", None, "neutral", "datav", "行政区划代码。"),
    ("name", "地市", "text", None, "neutral", "datav", "地级行政单元名称。"),
    ("state", "省份", "text", None, "neutral", "datav", "所属省级行政区。"),
    ("population", "常住人口", "int", "人", "neutral", "nbs_prefecture", "2023 年常住人口。"),
    ("land_km2", "土地面积", "km2", "平方公里", "neutral", "datav", "行政单元面积。"),
    ("density", "人口密度", "float", "人/平方公里", "neutral", "nbs_prefecture", "人口 ÷ 土地面积。"),
    ("income", "城镇居民收入", "int", "元/年", "good", "nbs_province", "城镇居民人均可支配收入。"),
    ("home_value", "住房总价", "int", "元", "neutral", "nbs_prefecture", "90 平方米住房估算总价。"),
    ("poverty", "相对低收入面", "pct", "0–1", "bad", "model", "按城乡收入差距构造的相对指标，不是官方贫困率。"),
    ("median_age", "年龄中位数", "float", "岁", "neutral", "nbs_province", "按省级年龄结构估算。"),
    ("foreign_born", "省外迁入", "pct", "0–1", "neutral", "model", "省外常住人口占比估算。"),
    ("bachelors", "大专以上", "pct", "0–1", "good", "nbs_province", "2020 年人口普查大专及以上占比。"),
    ("broadband", "宽带普及", "pct", "0–1", "good", "model", "家庭宽带渗透率估算。"),
    ("commute", "通勤时间", "float", "分钟", "bad", "model", "单程通勤时间估算。"),
    ("homeownership", "住房自有", "pct", "0–1", "neutral", "model", "自有住房比例估算。"),
    ("uninsured", "未参保", "pct", "0–1", "bad", "model", "基本医疗保险未覆盖比例估算。"),
    ("forest", "森林", "pct", "0–1", "good", "landcover_model", "格内森林占比均值。"),
    ("crop", "耕地", "pct", "0–1", "neutral", "landcover_model", "格内耕地占比均值。"),
    ("pasture", "牧草", "pct", "0–1", "neutral", "landcover_model", "格内牧草地占比均值。"),
    ("developed", "建设用地", "pct", "0–1", "neutral", "landcover_model", "格内建设用地占比均值。"),
    ("cbsa", "所属城市", "text", None, "neutral", "datav", "对应的 cities.json 城市 id。"),
    ("cell", "代表格", "int", None, "neutral", "hex", "离市中心最近的陆地六边形格。"),
    ("amenities", "生活便利度", "float", "指数", "good", "model", "按城市等级与服务业密度构造的便利度指数。"),
    ("disasters", "灾害记录", "int", "次", "bad", "disaster_index", "2000–2024 重大自然灾害记录次数。"),
]


def build(cities, world):
    rows = []
    for c in cities:
        cells = [i for i in c.get("footprint", []) if i >= 0]
        land_vals = {}
        for k in ["forest", "crop", "pasture", "developed"]:
            vals = [world["pct"][k][i] for i in cells] or [0]
            land_vals[k] = round(sum(vals) / len(vals) / 100, 4)
        density = c["population"] / max(1.0, c.get("area_km2") or 1.0)
        urban = 0.75 if c["name"] in ("北京", "上海", "深圳", "广州") else 0.62
        rows.append([
            c["id"], c["name"], c["states"][0], c["population"], c.get("area_km2") or 0, round(density, 1),
            c["median_income"], c["home_value"], round(min(0.25, max(0.02, 0.03 + max(0, 30000 - (c.get("rural_income") or 20000)) / 30000 * 0.12)), 4),
            round(32 + (c.get("aging") or 13) * 0.55, 1), round(min(0.12, 0.004 + (0.02 if c["name"] in ("深圳", "上海", "北京", "广州", "杭州") else 0.004)), 4),
            round((c.get("bachelors") or 13) / 100, 4), round(min(0.98, 0.80 + (0.12 if urban > 0.7 else 0)), 4),
            round(32 - urban * 12 + 4, 1), round(max(0.55, 0.96 - urban * 0.25), 4), round(0.02 + (1 - urban) * 0.04, 4),
            land_vals["forest"], land_vals["crop"], land_vals["pasture"], land_vals["developed"],
            c["id"], c["cell"], round(55 + urban * 25 + (0.1 if c["name"] in ("上海", "北京") else 0), 1),
            c.get("disaster_index") or 4,
        ])
    fields = [{"key": k, "label": label, "format": fmt, "unit": unit, "higher_is": hi, "source": src, "description": desc}
              for k, label, fmt, unit, hi, src, desc in COLS]
    data = {"vintage": "国家统计局 2023–2024 · 地级市数据", "fields": fields, "columns": [c[0] for c in COLS], "rows": rows}
    (OUT / "counties.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  counties", len(rows))
    return data
