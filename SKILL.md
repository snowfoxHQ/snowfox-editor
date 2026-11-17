---
name: snowfox-editor
display_name: Snowfox编辑
display_name_en: Snowfox Editor
description: "Snowfox编辑 —— 微信公众号排版唯一一套悬浮样式的全部版式、规范与自检工具。一份弹性参照稿（区块标注必留/弹性），板块数按字数自动算（字数÷150，同 px 自适应），必留区块由配置文件逐用户定制（fixed-blocks.json），支持整套调用与分块调用两种方式；含红绿蓝三色分工、字号行距参数、微信 HTML 合规约束、边框铁律、标点铁律、发布前八类确定性自检（带行号与修法）、一键自动修复、编码自适应、角色三值判定（显式标注/强词/视觉指纹/弱词只提醒）、交付契约与粘贴前净化、封面处理。当用户说「排版」「改排版」「按公众号规范排」「用悬浮样式」「悬浮样式排版」「给我一张金句卡」「加个分层说明」「这张卡换成悬浮的」「去掉阴影」「检查排版」「自动修一下」「必留区块改成 XX」「这段算金句吗」「配色」「字号行距」「封面裁图」「准备发布/交接」时激活。只管排版，不管推草稿箱与发布。"
description_zh: "Snowfox编辑 —— 微信公众号排版唯一一套悬浮样式的全部版式、规范与自检工具。一份弹性参照稿（区块标注必留/弹性），板块数按字数自动算（字数÷150，同 px 自适应），必留区块由配置文件逐用户定制（fixed-blocks.json），支持整套调用与分块调用两种方式；含红绿蓝三色分工、字号行距参数、微信 HTML 合规约束、边框铁律、标点铁律、发布前八类确定性自检（带行号与修法）、一键自动修复、编码自适应、角色三值判定（显式标注/强词/视觉指纹/弱词只提醒）、交付契约与粘贴前净化、封面处理。当用户说「排版」「改排版」「按公众号规范排」「用悬浮样式」「悬浮样式排版」「给我一张金句卡」「加个分层说明」「这张卡换成悬浮的」「去掉阴影」「检查排版」「自动修一下」「必留区块改成 XX」「这段算金句吗」「配色」「字号行距」「封面裁图」「准备发布/交接」时激活。只管排版，不管推草稿箱与发布。"
description_en: "Snowfox Editor - the single floating-card typesetting style for WeChat Official Account, with its layout library, rules and self-check tooling. One elastic reference template (blocks marked fixed / elastic), block count auto-computed from word count (words / 150, like responsive px), required blocks customised per user via a JSON config file, and two invocation modes (whole-template / single-block). Includes the three-colour role table, font-size and line-height parameters, WeChat HTML compliance constraints, the mandatory border rule, the punctuation rule, a deterministic eight-category pre-publish self-check (with line numbers and fix instructions), one-command auto-repair, encoding-tolerant file IO, three-level role detection (explicit annotation / strong keyword / visual fingerprint, with weak keywords only warned), a handoff contract plus paste-time cleanup, and cover image handling. Covers typesetting only - not draft-box push or publishing."
version: 2.5.2
author: SnowFox
category: content
allowed-tools: Read, Write, Edit, Bash
user-invocable: true
agent_created: true
---

# Snowfox编辑

微信公众号正文排版技能。**排版在这里做，推草稿箱不在这里做**（发布走 `wechat-oa-draft-publish`）。
平台页：https://skillhub.cn/skills/indiv-snowfox/snowfox-editor · 仓库：https://github.com/snowfoxHQ/snowfox-editor · 协议：Apache-2.0

## 一、两种调用方式

| 用户意图 | 方式 | 做法 |
|---|---|---|
| 给一整篇稿子 | 整套调用 | 整篇复制 `templates/style-floating.html` → 只改中文 → 按公式调板块数 → 自检 |
| 只要某一张卡 | 分块调用 | 从参照稿挑对应区块，直接给成品 HTML，**不反问** |

## 二、板块数与红底配额（按字数算，不写死）

```
可重复卡片数 = 全文字数 ÷ 150，取整，最少 2 张
红底配额     = ≤500字→1 张 · ≤1000字→2 张 · ≤2000字→3 张 · >2000字→4 张
```

**固定骨架**：底板 · 报头 · 导语 · 升华 · 事实来源 · 开源仓库 · AI 对话。
**弹性内容**（按公式增删）：胶囊栏目标 · 白卡 · 绿卡 · 红卡 · 蓝卡 · 提醒卡。

## 三、必留区块配置（用户自己定）

写在 `scripts/fixed-blocks.json` 的 `required` 数组，顺序 = 必留顺序。当前默认：`board → masthead → lede → subtitle → ai_chat`。

```bash
python scripts/fixed_blocks_check.py --show   # 看当前配置
python scripts/fixed_blocks_check.py 稿件.html # 按配置校验
```

可选 key：`board` 底板 · `masthead` 报头 · `lede` 导语 · `subtitle` 升华 · `reminder` 提醒卡 · `deep_dive` 文末① · `interact` 文末② · `repo` 文末③ · `ai_chat` 文末④。

⛔ 改配置前先问用户必留哪些，别自己替他决定。

## 四、参数速查

| 项 | 值 |
|---|---|
| 正文 | **16px**（h2 17px 配左 4px 蓝条；大标题/升华 18px；注释来源 12px；代码 14px） |
| 行距 | **1.75**，全篇统一 |
| 段间距 | 22px margin-bottom，**无首行缩进** |
| 字间距 | 0.5px（干货）/ 1px（长文），上限 2px |
| 两端边距 | 10px |
| 正文色 | `#3F3F3F`，禁用 `rgba(0,0,0,0.9)` |
| 封面 | 900×383（2.35:1），JPEG q92 |

## 五、配色（三色分工，不越界）

**红 = 强调与提醒 · 绿 = 分层与收尾 · 蓝 = 结构与规格。**
金句是红底 `#FDF3F2`，升华是绿底 `#F0F9F2`，别搞反。绿+蓝双主色是定版方案，**不要改成单色**。

| 语义 | 底色 |
|---|---|
| 金句 / 警示 / 提醒 / 文末① | `#FDF3F2` 红 |
| 分层 / 升华 / 报头 / 文末绿卡 | `#F0F9F2` 绿 |
| 导语 / 规格 | `#F4F8FC` 浅蓝（导语正文用蓝色 `#2B77BF`） |
| 资讯 / 白卡 / 事实来源 | `#FFFFFF` |

完整色值表与逐区块配色见 `@references/typography-and-color.md`。

## 六、悬浮样式与边框

所有卡片：`border-radius:12px` + `box-shadow: 0 2px 10px rgba(31,45,61,0.08)` + 内边距 18/20px。

**铁律：有 `background` 的 section 必须有整圈 `border`。**

| 档 | 值 | 用在 |
|---|---|---|
| 2px 亮绿 | `border: 2px solid #09B83E` | 封面级：报头、文末②③④ |
| 2px 红 | `border: 2px solid #D93F2B` | 文末①最值得深挖 |
| 1px 浅灰 | `border: 1px solid #E3E8EF` | 内容级：白卡/绿卡/红卡/蓝卡/升华/事实来源 |

合法例外（无边框）：导读块（刻意，按内容语义豁免，不按底色——`#F4F8FC` 规格卡必须有边框）· 底板 `#F2F3F5` · 代码块 `#282C34` · 数据表 · 章节条 · 场景标 · 分隔点。

分块索引（各卡底色/边框/用途）与整套配色分配都在 `@references/typography-and-color.md`。

## 七、标点铁律

禁直角引号 `「」`，一律中文双引号 `""`（嵌套内层 `''`）。写稿时就用对；交付前兜底：

```bash
python scripts/fix_quotes.py --check 稿件.html   # 退出码 1 = 有残留；不带 --check 则就地替换
```

## 八、微信 HTML 硬约束

- 所有样式必须内联 `style="..."`；不要用 class；不用 `<script>`/`onclick`
- 标签配对且嵌套正确
- 正文图片仅 `mmbiz.qpic.cn`；外链仅 `mp.weixin.qq.com`

## 九、发布前自检（八类，每篇必跑）

```bash
python scripts/typeset_check.py --fix 稿件.html   # 八类检查 + 自动修（改前留 .bak；--dry-run 预演）
python scripts/fix_quotes.py --check 稿件.html    # 标点
python scripts/fixed_blocks_check.py 稿件.html    # 必留区块
```

三个都 EXIT 0 才交付。每条违规带行号 + 为什么 + 怎么改。辅助参数：`--json`（机器可读）、`--explain B7`（查单条规则）、`--all`（全库）。

| 编号 | 抓什么 | 自动修 |
|---|---|---|
| B1 | `<style>`/`class`/`script`/行内事件 | ✅ |
| B2 | 有底色的 section/div 缺整圈 border | ✅ |
| B3 | 直角引号残留/不配对 | ✅（配对时） |
| B4 | 标签不配对、错位嵌套（栈式校验） | ❌ |
| B5 | 外域图片/外链 | ❌ |
| B6 | 语义越界（金句非红底、升华非绿底、规格非蓝底） | ✅（弱词除外） |
| B7 | 红底超配额 | ❌ |
| B8 | 封面级卡缺 border 或 2px 退化成 1px | ✅ |

B6 是三值判定：显式标注 `<!-- role:quote -->` / 强角色词 / 左 4px 色条 → 判错；通用词（如「注意：」）→ 只提醒。作者换了措辞认不出时：卡片里写 `<!-- role:x -->` 注释，或跑 `--annotate` 固化；常用词加进 `scripts/roles.json`。

每类坏法的 before/after 修法见 `@references/troubleshooting.md`。
改检查器判据时守三条实现约束：先等长剥 HTML 注释、按标签栈取卡片边界、关键词精确匹配（升华用「收尾金句」不是「金句」）。

## 十、编辑习惯

- 每段 3-5 行分段；一段最多加粗 1-2 个关键词；重点靠加粗/引用，不靠颜色堆砌
- 默认改写而非修补：可重写全文、重做结构、补缺失示例、删注水；**用户的一手经验、真实判断、具体数字必须保留**（换个人写不出来的句子就是用户的）
- 讲方法必须给可复制示例（提示词/配置/操作/数据），不能只描述
- 标题 ≤64 字节（约 21 汉字），留足余量；摘要约 120 字节，**不能截正文首句**，要有钩子
- 署名固定 `by SnowFox`（小写 by + 空格）
- 详细判例与病灶修法见 `@references/writing-and-editing.md`

## 十一、封面图处理

比例 2.35:1（900×383），JPEG q92。AI 生成图带水印，用 Pillow 裁掉底部约 8%，小幅度试裁：

```python
from PIL import Image
im = Image.open(src).convert('RGB')
W, H = im.size
im2 = im.crop((0, int(H*0.03), W, int(H*0.92)))
im2 = im2.resize((900, 383), Image.LANCZOS)
im2.save('cover_900x383.jpg', 'JPEG', quality=92, optimize=True)
```

## 十二、标准流程

1. 判断调用方式（整篇 → 整套；单卡 → 分块直接给代码）
2. 按字数定板块数（`字数÷150`），填内容只改中文
3. 三个自检都 EXIT 0（`--fix` 先自愈，B4/B5/B7 手改）
4. 封面裁到 900×383 去水印
5. 提醒用户真机预览（脚本不校验真机观感）
6. `python scripts/handoff.py --emit --strip 稿件.html` 生成交接包 + 净化版；推草稿箱转 `wechat-oa-draft-publish`

## 十三、排错速查

| 症状 | 处理 |
|---|---|
| 报 `[B1]`~`[B8]` | 照输出改；细则查 `@references/troubleshooting.md` |
| `EXIT 2` | 读文件/用法问题（路径、>32MB、参数错），不是排版问题 |
| 输出乱码 / GBK / BOM | 已内置编码自适应，不用手转 |
| `--fix` 改坏了 | 用同目录 `.bak` 回滚（只保留最近一次） |
| 报「待确认」但 EXIT 0 | 弱证据，扫一眼即可；要它判错就加 `<!-- role:x -->` |
| 必留区块报缺失 | 补区块或改 `fixed-blocks.json`（改前问用户） |
| 脚本合规但真机难看 | 超出能力边界，真机必须自己预览 |

⛔ 不要为了让脚本通过去改判据、删夹具或放宽配额。

## 十四、边界与红线

- 用户明确「只改排版」→ 不动内容
- 需要 Markdown 输入 → 按第三节选组件，把内容填进对应 section
- 没有 Pillow → 明确告知需手动裁图，不要假装已处理
- ⛔ 不擅自改用户的配色与字号（要改先问）；不把红色用成常态；不承诺"排完一定过审"

## 十五、文件索引

| 文件 | 用途 |
|---|---|
| `templates/style-floating.html` | 唯一弹性参照稿，区块标了【固定】/【弹性】 |
| `scripts/typeset_check.py` | 排版检查器（B1-B8 + `--fix`），每篇必跑 |
| `scripts/fix_quotes.py` | 标点检查/修复 |
| `scripts/fixed_blocks_check.py` + `fixed-blocks.json` | 必留区块校验 + 配置 |
| `scripts/roles.json` | B6 角色词表（可增补） |
| `scripts/handoff.py` | 交付契约：交接包 + `--strip` 净化版 |
| `scripts/skillio.py` | 共用 IO（编码识别/原子写/控制台降级），不要绕过它直接 open |
| `references/troubleshooting.md` | 排障手册：八类坏法 before/after + 环境 FAQ |
| `references/typography-and-color.md` | 字号/配色/边框判据与逐区块配色表 |
| `references/writing-and-editing.md` | 改写判例、病灶修法、简报要点 |
| `test/run_all.py` | 验证集入口（100 项断言） |

改样式模板后必须跑：`python scripts/typeset_check.py --all && python test/run_all.py`。
