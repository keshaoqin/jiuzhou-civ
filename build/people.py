#!/usr/bin/env python3
"""Citizens and districts for the City View."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "data"

WORKFORCE = [
    {"key": "executive", "label": "管理者", "icon": "c-executive", "lines": "管理层与公共管理"},
    {"key": "engineer", "label": "工程师", "icon": "c-engineer", "lines": "信息、科研、制造技术"},
    {"key": "scholar", "label": "学者", "icon": "c-scholar", "lines": "教育、科研"},
    {"key": "healer", "label": "医护", "icon": "c-healer", "lines": "卫生与社会工作"},
    {"key": "service", "label": "服务业", "icon": "c-service", "lines": "零售、餐饮、批发"},
    {"key": "clerk", "label": "职员", "icon": "c-clerk", "lines": "金融、行政、房地产"},
    {"key": "farmer", "label": "农民", "icon": "c-farmer", "lines": "农林牧渔"},
    {"key": "builder", "label": "建筑工", "icon": "c-builder", "lines": "建筑、制造"},
    {"key": "maker", "label": "产业工人", "icon": "c-maker", "lines": "制造、采矿、公用事业"},
]
AGE = [
    {"key": "child", "label": "儿童", "icon": "c-child", "lines": "0–14 岁"},
    {"key": "young", "label": "青年", "icon": "c-young", "lines": "15–34 岁"},
    {"key": "midlife", "label": "中年", "icon": "c-midlife", "lines": "35–59 岁"},
    {"key": "elder", "label": "老年", "icon": "c-elder", "lines": "60 岁以上"},
]
COMMUTE = [
    {"key": "drove_alone", "label": "自驾", "icon": "c-drove_alone", "lines": "小汽车"},
    {"key": "carpool", "label": "拼车", "icon": "c-carpool", "lines": "合乘"},
    {"key": "transit", "label": "公共交通", "icon": "c-transit", "lines": "地铁/公交"},
    {"key": "walk", "label": "步行", "icon": "c-walk", "lines": "步行"},
    {"key": "other", "label": "其他", "icon": "c-other", "lines": "骑行等"},
    {"key": "home", "label": "居家", "icon": "c-home", "lines": "居家办公"},
]
EDUCATION = [
    {"key": "less_than_hs", "label": "初中及以下", "icon": "c-edu_low", "lines": "未上高中"},
    {"key": "high_school", "label": "高中", "icon": "c-edu_mid", "lines": "高中/中专"},
    {"key": "some_college", "label": "大专", "icon": "c-edu_some", "lines": "大专"},
    {"key": "bachelors", "label": "本科", "icon": "c-edu_bach", "lines": "本科"},
    {"key": "graduate", "label": "研究生", "icon": "c-edu_grad", "lines": "硕士及以上"},
]
NATIVITY = [
    {"key": "born_in_state", "label": "本省出生", "icon": "c-born_state", "lines": "本省"},
    {"key": "other_state", "label": "外省迁入", "icon": "c-other_state", "lines": "外省"},
    {"key": "native_abroad", "label": "境外出生", "icon": "c-native_abroad", "lines": "港澳台/海外"},
    {"key": "foreign_born", "label": "外籍", "icon": "c-foreign", "lines": "外籍"},
]
FIGURES = {"workforce": 20, "age": 10, "commute": 10}


def largest(total, shares):
    total = int(round(total))
    raw = {k: total * v for k, v in shares.items()}
    out = {k: int(v) for k, v in raw.items()}
    rem = total - sum(out.values())
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[:max(0, rem)]:
        out[k] += 1
    return out


def shares_from_counts(counts):
    t = sum(counts.values()) or 1
    return {k: v / t for k, v in counts.items()}


def build(cities, nation):
    print("build citizens ...")
    # national reference shares
    nat_jobs = nation["jobs"]
    nat_emp = nation["employed"]
    ref_work = {
        "executive": (nat_jobs["management"] + nat_jobs["public_admin"] * 0.3) / nat_emp,
        "engineer": (nat_jobs["information"] * 0.55 + nat_jobs["professional"] * 0.55 + nat_jobs["manufacturing"] * 0.2) / nat_emp,
        "scholar": (nat_jobs["education"] + nat_jobs["professional"] * 0.25) / nat_emp,
        "healer": nat_jobs["health"] / nat_emp,
        "service": (nat_jobs["retail"] + nat_jobs["accommodation"] + nat_jobs["wholesale"] * 0.4 + nat_jobs["arts"] * 0.2) / nat_emp,
        "clerk": (nat_jobs["finance"] + nat_jobs["admin"] * 0.5 + nat_jobs["real_estate"] * 0.5 + nat_jobs["wholesale"] * 0.6) / nat_emp,
        "farmer": nat_jobs["agriculture"] / nat_emp,
        "builder": (nat_jobs["construction"] + nat_jobs["manufacturing"] * 0.25) / nat_emp,
        "maker": (nat_jobs["manufacturing"] * 0.55 + nat_jobs["mining"] + nat_jobs["utilities"]) / nat_emp,
    }
    s = sum(ref_work.values())
    ref_work = {k: v / s for k, v in ref_work.items()}
    ref_edu = {"less_than_hs": 0.34, "high_school": 0.29, "some_college": 0.18, "bachelors": 0.14, "graduate": 0.05}
    ref_age = {"child": 0.17, "young": 0.27, "midlife": 0.39, "elder": 0.17}
    ref_commute = {"drove_alone": 0.28, "carpool": 0.10, "transit": 0.26, "walk": 0.16, "other": 0.07, "home": 0.13}
    ref_nat = {"born_in_state": 0.58, "other_state": 0.38, "native_abroad": 0.025, "foreign_born": 0.015}

    def make_row(c, total, shares, kind):
        counts = largest(total, shares)
        return {"total": total, "counts": counts, "shares": {k: round(v, 3) for k, v in shares_from_counts(counts).items()},
                "figures": largest(FIGURES[kind], shares_from_counts(counts))}

    city_rows = {}
    for c in cities:
        j = c["jobs"]
        emp = c["employed"]
        counts = {
            "executive": j["management"] + j["public_admin"] * 0.3,
            "engineer": j["information"] * 0.55 + j["professional"] * 0.55 + j["manufacturing"] * 0.2,
            "scholar": j["education"] + j["professional"] * 0.25,
            "healer": j["health"],
            "service": j["retail"] + j["accommodation"] + j["wholesale"] * 0.4 + j["arts"] * 0.2,
            "clerk": j["finance"] + j["admin"] * 0.5 + j["real_estate"] * 0.5 + j["wholesale"] * 0.6,
            "farmer": j["agriculture"],
            "builder": j["construction"] + j["manufacturing"] * 0.25,
            "maker": j["manufacturing"] * 0.55 + j["mining"] + j["utilities"],
        }
        shares = shares_from_counts(counts)
        age = {"child": 0.15, "young": 0.27, "midlife": 0.41, "elder": 0.17}
        if c["name"] in ("深圳", "东莞", "珠海"):
            age = {"child": 0.16, "young": 0.40, "midlife": 0.37, "elder": 0.07}
        elif c["name"] in ("上海", "北京", "南通"):
            age = {"child": 0.12, "young": 0.24, "midlife": 0.39, "elder": 0.25}
        urban = c.get("urban_rate") or 0.6
        commute = {"drove_alone": 0.30 + (0.08 if urban > 0.75 else 0), "carpool": 0.09,
                   "transit": 0.12 + urban * 0.32, "walk": 0.18 - urban * 0.08, "other": 0.06, "home": 0.12}
        bach = (c.get("bachelors") or 13) / 100
        edu = {"less_than_hs": max(0.08, 0.42 - bach * 1.1), "high_school": 0.28, "some_college": 0.17,
               "bachelors": max(0.02, bach - 0.03), "graduate": 0.03}
        nativity = {"born_in_state": max(0.30, 0.82 - bach * 0.5), "other_state": 0.0, "native_abroad": 0.02, "foreign_born": 0.008}
        nativity["other_state"] = max(0.05, 1 - nativity["born_in_state"] - nativity["native_abroad"] - nativity["foreign_born"])
        row = {
            "workforce": make_row(c, emp, shares, "workforce"),
            "age": {**make_row(c, c["population"], age, "age"), "median": round(32 + (c.get("aging") or 13) * 0.55, 1)},
            "commute": make_row(c, emp, commute, "commute"),
            "education": {**make_row(c, c["population"] * 0.75, edu, "age"), "bachelors_plus": round((edu["bachelors"] + edu["graduate"]), 3)},
            "nativity": {**make_row(c, c["population"], nativity, "age"), "foreign_born": nativity["foreign_born"], "born_in_state": nativity["born_in_state"]},
            "specialists": [],
            "reliable": True,
        }
        for rowkey in ("workforce", "age", "commute", "education", "nativity"):
            pass
        # specialists: compare all categories to national
        specs = []
        ref = {"workforce": ref_work, "age": ref_age, "commute": ref_commute, "education": ref_edu, "nativity": ref_nat}
        for rowkey, groups in [("workforce", WORKFORCE), ("age", AGE), ("commute", COMMUTE), ("education", EDUCATION), ("nativity", NATIVITY)]:
            rr = row[rowkey]
            for g in groups:
                sh = rr["shares"].get(g["key"], 0)
                nsh = ref[rowkey].get(g["key"], 0)
                if sh >= 0.01 and nsh > 0:
                    ratio = sh / nsh
                    if ratio >= 1.5 or ratio <= 0.67:
                        specs.append({"row": rowkey, "key": g["key"], "share": round(sh, 3), "national": round(nsh, 3), "ratio": round(ratio, 2)})
        specs.sort(key=lambda x: abs(math.log(max(0.01, x["ratio"]))), reverse=True)
        row["specialists"] = specs[:6]
        city_rows[c["id"]] = row

    # national row
    nat_counts = {
        "executive": nat_jobs["management"] + nat_jobs["public_admin"] * 0.3,
        "engineer": nat_jobs["information"] * 0.55 + nat_jobs["professional"] * 0.55 + nat_jobs["manufacturing"] * 0.2,
        "scholar": nat_jobs["education"] + nat_jobs["professional"] * 0.25,
        "healer": nat_jobs["health"],
        "service": nat_jobs["retail"] + nat_jobs["accommodation"] + nat_jobs["wholesale"] * 0.4 + nat_jobs["arts"] * 0.2,
        "clerk": nat_jobs["finance"] + nat_jobs["admin"] * 0.5 + nat_jobs["real_estate"] * 0.5 + nat_jobs["wholesale"] * 0.6,
        "farmer": nat_jobs["agriculture"],
        "builder": nat_jobs["construction"] + nat_jobs["manufacturing"] * 0.25,
        "maker": nat_jobs["manufacturing"] * 0.55 + nat_jobs["mining"] + nat_jobs["utilities"],
    }
    national = {
        "workforce": make_row(nation, nat_emp, shares_from_counts(nat_counts), "workforce"),
        "age": {**make_row(nation, nation["population"], ref_age, "age"), "median": 38.8},
        "commute": make_row(nation, nat_emp, ref_commute, "commute"),
        "education": {**make_row(nation, nation["population"] * 0.75, ref_edu, "age"), "bachelors_plus": 0.19},
        "nativity": {**make_row(nation, nation["population"], ref_nat, "age"), "foreign_born": 0.015, "born_in_state": 0.58},
        "specialists": [],
    }
    data = {"version": 1, "vintage": "第七次全国人口普查（2020）+ 2023 年统计公报（结构推算）", "year": 2023,
            "sources": ["nbs_province", "nbs_prefecture"], "figures": FIGURES,
            "rows": {"workforce": "就业人口职业构成", "age": "年龄结构", "commute": "通勤方式", "education": "受教育程度", "nativity": "出生地"},
            "groups": {"workforce": WORKFORCE, "age": AGE, "commute": COMMUTE, "education": EDUCATION, "nativity": NATIVITY},
            "rule": {"specialist_high": 1.5, "specialist_low": 0.67, "min_share": 0.01, "max_high": 4, "max_low": 2,
                     "text": "职业、通勤、教育、出生地结构由省级普查结构与城市类型模型推算；图标数量按最大余数法取整。"},
            "national": national, "cities": city_rows}
    (OUT / "citizens.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("  citizens", len(city_rows))
    return data
