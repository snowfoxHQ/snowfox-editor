#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""必留区块校验器 —— 按用户自己的配置检查稿件

⛔ 每个用户的使用环境不同，必留的区块也不一样，所以「必留哪些」写在
   `scripts/fixed-blocks.json` 里，由用户自己改，本脚本只负责按配置校验。

用法：
    python fixed_blocks_check.py <draft.html> [...]   # 按配置校验稿件
    python fixed_blocks_check.py --show               # 打印当前配置
    python fixed_blocks_check.py --init               # 生成一份默认配置

退出码：0 = 必留区块齐全且顺序正确；1 = 缺失或顺序错；2 = 用法/配置错误/读文件失败
编码：稿件自动识别 UTF-8 / GBK / BOM，无需手工转码

配置怎么改：打开 scripts/fixed-blocks.json，改 required 数组即可。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillio import SkillIOError, read_text, say, setup_console, write_text  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "fixed-blocks.json")

# 区块特征 → 检测用的正则（认内容与样式，不认 class——微信正文不允许 class）
BLOCK_SIGNS = {
    "board": [
        (r"background:\s*#F2F3F5", "底板底色"),
    ],
    "masthead": [
        (r"letter-spacing:\s*2px", "报头刊名行（唯一）"),
        (r"by\s*SnowFox|by SnowFox", "报头署名"),
    ],
    "lede": [
        (r"color:\s*#2B77BF[^}]*", "导语蓝色字"),
        (r"本期看点|导读", "导语标题"),
    ],
    "subtitle": [
        (r"收尾金句|独立成行居中", "升华收尾文案"),
        (r"font-size:\s*18px[^}]*color:\s*#046B27", "升华 18px 绿字"),
    ],
    "reminder": [
        (r"最值得注意", "提醒卡文案"),
        (r"#A8281A", "提醒卡红字"),
    ],
    "deep_dive": [
        (r"border:\s*2px solid #D93F2B", "文末① 2px 红边"),
        (r"最值得深挖", "文末①文案"),
    ],
    "interact": [
        (r"评论区聊聊|哪条你最想", "文末②互动"),
        (r"text-align:\s*center[^}]*border-radius", "文末②居中卡"),
    ],
    "repo": [
        (r"GitHub开源仓库|开源仓库有好货", "文末③文案"),
        (r"mp\.weixin\.qq\.com/s/", "文末③内链"),
    ],
    "ai_chat": [
        (r"AI\s*对话已开通|AI对话已开通", "AI 对话引导"),
    ],
    # 弹性区块（不是必留，但可用来确认"有就合规"）
    "pill": [
        (r"border-radius:\s*20px", "胶囊栏目标"),
    ],
    "white_card": [
        (r"background:\s*#FFFFFF", "白卡"),
    ],
    "green_card": [
        (r"background:\s*#F0F9F2", "绿卡/升华底"),
    ],
    "blue_card": [
        (r"background:\s*#F4F8FC", "蓝卡/导语底"),
    ],
    "code_block": [
        (r"background:\s*#282C34", "代码块"),
    ],
}

DEFAULT_CONFIG = {
    "required": ["board", "masthead", "lede", "subtitle", "ai_chat"],
    "order_locked": True,
    "blocks": {
        "board": {"name": "底板", "desc": "#F2F3F5 外层容器"},
        "masthead": {"name": "报头", "desc": "2px 绿边 · 含署名"},
        "lede": {"name": "导语", "desc": "浅蓝底 · 蓝色正文"},
        "subtitle": {"name": "升华", "desc": "绿底 18px 居中"},
        "reminder": {"name": "提醒卡", "desc": "红底 1px"},
        "deep_dive": {"name": "文末①最值得深挖", "desc": "2px 红边"},
        "interact": {"name": "文末②互动问句", "desc": "2px 绿边 · 居中"},
        "repo": {"name": "文末③开源仓库", "desc": "2px 绿边 · 内链"},
        "ai_chat": {"name": "文末④AI 对话引导", "desc": "2px 绿边 · 最后一块"},
    },
}


def load_config():
    """读配置；坏配置不阻断校验，退回内置默认值并说明怎么修。"""
    if not os.path.isfile(CONFIG):
        return dict(DEFAULT_CONFIG), "（未找到 fixed-blocks.json，用内置默认值）"
    try:
        return json.loads(read_text(CONFIG)[0]), ""
    except (SkillIOError, ValueError) as e:
        return dict(DEFAULT_CONFIG), (
            f"⚠️ 配置读取失败：{e}\n"
            f"   → 用内置默认值继续。修法：删掉 {CONFIG} 后跑 "
            f"`python scripts/fixed_blocks_check.py --init` 重新生成。")


def _read_draft(path):
    """读稿：自动识别 UTF-8/GBK/BOM，读不到时给可执行修法而不是 traceback。"""
    return read_text(path)[0]


def strip_comments(html):
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)


def find_positions(html, key):
    """返回该区块在正文中的起始位置列表（按特征匹配）。"""
    signs = BLOCK_SIGNS.get(key)
    if not signs:
        return []
    pos = []
    for pat, _desc in signs:
        for m in re.finditer(pat, html):
            pos.append(m.start())
    return sorted(set(pos))


def check(path, cfg):
    html = strip_comments(_read_draft(path))       # 编码自动识别，读不到会抛 SkillIOError
    name = os.path.basename(path)
    OK, NG = setup_console()

    required = cfg.get("required", [])
    blocks = cfg.get("blocks", {})
    order_locked = cfg.get("order_locked", True)

    found, missing = [], []
    for key in required:
        ps = find_positions(html, key)
        if ps:
            found.append((key, blocks.get(key, {}).get("name", key), min(ps)))
        else:
            missing.append((key, blocks.get(key, {}).get("name", key)))

    say(f"=== 必留区块校验: {name} ===")
    say(f"配置要求 {len(required)} 个必留区块"
        f"（{'校验顺序' if order_locked else '不校验顺序'}）")

    if missing:
        say(f"{NG} 缺失 {len(missing)} 个必留区块：")
        for key, label in missing:
            say(f"   · {label}（{key}）")
        say("   → 要么把该区块加回稿件，要么改配置把这几项从 required 里去掉"
            "（改完跑 --show 确认）")
    else:
        say(f"{OK} 必留区块齐全（{len(found)}/{len(required)}）")

    # 按出现位置排序后，应与 required 声明的相对顺序一致
    pos_order = [k for k, _, _ in sorted(found, key=lambda x: x[2])]
    req_order = [k for k in required if k in pos_order]
    order_ok = pos_order == req_order
    if found and order_locked:
        if order_ok:
            say(f"{OK} 必留区块顺序正确")
        else:
            say(f"{NG} 必留区块顺序与配置不一致")
            say(f"   配置要求：{' → '.join(req_order)}")
            say(f"   实际出现：{' → '.join(pos_order)}")
            say("   → 调整区块位置，或把 order_locked 设为 false 只校验存在")

    ok = not missing and (order_ok if order_locked else True)
    say("")
    return 0 if ok else 1


def show_config(cfg, warn):
    if warn:
        say(warn)
    say("=== 当前必留区块配置（scripts/fixed-blocks.json）===")
    required = cfg.get("required", [])
    blocks = cfg.get("blocks", {})
    say(f"顺序校验：{'开' if cfg.get('order_locked') else '关'}")
    say(f"必留 {len(required)} 个：\n")
    for i, key in enumerate(required, 1):
        info = blocks.get(key, {})
        say(f"  {i}. {info.get('name', key):<16s} {info.get('desc', '')}")
        if info.get("note"):
            # ⛔ 这里原先是 ⓘ(U+24D8)，cp936 控制台无法编码会直接 traceback
            say(f"     i {info['note']}")
    optional = [k for k in blocks if k not in required]
    if optional:
        say(f"\n可加入 required 的（当前非必留）：{len(optional)} 个")
        say("  " + "、".join(blocks[k].get("name", k) for k in optional))
    say("\n改法：编辑 scripts/fixed-blocks.json 的 required 数组，再跑 --show 确认")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    setup_console()
    cfg, warn = load_config()

    if not args:
        say(__doc__)
        return 2
    if args[0] == "--show":
        show_config(cfg, warn)
        return 0
    if args[0] == "--init":
        write_text(CONFIG, json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2),
                   encoding="utf-8", backup=False)
        say("已生成默认配置:", CONFIG)
        return 0

    if warn:
        say(warn)
    bad = 0
    try:
        for p in args:
            if not os.path.isfile(p):
                say(f"读取失败：{p} 不存在（要指到具体的 .html 稿件）")
                bad += 2
                continue
            bad += check(p, cfg)
    except SkillIOError as e:
        say(f"❌ {e}")
        return 2
    except Exception as e:
        say(f"❌ 意外错误：{type(e).__name__}: {e}")
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
