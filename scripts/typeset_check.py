#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号正文排版合规检查器（确定性、纯标准库、零第三方依赖）

检查 8 类坏法，每类一条规则，**每条都带行号 + 为什么 + 怎么改 + 能否自动修**：
  B1 微信剥离  style标签 / class属性 / script / 行内事件属性残留
  B2 边框缺失  有底色的 section/div 没有整圈 border（灰底托盘、导读块、CLI黑底为例外）
  B3 标点违规  直角引号「」残留（本号铁律：一律用中文双引号）
  B4 结构损坏  标签开闭不配对或错位嵌套（栈式校验）
  B5 外域资源  非 mmbiz.qpic.cn 的图片/背景图、非 mp.weixin.qq.com 的外链
  B6 语义越界  金句/提醒该红底、升华/分层该绿底、规格卡该蓝底，串用即报
               判据三值：显式标注 / 强角色词 / 视觉指纹 → 判错；
               只命中「注意：」这类通用汉语 → 只提醒，不判错（避免误伤换了措辞的作者）
  B7 红底超配额 红底 #FDF3F2 卡片数超过按字数算出的上限
  B8 封面级卡退化 报头/文末卡应有 border 且宽度分档（封面级 2px / 内容级 1px）

⛔ B7 的配额随字数自动伸缩（同 px 自适应），不是固定值：
    ≤500 字 → 红底 ≤1 · ≤1000 字 → ≤2 · ≤2000 字 → ≤3 · >2000 字 → ≤4

用法：
    python typeset_check.py <draft.html> [...]        # 检查指定文件
    python typeset_check.py --all                     # 检查 templates/ 下全部 HTML
    python typeset_check.py --all --dir <路径>        # 检查指定目录
    python typeset_check.py --fix <draft.html>        # 自动修可修的（B1/B2/B3/B6/B8）
    python typeset_check.py --fix --dry-run <draft>   # 只看会改什么，不落盘
    python typeset_check.py --json <draft.html>       # 机器可读（纯 ASCII，管道安全）
    python typeset_check.py --explain B7              # 查一条规则的原因与修法
    python typeset_check.py --roles                   # 看角色词表（强/弱标记、底色、指纹）
    python typeset_check.py --annotate <draft.html>   # 给角色明确的卡补 <!-- role:x --> 标注

退出码：0 = 全部合规；1 = 有违规（逐条列出）；2 = 用法错误/读写失败。
「待确认」项（证据不足，如只命中「注意：」这类通用词）只列出，不计入退出码。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillio import (  # noqa: E402  （同目录共享模块，技能可整体拷走）
    SkillIOError,
    convert_quotes,
    read_text,
    say,
    setup_console,
    write_text,
)

# ---------------------------------------------------------------- 判据常量

# B2 合法例外：不参与卡片体系的底色
#   #F2F3F5 = 承载整篇的灰底托盘（背景容器，不是卡片）
#   #282C34 = 代码块 CLI 黑底（功能性色）
EXCLUDE_BG = {"#F2F3F5", "#282C34"}

# B2 语义例外：**导读块刻意无边框**（2026-10-13 用户确认「本来就没有边框」）
#   ⛔ 不能按底色豁免——#F4F8FC 也用于「规格卡」那块，规格卡是有边框的。
NO_BORDER_MARKERS = ("本期看点", "导读")

CARD_RE = re.compile(r'<(?:section|div)\s+style="([^"]*)"')
BG_RE = re.compile(r"background(?:-color)?:\s*(#[0-9A-Fa-f]{6})")

# B2 只认「整圈 border」。⛔ border-top 之类单边线不算——真机上另外三边是空的。
#   (?<![\w-]) 保证不匹配 border-top / border-radius / border-width
BORDER_FULL_RE = re.compile(r'(?<![\w-])border\s*:\s*[^;"\']*?(?:\d[^;"\']*)')
BORDER_WIDTH_RE = re.compile(r'(?<![\w-])border\s*:\s*(\d+)px')

# src/href 允许单双引号与裸写（微信编辑器两种都会产出）
IMG_RE = re.compile(r"""<img[^>]*\bsrc\s*=\s*["']?([^"'\s>]+)""", re.I)
HREF_RE = re.compile(r"""<a[^>]*\bhref\s*=\s*["']?([^"'\s>]+)""", re.I)
BG_IMG_RE = re.compile(r"""background(?:-image)?\s*:\s*url\(\s*["']?(https?://[^"')\s]+)""", re.I)

WECHAT_IMG_HOSTS = ("http://mmbiz.qpic.cn", "https://mmbiz.qpic.cn")
WECHAT_LINK_HOSTS = ("http://mp.weixin.qq.com", "https://mp.weixin.qq.com")

# ---------------------------------------------------------------- 角色词表（B6）
#
# 角色识别按内容语义（微信正文不允许 class，卡片顺序随文章变，没有更可靠的锚点）
#   ⛔ 金句块 = 红色（2026-10-13 用户定版）
#   ✅ 升华块 = 绿底
# ⛔ 关键词必须精确：升华块的示例文案是“收尾金句”，若用宽泛的“金句”做金句标记，
#    升华块会被误判成金句块。升华用“收尾金句”整体匹配，不拆“金句”二字。
#
# ⛔ 2026-10-18 分两级置信度。原因：二值判定必然在「误报」和「漏报」之间二选一，
#    「注意：」这种通用汉语出现在论述段里就要求人家改红底，是典型误报。
#      strong = 技能专用词（作者几乎不会在别处用到）→ 命中即判错
#      weak   = 通用汉语 → 单独命中只提醒（WARN），不卡交付、不自动改
DEFAULT_ROLES = [
    {"key": "quote", "label": "金句/重点提醒", "bg": "#FDF3F2",
     "strong": ["核心金句"], "weak": ["最值得注意", "注意："],
     "fingerprint": "border-left: 4px solid #D93F2B"},
    {"key": "layer", "label": "升华/分层", "bg": "#F0F9F2",
     "strong": ["升华块", "层名称", "一句话职能", "收尾金句"], "weak": [],
     "fingerprint": "border-left: 4px solid #09B83E"},
    {"key": "spec", "label": "规格信息", "bg": "#F4F8FC",
     "strong": ["规格项", "参数说明"], "weak": [],
     "fingerprint": ""},
]

ROLES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roles.json")

# 卡片里可以显式声明角色，优先级最高：微信不渲染注释，且作者改了措辞也照样认。
#   <!-- role:quote -->  → 这张卡是金句卡
ROLE_ANN_RE = re.compile(r"<!--\s*role\s*:\s*([A-Za-z_][\w-]*)\s*-->")


def load_roles():
    """读 scripts/roles.json（外置可增补）；缺失/损坏时回退内置默认，绝不因配置崩。"""
    try:
        data = json.loads(read_text(ROLES_PATH)[0])
        raw = data.get("roles") or []
        roles = []
        for r in raw:
            if not all(k in r for k in ("key", "label", "bg")):
                continue                       # 缺字段的角色整条跳过，不猜
            roles.append({
                "key": str(r["key"]).lower(),
                "label": str(r["label"]),
                "bg": str(r["bg"]),
                "strong": [str(x) for x in (r.get("strong") or [])],
                "weak": [str(x) for x in (r.get("weak") or [])],
                "fingerprint": str(r.get("fingerprint") or ""),
            })
        if roles:
            return roles
    except Exception:
        pass
    return [dict(r) for r in DEFAULT_ROLES]


ROLES = load_roles()


def _markers(key, kind):
    for r in DEFAULT_ROLES:
        if r["key"] == key:
            return tuple(r.get(kind) or ())
    return ()


# 兼容旧名：其它脚本与收敛矩阵按这几个名字审计实现，⛔ 不能删
RED_MARKERS = _markers("quote", "strong") + _markers("quote", "weak")
GREEN_MARKERS = _markers("layer", "strong") + _markers("layer", "weak")
BLUE_MARKERS = _markers("spec", "strong") + _markers("spec", "weak")

# 封面级/内容级标记 + 应有边框宽度（封面级=2px / 内容级=1px）
# ⛔ 2026-10-13 真实翻车：用户反馈文末「事实来源」「开源仓库」没有边框线条。
#    分档依据来自 references/typography-and-color.md 的配色表：
#    报头与文末引导/引流/提醒/互动是 2px 封面级，
#    事实来源与升华是内容级 1px —— 不能一律判 2px（否则误报）。
ENDING_BLOCKS = {
    "by SnowFox": 2,                                # 报头（封面级，与 references 配色表一致）
    "AI 对话已开通": 2, "AI对话已开通": 2,          # 文末④ AI 对话引导
    "GitHub开源仓库有好货": 2, "开源仓库有好货": 2,  # 文末③ 引流
    "今日最值得深挖": 2,                            # 文末① 提醒
    "评论区聊聊": 2, "哪条你最想": 2,                # 文末② 互动
    "事实来源": 1, "资料来源": 1, "参考来源": 1,      # 核对信息块 = 内容级
}

# 红底配额：字数上限 → 红底卡片数上限（随字数伸缩，不是固定值）
# ⛔ 短稿也要收紧：300 字的短评给 2 张红就等于满篇红，失去强调意义
RED = "#FDF3F2"
RED_QUOTA = [(500, 1), (1000, 2), (2000, 3), (10 ** 9, 4)]

# 需要校验嵌套的容器标签（微信正文里会成对出现的）
NEST_TAGS = ("section", "div", "p", "h2", "table", "thead", "tbody", "tr", "th", "td")
_TAG_RE = re.compile(r"<(/?)(%s)\b[^>]*?(/?)>" % "|".join(NEST_TAGS), re.I)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)

# ---------------------------------------------------------------- 规则说明（--explain）

RULE_DOCS = {
    "B1": ("微信剥离", "style 标签 / class 属性 / script / 行内事件属性",
           "微信正文会把 <style>、class、<script>、onclick 全部过滤掉；靠它们写的样式到真机就没了。",
           "把规则逐条内联进 style=\"\"，删掉 class 与事件属性。",
           True,
           '❌ <section class="card">…</section>\n✅ <section style="border:1px solid #E3E8EF;…">…</section>'),
    "B2": ("边框缺失", "有底色的 section/div 没有整圈 border",
           "卡片靠 1px 描边和浅底色拉开层次；缺边框在真机上会和底板糊成一片。",
           "在该 style 里补 border: 1px solid #E3E8EF;"
           "封面级卡（报头/文末①②③④）要 2px，见 B8。"
           "同底色下「本期看点/导读」是刻意无边框，属合法例外。",
           True,
           '❌ style="background:#F0F9F2;"\n✅ style="background:#F0F9F2;border:1px solid #E3E8EF;"'),
    "B3": ("标点违规", "直角引号「」残留",
           "本号标点铁律（2026-10-13 定版）：正文一律用中文双引号“”，禁用直角引号。",
           "跑 --fix 或 python scripts/fix_quotes.py <稿>；引号不配对时脚本会中止，需手工核对。",
           True,
           "❌ 所谓「主动记忆」\n✅ 所谓“主动记忆”"),
    "B4": ("结构损坏", "标签开闭不配对、错位嵌套",
           "微信对错位嵌套会整段吞掉样式，肉眼几乎看不出来。数量相等但顺序错也一样坏。",
           "按报错提示的行号看该处开闭顺序；常见是卡片复制时漏了一个 </section>。",
           False,
           "❌ <section><div></section></div>\n✅ <section><div></div></section>"),
    "B5": ("外域资源", "非 mmbiz.qpic.cn 图片 / 非 mp.weixin.qq.com 外链",
           "微信只显示自家图床的图片，外域图会显示空白；外链会被拦截或改写成不可点。",
           "图片先上传素材库换成 mmbiz 链接；外链换成公众号内链（mp.weixin.qq.com/s/…）。",
           False,
           '❌ <img src="https://example.com/a.png">\n✅ <img src="https://mmbiz.qpic.cn/mmbiz_jpg/…">'),
    "B6": ("语义越界", "金句/升华/规格卡的底色串用",
           "三色分工：红=强调提醒 · 绿=分层收尾 · 蓝=结构规格。金句做成绿底肉眼很难发现，但语义就错了。",
           "按卡片里的角色词换底色：核心金句/注意→#FDF3F2；升华/层名称→#F0F9F2；规格项→#F4F8FC。"
           "作者换了措辞就认不出来，此时可写 <!-- role:quote --> 显式声明角色（微信不渲染注释），"
           "或跑 --annotate 把已判定的角色固化下来。",
           True,
           '❌ style="background:#F0F9F2;" <p>核心金句…</p>\n✅ style="background:#FDF3F2;" <p>核心金句…</p>'),
    "B7": ("红底超配额", "红底卡片数超过按字数算出的上限",
           "红色是强调色，满篇红等于没有重点。配额随字数伸缩：≤500字→1 · ≤1000→2 · ≤2000→3 · >2000→4。",
           "把最弱的那张红卡降级成绿卡或白卡；真要保留就把正文写长，让配额跟着涨。",
           False,
           "❌ 900 字里塞 3 张红底\n✅ 900 字最多 2 张红底（留 1 张给真正的金句）"),
    "B8": ("封面级卡边框退化", "封面级卡缺 border 或宽度写错（该 2px 写成 1px）",
           "封面级区块是 2px 描边，内容级（含事实来源、升华）是 1px。退化后视觉层级塌掉——"
           "2026-10-13 用户真机截图发现的真实问题。",
           "按卡片文字定档：报头/AI对话/开源仓库/最值得深挖/互动问句→2px；"
           "事实来源/资料来源/升华→1px。",
           True,
           '❌ <section style="background:#F0F9F2;"…>AI 对话已开通</section>\n'
           '✅ <section style="background:#F0F9F2;border:2px solid #09B83E;"…>'),
}

# ---------------------------------------------------------------- 基础工具


def _norm(c):
    return (c or "").upper()


def _line_of(html, pos):
    """按位置算行号（1 起），报错必须能定位，否则等于让人全文搜。"""
    return html.count("\n", 0, max(0, pos)) + 1


def _strip_comments(html):
    """把 HTML 注释**等长替换成空格**（保留换行）。

    ⛔ 两个理由：
      1. 组件库里紧挨卡片的用法注释写着「核心金句」「升华块」，不剥会被当成卡片内容；
      2. 用等长替换而不是删除，才能让剥注释后的偏移量与原文一致（行号、--fix 都要对齐）。
    """
    return _COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), html)


def _tag_pairs(html):
    """一次扫描建开标签→闭合标签位置的映射，供取卡片真实内容用。

    ⛔ 原先用「最多看 600 字符」的固定窗口：卡片内容超过 600 字时，
      后半段的关键词（文末标记、角色词）会漏检。改为按标签栈取真实边界。
    """
    pairs, stack = {}, []
    for m in _TAG_RE.finditer(html):
        closing, tag, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if selfclose:                       # <br/> 之类自闭合，直接跳过
            continue
        if not closing:
            stack.append((tag, m.start()))
        else:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == tag:
                    pairs[stack[i][1]] = m.start()
                    del stack[i:]
                    break
    return pairs


def _card_inner(html, m, pairs):
    """取卡片自身内容：到它真正的闭合标签为止（取不到时退回 600 字符保守窗口）。"""
    close = pairs.get(m.start())
    if close is None or close <= m.end():
        return html[m.end(): m.end() + 600]
    return html[m.end():close]


def _style_key(st):
    """style 归一化：抹掉空格与大小写差异，供指纹比对（手写时空格随意）。"""
    return re.sub(r"\s+", "", st or "").upper()


def _resolve_role(st, inner_text, raw_inner=None):
    """判定卡片角色，返回 (role, level, evidence)；判不出来返回 (None, None, None)。

    level 即置信度，从高到低：
      declared    卡片里写了 <!-- role:quote -->  —— 作者显式声明，改了措辞也认
      strong      命中技能专用词（核心金句 / 升华块 / 规格项…）
      fingerprint 左侧 4px 色条属于某角色（视觉自证，与用词无关）
      weak        只命中通用汉语（「注意：」）→ 只提醒，不判错
    """
    if raw_inner:
        m = ROLE_ANN_RE.search(raw_inner)
        if m:
            key = m.group(1).lower()
            for r in ROLES:
                if r["key"] == key:
                    return r, "declared", f"卡片标注 role:{key}"
            return None, "unknown", f"卡片标注了不认识的角色 role:{key}"

    for r in ROLES:                            # 强词优先（金句 > 分层 > 规格）
        for k in r["strong"]:
            if k in inner_text:
                return r, "strong", f"角色词「{k}」"

    key = _style_key(st)
    for r in ROLES:                            # 视觉指纹：不依赖文案
        fp = r.get("fingerprint") or ""
        if fp and _style_key(fp) in key:
            return r, "fingerprint", "左侧 4px 色条（视觉指纹）"

    for r in ROLES:
        for k in r["weak"]:
            if k in inner_text:
                return r, "weak", f"通用词「{k}」"
    return None, None, None


def _ending_width(inner):
    """返回该封面级/内容级块应有的边框宽度与名字；都不是则返回 (None, None)。"""
    for k, w in ENDING_BLOCKS.items():
        if k in inner:
            return w, k
    return None, None


def _label_of(txt):
    """从卡片纯文本里取一个短标签，报错时好认。"""
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:16] if txt else "未命名卡片"


def _count_words(html):
    """统计正文可见字数（中文按字计）。

    排除：注释、style 属性、标签本身、a 链接整段（含文字）。
    B7 的配额靠它算，所以必须只算读者真能看到的字。
    """
    s = _strip_comments(html)
    s = re.sub(r"<a\b[^>]*>.*?</a>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"&[a-z]+;|&#\d+;", "", s)
    return len(re.sub(r"\s+", "", s))


def _red_quota(words):
    for lim, quota in RED_QUOTA:
        if words <= lim:
            return quota
    return RED_QUOTA[-1][1]


def _red_cards(html):
    """返回红底卡片 (位置, 标签) 列表。"""
    out = []
    clean = _strip_comments(html)
    pairs = _tag_pairs(clean)
    for m in CARD_RE.finditer(clean):
        bg = BG_RE.search(m.group(1))
        if bg and _norm(bg.group(1)) == RED:
            out.append((m.start(), _label_of(re.sub(r"<[^>]+>", " ", _card_inner(clean, m, pairs)))))
    return out


def _check_nesting(html):
    """栈式校验：既抓数量不配对，也抓"数量相等但错位嵌套"。返回 (消息, 位置) 或 None。"""
    stack, counts = [], {}
    for m in _TAG_RE.finditer(html):
        closing, tag, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        counts[tag] = counts.get(tag, 0) + (-1 if closing else 1)
        if selfclose:
            continue
        if not closing:
            stack.append((tag, m.start()))
        else:
            if not stack:
                return f"</{tag}> 没有对应的开标签", m.start()
            if stack[-1][0] != tag:
                return (f"嵌套错位：</{tag}> 出现时栈顶是 <{stack[-1][0]}>，"
                        f"应先闭合 </{stack[-1][0]}>"), m.start()
            stack.pop()
    if stack:
        names = "、".join(t for t, _ in stack[:5])
        return f"未闭合标签：{names}", stack[0][1]
    bad = [f"<{t}> 净差 {n:+d}" for t, n in counts.items() if n != 0]
    return ("开闭数量不等：" + "、".join(bad), 0) if bad else None


def _v(code, html, pos, msg, fix):
    why = RULE_DOCS[code][2]
    return {
        "code": code,
        "line": _line_of(html, pos) if pos is not None else None,
        "msg": msg,
        "why": why,
        "fix": fix,
        "auto": RULE_DOCS[code][4],
    }


# ---------------------------------------------------------------- 检查主体


def _violations(html):
    """返回 (违规列表, 待确认列表)。违规项含 code/line/msg/why/fix/auto。

    ⛔ 待确认（warns）**不计入退出码、不自动修**——它们只是「证据不足」，
       判成违规会误伤换了措辞的作者，判成合规又等于把不确定性藏起来。
    """
    out, warns = [], []
    clean = _strip_comments(html)
    pairs = _tag_pairs(clean)

    # ---- B1 微信会剥离/禁用的写法 ----
    for label, pat, howto in (
        ("<style> 标签", r"<style\b[^>]*>", "删掉 <style>…</style>，把规则搬进各标签的 style"),
        ("class 属性", r"""class\s*=\s*["'][^"']*["']""", "删掉 class，把样式内联到 style"),
        ("<script> 标签", r"<script\b[^>]*>", "删掉整段 <script>…</script>"),
        ("行内事件属性", r"""\son(?:click|load|error|mouseover|mouseout)\s*=\s*["'][^"']*["']""",
         "删掉事件属性（微信不执行 JS）"),
    ):
        ms = list(re.finditer(pat, clean, re.I))
        if ms:
            out.append(_v("B1", html, ms[0].start(),
                          f"{label} × {len(ms)}（微信正文会过滤掉，须为 0）", howto))

    # ---- B2 有底色必须有整圈边框（按元素计数，不按行） ----
    cards = missing = 0
    miss_bg, first_miss = [], None
    for m in CARD_RE.finditer(clean):
        st = m.group(1)
        bg = BG_RE.search(st)
        if not bg or _norm(bg.group(1)) in EXCLUDE_BG:
            continue
        inner = _card_inner(clean, m, pairs)
        # 导读块刻意无边框（2026-10-13 用户确认），按内容语义豁免，
        # 不能按底色豁免——#F4F8FC 也用于规格卡，规格卡必须有边框。
        if any(k in inner for k in NO_BORDER_MARKERS):
            continue
        cards += 1
        if not BORDER_FULL_RE.search(st):
            missing += 1
            miss_bg.append(_norm(bg.group(1)))
            if first_miss is None:
                first_miss = m.start()
    if missing:
        out.append(_v("B2", html, first_miss,
                      f"{missing}/{cards} 个有底色的 section 缺整圈 border"
                      f"（底色：{'、'.join(sorted(set(miss_bg)))}）",
                      "在该 style 里补 border: 1px solid #E3E8EF;"
                      "（⛔ border-top 这类单边线不算）"))

    # ---- B3 标点铁律：直角引号 ----
    l, r = clean.count("「"), clean.count("」")
    if l:
        pos = clean.find("「")
        if l != r:
            out.append(_v("B3", html, pos,
                          f"直角引号不配对（左{l}/右{r}），脚本不会自动改坏文件",
                          "手工核对这对引号；配平后再跑 fix_quotes.py"))
        else:
            out.append(_v("B3", html, pos,
                          f"残留 {l} 对直角引号「」，本号一律用中文双引号“”",
                          "python scripts/fix_quotes.py <稿>（或本脚本 --fix）"))

    # ---- B4 标签配对与嵌套顺序 ----
    bad = _check_nesting(clean)
    if bad:
        msg, pos = bad
        out.append(_v("B4", html, pos, msg, "按行号看该处开闭顺序，补上缺失的闭合标签"))

    # ---- B5 外域资源 ----
    ext = [u for u in IMG_RE.findall(clean) if not u.startswith(WECHAT_IMG_HOSTS)]
    if ext:
        out.append(_v("B5", html, clean.find(ext[0]),
                      f"{len(ext)} 张非 mmbiz.qpic.cn 图片（微信不显示外域图）",
                      "先上传素材库，把 src 换成 mmbiz.qpic.cn 链接"))
    bg_ext = [u for u in BG_IMG_RE.findall(clean) if not u.startswith(WECHAT_IMG_HOSTS)]
    if bg_ext:
        out.append(_v("B5", html, clean.find(bg_ext[0]),
                      f"{len(bg_ext)} 处背景图走外域（background:url 同样会被过滤）",
                      "背景图先上传素材库，换成 mmbiz.qpic.cn 链接"))
    bad_link = [u for u in HREF_RE.findall(clean)
                if u.startswith("http") and not u.startswith(WECHAT_LINK_HOSTS)]
    if bad_link:
        out.append(_v("B5", html, clean.find(bad_link[0]),
                      f"{len(bad_link)} 个非微信域名的外链",
                      "换成公众号内链 https://mp.weixin.qq.com/s/…"))

    # ---- B6 语义越界（三值：标注/强词/指纹判错，通用词只提醒） ----
    # ⛔ 两个前提缺一不可：
    #    ① 先剥HTML 注释（否则用法注释里的角色名会被当成卡片内容）
    #    ② 按卡片真实闭合边界取内容（否则固定窗口会跨卡片串味）
    for m in CARD_RE.finditer(clean):
        st = m.group(1)
        bg = BG_RE.search(st)
        if not bg:
            continue
        c = _norm(bg.group(1))
        if c in EXCLUDE_BG:
            continue
        inner = _card_inner(clean, m, pairs)
        raw = _card_inner(html, m, pairs)      # 未剥注释的原文，用来读 role: 标注
        role, level, evi = _resolve_role(st, inner, raw)
        if role is None:
            if level == "unknown":
                warns.append({"line": _line_of(html, m.start()), "msg": evi,
                              "fix": "改成 " + "/".join(r["key"] for r in ROLES)
                                     + " 之一，或删掉这条标注"})
            continue
        if c == _norm(role["bg"]):
            continue
        msg = (f"{role['label']}用了底色 {bg.group(1)}，应为 {role['bg']}"
               f"（判定依据：{evi}）")
        how = f"把 background 改成 {role['bg']}"
        if level == "weak":
            warns.append({"line": _line_of(html, m.start()), "msg": msg,
                          "fix": how + "；若这里只是普通论述，改掉措辞即可，不必改色"})
        else:
            out.append(_v("B6", html, m.start(), msg, how))

    # ---- B7 红底超配额（配额随字数自动伸缩） ----
    reds = _red_cards(html)
    if reds:
        words = _count_words(html)
        quota = _red_quota(words)
        if len(reds) > quota:
            lines = "、".join(str(_line_of(html, p)) for p, _ in reds)
            out.append(_v("B7", html, reds[0][0],
                          f"红底卡片 {len(reds)} 张，超出配额 {quota} 张"
                          f"（全文 {words} 字；出现位置：第 {lines} 行）",
                          f"把最弱的那张红卡改成绿卡/白卡，压到 {quota} 张以内"))

    # ---- B8 文末卡边框宽度（2px 封面级，不能退化） ----
    # ⛔ 真实翻车记录 2026-10-13：用户反馈文末「事实来源」「开源仓库」两块没有边框线条。
    #    根因是被当成普通内容卡写，没按封面级来。B2 只看"有没有 border"，
    #    看不出"该 2px 却写成 1px"，所以单靠 B2 抓不住这类退化。
    for m in CARD_RE.finditer(clean):
        st = m.group(1)
        bg = BG_RE.search(st)
        if not bg:
            continue                       # 无底色的容器不是卡片，不参与边框体系
        c = _norm(bg.group(1))
        if c in EXCLUDE_BG:
            # 底板是容器、代码块是功能性色：两者都不是卡片。
            # ⛔ 底板包着全篇，不排除会把文末卡的文案算到自己头上（实测误报过一次）
            continue
        inner = _card_inner(clean, m, pairs)
        want, name_ = _ending_width(inner)
        if want is None:
            continue
        level = "封面级" if want == 2 else "内容级"
        bd = BORDER_WIDTH_RE.search(st)
        if not bd:
            edge = "#D93F2B" if c == RED else "#09B83E"
            fix = (f"补 border: {want}px solid {edge}" if want == 2
                   else "补 border: 1px solid #E3E8EF")
            out.append(_v("B8", html, m.start(),
                          f"封面级卡「{name_}」有底色但没有 border，必须描边"
                          f"（{want}px {level}）", fix))
        elif int(bd.group(1)) != want:
            out.append(_v("B8", html, m.start(),
                          f"封面级卡「{name_}」边框是 {bd.group(1)}px，应为 {want}px（{level}）",
                          f"把 border 宽度改成 {want}px"))

    out.sort(key=lambda v: (v["line"] or 0, v["code"]))
    warns.sort(key=lambda w: w["line"] or 0)
    return out, warns


# ---------------------------------------------------------------- 自动修复


def _style_set_bg(st, color):
    m = BG_RE.search(st)
    if not m:
        return st.rstrip().rstrip(";") + f";background:{color};"
    return st[:m.start()] + re.sub(r"#[0-9A-Fa-f]{6}", color, m.group(0)) + st[m.end():]


def _style_set_border(st, width, color):
    decl = f"border: {width}px solid {color}"
    m = BORDER_FULL_RE.search(st)
    if m:
        return st[:m.start()] + decl + st[m.end():]
    return st.rstrip().rstrip(";") + ";" + decl + ";"


def fix_html(html):
    """自动修可修的 5 类（B1/B2/B3/B6/B8），返回 (新HTML, 修了什么[], 没修什么[])。

    不自动修的三类都有明确理由：
      B4 结构损坏 —— 自动补闭合标签会猜错位置，必须人看
      B5 外域资源 —— 需要先把图传到素材库才能拿到新链接
      B7 红底超配额 —— 删哪张是内容判断，不是排版判断
    """
    actions, skipped = [], []
    new = html

    # ---- B1：剥离会被微信过滤的写法 ----
    pairs = [
        (r"<style\b[^>]*>.*?</style>", "删 <style> 标签"),
        (r"<script\b[^>]*>.*?</script>", "删 <script> 标签"),
        (r"""\s+class\s*=\s*["'][^"']*["']""", "删 class 属性"),
        (r"""\s+on(?:click|load|error|mouseover|mouseout)\s*=\s*["'][^"']*["']""", "删事件属性"),
    ]
    for pat, what in pairs:
        new, n = re.subn(pat, "", new, flags=re.S | re.I)
        if n:
            actions.append(f"B1：{what} × {n}")

    # ---- B3：直角引号（不配对时放弃，绝不写坏文件） ----
    if "「" in new or "」" in new:
        try:
            new2 = convert_quotes(new)
            if new2 != new:
                actions.append(f"B3：替换 {new.count('「')} 对直角引号为中文双引号")
                new = new2
        except ValueError as e:
            skipped.append(f"B3：{e}")

    # ---- B2/B6/B8：逐卡片改 style（位置与原文对齐，所以用等长剥注释） ----
    blank = _strip_comments(new)
    tag_pairs = _tag_pairs(blank)
    edits = []
    for m in CARD_RE.finditer(blank):
        st = m.group(1)
        bg = BG_RE.search(st)
        if not bg or _norm(bg.group(1)) in EXCLUDE_BG:
            continue
        inner = _card_inner(blank, m, tag_pairs)
        if any(k in inner for k in NO_BORDER_MARKERS):
            continue                      # 导读块刻意无边框，不动
        color = _norm(bg.group(1))
        new_st = st

        # B6 先定语义底色（只改「证据够硬」的：标注/强词/指纹；通用词不动）
        role, level, evi = _resolve_role(st, inner, _card_inner(new, m, tag_pairs))
        if role and level in ("declared", "strong", "fingerprint") and color != _norm(role["bg"]):
            new_st = _style_set_bg(new_st, role["bg"])
            color = _norm(role["bg"])
            actions.append(f"B6：第 {_line_of(blank, m.start())} 行{role['label']}"
                           f"改底色 {role['bg']}（依据：{evi}）")
        elif role and level == "weak" and color != _norm(role["bg"]):
            # ⛔ 通用词证据不足：自动改色会把普通论述段刷成红底，宁可不改
            skipped.append(f"B6：第 {_line_of(blank, m.start())} 行{evi}证据不足，未改色")

        # B2 / B8 边框
        want, name_ = _ending_width(inner)
        has_border = bool(BORDER_FULL_RE.search(new_st))
        cur = BORDER_WIDTH_RE.search(new_st)
        if want == 2 and (not has_border or int(cur.group(1)) != 2):
            edge = "#D93F2B" if color == RED else "#09B83E"
            new_st = _style_set_border(new_st, 2, edge)
            actions.append(f"B8：第 {_line_of(blank, m.start())} 行封面级卡「{name_}」边框改 2px")
        elif want == 1 and (not has_border or int(cur.group(1)) != 1):
            new_st = _style_set_border(new_st, 1, "#E3E8EF")
            actions.append(f"B8：第 {_line_of(blank, m.start())} 行事实来源边框改 1px")
        elif not has_border:
            new_st = _style_set_border(new_st, 1, "#E3E8EF")
            actions.append(f"B2：第 {_line_of(blank, m.start())} 行补 1px 边框")

        if new_st != st:
            edits.append((m.start(1), m.end(1), new_st))

    for s, e, st in reversed(edits):
        new = new[:s] + st + new[e:]

    return new, actions, skipped


# ---------------------------------------------------------------- 输出


def annotate_html(html):
    """给角色明确的卡片补 <!-- role:xxx --> 标注，返回 (新文本, 补了几张)。

    ⛔ 目的：标注一旦写下，B6 就不再依赖文案措辞——作者改写标题词也照样认。
       微信不渲染注释，标注不会进真机；它是工作副本里的元信息。
    ⛔ 判不准的（只有通用词）不写：把猜测固化成事实比不标注更糟。
    """
    clean = _strip_comments(html)
    pairs = _tag_pairs(clean)
    inserts = []
    for m in CARD_RE.finditer(clean):
        st = m.group(1)
        bg = BG_RE.search(st)
        if not bg or _norm(bg.group(1)) in EXCLUDE_BG:
            continue
        inner = _card_inner(clean, m, pairs)
        raw = _card_inner(html, m, pairs)
        if ROLE_ANN_RE.search(raw):
            continue                            # 已有标注 → 幂等，重复跑不会叠加
        role, level, _evi = _resolve_role(st, inner, raw)
        if role is None or level == "weak":
            continue
        # ⛔ CARD_RE 只匹配到 style 属性结尾，标注必须插在开标签的 > 之后，
        #    插在 m.end() 会落进标签内部（实测写成 style="…"<!-- role --> 的畸形）。
        gt = html.find(">", m.end())
        inserts.append((gt + 1 if gt != -1 else m.end(), f"<!-- role:{role['key']} -->"))
    for pos, txt in reversed(inserts):
        html = html[:pos] + txt + html[pos:]
    return html, len(inserts)


def _print_report(html, name, vs, out=say, warns=None):
    words = _count_words(html)
    quota = _red_quota(words)
    reds = _red_cards(html)
    cards = sum(1 for m in CARD_RE.finditer(_strip_comments(html))
                if BG_RE.search(m.group(1))
                and _norm(BG_RE.search(m.group(1)).group(1)) not in EXCLUDE_BG)
    suggested = max(2, words // 150)

    out(f"=== 排版合规检查: {name} ===")
    out(f"统计：字数 {words} · 卡片 {cards} 张 · 红底 {len(reds)}/{quota} 张"
        f" · 建议卡片数≈{suggested} 张（字数÷150）")
    warns = warns or []
    if not vs:
        out("✅ 8 类检查全部合规" + (f"（另有 {len(warns)} 项待确认，见下）" if warns else ""))
        _print_warns(warns, out)
        return
    auto = sum(1 for v in vs if v["auto"])
    out(f"❌ {len(vs)} 项违规（其中 {auto} 项可 --fix 自动修，"
        f"{len(vs) - auto} 项需手工）")
    for v in vs:
        where = f"第 {v['line']} 行" if v["line"] else "全文"
        out("")
        out(f"[{v['code']}] {where} · {v['msg']}")
        out(f"     为什么：{v['why']}")
        out(f"     怎么改：{v['fix']}")
        out(f"     {'自动修：python scripts/typeset_check.py --fix <稿>' if v['auto'] else '需手工处理（自动改会猜错）'}")
    _print_warns(warns, out)


def _print_warns(warns, out=say):
    """待确认项：证据不足，不判违规也不自动改，只列出来让人扫一眼。

    ⛔ 刻意不带 [Bx] 编号——带了就会被当成违规统计进去（A/B 增益对照按 [Bx] 计数）。
    """
    if not warns:
        return
    out("")
    out(f"⚠️  {len(warns)} 项待确认（不计入退出码、不自动修，扫一眼即可）")
    for w in warns:
        out(f"   第 {w['line']} 行 · {w['msg']}")
        out(f"      怎么改：{w['fix']}")


def _report_json(html, name, vs, path, warns=None):
    words = _count_words(html)
    return {
        "file": os.path.abspath(path),
        "name": name,
        "words": words,
        "cards": sum(1 for m in CARD_RE.finditer(_strip_comments(html))
                     if BG_RE.search(m.group(1))
                     and _norm(BG_RE.search(m.group(1)).group(1)) not in EXCLUDE_BG),
        "red_cards": len(_red_cards(html)),
        "red_quota": _red_quota(words),
        "suggested_cards": max(2, words // 150),
        "violations": [{"code": v["code"], "line": v["line"], "message": v["msg"],
                        "fix": v["fix"], "auto_fixable": v["auto"]} for v in vs],
        "warnings": [{"line": w["line"], "message": w["msg"], "fix": w["fix"]}
                     for w in (warns or [])],
        "ok": not vs,
    }


# ---------------------------------------------------------------- 入口


def check_file(path, fix=False, dry_run=False, as_json=False, no_backup=False,
               annotate=False):
    """检查单个文件。返回 0（合规）/1（有违规）/2（读写失败）。

    fix=True 时先自动修再报告；dry_run=True 时只预演不落盘；
    annotate=True 时给角色明确的卡片补 <!-- role:xxx --> 标注。
    """
    html, enc, _bom = read_text(path)
    name = os.path.basename(path)
    OK, _NG = setup_console()

    actions, skipped, bak = [], [], None
    if annotate:
        marked, n = annotate_html(html)
        if n:
            if not dry_run:
                bak = write_text(path, marked, encoding=enc, backup=not no_backup)
            html = marked
            actions.append(f"标注：给 {n} 张卡片补了 role 标注")
        else:
            actions.append("标注：没有需要补标注的卡片（都已标注或判不准）")

    if fix:
        fixed, acts, skipped = fix_html(html)
        actions += acts
        if fixed != html:
            if not dry_run:
                bak = write_text(path, fixed, encoding=enc, backup=not no_backup)
            html = fixed

    vs, warns = _violations(html)

    if as_json:
        data = _report_json(html, name, vs, path, warns)
        data["fixed"] = actions
        data["skipped"] = skipped
        data["backup"] = bak
        data["dry_run"] = bool(dry_run)
        # ensure_ascii=True：任何编码的管道都能安全解析
        print(json.dumps(data, ensure_ascii=True, indent=2))
        return 0 if not vs else 1

    if fix or annotate:
        say(f"=== 自动处理: {name} ===")
        if not actions and not skipped:
            say("· 没有可自动处理的项")
        for a in actions:
            say(f"  {OK} {a}")
        for s in skipped:
            say(f"  ⚠️ 跳过 {s}")
        if bak:
            say(f"  （原文件已备份到 {os.path.basename(bak)}，改坏了可以拷回来）")
        elif dry_run and actions:
            say("  （--dry-run：只是预演，没写入文件）")
        say("")

    _print_report(html, name, vs, out=say, warns=warns)
    return 0 if not vs else 1


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    OK, NG = setup_console()

    if not args or "--help" in args or "-h" in args:
        say(__doc__)
        return 0 if args else 2

    if "--explain" in args:
        i = args.index("--explain")
        code = (args[i + 1] if i + 1 < len(args) else "").upper()
        doc = RULE_DOCS.get(code)
        if not doc:
            say(f"没有这条规则：{code or '(空)'}")
            say("可选：" + "、".join(sorted(RULE_DOCS)))
            return 2
        title, what, why, how, auto, sample = doc
        say(f"[{code}] {title} —— {what}")
        say(f"  为什么：{why}")
        say(f"  怎么改：{how}")
        say(f"  能否自动修：{'能（--fix）' if auto else '不能，需手工'}")
        say(f"  对比：\n{sample}")
        return 0

    if "--roles" in args:
        say(f"角色词表（来自 {os.path.basename(ROLES_PATH)}，可直接改文件增补）")
        for r in ROLES:
            say(f"  {r['key']} · {r['label']} · 底色 {r['bg']}")
            if r["strong"]:
                say(f"      强标记（判错）：{'、'.join(r['strong'])}")
            if r["weak"]:
                say(f"      弱标记（只提醒）：{'、'.join(r['weak'])}")
            if r["fingerprint"]:
                say(f"      视觉指纹：{r['fingerprint']}")
        say("  卡片里写 <!-- role:quote --> 可显式声明角色（优先级最高）")
        return 0

    do_fix = "--fix" in args
    dry_run = "--dry-run" in args
    as_json = "--json" in args
    no_backup = "--no-backup" in args
    do_all = "--all" in args
    do_annotate = "--annotate" in args

    # 逐个解析，避免把 --dir 的路径参数误当成待检查文件
    files, target_dir = [], None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--dir":
            if i + 1 >= len(args):
                say("--dir 后面要跟目录路径，例如 --dir templates")
                return 2
            target_dir = args[i + 1]
            i += 2
            continue
        if a not in ("--fix", "--dry-run", "--json", "--no-backup", "--all", "--annotate"):
            files.append(a)
        i += 1

    if not files and not do_all:
        say("没有指定文件。python scripts/typeset_check.py <稿.html> 或 --all")
        return 2

    bad = 0
    try:
        if do_all:
            d = target_dir or os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
            if not os.path.isdir(d):
                say(f"目录不存在：{d}")
                return 2
            names = sorted(f for f in os.listdir(d) if f.lower().endswith((".html", ".htm")))
            if not names:
                say(f"目录内没有 HTML 文件：{d}")
                return 2
            if not as_json:
                say(f"=== 排版合规全库检查: {d} ===")
            for f in names:
                bad += check_file(os.path.join(d, f), do_fix, dry_run, as_json,
                                  no_backup, do_annotate)
            if not as_json:
                say("=" * 50)
                say((OK + " 全库合规") if bad == 0 else f"{NG} 全库有不合规文件")
            return 1 if bad else 0

        for p in files:
            bad += check_file(p, do_fix, dry_run, as_json, no_backup, do_annotate)
        return 1 if bad else 0
    except SkillIOError as e:
        # 读不到/编码识别失败：给可执行的修法，不吐 traceback
        if as_json:                             # 机器读的时候也要能解析
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=True, indent=2))
        else:
            say(f"{NG} {e}")
        return 2
    except KeyboardInterrupt:
        say("\n已中断，文件未被修改")
        return 2
    except Exception as e:                      # 任何意外都不吐 traceback
        msg = f"意外错误：{type(e).__name__}: {e}"
        if as_json:
            print(json.dumps({"ok": False, "error": msg}, ensure_ascii=True, indent=2))
        else:
            say(f"{NG} {msg}")
            say("   → 请把这行报错连同稿件一起反馈；稿件未被修改。")
        return 2


if __name__ == "__main__":
    sys.exit(main())
