#!/usr/bin/env python3
"""nation.json and sources.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "data"

INDUSTRIES = {
    "agriculture": "农林牧渔业", "mining": "采矿业", "construction": "建筑业", "manufacturing": "制造业",
    "wholesale": "批发业", "retail": "零售业", "transportation": "交通运输、仓储和邮政", "utilities": "电力、热力、燃气及水",
    "information": "信息传输与软件", "finance": "金融业", "real_estate": "房地产业", "professional": "科研与专业技术服务",
    "management": "企业管理服务", "admin": "公共管理与社会组织", "education": "教育", "health": "卫生与社会工作",
    "arts": "文化、体育和娱乐", "accommodation": "住宿和餐饮", "other": "其他服务业", "public_admin": "公共管理",
}

YIELDS = [
    {"key": "food", "icon": "y-food", "emoji": "🌾", "label": "粮食", "color": "#7fbf3f", "unit": "workers",
     "description": "农林牧渔业从业人员。按常住地就业统计，反映乡村与农业比重。"},
    {"key": "production", "icon": "y-production", "emoji": "⚙️", "label": "生产", "color": "#d08a3e", "unit": "workers",
     "description": "制造、采矿、建筑与公用事业从业人员。"},
    {"key": "gold", "icon": "y-gold", "emoji": "💰", "label": "金币", "color": "#e6b84a", "unit": "usd",
     "description": "地区生产总值（GDP），按当年价格计算，单位人民币。这是地图上的「金币」产出。"},
    {"key": "science", "icon": "y-science", "emoji": "🔬", "label": "科技", "color": "#5b9bd5", "unit": "workers",
     "description": "信息、科研、专业技术与教育从业人员。"},
    {"key": "culture", "icon": "y-culture", "emoji": "🎭", "label": "文化", "color": "#b07cc6", "unit": "workers",
     "description": "文化、体育、娱乐、住宿与餐饮从业人员。"},
]

SOURCES = [
    {"id": "nbs_province", "title": "中国统计年鉴 / 各省统计公报（省级面板）", "publisher": "国家统计局及各省统计局",
     "homepage": "https://www.stats.gov.cn/", "license": "政府公开统计数据（合理引用）",
     "description": "31 个省级行政区的 GDP、常住人口、城镇化率、城乡居民收入、受教育程度等年度数据；2024 年 GDP、2023 年人口为主。",
     "used_for": ["省级 GDP 与人口", "收入与城镇化镜头", "省级汇总"], "vintage": "2023–2024",
     "files": [{"file": "province_stats.json", "url": "https://www.stats.gov.cn/sj/ndsj/", "retrieved": "2026-11-26", "bytes": 12000}]},
    {"id": "taiwan_stats", "title": "台湾地区统计资料（公开整理）", "publisher": "台湾地区统计部门及公开年鉴",
     "homepage": "https://www.stat.gov.tw/", "license": "公开统计数据（合理引用）",
     "description": "台湾地区 2023–2024 年人口、GDP、城镇化与主要城市/县人口、GDP 的近似整理；城市值用于地图分配，不是官方逐市统计。",
     "used_for": ["台湾省级与城市数据"], "vintage": "2023–2024",
     "files": [{"file": "taiwan.py", "url": "", "retrieved": "2026-11-26", "bytes": 0}]},
    {"id": "nbs_prefecture", "title": "中国城市统计年鉴 / 地级市统计公报", "publisher": "国家统计局城市社会经济调查司",
     "homepage": "https://www.stats.gov.cn/", "license": "政府公开统计数据（合理引用）",
     "description": "333 个地级及以上城市（含 4 个直辖市）的 GDP、GDP 人均、人口与产业结构的公开整理；部分城市为 2019–2024 年最新可得值。",
     "used_for": ["城市 GDP / 人口", "城市面板", "镜头分配"], "vintage": "2019–2024",
     "files": [{"file": "prefecture_stats.json", "url": "https://www.stats.gov.cn/sj/ndsj/", "retrieved": "2026-11-26", "bytes": 100000}]},
    {"id": "datav", "title": "DataV GeoAtlas 中国行政区划边界", "publisher": "阿里云 DataV",
     "homepage": "https://datav.aliyun.com/portal/school/atlas/area_selector", "license": "公开地图边界数据（仅用于可视化）",
     "description": "省、地级行政单元 GeoJSON 边界与行政中心坐标，用于六边形网格归属和城市定位。",
     "used_for": ["地图边界", "城市中心", "网格归属"], "vintage": "2024",
     "files": [{"file": "datav_china.json", "url": "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json", "retrieved": "2026-11-26", "bytes": 583000}]},
    {"id": "etopo", "title": "AWS Terrarium / Mapzen 地形瓦片（ETOPO 类）", "publisher": "Amazon Web Services / Mapzen",
     "homepage": "https://registry.opendata.aws/terrain-tiles/", "license": "Open data (CC-BY / public domain)",
     "description": "全球高程瓦片，缩放 6 级约 2 km 分辨率；每格取 7 个采样点计算平均高程、起伏与山体阴影。",
     "used_for": ["海拔", "地形起伏", "地图底纹"], "vintage": "2021",
     "files": [{"file": "terrain/6/*.png", "url": "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/6/{x}/{y}.png", "retrieved": "2026-11-26", "bytes": 4500000}]},
    {"id": "landcover_model", "title": "生态分区土地覆盖模型", "publisher": "本项目（基于气候带、地形与省级森林覆盖率校准）",
     "homepage": "", "license": "本项目生成（CC-BY 4.0）",
     "description": "按经度、纬度、海拔、起伏与城市距离生成森林、耕地、草地、荒漠、湿地与建设用地比例，并用各省森林覆盖率校准。不是逐像元遥感分类。",
     "used_for": ["土地覆盖", "森林/耕地镜头", "地图上色"], "vintage": "2024",
     "files": [{"file": "world.json#pct", "url": "", "retrieved": "2026-11-26", "bytes": 0}]},
    {"id": "disaster_index", "title": "重大自然灾害公开记录整理", "publisher": "中国地震台网、应急管理部、气象局公开信息",
     "homepage": "https://www.mem.gov.cn/", "license": "政府公开信息（合理引用）",
     "description": "2000–2024 年地震、洪涝、台风、干旱、滑坡等重大灾害事件的省级次数整理，为近似指数，不等同于损失。",
     "used_for": ["灾害镜头", "灾害说明"], "vintage": "2000–2024",
     "files": [{"file": "disaster_index", "url": "https://www.mem.gov.cn/", "retrieved": "2026-11-26", "bytes": 0}]},
    {"id": "wri_power", "title": "Global Power Plant Database", "publisher": "World Resources Institute",
     "homepage": "https://datasets.wri.org/dataset/globalpowerplantdatabase", "license": "CC-BY 4.0",
     "description": "全球电厂位置、燃料类型与装机容量；中国部分按容量阈值筛选后上图。",
     "used_for": ["电厂点位", "能源镜头", "省级装机"], "vintage": "2021",
     "files": [{"file": "global_power_plants.csv", "url": "https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv", "retrieved": "2026-11-26", "bytes": 0}]},
    {"id": "curated_mines", "title": "大型矿区与油气田公开资料", "publisher": "本项目整理（自然资源部、能源局、企业公开资料）",
     "homepage": "https://www.mnr.gov.cn/", "license": "公开信息整理（CC-BY 4.0）",
     "description": "按规模选取的煤矿区、铁矿区、铜矿、稀土、金矿与主要油气田，坐标为矿区中心近似。",
     "used_for": ["矿产资源点位", "能源顾问"], "vintage": "2023",
     "files": [{"file": "curated_mines", "url": "", "retrieved": "2026-11-26", "bytes": 0}]},
    {"id": "natural_earth_roads", "title": "Natural Earth 1:50m 地理底图", "publisher": "Natural Earth",
     "homepage": "https://www.naturalearthdata.com/", "license": "Public domain",
     "description": "国界、陆地、湖泊与主要河流，用于地图底图与国界外陆地。道路与铁路则由本项目按国家高速/高铁干线走向示意生成。",
     "used_for": ["国界", "湖泊", "河流", "邻国陆地"], "vintage": "5.1.2",
     "files": [{"file": "ne_50m_land.geojson", "url": "https://www.naturalearthdata.com/", "retrieved": "2026-11-26", "bytes": 1600000}]},
    {"id": "mot_ports", "title": "全国港口货物吞吐量统计", "publisher": "交通运输部",
     "homepage": "https://www.mot.gov.cn/", "license": "政府公开统计",
     "description": "2023 年主要沿海与内河港口货物吞吐量排序，取前 20 名。", "used_for": ["港口点位", "港口规模"],
     "vintage": "2023", "files": [{"file": "ports", "url": "https://www.mot.gov.cn/", "retrieved": "2026-11-26", "bytes": 0}]},
    {"id": "caac_airports", "title": "民航机场旅客吞吐量统计", "publisher": "中国民用航空局",
     "homepage": "https://www.caac.gov.cn/", "license": "政府公开统计",
     "description": "2023 年机场旅客吞吐量排序，取前 30 名。", "used_for": ["机场点位", "航空枢纽"],
     "vintage": "2023", "files": [{"file": "airports", "url": "https://www.caac.gov.cn/", "retrieved": "2026-11-26", "bytes": 0}]},
    {"id": "national_parks", "title": "中国国家公园名单", "publisher": "国家林业和草原局",
     "homepage": "https://www.forestry.gov.cn/", "license": "政府公开信息",
     "description": "首批 5 个国家公园及其范围示意。", "used_for": ["奇观：国家公园"], "vintage": "2024", "files": []},
    {"id": "mct_5a", "title": "国家 5A 级旅游景区名单与接待量", "publisher": "文化和旅游部及景区公开数据",
     "homepage": "https://www.mct.gov.cn/", "license": "政府公开信息（合理引用）",
     "description": "5A 级景区名单与公开年接待游客量，用于奇观排序。", "used_for": ["奇观：景区"], "vintage": "2024", "files": []},
    {"id": "moe_universities", "title": "教育部直属高校与预算公开", "publisher": "教育部 / 各高校",
     "homepage": "https://www.moe.gov.cn/", "license": "政府公开信息",
     "description": "研究型大学名单与公开预算经费，用于奇观排序。", "used_for": ["奇观：大学"], "vintage": "2024", "files": []},
    {"id": "unesco", "title": "世界遗产名录（中国）", "publisher": "UNESCO World Heritage Centre",
     "homepage": "https://whc.unesco.org/", "license": "公开信息",
     "description": "中国世界遗产与国家级地标，用于奇观中的地标选取。", "used_for": ["奇观：地标"], "vintage": "2024", "files": []},
    {"id": "model", "title": "本项目估算模型", "publisher": "本项目",
     "homepage": "", "license": "CC-BY 4.0",
     "description": "城市内部人口/产出分配、就业结构、收入与便利度等无法逐市获得的指标，由省级结构与城市类型模型估算，已在相关图层注明。",
     "used_for": ["城市内部插值", "部分镜头"], "vintage": "2026", "files": []},
    {"id": "hex", "title": "等面积六边形网格", "publisher": "本项目",
     "homepage": "", "license": "CC-BY 4.0",
     "description": "中国 Albers 等面积投影（标准纬线 25°N/47°N，中央经线 105°E），25 km 半径尖顶六边形网格。",
     "used_for": ["地图网格"], "vintage": "2026", "files": []},
]


def build(nation_core):
    nation = {
        "vintage": "国家统计局 2023–2024", "year": 2024, "gdp_vintage": "省级 GDP 2024（国家统计局）",
        "nation": {**nation_core, "gdp_industries": {k: nation_core["gdp_by_industry"][k] for k in INDUSTRIES}},
        "yields": YIELDS, "industries": INDUSTRIES,
        "gdp_industries": {k: INDUSTRIES[k] for k in INDUSTRIES},
    }
    (OUT / "nation.json").write_text(json.dumps(nation, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "sources.json").write_text(json.dumps(SOURCES, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  nation + sources")
    return nation
