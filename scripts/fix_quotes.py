#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把公众号正文里的直角引号「」统一换成中文双引号“”（内层嵌套用‘’）。

**排版铁律（2026-10-13 用户定版）**：本号草稿文章禁用直角引号，一律用双引号。

用法:
    python fix_quotes.py <draft.html> [...]           # 就地替换（自动备份 .bak）
    python fix_quotes.py --check <draft.html> [...]   # 只检查不修改，有残留则退出码 1
    python fix_quotes.py --no-backup <draft.html>     # 不生成 .bak

不配对时中止并报错，不会写出半吊子正文；写盘走原子替换，中途崩不会毁稿。
`「」` 在 HTML 注释里也会被替换（注释不进正文，替换无副作用）。

退出码：0 = 合规/已修好；1 = 仍有残留（--check）；2 = 用法错误/读写失败。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillio import (  # noqa: E402
    SkillIOError,
    convert_quotes,
    read_text,
    say,
    setup_console,
    write_text,
)


def process(path, check=False, backup=True):
    """返回 0/1/2。单个文件的失败不影响其他文件继续处理。"""
    OK, NG = setup_console()
    try:
        src, enc, _bom = read_text(path)
    except SkillIOError as e:
        say(f"{NG} {e}")
        return 2

    left, right = src.count("「"), src.count("」")
    if left != right:
        say(f"{NG} {path}: 引号不配对（左 {left} / 右 {right}），需手工核对；文件未改动")
        return 1

    if check:
        if left:
            say(f"{NG} {path}: 残留 {left} 对直角引号，应改成双引号")
            say(f"   → python scripts/fix_quotes.py {path}")
            return 1
        say(f"{OK} {path}: 无直角引号")
        return 0

    if not left:
        say(f"· {path}: 无需修改")
        return 0

    try:
        dst = convert_quotes(src)
    except ValueError as e:            # 理论上已被上面的配对检查挡住，兜底
        say(f"{NG} {path}: {e}；文件未改动")
        return 1

    bak = write_text(path, dst, encoding=enc, backup=backup)
    say(f"{OK} {path}: 已替换 {left} 对引号为双引号"
        + (f"（备份 {os.path.basename(bak)}）" if bak else ""))
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    setup_console()

    check = "--check" in args
    backup = "--no-backup" not in args
    files = [a for a in args if not a.startswith("-")]

    if not files:
        say(__doc__)
        return 2

    worst = 0
    for path in files:
        worst = max(worst, process(path, check=check, backup=backup))
    return worst


if __name__ == "__main__":
    sys.exit(main())
