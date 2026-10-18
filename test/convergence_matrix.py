#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收敛矩阵验收：硬卡未分类 / 规则未声明 covers / 孤儿格 / 规则重叠 / 规格与实现漂移。

用法：
    python convergence_matrix.py --spec test/convergence_spec.json --audit scripts/typeset_check.py

退出码：0 = 收敛；1 = 存在逃逸面或漂移
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
from skillio import read_text, say, setup_console  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--audit", required=True)
    a = ap.parse_args()
    setup_console()

    spec = json.loads(read_text(a.spec)[0])
    impl = read_text(a.audit)[0]

    problems = []

    # 1. 每种坏法必须都有规则
    bad_kinds = set(spec["bad_kinds"])
    rule_ids = [r["id"] for r in spec["rules"]]
    missing = bad_kinds - set(rule_ids)
    if missing:
        problems.append(f"未分类/无规则的坏法：{sorted(missing)}")

    # 2. 规则不得覆盖规格外的坏法（规则重叠 = 同一种坏法两条规则）
    orphan = set(rule_ids) - bad_kinds
    if orphan:
        problems.append(f"规则超出规格声明的坏法（重叠/臆造）：{sorted(orphan)}")

    # 3. 每条规则必须声明 covers，且非空
    for r in spec["rules"]:
        if not r.get("covers"):
            problems.append(f"规则 {r['id']} 未声明 covers")

    # 4. 孤儿格：规格声明的 covers 维度值，必须在实现里有对应判据痕迹
    #    做法：把 covers 的第二个元素（坏法细分）拿去实现源码里找关键词
    KEYWORD = {
        "微信剥离写法": "B1", "属性残留": "class=",
        "class 单引号写法": r"class\s*=",
        "脚本残留": "on(?:click",
        "有底色无边框": "BORDER_FULL_RE", "边框档位错误": "BORDER_FULL_RE",
        "单边 border 不算边框": "BORDER_FULL_RE",
        "按行计数偏差": "CARD_RE",
        "div 形式卡片同样受检": "(?:section|div)",
        "无底色容器不算卡片不误报": "EXCLUDE_BG",
        "残留直角引号": "count(", "引号不配对": "count(",
        "内层应转单引号": "count(",
        "开闭数量不等": "_check_nesting", "错位嵌套（数量相等）": "_check_nesting",
        "多余闭合标签": "_check_nesting", "br 等不参与配对": "selfclose",
        "table/thead/tbody/tr/th/td 层级": "NEST_TAGS",
        "外域域名": "IMG_RE", "合规 mmbiz 域名": "mmbiz.qpic.cn",
        "非微信域名": "HREF_RE", "合规 mp.weixin 域名": "mp.weixin.qq.com",
        "背景图外域": "BG_IMG_RE", "背景图合规": "BG_IMG_RE",
        "红底 #FDF3F2": "RED_MARKERS", "误用绿底": "RED_MARKERS",
        "误用蓝底": "_card_inner",
        "绿底 #F0F9F2": "GREEN_MARKERS", "误用红底": "GREEN_MARKERS",
        "蓝底 #F4F8FC": "BLUE_MARKERS",
        "不得串味": "_card_inner",
        "长卡片超过 600 字不漏检": "_tag_pairs",
        "用法注释中的角色名不得误判": "_strip_comments",
        "红底 1 张": "_red_quota", "红底 2 张": "_red_quota",
        "红底 3 张": "_red_quota", "红底 4 张": "RED_QUOTA",
        "红底恰好等于配额（边界合规）": "#FDF3F2",
        "红底超配额 1 张（应拦）": "_count_words",
        "显式标注 role: 优先级最高": "ROLE_ANN_RE",
        "视觉指纹（左侧 4px 色条）仍可判": "fingerprint",
        "弱标记只提醒不判错": '"weak"',
        "外置 roles.json 可增补": "load_roles",
        "文末卡缺 border": "ENDING_BLOCKS",
        "文末卡宽度退化": "BORDER_WIDTH_RE",
        "报头属封面级 2px": "by SnowFox",
        "事实来源属内容级 1px": "ENDING_BLOCKS",
        "底板容器包着文末卡不误报": "EXCLUDE_BG",
    }
    for r in spec["rules"]:
        for cell in r.get("covers", []):
            bad = cell[1]
            kw = KEYWORD.get(bad)
            if kw is None:
                problems.append(f"规则 {r['id']} 的格「{bad}」未登记验收关键词")
            elif kw not in impl:
                problems.append(
                    f"孤儿格：规则 {r['id']} 声明管「{bad}」，但实现里找不到判据「{kw}」")

    # 5. 规则数 vs 格子数（收敛趋势判据）
    cells = sum(len(r.get("covers", [])) for r in spec["rules"])
    rules = len(spec["rules"])
    say(f"规则数 = {rules}    格子数 = {cells}    格均规则数 = {cells/rules:.2f}")

    # 6. 版本漂移：规格 version 必须与 SKILL.md version 一致
    skill_md = os.path.join(os.path.dirname(HERE), "SKILL.md")
    if os.path.isfile(skill_md):
        m = re.search(r"^version:\s*(\S+)", read_text(skill_md)[0], re.M)
        if m and m.group(1) != spec["version"]:
            problems.append(
                f"规格与实现漂移：convergence_spec version={spec['version']}，"
                f"SKILL.md version={m.group(1)}")

    say("")
    if problems:
        say("❌ 未收敛：")
        for p in problems:
            say("   - " + p)
        return 1
    say(f"✅ 收敛：{rules} 条规则覆盖 {cells} 个格，无未分类、无孤儿格、无重叠、无漂移")
    return 0


if __name__ == "__main__":
    sys.exit(main())
