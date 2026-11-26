#!/usr/bin/env python3
"""Districts and city-type badges."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "data"

CATALOG = [
    {"id": "campus", "name": "学府区", "icon": "d-campus", "color": "#4a7bd0",
     "description": "高校、科研院所、软件与数据服务集中的城区。", "caveat": None},
    {"id": "commercial_hub", "name": "商务中心", "icon": "d-commercial-hub", "color": "#c9a45c",
     "description": "金融、批发、保险与总部经济集中的城区。", "caveat": None},
    {"id": "industrial_zone", "name": "工业区", "icon": "d-industrial-zone", "color": "#a05a32",
     "description": "制造、采矿、化工与能源加工集中的城区。", "caveat": None},
    {"id": "harbor", "name": "港口", "icon": "d-harbor", "color": "#2b6d96",
     "description": "沿海或沿江港口与航运服务。", "caveat": "内河港口按城市中心近似。"},
    {"id": "theater_square", "name": "文化广场", "icon": "d-theater-square", "color": "#8a5a9a",
     "description": "文化、体育、传媒与艺术机构集中的城区。", "caveat": None},
    {"id": "entertainment_complex", "name": "休闲区", "icon": "d-entertainment-complex", "color": "#b06a8a",
     "description": "住宿、餐饮、购物与娱乐业集中的城区。", "caveat": None},
    {"id": "aerodrome", "name": "航空港", "icon": "d-aerodrome", "color": "#5a7a9a",
     "description": "机场、航空运输与临空产业。", "caveat": None},
    {"id": "government_plaza", "name": "政务区", "icon": "d-government-plaza", "color": "#7a6a4a",
     "description": "党政机关、公共管理与社会组织集中的城区。", "caveat": None},
    {"id": "encampment", "name": "驻防", "icon": "d-encampment", "color": "#8796ab",
     "description": "公开资料中的军事机关与院校驻地（仅用于地图示意）。", "caveat": "不包含任何非公开部署信息。"},
    {"id": "aqueduct", "name": "水利枢纽", "icon": "d-aqueduct", "color": "#3a7a8a",
     "description": "电力、热力、燃气与水生产供应。", "caveat": None},
]

BADGE = {
    "campus": "科技城", "commercial_hub": "金融城", "industrial_zone": "制造之都", "harbor": "港城",
    "theater_square": "文化名城", "entertainment_complex": "休闲之城", "aerodrome": "航空枢纽",
    "government_plaza": "政治中心", "encampment": "军事重镇", "aqueduct": "能源之城",
}
PORT_CITIES = {"上海", "宁波", "舟山", "唐山", "青岛", "广州", "日照", "苏州", "天津", "烟台", "大连", "厦门", "福州", "泉州", "深圳", "连云港", "南通", "南京", "武汉", "重庆", "芜湖", "九江", "岳阳"}
AIRPORT_CITIES = {"北京", "上海", "广州", "深圳", "成都", "重庆", "昆明", "西安", "杭州", "南京", "厦门", "长沙", "武汉", "郑州", "青岛", "海口", "乌鲁木齐", "三亚", "贵阳", "哈尔滨", "沈阳", "济南", "天津", "大连", "福州", "南宁", "宁波"}
SPECIAL_BADGE = {
    "北京": "首都", "上海": "金融之城", "深圳": "科技之城", "广州": "商贸之城", "杭州": "数字之城",
    "成都": "休闲之都", "重庆": "山城", "武汉": "江城", "西安": "古都", "苏州": "制造之城",
    "东莞": "世界工厂", "佛山": "制造之城", "宁波": "港城", "青岛": "帆船之都", "厦门": "海上花园",
    "唐山": "钢铁之城", "大庆": "石油之城", "鄂尔多斯": "能源之城", "三亚": "旅游名城",
    "桂林": "山水名城", "丽江": "古城", "张家界": "旅游名城", "黄山": "旅游名城", "拉萨": "高原古城",
}


def build(cities, nation_full):
    print("build districts ...")
    nation = nation_full.get("nation", nation_full)
    industries = nation_full.get("industries", nation.get("industries", {}))
    nat_jobs = nation["jobs"]
    nat_emp = nation["employed"]
    nat_shares = {k: v / nat_emp for k, v in nat_jobs.items()}
    catalog = CATALOG
    cat_by_id = {c["id"]: c for c in catalog}
    # national reference per district
    nat_dist = {
        "campus": nat_shares["information"] + nat_shares["professional"] + nat_shares["education"],
        "commercial_hub": nat_shares["finance"] + nat_shares["wholesale"] + nat_shares["retail"] * 0.3,
        "industrial_zone": nat_shares["manufacturing"] + nat_shares["mining"] + nat_shares["construction"] * 0.4,
        "harbor": nat_shares["transportation"] * 0.20,
        "theater_square": nat_shares["arts"],
        "entertainment_complex": nat_shares["accommodation"] + nat_shares["retail"] * 0.3,
        "aerodrome": nat_shares["transportation"] * 0.12,
        "government_plaza": nat_shares["public_admin"] + nat_shares["admin"] * 0.5,
        "encampment": 0.0001,
        "aqueduct": nat_shares["utilities"],
    }
    city_out = {}
    county_out = {}
    for c in cities:
        j = c["jobs"]
        emp = c["employed"]
        name = c["name"]
        vals = {
            "campus": j["information"] + j["professional"] + j["education"],
            "commercial_hub": j["finance"] + j["wholesale"] + j["retail"] * 0.3,
            "industrial_zone": j["manufacturing"] + j["mining"] + j["construction"] * 0.4,
            "harbor": (j["transportation"] * 0.25 + j["wholesale"] * 0.1) if name in PORT_CITIES else 0,
            "theater_square": j["arts"],
            "entertainment_complex": j["accommodation"] + j["retail"] * 0.3,
            "aerodrome": (j["transportation"] * 0.30) if name in AIRPORT_CITIES else 0,
            "government_plaza": j["public_admin"] + j["admin"] * 0.5,
            "encampment": 0,
            "aqueduct": j["utilities"],
        }
        ds = []
        for did, val in vals.items():
            if val <= 0:
                continue
            share = val / emp
            nshare = nat_dist.get(did, 0.0001)
            lq = share / nshare if nshare > 0 else 0
            if (lq >= 1.25 and val >= 1000) or (share >= 0.01 and lq >= 1.1):
                ds.append({"id": did, "lq": round(lq, 2), "emp": int(val), "share": round(share, 4),
                           "avg_pay": c["median_income"], "sub": None, "sub_lq": None, "sub_emp": None,
                           "via": "broad", "strength": round(val - val / lq if lq > 0 else val, 0),
                           "suppressed": 0, "lower_bound": False})
        ds.sort(key=lambda x: x["strength"], reverse=True)
        ds = ds[:5]
        badge = None
        if name in SPECIAL_BADGE:
            badge = {"id": "special", "label": SPECIAL_BADGE[name], "district": ds[0]["id"] if ds else None, "basis": "curated", "text": "按城市真实产业与城市职能命名。"}
        elif ds:
            top = ds[0]
            badge = {"id": top["id"], "label": BADGE.get(top["id"], "综合城市"), "district": top["id"], "basis": "model",
                     "text": f"{cat_by_id[top['id']]['name']}就业占全市 {top['share']*100:.1f}%，为全国平均的 {top['lq']:.1f} ×。"}
        city_out[c["id"]] = {"emp": emp, "avg_pay": c["median_income"], "counties": [1, 1],
                             "top": [{"naics": d["id"], "emp": d["emp"], "lq": d["lq"], "avg_pay": d["avg_pay"], "oty_pct": 0.01, "suppressed": 0, "lower_bound": False} for d in ds],
                             "districts": ds, "badge": badge}
        county_out[c["id"]] = {"emp": emp, "districts": [[d["id"], d["lq"], d["emp"]] for d in ds]}
    data = {"version": 1, "vintage": "2023 年城市统计与行业结构模型", "year": 2023, "sources": ["nbs_prefecture", "nbs_province"],
            "rule": {"min_lq": 1.25, "min_jobs": 1000, "min_share": 0.01, "specialty_lq": 3.0, "specialty_jobs": 5000,
                     "specialty_share": 0.005, "max_per_city": 5, "harbor_needs_water": True, "badge_lq": 6.0,
                     "badge_share": 0.03, "college_share": 0.15,
                     "text": "城区类型由行业就业份额与全国平均的区位商（LQ）判定：LQ ≥ 1.25 且就业 ≥ 1,000 人，或就业占比 ≥ 1% 且 LQ ≥ 1.1；每个城市最多取 5 个最强城区。",
                     "county_note": "地级市即一个县级单元，因此县级城区与市级相同。"},
            "catalog": catalog, "industries": {k: {"title": v, "us_emp": nation["jobs"].get(k, 0)} for k, v in industries.items()},
            "national": {"emp": nat_emp, "avg_pay": nation["median_income"]}, "cities": city_out, "counties": county_out}
    (OUT / "districts.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  districts", len(city_out))
    return data
