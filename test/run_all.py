# -*- coding: utf-8 -*-
"""公众号排版检查器验证集：每类坏法配正反夹具，bad→EXIT 1、good→EXIT 0。

用法：python test/run_all.py     任一失败整体非零退出
"""
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
CHECK = os.path.join(SKILL, "scripts", "typeset_check.py")
FIXQ = os.path.join(SKILL, "scripts", "fix_quotes.py")

sys.path.insert(0, os.path.join(SKILL, "scripts"))
from skillio import setup_console  # noqa: E402

OK, NG = setup_console()

# 子进程统一 UTF-8：不然中文 Windows 的 cp936 输出会被按 UTF-8 解码失败，
# 整个套件在第一步就崩（2026-10-18 实测）。子进程内部也会自己切 UTF-8，这里双保险。
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

# 金句块 = 红色（2026-10-13 定版）
GREEN_CARD = ('<section style="margin-bottom:22px;background:#F0F9F2;'
              'border:1px solid #E3E8EF;padding:18px 20px;">'
              '<p style="margin:0;">升华块：测试</p></section>')

RED = ('<section style="background:#FDF3F2;border:1px solid #E3E8EF;padding:16px 20px;border-radius:12px;box-shadow: 0 2px 10px rgba(31,45,61,0.08);"><p>金句。</p></section>')
WHT = ('<section style="background:#FFFFFF;border:1px solid #E3E8EF;padding:18px 20px;border-radius:12px;box-shadow: 0 2px 10px rgba(31,45,61,0.08);"><p>%s</p></section>')

# (用例名, HTML, 期望退出码, 期望命中的坏法编号或None)
CASES = [
    # ---------- 正常稿：全部合规 ----------
    ("good-纯净合规稿",
     '<section style="font-size:16px;line-height:1.75;color:#3F3F3F;">'
     '<p style="margin:0;">正文段落</p></section>' + GREEN_CARD,
     0, None),

    ("good-合法例外-代码块黑底无边框",
     '<section style="background:#282C34;border-radius:6px;">'
     '<p style="margin:0;">代码</p></section>',
     0, None),

    ("good-合法例外-灰底托盘无边框",
     '<section style="background:#F2F3F5;">'
     '<p style="margin:0;">托盘</p></section>',
     0, None),

    # ---------- B1 微信剥离类----------
    ("bad-B1-style标签残留",
     '<style>p{color:red}</style><section><p>正文</p></section>', 1, "B1"),

    ("bad-B1-class属性残留",
     '<section class="card"><p>正文</p></section>', 1, "B1"),

    ("bad-B1-script残留",
     '<section><script>alert(1)</script><p>正文</p></section>', 1, "B1"),

    ("bad-B1-onclick残留",
     '<section onclick="x()"><p>正文</p></section>', 1, "B1"),

    # ---------- B2 边框缺失（结构性铁律） ----------
    ("bad-B2-有底色无边框",
     '<section style="background:#F0F9F2;"><p>绿底卡</p></section>', 1, "B2"),

    ("bad-B2-浅蓝底无边框",
     '<section style="background:#F4F8FC;"><p>蓝底卡</p></section>', 1, "B2"),

    ("bad-B2-同一行多卡片只漏一个",
     GREEN_CARD + '<section style="background:#FFF8EC;"><p>橙</p></section>', 1, "B2"),

    # 真实逃逸面（由 A/B 对照实测发现）：作者图省事用 div 包卡片，
    # 只查 section 会让 div 形式的缺边框卡片逃逸
    ("bad-B2-div形式的缺边框卡片",
     '<div style="background:#F0F9F2;"><p>div 绿底卡</p></div>', 1, "B2"),

    ("good-B2-div形式合规卡片",
     '<div style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>div 合规</p></div>', 0, None),

    ("good-B2-div无底色不算卡片",
     '<div style="color:#3F3F3F;"><p>无底色 div</p></div>', 0, None),

    # ---------- B3 标点铁律 ----------
    ("bad-B3-残留直角引号",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>这是「主动记忆」概念</p></section>', 1, "B3"),

    ("bad-B3-直角引号不配对",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>「未闭合</p></section>', 1, "B3"),

    # ---------- B4 标签配对 ----------
    ("bad-B4-section不配对",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>少一个闭合</p>', 1, "B4"),

    ("bad-B4-div未闭合",
     '<section><div><p>正文</p></section>', 1, "B4"),

    # 数量相等但错位：计数法抓不到，只有栈式校验能抓
    ("bad-B4-错位嵌套-数量相等",
     '<section><div></section></div>', 1, "B4"),

    ("bad-B4-多余闭合标签",
     '<section><p>正文</p></section></section>', 1, "B4"),

    ("good-B4-标准嵌套含表格",
     '<section><table><thead><tr><th>a</th></tr></thead>'
     '<tbody><tr><td>b</td></tr></tbody></table></section>', 0, None),

    ("good-B4-自闭合br不参与配对",
     '<section><p>行一<br/>行二</p></section>', 0, None),

    # ---------- B5 外域资源 ----------
    ("bad-B5-外域图片",
     '<section><img src="https://example.com/a.png"/></section>', 1, "B5"),

    ("good-B5-合规mmbiz图片",
     '<section><img src="https://mmbiz.qpic.cn/mmbiz_jpg/x/640?wx_fmt=jpeg"/>'
     '</section>', 0, None),

    ("bad-B5-非微信域外链",
     '<section><a href="https://example.com/post">外链</a></section>', 1, "B5"),

    ("good-B5-合规mp.weixin外链",
     '<section><a href="https://mp.weixin.qq.com/s/abc">内链</a></section>', 0, None),

    # ---------- B6 语义越界（2026-10-13 定版：金句=红，升华=绿，规格卡=蓝） ----------
    ("bad-B6-金句用了绿底",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>核心金句：不该是绿底</p></section>', 1, "B6"),

    ("bad-B6-金句用了蓝底",
     '<section style="background:#F4F8FC;border:1px solid #E3E8EF;">'
     '<p>核心金句：不该是蓝底</p></section>', 1, "B6"),

    ("bad-B6-升华块用了蓝底",
     '<section style="background:#F4F8FC;border:1px solid #E3E8EF;">'
     '<p>收尾金句：升华块不该是蓝底</p></section>', 1, "B6"),

    ("bad-B6-升华块用了红底",
     '<section style="background:#FDF3F2;border:1px solid #E3E8EF;">'
     '<p>收尾金句：升华块不该是红底</p></section>', 1, "B6"),

    ("bad-B6-分层卡用了蓝底",
     '<section style="background:#F4F8FC;border:1px solid #E3E8EF;">'
     '<p>层名称：分层卡不该是蓝底</p></section>', 1, "B6"),

    ("bad-B6-规格卡用了绿底",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>规格项：不该是绿底</p></section>', 1, "B6"),

    ("good-B6-金句用红底",
     '<section style="background:#FDF3F2;border:1px solid #E3E8EF;">'
     '<p>核心金句：红底正确</p></section>', 0, None),

    ("good-B6-升华块用绿底",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>收尾金句：绿底正确</p></section>', 0, None),

    ("good-B6-规格卡用蓝底",
     '<section style="background:#F4F8FC;border:1px solid #E3E8EF;">'
     '<p>规格项：蓝底正确</p></section>', 0, None),

    # B6 误报回归：升华块文案含“金句”二字，不能被金句规则误抓
    ("good-B6-升华块文案含金句二字不误报",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>收尾金句，独立成行居中。</p></section>', 0, None),

    # B6 误报回归：用法注释里的角色名不能被当成卡片内容
    ("good-B6-注释里的角色名不误报",
     '<!-- 用法：核心金句、升华块的核心观点 -->\n'
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>升华块：绿底</p></section>', 0, None),

    # B6 串味回归：紧邻卡片不能互相污染
    ("good-B6-相邻卡片不串味",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>升华块：绿底</p></section>'
     '<section style="background:#FDF3F2;border:1px solid #E3E8EF;">'
     '<p>核心金句：红底</p></section>', 0, None),

    # ---------- B6 三值判定（2026-10-18 加：作者改写措辞也要认） ----------
    # 视觉指纹：左侧 4px 红边条就是金句卡的形态，**与文案用词无关**
    ("bad-B6-红边条配白底按指纹判错",
     '<section style="background:#FFFFFF;border:1px solid #E3E8EF;'
     'border-left: 4px solid #D93F2B;padding:18px 20px;">'
     '<p>改过措辞的金句</p></section>', 1, "B6"),
    # 显式标注优先级最高：微信不渲染注释，标注是工作副本里的元信息
    ("bad-B6-标注quote配蓝底",
     '<section style="background:#F4F8FC;border:1px solid #E3E8EF;padding:18px 20px;">'
     '<!-- role:quote --><p>完全改写的措辞</p></section>', 1, "B6"),
    ("good-B6-标注quote配红底",
     '<section style="background:#FDF3F2;border:1px solid #E3E8EF;padding:18px 20px;">'
     '<!-- role:quote --><p>完全改写的措辞</p></section>', 0, None),

    # ---------- 边界：空文件 / 纯文本 / 超长 ----------



    # ---------- B2 语义豁免：导读无边框，但同底色的规格卡仍必须有边框 ----------
    ("good-B2-导读块无边框合法",
     '<section style="background:#F4F8FC;border-radius:12px;padding:18px 20px;">'
     '<p>本期看点</p><p>导读内容</p></section>', 0, None),
    ("good-B2-导读块写导读二字也无边框",
     '<section style="background:#F4F8FC;border-radius:12px;padding:18px 20px;">'
     '<p>导读</p></section>', 0, None),
    # ⛔ 回归：若按底色豁免 #F4F8FC，规格卡会跟着漏检
    ("bad-B2-规格卡同底色仍需边框",
     '<section style="background:#F4F8FC;border-radius:12px;padding:18px 20px;">'
     '<p>规格项</p><p>参数说明</p></section>', 1, "B2"),
    # ---------- B8 文末卡边框退化（真实翻车：事实来源/开源仓库无边框） ----------
    ("bad-B8-文末开源仓库卡无边框",
     '<section style="background:#F0F9F2;padding:20px 22px;">'
     '<p>作者GitHub开源仓库有好货</p></section>', 1, "B8"),
    ("bad-B8-文末事实来源卡无边框",
     '<section style="background:#FFFFFF;padding:18px 20px;">'
     '<p>事实来源：彭博社</p></section>', 1, "B8"),
    ("bad-B8-文末卡退化成1px",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;padding:20px 22px;">'
     '<p>AI 对话已开通</p></section>', 1, "B8"),
    ("good-B8-文末卡合规2px",
     '<section style="background:#F0F9F2;border:2px solid #09B83E;padding:20px 22px;">'
     '<p>AI 对话已开通</p></section>', 0, None),
    # 事实来源是内容级 1px（不是封面级 2px）——B8 必须分档判，不能一律要2px
    ("good-B8-事实来源1px合规",
     '<section style="background:#FFFFFF;border:1px solid #E3E8EF;padding:18px 20px;">'
     '<p>事实来源</p></section>', 0, None),
    # 报头是封面级 2px：退化成 1px 要报（与 references 配色表一致）
    ("bad-B8-报头退化成1px",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;padding:24px 22px;'
     'text-align:center;"><p style="margin:0;letter-spacing:2px;">独立印象馆</p>'
     '<p style="margin:0;">by SnowFox</p></section>', 1, "B8"),
    ("good-B8-报头2px合规",
     '<section style="background:#F0F9F2;border:2px solid #09B83E;padding:24px 22px;'
     'text-align:center;"><p style="margin:0;letter-spacing:2px;">独立印象馆</p>'
     '<p style="margin:0;">by SnowFox</p></section>', 0, None),
    ("bad-B8-事实来源误用2px不强制",
     '<section style="background:#FFFFFF;border:2px solid #E3E8EF;padding:18px 20px;">'
     '<p>事实来源</p></section>', 1, "B8"),
    # 回归：B8 曾误报合规的 2px 卡（group(1) 是 "2" 却比 "2px"）
    ("good-B8-2px合规卡不误报",
     '<section style="background:#F0F9F2;border:2px solid #09B83E;border-radius:12px;'
     'box-shadow:0 2px 10px rgba(0,0,0,0.08);padding:20px 22px;">'
     '<p>AI 对话已开通</p></section>', 0, None),
    # 回归：border-radius 不得被当成 border 宽度
    ("good-B8-border-radius不算边框",
     '<section style="background:#F0F9F2;border:2px solid #09B83E;border-radius:20px;'
     'padding:20px 22px;"><p>AI 对话已开通</p></section>', 0, None),
    # ---------- B7 红底配额随字数伸缩（不是固定值） ----------
    ("good-B7-950字2红未超配额",
     RED*2 + WHT % ('测'*900), 0, None),
    ("bad-B7-950字3红超配额2",
     RED*3 + WHT % ('测'*900), 1, "B7"),
    ("good-B7-1900字3红未超配额",
     RED*3 + WHT % ('测'*1800), 0, None),
    ("bad-B7-1900字4红超配额3",
     RED*4 + WHT % ('测'*1800), 1, "B7"),
    ("good-B7-3100字4红未超配额",
     RED*4 + WHT % ('测'*3000), 0, None),
    ("bad-B7-3100字5红超配额4",
     RED*5 + WHT % ('测'*3000), 1, "B7"),
    # 短稿配额更紧：400 字只给 1 张红
    ("good-B7-400字1红未超配额",
     RED*1 + WHT % ('测'*380), 0, None),
    ("bad-B7-400字2红超配额1",
     RED*2 + WHT % ('测'*380), 1, "B7"),
    # ---------- 判据逃逸面（v2.4.0 补：都曾能绕过检查） ----------
    # 只有上边线不算「卡片有边框」——真机上另外三边是空的
    ("bad-B2-只有border-top不算整圈边框",
     '<section style="background:#F0F9F2;border-top:1px solid #E3E8EF;">'
     '<p>只有上边线</p></section>', 1, "B2"),
    # class 用单引号时，旧正则只认双引号，直接被微信剥掉却查不出来
    ("bad-B1-class用单引号",
     "<section class='card'><p>正文</p></section>", 1, "B1"),
    # 背景图走外域同样会被微信过滤，旧版只查 <img src>
    ("bad-B5-背景图走外域",
     '<section style="background:#FFFFFF;border:1px solid #E3E8EF;'
     'background-image:url(https://example.com/bg.png);">'
     '<p>背景图</p></section>', 1, "B5"),
    ("good-B5-背景图走mmbiz",
     '<section style="background:#FFFFFF;border:1px solid #E3E8EF;'
     'background-image:url(https://mmbiz.qpic.cn/mmbiz_png/x/0);">'
     '<p>背景图</p></section>', 0, None),
    # 文末标记出现在第 600 字之后：旧实现用 600 字符固定窗口，会漏检
    ("bad-B8-长卡片第700字后的文末标记仍能抓到",
     '<section style="background:#FFFFFF;padding:18px 20px;"><p>'
     + "测" * 700 + '事实来源：彭博社</p></section>', 1, "B8"),
    # 底板包着全篇：不能把里面的文末卡文案算到容器自己的边框要求上（实测误报过）
    ("good-B8-底板包着文末卡不误报",
     '<section style="background:#F2F3F5;padding:18px 12px;">'
     '<section style="background:#F0F9F2;border:2px solid #09B83E;">'
     '<p>AI 对话已开通</p></section></section>', 0, None),

    ("boundary-空文件", "", 0, None),
    ("boundary-纯文本无标签", "就是一段普通文字，没有任何标签。", 0, None),
    ("boundary-只有背景无子元素",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;"></section>', 0, None),
    ("boundary-大写色值HEX",
     '<section style="background:#f0f9f2;border:1px solid #E3E8EF;">'
     '<p>升华块：小写色值也应识别</p></section>', 0, None),
    ("boundary-中文引号正确写法",
     '<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
     '<p>这是“主动记忆”概念</p></section>', 0, None),
]


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=CHILD_ENV)


def run_check(path, *extra):
    r = _run([sys.executable, CHECK, path, *extra])
    return r.returncode, r.stdout


def main():
    passed = failed = 0
    fails = []
    tmp = os.path.join(HERE, "_tmp_case.html")

    for name, html, want_exit, want_code in CASES:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(html)
        code, out = run_check(tmp)

        ok = (code == want_exit)
        # 反向用例必须真的命中对应坏法编号，不能只是"非零退出"
        if ok and want_code is not None:
            ok = f"[{want_code}]" in out

        if ok:
            passed += 1
            print(f"  PASS  {name}")
        else:
            failed += 1
            detail = f"期望 EXIT {want_exit}"
            if want_code:
                detail += f" 且命中 [{want_code}]"
            fails.append(f"{name}（{detail}，实得 EXIT {code}）")
            print(f"  FAIL  {name}  → EXIT {code}，{detail}")
            print(f"        输出：{out.strip()[:200]}")

    # fix_quotes 独立验证
    print("\n-- fix_quotes 替换行为 --")
    fix_cases = [
        ("fx-直角引号被替换", "甲「乙」丙", 0, "甲“乙”丙"),
        ("fx-嵌套内层用单引号", "「外「内」外」", 0, "“外‘内’外”"),
        ("fx-无需修改", "已经“正确”了", 0, "已经“正确”了"),
    ]
    for name, src, want_exit, want_out in fix_cases:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(src)
        r = _run([sys.executable, FIXQ, tmp, "--no-backup"])
        got = open(tmp, encoding="utf-8").read()
        ok = (r.returncode == want_exit and got == want_out)
        if ok:
            passed += 1
            print(f"  PASS  {name}")
        else:
            failed += 1
            fails.append(f"{name}（期望 {want_out!r}，实得 {got!r}）")
            print(f"  FAIL  {name} → {got!r}")

    # 不配对必须中止、不改文件、且非零退出（v2.4.0 起从 0 改成 1：
    # 修不了还返回成功会让调用方误以为已修好）
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("「未闭合")
    r = _run([sys.executable, FIXQ, tmp])
    unchanged = open(tmp, encoding="utf-8").read() == "「未闭合"
    if r.returncode == 1 and unchanged:
        passed += 1
        print("  PASS  fx-不配对中止且不写坏文件（EXIT 1）")
    else:
        failed += 1
        fails.append("fx-不配对中止且不写坏文件")
        print(f"  FAIL  fx-不配对中止 → EXIT {r.returncode}，文件={unchanged}")

    # 稿件是 GBK 编码时也要能读（中文 Windows 另存常见）
    gbk_ok = False
    try:
        with open(tmp, "wb") as f:
            f.write('<section style="background:#F0F9F2;border:1px solid #E3E8EF;">'
                    '<p>中文正文</p></section>'.encode("gb18030"))
        r = _run([sys.executable, CHECK, tmp])
        gbk_ok = (r.returncode == 0)
    except Exception:
        gbk_ok = False
    if gbk_ok:
        passed += 1
        print("  PASS  enc-GBK 稿件自动识别编码（不崩、不误报）")
    else:
        failed += 1
        fails.append("enc-GBK 稿件读取失败")
        print("  FAIL  enc-GBK 稿件 → 未能正常识别")

    # 读取失败要给友好提示，而不是 traceback
    r = _run([sys.executable, CHECK, os.path.join(HERE, "不存在的稿件.html")])
    if r.returncode == 2 and "Traceback" not in r.stdout + r.stderr:
        passed += 1
        print("  PASS  err-文件不存在时 EXIT 2 且无 traceback")
    else:
        failed += 1
        fails.append("文件不存在时应 EXIT 2 且不吐 traceback")
        print(f"  FAIL  err-缺失文件 → EXIT {r.returncode}")

    if os.path.exists(tmp):
        os.remove(tmp)
    if os.path.exists(tmp + ".bak"):
        os.remove(tmp + ".bak")

    # ---------- 待确认通道 + 角色标注（v2.5.0） ----------
    print("\n-- 待确认通道（证据不足：只提醒，不卡交付） --")

    weak = ('<section style="background:#FFFFFF;border:1px solid #E3E8EF;padding:18px 20px;">'
            '<p>注意：下面是普通论述，不是金句</p></section>')
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(weak)
    code, out = run_check(tmp)
    if code == 0 and "待确认" in out and "[B6]" not in out:
        passed += 1
        print("  PASS  warn-通用词「注意：」只提醒，不判错（EXIT 0）")
    else:
        failed += 1
        fails.append("warn-通用词应 EXIT 0 且只列待确认")
        print(f"  FAIL  warn-通用词 → EXIT {code}，含[B6]={'[B6]' in out}")

    # ⛔ 关键回归：通用词证据不足，--fix 绝不能把普通论述段刷成红底
    code, _ = run_check(tmp, "--fix")
    after_fix = open(tmp, encoding="utf-8").read()
    if code == 0 and "#FDF3F2" not in after_fix:
        passed += 1
        print("  PASS  warn-通用词不被 --fix 自动改色（避免误伤）")
    else:
        failed += 1
        fails.append("warn-通用词被 --fix 改了色")
        print(f"  FAIL  warn-通用词被改色 → EXIT {code}")

    # --annotate：把已判定的角色固化成注释，之后改措辞也认
    ann = ('<section style="background:#FDF3F2;border:1px solid #E3E8EF;padding:18px 20px;">'
           '<p>核心金句：已是红底</p></section>')
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(ann)
    run_check(tmp, "--annotate")
    one = open(tmp, encoding="utf-8").read()
    run_check(tmp, "--annotate")
    two = open(tmp, encoding="utf-8").read()
    if "<!-- role:quote -->" in one and one == two and one.count("role:quote") == 1:
        passed += 1
        print("  PASS  annotate-补标注且幂等（重复跑不叠加）")
    else:
        failed += 1
        fails.append("annotate 未补标注或不幂等")
        print(f"  FAIL  annotate → {one[:120]!r}")

    # ⛔ 回归：标注插进开标签内部属于畸形（曾实测写成 style="…"<!-- role --> ）
    broken_tag = 'style="background:#FDF3F2;border:1px solid #E3E8EF;padding:18px 20px;"<!--'
    if broken_tag not in one:
        passed += 1
        print("  PASS  annotate-标注插在开标签之后（不污染 style）")
    else:
        failed += 1
        fails.append("annotate 把标注插进了标签内部")
        print("  FAIL  annotate-插入位置错误")

    for _p in (tmp, tmp + ".bak"):
        if os.path.exists(_p):
            os.remove(_p)

    # --roles 能打出词表（作者改词表的入口）
    r = _run([sys.executable, CHECK, "--roles"])
    if r.returncode == 0 and "quote" in r.stdout and "核心金句" in r.stdout:
        passed += 1
        print("  PASS  --roles 打出角色词表（强/弱标记可自查）")
    else:
        failed += 1
        fails.append("--roles 输出异常")
        print(f"  FAIL  --roles → EXIT {r.returncode}")

    # ---------- --fix 自动修复闭环（v2.4.0 新增能力） ----------
    print("\n-- --fix 自动修复闭环 --")
    dirty = (
        '<style>p{color:red}</style>'
        '<section class="card" style="background:#F0F9F2;padding:18px 20px;">'
        '<p>核心金句：这句该红底</p></section>'
        '<section style="background:#F0F9F2;padding:18px 20px;">'
        '<p>AI 对话已开通</p></section>'
        '<p>所谓「主动记忆」</p>'
    )
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(dirty)

    # 1) 预演不落盘
    r = _run([sys.executable, CHECK, "--fix", "--dry-run", tmp])
    after_dry = open(tmp, encoding="utf-8").read()
    if r.returncode == 0 and after_dry == dirty:
        passed += 1
        print("  PASS  fix-dry-run 预演不写文件，且报告已修完")
    else:
        failed += 1
        fails.append(f"fix-dry-run 行为异常（EXIT {r.returncode}，文件被改={after_dry != dirty}）")
        print(f"  FAIL  fix-dry-run → EXIT {r.returncode}，被改={after_dry != dirty}")

    # 2) 真修：EXIT 0 + 五类问题都归零
    r = _run([sys.executable, CHECK, "--fix", tmp])
    fixed = open(tmp, encoding="utf-8").read()
    checks = {
        "无 style 标签": "<style" not in fixed,
        "无 class": "class=" not in fixed,
        "金句改红底": "background:#FDF3F2" in fixed,
        "文末卡 2px 边框": "border: 2px solid #09B83E" in fixed,
        "直角引号已替换": "「" not in fixed,
    }
    if r.returncode == 0 and all(checks.values()):
        passed += 1
        print("  PASS  fix-一次修好 B1/B2/B3/B6/B8 并复检归零")
    else:
        failed += 1
        fails.append("fix 自动修复未归零：" + "、".join(k for k, v in checks.items() if not v))
        print(f"  FAIL  fix → EXIT {r.returncode}，未达成："
              f"{[k for k, v in checks.items() if not v]}")

    # 3) 幂等：再跑一次不应再改
    r = _run([sys.executable, CHECK, "--fix", tmp])
    if r.returncode == 0 and open(tmp, encoding="utf-8").read() == fixed:
        passed += 1
        print("  PASS  fix-幂等（第二次跑不再改动）")
    else:
        failed += 1
        fails.append("fix 不幂等")
        print("  FAIL  fix-幂等")

    # 4) 备份存在，且内容=原稿
    bak = tmp + ".bak"
    if os.path.isfile(bak) and open(bak, encoding="utf-8").read() == dirty:
        passed += 1
        print("  PASS  fix-改前自动备份 .bak（可回滚）")
    else:
        failed += 1
        fails.append("fix 未生成可回滚的 .bak")
        print("  FAIL  fix-备份")

    # 5) --json 输出可解析
    r = _run([sys.executable, CHECK, "--json", tmp])
    try:
        data = json.loads(r.stdout)
        json_ok = isinstance(data, dict) and data.get("ok") is True
    except Exception:
        json_ok = False
    if json_ok:
        passed += 1
        print("  PASS  --json 输出合法 JSON 且可被任何编码解析")
    else:
        failed += 1
        fails.append("--json 输出不可解析")
        print(f"  FAIL  --json → {r.stdout[:120]!r}")

    # 6) --explain 能解释规则
    r = _run([sys.executable, CHECK, "--explain", "B7"])
    if r.returncode == 0 and "配额" in r.stdout:
        passed += 1
        print("  PASS  --explain B7 打出原因与修法")
    else:
        failed += 1
        fails.append("--explain 无效")
        print(f"  FAIL  --explain → EXIT {r.returncode}")

    for p in (tmp, bak):
        if os.path.exists(p):
            os.remove(p)

    # 组件库模板必须自身合规
    print("\n-- 弹性参照稿自检 --")
    for tname in ("style-floating.html",):
        tpl = os.path.join(SKILL, "templates", tname)
        code, out = run_check(tpl)
        if code == 0:
            passed += 1
            print(f"  PASS  {tname} 自身合规")
        else:
            failed += 1
            fails.append(f"{tname} 自身不合规")
            print(f"  FAIL  {tname} → {out.strip()[:300]}")

    # 必留区块校验：按 fixed-blocks.json 配置检查
    print("\n-- 必留区块校验（配置驱动） --")
    FBC = os.path.join(SKILL, "scripts", "fixed_blocks_check.py")
    cfg = os.path.join(SKILL, "scripts", "fixed-blocks.json")
    tpl2 = os.path.join(SKILL, "templates", "style-floating.html")

    # --show 能跑通= 配置可读
    r = subprocess.run([sys.executable, FBC, "--show"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0 and "必留" in r.stdout:
        passed += 1
        print("  PASS  fixed-blocks.json 配置可读（--show）")
    else:
        failed += 1
        fails.append("fixed-blocks.json 配置读取失败")
        print(f"  FAIL  --show → EXIT {r.returncode}")

    # 模板本身必留区块齐全
    if os.path.isfile(tpl2) and os.path.isfile(cfg):
        r = subprocess.run([sys.executable, FBC, tpl2],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            passed += 1
            print("  PASS  style-floating.html 必留区块齐全且顺序正确")
        else:
            failed += 1
            fails.append("参照稿必留区块不齐全")
            print(f"  FAIL  必留区块 → EXIT {r.returncode}")

        # 负例：删掉升华（配置里必留），应报缺失
        import re as _re
        html2 = io.open(tpl2, encoding="utf-8").read()
        stripped = _re.sub(
            r'<section[^>]*>\s*<p[^>]*>收尾金句.*?</section>', '', html2,
            flags=_re.S)
        if stripped != html2:
            tmp2 = os.path.join(HERE, "_tmp_fixed.html")
            with open(tmp2, "w", encoding="utf-8") as f:
                f.write(stripped)
            r2 = subprocess.run([sys.executable, FBC, tmp2],
                                capture_output=True, text=True, encoding="utf-8")
            if r2.returncode == 1 and "缺失" in r2.stdout:
                passed += 1
                print("  PASS  删掉必留的升华区块被抓出")
            else:
                failed += 1
                fails.append("缺失必留区块未被拦")
                print(f"  FAIL  缺失未拦 → EXIT {r2.returncode}")
            if os.path.exists(tmp2):
                os.remove(tmp2)

    # 真实草稿回归：用真稿校准判分器，比人造夹具可信
    #   注意 moonshot_final.html 是 2026-10-12 的稿子，早于 10-13 标点铁律定版，
    #   它的 18 对直角引号是**真实历史违规**，不是判据脱节 —— 故只校准今天的简报稿
    print("\n-- 真实草稿回归（判分器不得与实际写法脱节） --")
    real = [
        ("ai-briefing-1013.html",
         "C:/Users/admin/WorkBuddy/2026-10-13-08-41-48/work/ai-briefing-1013.html"),
    ]
    for label, path in real:
        if not os.path.isfile(path):
            print(f"  SKIP  {label}（文件不存在，跳过）")
            continue
        code, out = run_check(path)
        if code == 0:
            passed += 1
            print(f"  PASS  {label} 零违规")
        else:
            failed += 1
            fails.append(f"{label} 报违规（判据可能与实际写法脱节）")
            print(f"  FAIL  {label} → {out.strip()[:300]}")

    # 历史稿的已知违规：确认检查器确实抓得到（正向证明判据有效）
    print("\n-- 历史稿已知违规（正向证明判据抓得到） --")
    hist = "C:/Users/admin/WorkBuddy/2026-10-12-22-21-04/.wechat/moonshot_final.html"
    if os.path.isfile(hist):
        code, out = run_check(hist)
        if code == 1 and "[B3]" in out:
            passed += 1
            print("  PASS  moonshot_final.html 18 对直角引号被抓出（10-13 定版前旧稿）")
        else:
            failed += 1
            fails.append("moonshot_final.html 的历史引号违规未被抓出")
            print(f"  FAIL  未抓到历史违规 → EXIT {code}")

    # ---------- 判分器防 flaky（v2.5.0：A/B 结论的地基） ----------
    print("\n-- 判分器确定性（同一输入重复判分必须一致） --")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write('<section style="background:#F0F9F2;border:1px solid #E3E8EF;'
                'padding:18px 20px;"><p>核心金句：金句该红底</p></section>')
    runs = {run_check(tmp) for _ in range(3)}
    if len(runs) == 1:
        passed += 1
        print("  PASS  flaky-同一份稿子判 3 次结果完全一致")
    else:
        failed += 1
        fails.append("判分器不确定（同一输入结果不同），A/B 增益结论不可信")
        print(f"  FAIL  flaky-结果不一致：{len(runs)} 种")

    # ---------- 交付契约 + 粘贴前净化（v2.5.0） ----------
    print("\n-- 交付契约 handoff（本技能不实现推送，只交接口） --")
    handoff = os.path.join(SKILL, "scripts", "handoff.py")
    tpl = os.path.join(SKILL, "templates", "style-floating.html")
    work = os.path.join(HERE, "_tmp_handoff.html")
    shutil.copyfile(tpl, work)
    r = _run([sys.executable, handoff, "--emit", "--strip", "--title", "测试标题", work])
    pkg = os.path.join(HERE, "_tmp_handoff.handoff.json")
    cleaned = os.path.join(HERE, "_tmp_handoff.wechat.html")
    try:
        data = json.loads(io.open(pkg, encoding="utf-8").read())
    except Exception:
        data = {}
    if r.returncode == 0 and data.get("ready") is True and "wechat-oa-draft-publish" in str(data.get("next")):
        passed += 1
        print("  PASS  handoff-交接包 ready=true 且写明下一步交给发布技能")
    else:
        failed += 1
        fails.append("handoff 交接包异常")
        print(f"  FAIL  handoff → EXIT {r.returncode}，ready={data.get('ready')}")

    # 发布侧缺字段必须写进 missing，不能装作齐全
    if "digest" in (data.get("missing") or []) and "cover" in (data.get("missing") or []):
        passed += 1
        print("  PASS  handoff-缺标题/摘要/封面时写进 missing（不假装齐全）")
    else:
        failed += 1
        fails.append("handoff 未标记缺失字段")
        print(f"  FAIL  handoff missing → {data.get('missing')}")

    if os.path.isfile(cleaned) and "<!--" not in io.open(cleaned, encoding="utf-8").read():
        passed += 1
        print("  PASS  strip-净化版去掉全部注释（可直接粘进编辑器）")
    else:
        failed += 1
        fails.append("strip 未去掉注释")
        print("  FAIL  strip-注释残留")

    # 自检没过 → ready=false 且 EXIT 1，别让人拿着没过的稿子去发
    bad = os.path.join(HERE, "_tmp_handoff_bad.html")
    io.open(bad, "w", encoding="utf-8").write(
        '<section style="background:#FFFFFF;border:1px solid #E3E8EF;padding:18px 20px;">'
        '<p>所谓「主动记忆」</p></section>')
    r = _run([sys.executable, handoff, "--emit", bad])
    try:
        bad_data = json.loads(io.open(os.path.join(HERE, "_tmp_handoff_bad.handoff.json"),
                                      encoding="utf-8").read())
    except Exception:
        bad_data = {}
    if r.returncode == 1 and bad_data.get("ready") is False:
        passed += 1
        print("  PASS  handoff-自检未过时 ready=false 且 EXIT 1")
    else:
        failed += 1
        fails.append("handoff 未拦下未过检的稿件")
        print(f"  FAIL  handoff-未过检 → EXIT {r.returncode}，ready={bad_data.get('ready')}")

    for p in (work, pkg, cleaned, bad,
              os.path.join(HERE, "_tmp_handoff_bad.handoff.json")):
        if os.path.exists(p):
            os.remove(p)

    if os.path.exists(tmp):            # 用例临时文件不要留在包里
        os.remove(tmp)

    print("\n" + "=" * 56)
    print(f"套件：排版检查器 + 引号修复器 + 模板自检")
    print(f"断言：{passed + failed}项    通过：{passed}    失败：{failed}")
    if fails:
        print("\n失败明细：")
        for x in fails:
            print("  - " + x)
    print("=" * 56)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
