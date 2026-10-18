#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能内共用 IO / 控制台兼容层（纯标准库，零第三方依赖）。

为什么需要它（2026-10-18 在中文 Windows 上实测到两次真崩）：

1. **控制台编码**：管道/控制台的编码是 cp936 时，脚本里的 `print("✅ ...")`
   会直接抛 `UnicodeEncodeError`，于是「明明合规」的稿子也变成 traceback + 退出码 1。
   实测命令：`python scripts/typeset_check.py templates/style-floating.html`
2. **稿件编码**：稿件常被存成 GBK / 带 BOM，硬编码 `encoding="utf-8"`
   会抛 `UnicodeDecodeError`，而且是在 check_file 里裸露 traceback。

对外接口：
    setup_console()              控制台降级，返回 (OK 标记, NG 标记)
    read_text(path)              → (text, encoding, had_bom) 自动识别编码
    write_text(path, text, ...)  原子写 + 可选 .bak 备份（写到一半崩不会毁稿）
    convert_quotes(text)         「」→“”，内层 ‘’；不配对抛 ValueError
    SkillIOError                 可直接捕获后 exit 2 的友好异常（不吐 traceback）
"""
import codecs
import os
import shutil
import sys
import tempfile

# 单文件上限：超过这个体积基本是打包/整站导出，不是单篇稿子
MAX_BYTES = 32 * 1024 * 1024


class SkillIOError(Exception):
    """可直接打印给用户看的错误（脚本应捕获它并 exit 2，而不是吐 traceback）。"""


def _can_encode(stream, ch):
    enc = getattr(stream, "encoding", None) or "utf-8"
    try:
        ch.encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def setup_console():
    """让输出永不因编码崩掉，并返回与当前输出端兼容的对错标记。

    分两种场景（2026-10-18 实测都踩过）：
    - **被管道/编辑器捕获**（非 TTY）→ 强制 UTF-8。否则 CodeBuddy、CI、`> log.txt`
      拿到的是 cp936 字节，按 UTF-8 一读就是乱码。
    - **真实控制台**（TTY，中文 Windows 默认 cp936）→ 保持系统编码，
      只把不可编码字符降级成 ?，中文字正常显示、emoji 降级不报错。
    """
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        try:
            if getattr(stream, "isatty", lambda: False)():
                stream.reconfigure(errors="replace")
            else:
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ok = "✅" if _can_encode(sys.stdout, "✅") else "[OK]"
    ng = "❌" if _can_encode(sys.stdout, "❌") else "[X]"
    return ok, ng


def say(*args, **kw):
    """print 的兜底版：极端情况下编码仍失败时退回 ASCII，绝不抛异常。"""
    try:
        print(*args, **kw)
    except UnicodeEncodeError:
        safe = [str(a).encode("ascii", "replace").decode("ascii") for a in args]
        print(*safe, **kw)


# 候选编码按「可信度」排序：BOM 优先，然后 UTF-8（严格），最后 GB18030 兜底
_TEXT_BOMS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


def read_text(path, max_bytes=MAX_BYTES):
    """读稿子：自动识别 UTF-8 / UTF-8 BOM / GBK / UTF-16。

    返回 (text, encoding, had_bom)。
    失败时抛 SkillIOError（含具体修法），不抛 UnicodeDecodeError。
    """
    if not os.path.exists(path):
        raise SkillIOError(f"文件不存在：{path}")
    if os.path.isdir(path):
        raise SkillIOError(f"这是文件夹不是文件：{path}（要指到具体的 .html）")

    size = os.path.getsize(path)
    if size > max_bytes:
        raise SkillIOError(
            f"文件过大：{path} 有 {size / 1048576:.1f} MB，超过 {max_bytes//1048576} MB 上限。"
            f"\n   → 单篇公众号稿通常 < 500 KB；请确认是不是把整站导出/打包文件当成稿件了。"
        )
    if size == 0:
        return "", "utf-8", False

    with open(path, "rb") as f:
        raw = f.read()

    head = raw[:4096]
    if b"\x00" in head and not any(raw.startswith(b) for b, _ in _TEXT_BOMS):
        raise SkillIOError(
            f"看起来是二进制/压缩文件（含 NUL 字节）：{path}"
            f"\n   → 本技能只校验 HTML 文本稿（.html / .htm / .txt）。"
        )

    for bom, enc in _TEXT_BOMS:
        if raw.startswith(bom):
            try:
                return raw.decode(enc), enc, True
            except UnicodeDecodeError:
                break

    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc), enc, False
        except UnicodeDecodeError:
            continue

    raise SkillIOError(
        f"无法识别文件编码：{path}（已试 UTF-8 / GBK(GB18030) / UTF-16）"
        f"\n   → 用 VSCode 打开后「另存为编码 → UTF-8」，或 PowerShell 执行："
        f"\n     Get-Content '{path}' -Encoding Default | Set-Content '{path}' -Encoding UTF8"
    )


def write_text(path, text, encoding="utf-8", backup=True):
    """原子写：先写同目录临时文件再 os.replace，中途崩不会留下半个稿子。

    返回备份文件路径（没备份则 None）。
    """
    enc = encoding or "utf-8"
    try:
        data = text.encode(enc)
    except (LookupError, UnicodeEncodeError):
        enc, data = "utf-8", text.encode("utf-8")

    bak = None
    if backup and os.path.exists(path):
        bak = path + ".bak"
        try:
            shutil.copy2(path, bak)
        except OSError:
            bak = None

    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".snowfox-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    return bak


def convert_quotes(text):
    """直角引号「」→ 中文双引号“”，嵌套层用‘’。

    逐字符走，天然处理不连续出现与嵌套；不配对时抛 ValueError（调用方不得写回文件）。
    """
    out = []
    depth = 0  # 0 = 双引号层，1 = 单引号层
    for ch in text:
        if ch == "「":
            out.append("“" if depth == 0 else "‘")
            depth ^= 1
        elif ch == "」":
            depth ^= 1
            out.append("”" if depth == 0 else "’")
        else:
            out.append(ch)
    if depth != 0:
        raise ValueError("直角引号不配对：多出 1 个左引号「，须手工核对")
    return "".join(out)
