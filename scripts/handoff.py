#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交付契约：把排版产物打包成交接包，交给 wechat-oa-draft-publish。

⛔ 本脚本**不推送草稿箱、不发文章**——发布不在本技能范围，硬做就越界了。
   它只做三件事：
   1. 跑三个自检，把退出码写进交接包（没过就 ready=false，接手的人一眼能看到）
   2. 把发布侧必需字段（标题/摘要/封面/作者）摆到明面上，缺什么就写缺什么
   3. 可选 --strip：生成可直接粘进微信编辑器的净化版正文

用法：
    python handoff.py --emit <draft.html>              # 生成 <draft>.handoff.json
    python handoff.py --emit --strip <draft.html>      # 先净化，再按净化版打包
    python handoff.py --emit --title "标题" --digest "摘要" --cover 封面.jpg <draft.html>
    python handoff.py --strip <draft.html>             # 只要净化版正文 <draft>.wechat.html

退出码：0 = 交接包可交付；1 = 自检未过（包照样写，但 ready=false）；2 = 读写失败。
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillio import read_text, say, setup_console, write_text  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
CHECK = os.path.join(HERE, "typeset_check.py")
FIXQ = os.path.join(HERE, "fix_quotes.py")
FBLOCKS = os.path.join(HERE, "fixed_blocks_check.py")

CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

# 报头标题在参照稿里是 20px，用它做「最可能是标题」的启发式（猜错也比留空好认）
TITLE_RE = re.compile(r"<p[^>]*font-size:\s*(?:2[0-9]|[3-9]\d)px[^>]*>(.*?)</p>", re.S)


def clean_html(html):
    """粘贴前净化：去注释、压空行、去行尾空格。

    ⛔ 只动「微信本来就会忽略」的东西：注释在微信里不渲染，留在工作副本是给人和
       脚本看的，粘进编辑器却可能造成空白段落。
    ⛔ 净化会连 <!-- role:xxx --> 标注一起去掉——标注是工作副本的元信息，
       粘进微信前本来就该剥掉；检查要在工作副本上做，不要在净化版上做。
    """
    out = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    out = re.sub(r"[ \t]+$", "", out, flags=re.M)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.rstrip() + "\n"


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=CHILD_ENV)
    return r.returncode


def run_checks(path):
    """三个自检都要跑：排版 / 标点 / 必留区块。返回 {名称: 退出码}。"""
    return {
        "typeset": _run([sys.executable, CHECK, path]),
        "quotes": _run([sys.executable, FIXQ, "--check", path]),
        "fixed_blocks": _run([sys.executable, FBLOCKS, path]),
    }


def guess_title(html):
    m = TITLE_RE.search(html)
    if not m:
        return None
    t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return t or None


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    OK, NG = setup_console()

    if not args or "--help" in args:
        say(__doc__)
        return 2

    do_emit = "--emit" in args
    do_strip = "--strip" in args

    def opt(name):
        return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else None

    # 逐个解析：带值的选项要连它的值一起跳过，不能把值当成稿件路径
    valopts = ("--title", "--digest", "--cover")
    files, i = [], 0
    while i < len(args):
        a = args[i]
        if a in valopts:
            i += 2
            continue
        if not a.startswith("--"):
            files.append(a)
        i += 1
    if not files:
        say("没有指定稿件。python scripts/handoff.py --emit <draft.html>")
        return 2
    draft = files[0]

    try:
        html, enc, _bom = read_text(draft)
    except Exception as e:
        say(f"{NG} 读不了这篇稿子：{e}")
        return 2

    body_path = draft
    if do_strip:
        cleaned = clean_html(html)
        body_path = os.path.splitext(draft)[0] + ".wechat.html"
        write_text(body_path, cleaned, encoding="utf-8", backup=False)
        say(f"{OK} 净化版正文：{os.path.basename(body_path)}"
            f"（去注释 / 压空行 / 去行尾空格，可直接粘进微信编辑器）")

    if not do_emit:
        return 0

    checks = run_checks(body_path)
    ready = all(v == 0 for v in checks.values())
    title = opt("--title") or guess_title(html)
    digest = opt("--digest")
    cover = opt("--cover")

    data = {
        "ready": ready,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "body": {"path": os.path.abspath(body_path), "cleaned": do_strip,
                 "encoding": enc},
        "title": title,
        "digest": digest,
        "cover": cover,
        "author": "by SnowFox",
        "checks": [{"name": k, "exit": v, "ok": v == 0} for k, v in checks.items()],
        "missing": [k for k, v in (("title", title), ("digest", digest), ("cover", cover))
                    if not v],
        "next": "交给 wechat-oa-draft-publish 推草稿箱；本技能只管排版，不实现推送。",
    }
    out_path = os.path.splitext(draft)[0] + ".handoff.json"
    write_text(out_path, json.dumps(data, ensure_ascii=False, indent=2),
               encoding="utf-8", backup=False)

    say(f"\n=== 交付交接包: {os.path.basename(out_path)} ===")
    say(f"  正文：{os.path.basename(body_path)}")
    say(f"  标题：{title or '(缺失，发布前必填)'}")
    say(f"  摘要：{digest or '(缺失，发布前必填)'}")
    say(f"  封面：{cover or '(缺失，发布前必填)'}")
    for k, v in checks.items():
        say(f"  自检 {k}：{OK + ' 通过' if v == 0 else NG + f' 未过（EXIT {v}）'}")
    if data["missing"]:
        say(f"  ⚠️ 发布侧还缺：{'、'.join(data['missing'])}")
    say(f"  下一步：{data['next']}")
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
