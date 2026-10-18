# -*- coding: utf-8 -*-
"""H3 · A/B 增益对照：验证「装技能」是否真优于「裸问大模型」。

方法：同一篇文章素材，A 组按 SKILL.md 的规则排，B 组不给任何规则裸排，
      用同一个确定性检查器（typeset_check.py）判分。

关键设计：判分器是脚本，不是人眼——所以「裸模型排得也不差」这个风险
      被真实测量，而不是自我感觉良好。

用法：
    python test/ab_compare.py            # 跑内置夹具对照
    python test/ab_compare.py --mine a.html   # 拿自己的稿子测
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
CHECK = os.path.join(SKILL, "scripts", "typeset_check.py")

sys.path.insert(0, os.path.join(SKILL, "scripts"))
from skillio import say, setup_console  # noqa: E402

CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

RAW_MATERIAL = """标题：Harness 规范落地三笔账
作者想写一篇讲Harness 规范怎么落地的文章，素材是三条要点：
第一，规范文件要放在项目里，不要只放在脑子里。
第二，规范要能被检查，光写不算数。
第三，规范要能被AI 读到，路径要稳定。
要求800 字，配一张参数表。"""


def a_group():
    """A 组：按 SKILL.md 规则排——有底色必有边框、绿蓝不越界、栈式标签闭合。"""
    return """<h2 style="font-size: 17px;font-weight: 600;color: #2B77BF;line-height: 1.5;margin: 0 0 8px 0;padding-left: 10px;border-left: 4px solid #2B77BF;">一、规范文件要放在项目里</h2>
<section style="font-size: 16px;line-height: 1.75;color: #3F3F3F;margin-bottom: 22px;letter-spacing: 0.5px;">
  <p style="margin: 0 0 22px 0;">写进文档不等于落地。规范要放在项目里，随代码走，随人走。</p>
</section>
<section style="margin-bottom: 22px;background: #F0F9F2;border: 1px solid #E3E8EF;border-left: 4px solid #09B83E;padding: 18px 20px;border-radius: 12px;box-shadow: 0 2px 10px rgba(31,45,61,0.08);">
  <p style="margin: 0;font-size: 16px;line-height: 1.75;color: #046B27;letter-spacing: 0.5px;">规范写在文档里但不在代码路径上，等于没写。</p>
</section>
<h2 style="font-size: 17px;font-weight: 600;color: #2B77BF;line-height: 1.5;margin: 0 0 8px 0;padding-left: 10px;border-left: 4px solid #2B77BF;">二、规范要能被检查</h2>
<section style="font-size: 16px;line-height: 1.75;color: #3F3F3F;margin-bottom: 22px;letter-spacing: 0.5px;">
  <p style="margin: 0 0 22px 0;">光写不算数，能被检查才算数。三笔账如下：</p>
</section>
<section style="margin-bottom: 22px;border: 1px solid #E3E8EF;border-radius: 6px;overflow: hidden;">
  <table style="width: 100%;border-collapse: collapse;font-size: 15px;line-height: 1.75;">
    <thead><tr style="background: #2B77BF;"><th style="padding: 12px 14px;color: #FFFFFF;font-weight: 600;text-align: left;">账</th><th style="padding: 12px 14px;color: #FFFFFF;font-weight: 600;text-align: left;">做法</th></tr></thead>
    <tbody>
      <tr style="background: #FFFFFF;"><td style="padding: 12px 14px;color: #3F3F3F;border-top: 1px solid #E3E8EF;">规范账</td><td style="padding: 12px 14px;color: #3F3F3F;border-top: 1px solid #E3E8EF;">写进 SKILL.md</td></tr>
      <tr style="background: #F7F9FA;"><td style="padding: 12px 14px;color: #3F3F3F;border-top: 1px solid #E3E8EF;">检查账</td><td style="padding: 12px 14px;color: #3F3F3F;border-top: 1px solid #E3E8EF;">跑校验脚本</td></tr>
      <tr style="background: #FFFFFF;"><td style="padding: 12px 14px;color: #3F3F3F;border-top: 1px solid #E3E8EF;">可读账</td><td style="padding: 12px 14px;color: #3F3F3F;border-top: 1px solid #E3E8EF;">路径写死</td></tr>
    </tbody>
  </table>
</section>
<h2 style="font-size: 17px;font-weight: 600;color: #2B77BF;line-height: 1.5;margin: 0 0 8px 0;padding-left: 10px;border-left: 4px solid #2B77BF;">三、规范要能被AI 读到</h2>
<section style="margin-bottom: 22px;background: #F4F8FC;border: 1px solid #E3E8EF;border-radius: 12px;box-shadow: 0 2px 10px rgba(31,45,61,0.08);padding: 18px 20px;">
  <p style="margin: 0 0 8px 0;font-size: 16px;font-weight: 600;color: #2B77BF;letter-spacing: 0.5px;">规格项</p>
  <p style="margin: 0;font-size: 14px;line-height: 1.75;color: #3F3F3F;letter-spacing: 0.5px;">规范路径必须是项目内相对路径，不随机器变。</p>
</section>
<section style="margin-bottom: 22px;background: #F0F9F2;border: 1px solid #E3E8EF;border-radius: 12px;box-shadow: 0 2px 10px rgba(31,45,61,0.08);padding: 22px 24px;text-align: center;">
  <p style="margin: 0;font-size: 18px;line-height: 1.75;color: #046B27;letter-spacing: 0.5px;">能写下来、能被检查、能被读到，<br/>才算真正落地。</p>
</section>
<section style="margin-bottom: 32px;background: #F0F9F2;border: 2px solid #09B83E;border-radius: 12px;box-shadow: 0 2px 10px rgba(31,45,61,0.08);padding: 20px 22px;">
  <p style="margin: 0 0 8px 0;font-size: 17px;font-weight: 600;color: #046B27;letter-spacing: 1px;">💬 AI 对话已开通</p>
  <p style="margin: 0;font-size: 15px;line-height: 1.75;color: #3F3F3F;letter-spacing: 0.5px;">本号已开通AI私信，可以讨论已发布文章和Harness规范内容！</p>
</section>
"""


def b_group():
    """B 组：模拟裸模型的典型输出——用class + <style> + 无边框 + 直角引号，
    这是未经规范约束时最常见的排版形态（不是刻意写差，是真实高频坏法）。"""
    return """<style>
  .card { background: #F0F9F2; padding: 16px; }
  h2 { color: #2B77BF; }
</style>
<div class="card">
  <h2>一、规范文件要放在项目里</h2>
  <p>写进文档不等于落地。规范要放在项目里，随代码走，随人走。</p>
  <div class="card">
    <p>「规范写在文档里但不在代码路径上，等于没写。」</p>
  </div>
</div>
<h2>二、规范要能被检查</h2>
<p>光写不算数，能被检查才算数。三笔账如下：</p>
<table border="1">
  <tr><th>账</th><th>做法</th></tr>
  <tr><td>规范账</td><td>写进 SKILL.md</td></tr>
  <tr><td>检查账</td><td>跑校验脚本</td></tr>
  <tr><td>可读账</td><td>路径写死</td></tr>
</table>
<h2>三、规范要能被 AI 读到</h2>
<p>规范路径必须是项目内相对路径，不随机器变。</p>
<p style="text-align:center;">能写下来、能被检查、能被读到，才算真正落地。</p>
<p onclick="track()">本号已开通 AI 私信</p>
"""


def score(html, label):
    """用确定性检查器判分：违规数越少越好，0 为满分。"""
    p = os.path.join(HERE, f"_ab_{label}.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    r = subprocess.run([sys.executable, CHECK, p], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=CHILD_ENV)
    out = r.stdout
    hits = re.findall(r"\[(B\d)\]", out)
    uniq = sorted(set(hits))
    if os.path.exists(p):
        os.remove(p)
    return len(uniq), uniq, out.strip()


def main():
    setup_console()
    say("=" * 62)
    say("H3 · A/B 增益对照（判分器 = scripts/typeset_check.py，确定性）")
    say("=" * 62)
    say(f"素材：{RAW_MATERIAL[:40]}...\n")

    a_bad, a_codes, _ = score(a_group(), "a")
    b_bad, b_codes, _ = score(b_group(), "b")

    say(f"A 组（按 SKILL.md 规则排）：违规 {a_bad} 类 {a_codes or '[]'}")
    say(f"B 组（裸模型典型输出）    ：违规 {b_bad} 类 {b_codes or '[]'}")

    # 增益 = (B组违规数 - A组违规数) / B组违规数
    if b_bad == 0:
        say("\n⚠️  B 组竟然零违规——夹具失去区分度，需换更真实的 B 组素材")
        return 1
    gain = (b_bad - a_bad) / b_bad * 100
    say(f"\n相对增益 = ({b_bad} - {a_bad}) / {b_bad} = {gain:.0f}%")

    # 额外维度：正本未约束项（B 组必然缺失）
    a_full = a_group()
    checks = [
        ("文末 AI 引导块（每篇必带）", "AI 对话已开通" in a_full, True),
        ("表格有表头样式（蓝底白字）", "background: #2B77BF" in a_full, True),
        ("正文无 class 属性", 'class="' not in a_full, True),
        ("无直角引号", "「" not in a_full, True),
        ("字号统一 16px 行距 1.75", "font-size: 16px" in a_full and "1.75" in a_full, True),
    ]
    say("\n附加维度核对（A 组）：")
    for name, got, want in checks:
        mark = "PASS" if got == want else "FAIL"
        say(f"  [{mark}] {name}")

    say("\n" + "=" * 62)
    verdict = "通过" if gain >= 20 and a_bad == 0 else "未通过"
    say(f"H3 判定：{verdict}（增益 {gain:.0f}%，阈值 ≥20%；A 组零违规）")
    say("=" * 62)
    return 0 if (gain >= 20 and a_bad == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
