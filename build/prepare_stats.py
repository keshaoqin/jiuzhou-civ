#!/usr/bin/env python3
"""Prepare province & prefecture statistics for the 九州 map.

Sources:
  - zh/en Wikipedia mirrors of the National Bureau of Statistics yearbooks:
      * List of Chinese administrative divisions by GDP (2024)
      * List of Chinese administrative divisions by population (2023)
      * List of prefecture-level divisions of China by GDP
      * List of top Chinese cities by GDP (2024)
  - DataV GeoAtlas administrative polygons (adcode, Chinese names, centres)

Outputs build/cache/province_stats.json and build/cache/prefecture_stats.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import pandas as pd
from pypinyin import lazy_pinyin

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"

PROVINCES = [
    ("110000", "北京", "Beijing"), ("120000", "天津", "Tianjin"), ("130000", "河北", "Hebei"),
    ("140000", "山西", "Shanxi"), ("150000", "内蒙古", "Inner Mongolia"), ("210000", "辽宁", "Liaoning"),
    ("220000", "吉林", "Jilin"), ("230000", "黑龙江", "Heilongjiang"), ("310000", "上海", "Shanghai"),
    ("320000", "江苏", "Jiangsu"), ("330000", "浙江", "Zhejiang"), ("340000", "安徽", "Anhui"),
    ("350000", "福建", "Fujian"), ("360000", "江西", "Jiangxi"), ("370000", "山东", "Shandong"),
    ("410000", "河南", "Henan"), ("420000", "湖北", "Hubei"), ("430000", "湖南", "Hunan"),
    ("440000", "广东", "Guangdong"), ("450000", "广西", "Guangxi"), ("460000", "海南", "Hainan"),
    ("500000", "重庆", "Chongqing"), ("510000", "四川", "Sichuan"), ("520000", "贵州", "Guizhou"),
    ("530000", "云南", "Yunnan"), ("540000", "西藏", "Tibet"), ("610000", "陕西", "Shaanxi"),
    ("620000", "甘肃", "Gansu"), ("630000", "青海", "Qinghai"), ("640000", "宁夏", "Ningxia"),
    ("650000", "新疆", "Xinjiang"),
]
EN2CODE = {en.lower(): (code, zh) for code, zh, en in PROVINCES}
# Wikipedia sometimes uses these names.
EN2CODE.update({"xizang": ("540000", "西藏"), "inner mongol": ("150000", "内蒙古"), "tibet autonomous region": ("540000", "西藏"),
                "guangxi zhuang": ("450000", "广西"), "xinjiang uygur": ("650000", "新疆"), "ningxia hui": ("640000", "宁夏")})

# City names whose English form is not the pinyin of the Chinese name.
ALIASES = {
    "ngari": "阿里", "qamdo": "昌都", "xigazê": "日喀则", "xigaze": "日喀则", "lhoka": "山南",
    "altay": "阿勒泰", "bortala": "博尔塔拉", "tarbaĝatay": "塔城", "tarbagatay": "塔城",
    "ürümqi": "乌鲁木齐", "urumqi": "乌鲁木齐", "kizilsu": "克孜勒苏", "aksu": "阿克苏",
    "bayingolin": "巴音郭楞", "ili": "伊犁", "harbin": "哈尔滨", "ulanqab": "乌兰察布", "chaoyang": "朝阳", "golog": "果洛",
    "changzhi": "长治", "lüliang": "吕梁", "lulang": "吕梁", "garzê": "甘孜", "garze": "甘孜",
    "ngawa": "阿坝", "ili": "伊犁", "dêqên": "迪庆", "deqen": "迪庆", "luohe": "漯河",
    "hohhot": "呼和浩特", "urumqi": "乌鲁木齐", "lhasa": "拉萨", "harbin": "哈尔滨",
    "hulunbuir": "呼伦贝尔", "ordos": "鄂尔多斯", "qiqihar": "齐齐哈尔", "sanya": "三亚",
    "haikou": "海口", "karamay": "克拉玛依", "kashgar": "喀什", "hotan": "和田",
    "turpan": "吐鲁番", "hami": "哈密", "korla": "库尔勒", "shigatse": "日喀则",
    "chamdo": "昌都", "nyingchi": "林芝", "shannan": "山南", "nagqu": "那曲",
    "hainan": "海南", "haixi": "海西", "huangnan": "黄南", "haibei": "海北",
    "guoluo": "果洛", "yushu": "玉树", "haidong": "海东", "xilingol": "锡林郭勒",
    "alxa": "阿拉善", "hinggan": "兴安", "hulun buir": "呼伦贝尔", "bayannur": "巴彦淖尔",
    "ulaanqab": "乌兰察布", "chifeng": "赤峰", "tongliao": "通辽", "huludao": "葫芦岛",
    "daxinganling": "大兴安岭", "xiangxi": "湘西", "enyi": "恩施", "qianxinan": "黔西南",
    "qiandongnan": "黔东南", "qiannan": "黔南", "liangshan": "凉山", "ganzi": "甘孜",
    "aba": "阿坝", "deqen": "迪庆", "nujiang": "怒江", "dali": "大理", "chuxiong": "楚雄",
    "honghe": "红河", "wenshan": "文山", "xishuangbanna": "西双版纳", "lincang": "临沧",
    "pu'er": "普洱", "baoshan": "保山", "lijiang": "丽江", "zhaotong": "昭通",
}

STRIP = re.compile(r"(市|地区|自治州|自治县|盟|区|县|特别行政区)$")


def norm_cn(name: str) -> str:
    name = STRIP.sub("", name.strip())
    name = name.replace("蒙古族自治州", "").replace("藏族自治州", "").replace("彝族自治州", "")
    name = re.sub(r"(回族|藏族|彝族|苗族|侗族|布依族|土家族|白族|傣族|景颇族|傈僳族|哈尼族|壮族|蒙古族|朝鲜族|羌族|哈萨克族|柯尔克孜族)+", "", name)
    for eth in ("哈萨克", "蒙古", "柯尔克孜", "回", "藏", "彝", "苗", "侗", "布依", "土家", "白", "傣", "景颇", "傈僳", "哈尼", "壮", "朝鲜", "羌"):
        if name.endswith(eth):
            name = name[: -len(eth)]
    return name


def pinyin_key(name: str) -> str:
    return "".join(lazy_pinyin(norm_cn(name))).lower()


def norm_en(name: str) -> str:
    name = re.sub(r"\*", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\b(city|prefecture|autonomous|region|league|county)\b", " ", name, flags=re.I)
    return re.sub(r"[^a-z]", "", name.lower())


def match_score(cn: str, en: str) -> float:
    e = norm_en(en)
    if en.replace("*", "").strip().lower() in ALIASES:
        alias = norm_cn(ALIASES[en.replace("*", "").strip().lower()])
        return 1.0 if alias == norm_cn(cn) or alias in cn else 0.0
    p = pinyin_key(cn)
    if not p or not e:
        return 0.0
    if p == e:
        return 1.0
    if p.startswith(e) or e.startswith(p):
        return 0.9
    # longest common prefix ratio
    n = 0
    for a, b in zip(p, e):
        if a != b:
            break
        n += 1
    return n / max(len(p), len(e))


def fetch(url: str, filename: str) -> Path:
    path = CACHE / filename
    if path.exists() and path.stat().st_size > 10000:
        return path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


def main():
    # --- provinces -------------------------------------------------------------
    gdp_html = fetch("https://en.wikipedia.org/wiki/List_of_Chinese_administrative_divisions_by_GDP", "prov_gdp.html")
    pop_html = fetch("https://en.wikipedia.org/wiki/List_of_Chinese_administrative_divisions_by_population", "prov_pop.html")
    gdp_tables = pd.read_html(gdp_html)
    # Table 2 is the current (2024) ranking: region, GDP(CN¥ mil.), GDP(US$ mil.), share, growth.
    gdp = gdp_tables[2].copy()
    gdp.columns = ["region", "gdp_cny_mil", "gdp_usd_mil", "share", "real_growth", "nominal_growth"]
    pop_tables = pd.read_html(pop_html)
    pop = next(t for t in pop_tables if len(t.columns) >= 3 and "Division" in str(t.columns[0]))
    pop.columns = [str(c) for c in pop.columns]

    hist = pop_tables[5].copy()
    hist.columns = [str(c) for c in hist.columns]
    pop2020 = {}
    for _, hr in hist.iterrows():
        nm = re.sub(r"\[.*?\]", "", str(hr.iloc[0])).strip()
        key = nm.lower()
        if key in EN2CODE:
            try:
                pop2020[EN2CODE[key][0]] = float(str(hr.iloc[1]).replace(",", ""))
            except Exception:
                pass

    provinces = []
    for _, row in gdp.iterrows():
        region = re.sub(r"\[.*?\]", "", str(row["region"])).strip()
        if region.lower() in ("china (mainland)", "mainland china"):
            continue
        key = region.lower()
        if key not in EN2CODE:
            print("  ? province not mapped:", region)
            continue
        code, zh = EN2CODE[key]
        try:
            gdp_cny = float(str(row["gdp_cny_mil"]).replace(",", "")) * 1e6
        except Exception:
            continue
        p = pop[pop["Division"].astype(str).str.strip().str.lower() == key]
        population = None
        urban = None
        if len(p):
            population = float(p.iloc[0]["Total"])
            urban = float(p.iloc[0]["Urban"]) if "Urban" in p.columns and pd.notna(p.iloc[0]["Urban"]) else None
        provinces.append({"adcode": code, "name": zh, "gdp": gdp_cny, "population": population, "urban_population": urban,
                          "population_2020": pop2020.get(code), "gdp_year": 2024, "pop_year": 2023})
    from taiwan import TAIWAN_STATS
    provinces.append(dict(TAIWAN_STATS))
    print("provinces:", len(provinces))
    (CACHE / "province_stats.json").write_text(json.dumps(provinces, ensure_ascii=False, indent=1))

    # --- DataV cities ----------------------------------------------------------
    datav = {}
    for code, zh, en in PROVINCES:
        d = json.loads((Path("/tmp/datav") / f"{code}.json").read_text())
        feats = [f for f in d["features"] if f["properties"].get("level") == "city"]
        if code in ("110000", "120000", "310000", "500000"):
            feats = []
        for f in feats:
            pr = f["properties"]
            datav[pr["adcode"]] = {"adcode": str(pr["adcode"]), "name": pr["name"], "province": zh,
                                   "prov_code": code, "center": pr.get("center") or pr.get("centroid")}
        if not feats:
            # municipality: one polygon from the country file
            country = json.loads((CACHE / "datav_china.json").read_text()) if (CACHE / "datav_china.json").exists() else None
            if country is None:
                country = json.loads(Path("/tmp/datav_china.json").read_text())
            f = next(x for x in country["features"] if str(x["properties"].get("adcode")) == code)
            pr = f["properties"]
            datav[code] = {"adcode": code, "name": zh + "市", "province": zh, "prov_code": code,
                           "center": pr.get("center") or pr.get("centroid")}
    print("datav city rows:", len(datav))

    # --- prefecture GDP table --------------------------------------------------
    pref_html = fetch("https://en.wikipedia.org/wiki/List_of_prefecture-level_divisions_of_China_by_GDP", "pref_gdp.html")
    pref = pd.read_html(pref_html)[0]
    pref.columns = [str(c) for c in pref.columns]
    rows = []
    for _, r in pref.iterrows():
        en_name = str(r["Name"]).strip()
        prov_en = str(r["Province"]).strip()
        pkey = prov_en.lower()
        if pkey not in EN2CODE:
            print("  ? pref province:", prov_en)
            continue
        pcode, pzh = EN2CODE[pkey]
        def num(x):
            import re as _re
            m = _re.search(r"-?\d[\d,]*\.?\d*", str(x))
            return float(m.group(0).replace(",", "")) if m else None
        gdp = num(r.get("GDP (billion CN¥)"))
        gdppc = num(r.get("GDP per capita (CN¥)"))
        try:
            gdp_cny = float(gdp) * 1e9
        except Exception:
            continue
        try:
            gdppc = float(gdppc)
            pop = gdp_cny / gdppc if gdppc > 0 else None
        except Exception:
            gdppc = None
            pop = None
        date = str(r.get("Date", ""))
        m = re.search(r"(20\d\d)", date)
        year = int(m.group(1)) if m else 2023
        rows.append({"en": en_name, "province": pzh, "prov_code": pcode, "gdp": gdp_cny, "gdp_pc": gdppc,
                     "population": pop, "year": year})
    print("pref rows:", len(rows))

    # --- match to DataV --------------------------------------------------------
    by_prov = {}
    for c in datav.values():
        by_prov.setdefault(c["province"], []).append(c)
    matched, used = [], set()
    for row in rows:
        cands = [c for c in by_prov.get(row["province"], []) if c["adcode"] not in used]
        best, score = None, 0
        for c in cands:
            s = match_score(c["name"], row["en"])
            if s > score:
                best, score = c, s
        if best and score >= 0.72:
            used.add(best["adcode"])
            matched.append({**row, **best, "score": round(score, 2), "cn": best["name"]})
        else:
            matched.append({**row, "adcode": None, "cn": None, "score": round(score, 2)})
    unmatched = [m for m in matched if not m["adcode"]]
    print("matched:", len(matched) - len(unmatched), "unmatched:", len(unmatched))
    for m in unmatched:
        print("  ?", m["province"], m["en"], "-> best", m["score"])

    # --- 2024 top-50 city GDP overrides ---------------------------------------
    top_html = fetch("https://en.wikipedia.org/wiki/List_of_top_Chinese_cities_by_GDP", "top50_gdp.html")
    top = pd.read_html(top_html)[0]
    top.columns = ["rank", "city_en", "city_cn", "province_en", "gdp2024", "gdp2024_usd", "gdp2023", "gdp2023_usd"]
    by_cn = {}
    for row in matched:
        if row.get("cn"):
            by_cn.setdefault(norm_cn(row["cn"]), []).append(row)
    updated = 0
    for _, r in top.iterrows():
        cn = str(r["city_cn"]).strip()
        cands = by_cn.get(norm_cn(cn), [])
        if not cands:
            # match a DataV name that starts with the short city name
            cands = [x for x in matched if x.get("cn") and norm_cn(x["cn"]).startswith(norm_cn(cn))]
        if not cands:
            print("  ? top50 city unmatched:", cn)
            continue
        row = cands[0]
        try:
            row["gdp"] = float(str(r["gdp2024"]).replace(",", "")) * 1e6
            row["gdp_year"] = 2024
            if row.get("gdp_pc"):
                row["population"] = row["gdp"] / float(row["gdp_pc"]) if float(row["gdp_pc"]) > 0 else row.get("population")
            updated += 1
        except Exception:
            pass
    print("top50 updated:", updated)
    (CACHE / "prefecture_stats.json").write_text(json.dumps(matched, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
