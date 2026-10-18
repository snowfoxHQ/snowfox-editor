#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""稳定性证据（确定性，零第三方依赖）

换模型压测成本高，这里用三件更便宜但同样可验证的事替代：

  1. 判分器防 flaky：同一份输入跑 N 次，输出与退出码必须完全一致。
     ⛔ 判分器一旦不确定，A/B 增益对照就失去意义——这是所有稳定性结论的地基。
  2. best-of-N 分布：给 N 份候选稿打分，报均值/方差/最坏值，并挑出最好的那份。
     模型稳定性差异主要表现为 σ 变大，σ 本身就是指标，无需真换模型。
  3. 黄金集回归：templates/ 与真稿的固定基线，改判据后必须一致。

用法：
    python test/stability.py                      # 防 flaky + 黄金集
    python test/stability.py --repeat 5 <稿.html>  # 指定文件重复判分
    python test/stability.py --candidates <目录>   # 给目录里所有候选稿打分并出分布
    python test/stability.py --golden --update     # 重录黄金集基线

退出码：0 = 全部稳定；1 = 有不稳定/回归；2 = 用法或读写失败。
"""
import json
import os
import re
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
CHECK = os.path.join(SKILL, "scripts", "typeset_check.py")
GOLDEN = os.path.join(HERE, "golden_expect.json")

sys.path.insert(0, os.path.join(SKILL, "scripts"))
from skillio import say, setup_console  # noqa: E402

CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

# 黄金集：技能自带的参照稿 + 用户真机跑过的真稿（真稿路径不存在就跳过，不报错）
GOLDEN_FILES = [
    os.path.join(SKILL, "templates", "style-floating.html"),
    "C:/Users/admin/WorkBuddy/2026-10-13-08-41-48/work/ai-briefing-1013.html",
    "C:/Users/admin/WorkBuddy/2026-10-12-22-21-04/.wechat/moonshot_final.html",
]


def judge(path):
    """判分一次：返回 (退出码, 违规编号列表)。"""
    r = subprocess.run([sys.executable, CHECK, "--json", path],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=CHILD_ENV)
    try:
        data = json.loads(r.stdout)
        codes = sorted({v["code"] for v in data["violations"]})
    except Exception:
        codes = sorted(set(re.findall(r"\[(B\d)\]", r.stdout)))
    return r.returncode, codes


def raw_out(path):
    r = subprocess.run([sys.executable, CHECK, path], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=CHILD_ENV)
    return r.returncode, r.stdout


def flaky(path, n=5):
    """同一输入重复判分：输出必须逐字节一致。"""
    base = raw_out(path)
    for _ in range(n - 1):
        if raw_out(path) != base:
            return False
    return True


def golden(update=False):
    """黄金集：与基线比对（--update 重录）。"""
    present = [p for p in GOLDEN_FILES if os.path.isfile(p)]
    if not present:
        say("⚠️  黄金集里没有任何可访问的文件，跳过")
        return 0

    # ⛔ 基线按文件名存，不存绝对路径：真稿在用户机器上、路径会变，
    #    存绝对路径等于把基线绑死在一台机器上。
    current = {os.path.basename(p): judge(p) for p in present}
    if update:
        with open(GOLDEN, "w", encoding="utf-8") as f:
            json.dump({k: list(v) for k, v in current.items()},
                      f, ensure_ascii=False, indent=2)
        say(f"✅ 已重录黄金集基线（{len(present)} 份）→ {os.path.basename(GOLDEN)}")
        return 0

    if not os.path.isfile(GOLDEN):
        say("❌ 没有黄金集基线，先跑 python test/stability.py --golden --update")
        return 1

    with open(GOLDEN, encoding="utf-8") as f:
        expect = json.load(f)

    bad = 0
    for name, got in current.items():
        want = expect.get(name)
        if want is None:
            say(f"⚠️  基线里没有这份：{name}（用 --update 补录）")
            continue
        if list(got) != list(want):
            bad += 1
            say(f"❌ 回归：{name} 期望 {want}，实得 {list(got)}")
        else:
            say(f"   PASS  {name} 与基线一致 {list(got)}")
    return 1 if bad else 0


def candidates(d):
    """给目录里所有候选稿打分：出分布，并挑出最好的那份。"""
    if not os.path.isdir(d):
        say(f"❌ 目录不存在：{d}")
        return 2
    files = sorted(f for f in os.listdir(d) if f.lower().endswith((".html", ".htm")))
    if not files:
        say(f"⚠️  目录里没有 HTML 候选稿：{d}")
        return 2

    scores = []
    for f in files:
        code, codes = judge(os.path.join(d, f))
        scores.append((len(codes), f, codes))
        say(f"   {f}：违规 {len(codes)} 类 {codes or '[]'}（EXIT {code}）")

    nums = [s[0] for s in scores]
    mean = statistics.mean(nums)
    sd = statistics.pstdev(nums)
    say(f"\n   N={len(nums)}  均值={mean:.2f}  σ={sd:.2f}  最好={min(nums)}  最坏={max(nums)}")
    if sd == 0:
        say("   ✅ 各次结果完全一致（σ=0）")
    else:
        say(f"   ⚠️  各次结果有波动（σ={sd:.2f}）：建议 best-of-N 取最好的那份，"
            f"并把波动最大的素材补进黄金集")
    best = min(scores)[1]
    say(f"   best-of-N 推荐：{best}")
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    setup_console()
    failed = 0

    if "--candidates" in args:
        i = args.index("--candidates")
        return candidates(args[i + 1] if i + 1 < len(args) else "")

    if "--golden" in args:
        return golden(update="--update" in args)

    if "--repeat" in args:
        i = args.index("--repeat")
        try:
            n = int(args[i + 1]) if i + 1 < len(args) else 5
        except ValueError:
            n = 5
        paths = [a for a in args[i + 2:]] or [GOLDEN_FILES[0]]
    else:
        n = 5
        paths = [p for p in GOLDEN_FILES if os.path.isfile(p)]

    say("=" * 60)
    say(f"判分器防 flaky：同一输入重复判分 {n} 次，输出必须逐字节一致")
    say("=" * 60)
    for p in paths:
        if not os.path.isfile(p):
            continue
        if flaky(p, n):
            say(f"   PASS  {os.path.basename(p)} × {n} 次结果一致")
        else:
            failed += 1
            say(f"   FAIL  {os.path.basename(p)} 出现不一致 —— 判分器不确定，"
                f"A/B 结论不可信")

    say("")
    failed += 1 if golden() else 0
    say("")
    say("=" * 60)
    say("稳定性判定：" + ("通过" if failed == 0 else f"未通过（{failed} 项）"))
    say("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
