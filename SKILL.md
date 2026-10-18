---
name: snowfox-editor
display_name: Snowfox编辑
display_name_en: Snowfox Editor
description: "Snowfox编辑 —— 微信公众号排版唯一一套悬浮样式的全部版式、规范与自检工具。一份弹性参照稿（区块标注必留/弹性），板块数按字数自动算（字数÷150，同 px 自适应），必留区块由配置文件逐用户定制（fixed-blocks.json），支持整套调用与分块调用两种方式；含红绿蓝三色分工、字号行距参数、微信 HTML 合规约束、边框铁律、标点铁律、发布前八类确定性自检（带行号与修法）、一键自动修复、编码自适应、角色三值判定（显式标注/强词/视觉指纹/弱词只提醒）、交付契约与粘贴前净化、封面处理。当用户说「排版」「改排版」「按公众号规范排」「用悬浮样式」「悬浮样式排版」「给我一张金句卡」「加个分层说明」「这张卡换成悬浮的」「去掉阴影」「检查排版」「自动修一下」「必留区块改成 XX」「这段算金句吗」「配色」「字号行距」「封面裁图」「准备发布/交接」时激活。只管排版，不管推草稿箱与发布。"
description_zh: "Snowfox编辑 —— 微信公众号排版唯一一套悬浮样式的全部版式、规范与自检工具。一份弹性参照稿（区块标注必留/弹性），板块数按字数自动算（字数÷150，同 px 自适应），必留区块由配置文件逐用户定制（fixed-blocks.json），支持整套调用与分块调用两种方式；含红绿蓝三色分工、字号行距参数、微信 HTML 合规约束、边框铁律、标点铁律、发布前八类确定性自检（带行号与修法）、一键自动修复、编码自适应、角色三值判定（显式标注/强词/视觉指纹/弱词只提醒）、交付契约与粘贴前净化、封面处理。当用户说「排版」「改排版」「按公众号规范排」「用悬浮样式」「悬浮样式排版」「给我一张金句卡」「加个分层说明」「这张卡换成悬浮的」「去掉阴影」「检查排版」「自动修一下」「必留区块改成 XX」「这段算金句吗」「配色」「字号行距」「封面裁图」「准备发布/交接」时激活。只管排版，不管推草稿箱与发布。"
description_en: "Snowfox Editor - the single floating-card typesetting style for WeChat Official Account, with its layout library, rules and self-check tooling. One elastic reference template (blocks marked fixed / elastic), block count auto-computed from word count (words / 150, like responsive px), required blocks customised per user via a JSON config file, and two invocation modes (whole-template / single-block). Includes the three-colour role table, font-size and line-height parameters, WeChat HTML compliance constraints, the mandatory border rule, the punctuation rule, a deterministic eight-category pre-publish self-check (with line numbers and fix instructions), one-command auto-repair, encoding-tolerant file IO, three-level role detection (explicit annotation / strong keyword / visual fingerprint, with weak keywords only warned), a handoff contract plus paste-time cleanup, and cover image handling. Covers typesetting only - not draft-box push or publishing."
version: 2.5.0
author: SnowFox
category: content
allowed-tools: Read, Write, Edit, Bash
user-invocable: true
agent_created: true
---

# Snowfox编辑

公众号正文的排版执行标准。**排版在这里做，推草稿箱不在这里做**（发布类需求走 `wechat-oa-draft-publish`）。

规范正本在资料库 → 个人空间 → `公众号运营规范/`：
《公众号开发环境与排版规范》《公众号排版参数（落地方案）》《公众号排版组件库》。
本技能是那三份正本的**可执行化**：把散文式规范变成可复制组件 + 可运行断言。

细则展开见 `@references/typography-and-color.md`（字号/配色/边框判据）与 `@references/writing-and-editing.md`（改写判例与病灶修法）。

---

## 零、30 秒上手（细则都在第三节，这里只给判断依据）

**⛔ 本号只有一套样式——悬浮。** 所有区块都是悬浮卡片，形态恒定。

| 用户意图 | 调用方式 |
|---|---|
| 给一整篇稿子 | **整套调用**：整篇复制 `templates/style-floating.html`，只改中文 |
| 只要某一张卡 | **分块调用**：直接给成品 HTML，不必整篇 |

- **板块数不预设**：`可重复卡片数 = 全文字数 ÷ 150`（取整，最少 2 张）；红底配额随字数收紧。
- **必留区块不写死**：改 `scripts/fixed-blocks.json` 的 `required`；`--show` 看当前配置。
  **⛔ 改配置前先问用户必留哪些**，别自己替他决定。
- **⛔ 分块调用不要反问**：用户说「给我一张金句卡」，直接给代码。

交付前三个自检都要 EXIT 0。`--fix` 能自动修 5 类，剩余 3 类按报错手改：

```bash
python scripts/typeset_check.py --fix draft.html   # 排版八类（先加 --dry-run 可预演不落盘）
python scripts/fix_quotes.py --check draft.html    # 标点
python scripts/fixed_blocks_check.py draft.html    # 必留区块（按配置）
```

- **作者换了措辞导致 B6 认不出角色**：卡片里写 `<!-- role:quote -->` 显式声明（微信不渲染注释），
  或跑 `--annotate` 把已判定的角色一次性固化；词表本身在 `scripts/roles.json`，可自行增补。
- **准备发布**：`python scripts/handoff.py --emit --strip draft.html` 生成交接包 + 可直接粘贴的净化版；
  推草稿箱交给 `wechat-oa-draft-publish`，本技能不做。

**报错看不懂时查 `@references/troubleshooting.md`**：每条坏法都给了原因 + before/after 代码 + 验证命令。

---

## 一、参数速查（长期固定，不逐篇调整）

| 项 | 值 | 说明 |
|---|---|---|
| 正文 | **16px** | 资讯科普定位；15px 偏文艺、14px 偏精致 |
| h2 小标题 | 17px | 配左 4px 蓝色色条 |
| 大标题 / 结尾升华 | 18px | 悬浮（收尾语义）里居中 |
| 注释、来源 | 12px | 辅助信息 |
| 代码块 | 14px | 等宽字体，行高 1.9 |
| **行距** | **1.75** | 全篇统一，不逐段调 |
| 段间距 | 22px | margin-bottom，**无首行缩进** |
| 字间距 | 0.5px / 1px | 干货短稿 0.5px，长技术文 1px（**上限 2px**） |
| 两端边距 | 10px | 由 section padding 控制 |
| 正文色 | `#3F3F3F` | **禁用 `rgba(0,0,0,0.9)`** |
| 封面 | 900×383 | 2.35:1，JPEG q92 |

---

## 二、配色表（三色分工）

| 角色 | 色值 | 用途 |
|---|---|---|
| 正文 | `#3F3F3F` | 所有段落 |
| 结构蓝 | `#2B77BF` | 章节条、导语蓝正文、表头、结构标识 |
| 绿系字 | `#046B27` | 分层绿、居中绿、封面绿、栏目标 |
| 绿系边 | `#09B83E` | 绿块左4px 边条、2px 绿边框、栏目标序号 |
| 红系字 | `#A8281A` | 金句红、警示红、封面红 |
| 红系边 | `#D93F2B` | 红块左 4px 边条、2px 红边框 |
| 场景橙 | `#8A5A0B` 字 / `#E8A33D` 边 / `#FFF8EC` 底 | 场景标，**3 处以内** |
| 代码底 | `#282C34` + 文字 `#E4E6EB` | 代码块（**不占主色额度**） |
| 绿系浅底 | `#F0F9F2` | 分层绿 / 居中绿 / 封面绿 / 互动绿 / 引流绿 / 对话绿 |
| 蓝系浅底 | `#F4F8FC` | 导语蓝 / 规格蓝 |
| 红系浅底 | `#FDF3F2` | 金句红 / 警示红 / 封面红 |
| 中性浅底 | `#F7F9FA` | 数据表隔行 |
| 边框灰 | `#E3E8EF` | 1px 边框（内容级） |

### 三色分工不越界（检查器 B6 会抓）

> **红 = 强调与提醒 · 绿 = 分层与收尾 · 蓝 = 结构与规格**

**⛔ 金句是红色（`#FDF3F2`），升华是绿底（`#F0F9F2`）—— 2026-10-13 定版，别搞反。**

悬浮的配色必须按语义取（完整参数表见第三节）：

| 语义 | 正确底色 | 常见错法 |
|---|---|---|
| **金句 / 强调** | `#FDF3F2` 红 | ⛔ 误用绿底或蓝底 |
| 警示 / 封面警示卡 | `#FDF3F2` 红 | — |
| **升华 / 收尾** | `#F0F9F2` 绿 | ⛔ 误用红底或蓝底 |
| 分层 / 归类 | `#F0F9F2` 绿 | ⛔ 误用蓝底 |
| 报头 / 文末引导 | `#F0F9F2` 绿 | — |
| 导语 / 规格 | `#F4F8FC` 浅蓝 | ⛔ 误用绿底 |
| 导语（正文） | **蓝色 `#2B77BF`** | ⛔ 正文写成深灰 |
| 资讯 | `#FFFFFF` | — |

历史上出过一次错：金句被做成绿底。肉眼很难发现，靠 `typeset_check.py` 兜住。

> **重要**：用户实测确认**绿+蓝双主色比单色方案好看**。曾按「三色定律 + 禁绿」改过一版，反馈不如原版，已回退。**不要再改成单色方案。**

---

## 三、唯一一套样式：悬浮

**⛔ 本号只有一套样式——悬浮。** 所有区块都是悬浮卡片：
`border-radius:12px` + `box-shadow: 0 2px 10px rgba(31,45,61,0.08)` + `border: 1px solid #E3E8EF`（封面级用 2px 绿/红）

⛔ **简报 / 长文 / 观点文不是不同样式，只是卡片密度与字数不同。** 不要按稿型造新样式。

### 底色语义（唯一需要判断的事）

| 底色 | 语义 | 用在 |
|---|---|---|
| **`#FDF3F2` 红** | 强调 / 提醒 | 金句、提醒、文末① |
| **`#F0F9F2` 绿** | 分层 / 收尾 | 分层、升华、报头、文末绿卡 |
| **`#F4F8FC` 蓝** | 结构 / 规格 | 导语（**正文蓝色**）、规格卡 |
| `#FFFFFF` 白 | 内容 | 资讯卡、胶囊栏目标 |

无阴影的例外：底板 `#F2F3F5` · 代码块 `#282C34` · 数据表（6px 圆角）· 章节条 · 场景标 · 分隔点

---

### 两种调用规则（⛔ 按用户意图自动选，别问「你要哪套」）

| 用户意图 | 调用方式 | 怎么做 |
|---|---|---|
| **给一整篇稿子** | **整套调用** | 整篇复制某份参照稿 → 只改中文 → 自检 |
| **只要某一张卡** | **分块调用** | 从 `style-floating.html` 挑对应区块 → 直接给成品 HTML → 不用整篇 |

⛔ **分块调用不必反问**。用户说「给我一张金句卡」「这张卡换成悬浮的」，直接给成品代码。

### ⛔ 板块数按字数自动伸缩（同 px 自适应，不是固定值）

⛔⛔ **不要按「一篇几个板块」来排版。板块数是算出来的，跟文章长度一起变。**

**板块数公式**（每张卡承载 150 字）：

```
可重复卡片数 = 全文字数 ÷ 150，取整，最少 2 张
→ 600 字 → 4 张 · 1000 字 → 7 张 · 2000 字 → 13 张 · 3000 字 → 20 张
```

**红底配额公式**（随字数收紧，⛔ 不是固定值）：

```
≤500 字 → 红底 ≤1 张 · ≤1000 字 → ≤2 张 · ≤2000 字 → ≤3 张 · >2000 字 → ≤4 张
```

`typeset_check.py` 的 **B7** 会实测这两条并报告实际字数与配额，退出码非 0 就是超了。

### ⛔ 必留区块可配置（每个用户不一样）

⛔ **「每篇必留哪些」写在 `scripts/fixed-blocks.json` 里，由用户自己定，不写死在技能里。**
不同公众号的使用环境不同，必留区块也不一样——改配置即可，不用动 SKILL.md 和模板。

```bash
python scripts/fixed_blocks_check.py --show    # 看当前必留哪些
# 改 scripts/fixed-blocks.json 的 required 数组，增删就是调整必留区块
python scripts/fixed_blocks_check.py <draft.html>   # 按配置校验稿件
```

**配置里能调的**：

| 字段 |作用 |
|---|---|
| `required` | 必留区块 key 的数组，**顺序 = 必留顺序** |
| `order_locked` | `true` 校验先后顺序 · `false` 只校验存在不校验顺序 |
| `blocks` | 每个区块的名称、说明、备注（`--show` 会显示） |

**可选区块 key**：`board` 底板 · `masthead` 报头 · `lede` 导语 · `subtitle` 升华 ·
`reminder` 提醒卡 · `deep_dive` 文末①最值得深挖 · `interact` 文末②互动问句 ·
`repo` 文末③开源仓库 · `ai_chat` 文末④AI 对话

**默认配置**（本号当前）：`board → masthead → lede → subtitle → ai_chat`

⛔ **改配置前先问用户必留哪些**，别自己替他决定。配置文件里有常见配置示例（资讯号/简报号/长文号/最小集）。

**弹性内容（按字数公式增删，与必留无关）**：胶囊栏目标 · 白卡 · 绿卡 · 红卡 · 蓝卡 · 提醒卡

### 唯一参照稿：`templates/style-floating.html`

**一份弹性参照稿，所有区块都标了 `【固定】` 或 `【弹性】`**，照着增删即可。
⛔ 不按简报/长文分多份模板——**它们只是密度不同，结构一样**，
密度靠「字数 ÷ 150」公式控制，必留区块靠 `fixed-blocks.json` 配置控制。

### 分块调用索引

要单独某一张卡时，按名字取（全部在 `style-floating.html` 里）：

| 名字 | 底色 | 边框 | 用在 |
|---|---|---|---|
| **报头** | `#F0F9F2` 绿 | **2px 绿** | 全篇第一块，居中含 `by SnowFox` |
| **导语** | `#F4F8FC` 蓝 | 1px | 开篇导语，⛔ 正文用蓝色 `#2B77BF` |
| **胶囊栏目标** | `#FFFFFF` 白 | 1px | 20px 圆角，序号 `#09B83E` |
| **白卡** | `#FFFFFF` 白 | 1px | 论述、资讯 |
| **绿卡** | `#F0F9F2` 绿 | 1px + 左 4px 绿 | 分层、归类 |
| **红卡** | **`#FDF3F2` 红** | 1px + 左 4px 红 | **金句**，全文 1-2 处 |
| **蓝卡** | `#F4F8FC` 蓝 | 1px | 规格、参数 |
| **提醒卡** | `#FDF3F2` 红 | 1px | 重点提醒，密度稿里 1 处 |
| **升华** | `#F0F9F2` 绿 | 1px | 收尾，18px 居中 |
| **文末①** | `#FDF3F2` 红 | **2px 红** | 最值得深挖 |
| **开源仓库** | `#F0F9F2` 绿 | **2px 绿** | 引流，内链限 `mp.weixin.qq.com` |
| **AI 对话** | `#F0F9F2` 绿 | **2px 绿** | ⛔ 全篇最后一块，每篇必带 |

### 常见说法 → 动作

| 用户说 | 动作 |
|---|---|
| 「排版」「按公众号规范排」 | 整套调用 `style-floating.html`，改内容，按公式调板块数，自检 |
| 「用悬浮样式」「悬浮样式排版」 | 同上 |
| 「早报 / 周报 / 简报」 | 整套调用 `style-floating.html`，按 `字数÷150` 压低卡片密度 |
| 「长文 / 深度 / 评测」 | 整套调用 `style-floating.html`，按 `字数÷150` 放开卡片密度 |
| 「给我一张金句卡」 | **分块调用**，直接给红卡成品代码 |
| 「这张卡换成悬浮的」 | 分块调用，补 `border-radius:12px` + `box-shadow` |
| 「加个分层说明」 | 分块调用，给绿卡 |
| 「这段不要阴影」 | 去 `box-shadow` |
| 「检查排版」 | 只跑脚本，不改稿 |
| 「自动修一下」「按报错改好」 | `typeset_check.py --fix`，再复检一遍把结果报给用户 |
| 「必留区块改成 XX」 | 改 `fixed-blocks.json` 的 required，再 `--show` 确认 |
| 「这篇可以不升华」 | 从 required 里删掉 subtitle，或临时改配置 |
| 「太长了/太短了」 | 按 `字数÷150` 增删弹性卡，固定骨架不动 |

### 怎么用

```bash
# 1. 整篇复制起点模板
cp templates/style-floating.html  my-draft.html

# 2. 只改中文，不动 style 结构

# 3. 交付前自检——报告会告诉你字数、卡片数、红底配额、建议卡片数
python scripts/typeset_check.py my-draft.html

# 4. 有报错就先让它自愈（改前自动留 .bak），再复检
python scripts/typeset_check.py --fix my-draft.html
python scripts/fix_quotes.py --check my-draft.html

# 5. 按配置校验必留区块（缺一个就 EXIT 1）
python scripts/fixed_blocks_check.py my-draft.html

# 6. 按报告里的「建议卡片数」增删弹性卡，直到三个自检都 EXIT 0
```

⛔ **板块数不预设**：写完看自检报告里的「字数」与「建议卡片数」，
多了就删弹性卡，少了就复制白卡，**直到两者接近**再交付。

### 三条恒定规则（无论怎么调用）

| 规则 | 内容 |
|---|---|
| 边框分档 | **2px = 封面级**（报头/文末①②③④） · **1px = 内容级**（白卡/绿卡/红卡/蓝卡/升华/事实来源） |
| ⛔ 无边框例外 | **导读块刻意无边框**（底色已足够分隔） · 底板 `#F2F3F5` · 代码块 `#282C34` |
| 必留区块 | ⛔ **由 `fixed-blocks.json` 配置决定**，不写死在技能里 |
| 红色配额 | ⛔ **随字数算**：≤500字→1 · ≤1000字→2 · ≤2000字→3 · >2000字→4（B7 强制） |
| 标点 | ⛔ 禁直角引号，一律中文双引号 |

---

## 四、边框铁律（结构性，与文章内容无关）

> **正文里每一个有底色的 `section`，都必须有 `border`。**

**唯一判据：这个 section 有 `background` 吗？有 → 就必须有 `border`。**

必须按**结构**判角色，**绝不能靠"看着这篇文章有哪些卡片再逐个加"**——每篇正文内容都不一样，按内容数卡片必然漏（本号已连续漏过 4 处：报头、导语、警示红卡、栏目标）。

### 三档边框

| 档 | 用在哪 | 值 |
|---|---|---|
| **2px 亮绿** | 封面级区块 —— 报头、文末引导/引流/互动卡 | `border: 2px solid #09B83E` |
| **2px 红** | 提醒型卡 —— 「本周最值得深挖」 | `border: 2px solid #D93F2B` |
| **1px 浅灰** | 正文内容区块 —— 中间所有内容 | `border: 1px solid #E3E8EF` |

### 卡片统一造型（悬浮式）

```
border-radius: 12px;
box-shadow: 0 2px 10px rgba(31,45,61,0.08);
```

### 合法例外：不加边框

| 元素 | 原因 |
|---|---|
| `#F2F3F5` 灰底托盘 | 承载整篇的背景容器，不是卡片 |
| `#282C34` 代码块黑底 | 功能性色，不参与卡片体系 |

---

## 五、标点铁律（强制）

**本号所有文章一律禁用直角引号 `「` `」`，统一用中文双引号 `""`。**

- 写稿时就用双引号，别写完再改
- 嵌套引用：外层 `""`，内层 `''`
- 交付前兜底跑 `python scripts/fix_quotes.py --check <draft.html>`（退出码 1 = 有残留）
- 不带 `--check` 则就地替换；**引号不配对时中止报错**，不会写出半吊子正文

---

## 六、微信 HTML 硬约束

- **所有样式必须内联**（`style="..."`）—— 微信会过滤 `<style>` 标签
- **不要用 class 属性** —— 微信不保留
- 不使用 `<script>`、`onclick`
- 标签必须正确配对**且嵌套顺序正确**
- 正文图片只能用 `mmbiz.qpic.cn` 域名（外部图片必须先上传素材库）
- 外链只允许 `mp.weixin.qq.com`（微信会把短链改写成长链，属正常）

---

## 七、发布前自检（八类，**每篇必跑**）

```bash
python scripts/typeset_check.py <draft.html>          # 单篇；0=合规 1=有违规 2=读文件失败
python scripts/typeset_check.py --fix <draft.html>    # 自动修 5 类，改前留 .bak
python scripts/typeset_check.py --fix --dry-run <稿>  # 预演，只报会改什么
python scripts/typeset_check.py --json <draft.html>   # 机器可读（纯 ASCII，管道安全）
python scripts/typeset_check.py --explain B7          # 单条规则的原因与修法
python scripts/typeset_check.py --all                 # 全库 templates/
python scripts/fix_quotes.py --check <draft.html>     # 引号，退出码 0 = 合规
python scripts/fixed_blocks_check.py <draft.html>     # 必留区块（按配置）
```

输出格式：每条违规带 **行号 + 为什么 + 怎么改 + 能否自动修**，不用再猜。
`--fix` 自动修 **B1/B2/B3/B6/B8**；**B4/B5/B7 必须手工**（原因见 `@references/troubleshooting.md`）。

**B6 是三值判定**（微信禁 class，只能靠内容与视觉推断角色）：

| 证据 | 例子 | 判定 |
|---|---|---|
| 显式标注 | `<!-- role:quote -->` | **判错**（优先级最高，改了措辞也认） |
| 强角色词 | 核心金句 / 升华块 / 规格项 | **判错** |
| 视觉指纹 | 左侧 4px 红（绿）色条 | **判错**（与用词无关） |
| 通用汉语 | 「注意：」 | **只提醒**：列出待确认，不计退出码、不自动改色 |

⛔ 二值判定必然在「误报」和「漏报」之间二选一——通用词出现在论述段就要求改红底是典型误报，
所以弱证据单独出现时走「待确认」通道，既不误伤也不把不确定性藏起来。

检查器覆盖八类坏法，**每类坏法一条规则**，不是逐个字段一条：

| 编号 | 坏法 | 抓什么 | 可自动修 |
|---|---|---|---|
| **B1** | 微信剥离 | `style` 标签 / `class`（单双引号都认）/ `script` / 行内事件 | ✅ |
| **B2** | 边框缺失 | 有底色的 section/div 缺**整圈** border（按元素计数；`border-top` 单边线不算）；导读块为语义例外 | ✅ |
| **B3** | 标点违规 | 直角引号 `「」` 残留 / 不配对 | ✅（配对时） |
| **B4** | 结构损坏 | 标签开闭不配对、**错位嵌套**（栈式校验，数量相等也能抓） | ❌ |
| **B5** | 外域资源 | 非 `mmbiz.qpic.cn` 的图片/背景图、非 `mp.weixin.qq.com` 外链 | ❌ |
| **B6** | 语义越界 | 金句误用非红底、升华误用非绿底、规格卡误用非蓝底 | ✅（弱词除外） |
| **B7** | 红底超配额 | 红底 `#FDF3F2` 卡片数超过按字数算出的上限（**配额随字数伸缩**） | ❌ |
| **B8** | 封面级卡边框退化 | 报头/文末卡缺 border 或该 2px 写成 1px（封面级/内容级分档） | ✅ |

**判据的三条实现约束**（改脚本时务必保留，否则会误报/漏报）：

1. **先等长剥 HTML 注释** —— 版式库里紧挨卡片的注释写着"核心金句""升华"；等长替换才能让行号与 `--fix` 偏移对齐
2. **按标签栈取卡片真实边界** —— 固定 600 字符窗口既会跨卡片串味，也会漏掉长卡片后半段的角色词
3. **关键词精确** —— 升华文案是"收尾金句"，用宽泛的"金句"会把升华误判成金句

配额表、B8 分档表、每类坏法的 before/after 修法，都在 `@references/troubleshooting.md`。

**为什么要用脚本而不是肉眼或 shell grep：**

- shell `grep -c` 按**行**计数，同一行多个 `<section>` 会让「报 N 处」与实际列出行数对不上 → 必须按元素计数
- 判断边框别写 `grep 'background:...;border'`，会误匹配 `border-radius`
- 定位漏网行要用 `grep -v 'border:'`（**带冒号**），只写 `'border'` 会连 `border-radius` 一起滤掉，列表永远为空

---

## 八、封面图处理

- 标准头图比例 **2.35:1**（900×383），JPEG q92
- **AI 生成图通常带「AI生成」水印**，必须用 Pillow 裁掉底部约 8%
- 裁切要**小幅度试**：主体是三层结构时裁多了会切掉底层
- 主体偏左时，在生成 prompt 里加「画面完全居中构图，左右留白均衡」

```python
from PIL import Image
im = Image.open(src).convert('RGB')
W, H = im.size
im2 = im.crop((0, int(H*0.03), W, int(H*0.92)))   # 上下各裁一点
im2 = im2.resize((900, 383), Image.LANCZOS)
im2.save('cover_900x383.jpg', 'JPEG', quality=92, optimize=True)
```

Pillow 已装在 `C:/Users/admin/.workbuddy/binaries/python/envs/default`。

---

## 九、结构与编辑习惯

### 段落

1. 每段 **3-5 行**就分段，避免「文字墙」
2. 一段最多加粗 **1-2 个关键词**，禁止通篇狂加粗
3. 重点靠加粗或引用样式，**不要靠颜色堆砌**
4. 字体不超过两种（后台默认微软雅黑/苹方，原生不可换）
5. **无首行缩进**（微信阅读习惯）

### 编辑方式（重写而非修补）

用户给的是**草稿不是定稿**。可以重写全文、重做结构、理顺小标题、补缺失示例、删减注水；**用户的一手经验、真实判断、具体数字细节必须保留**。

> **判断方法**：如果某句话换个人写就写不出来，那是用户的，保留。如果只是「正确的废话」，重写或删掉。

**补示例是硬要求** —— 「知道」和「做到」之间的差距是文章价值的分水岭：

| 文章类型 | 必须有的示例 |
|---|---|
| 讲提示词 | 可直接复制的完整提示词，不能只描述 |
| 讲配置 | 完整配置文件或命令 |
| 讲操作 | 逐步操作示例 |
| 讲原理 | 具体数字、参数、对比表 |

### 标题与摘要

- 标题 **≤64 字节**（约 21 汉字），**留足余量** —— 余量 <10 字节时改一个字就可能超限
- 摘要约 120 字节（约 40 汉字），**不能截正文首句**（首句常含小标题会粘连成乱麻）
- 摘要要有钩子，保留文章里最有力的金句

### 作者署名

固定 **`by SnowFox`**（小写 by + 一个空格；⛔ 不是 `—— SnowFox`、也不是光写 `SnowFox`）。

---

## 十、标准作业流程

1. **判断调用方式** —— 给整篇稿 → 整套复制参照稿；只要一张卡 → 分块给成品代码
2. **按字数定板块数** —— `字数÷150` 算出弹性卡数量，增删到位；固定骨架不动
3. **填内容** —— 只改中文，不动 style 结构
4. **套自检** —— `typeset_check.py --fix` 先自愈，再 `fix_quotes.py --check` + `fixed_blocks_check.py`，**三个都要退出码 0**
5. **处理封面** —— 裁到 900×383，去掉 AI 水印
6. **提醒真机预览** —— 不同设备对字号行距呈现有差异，⛔ 不要替用户判断真机效果
7. **交接发布** —— `handoff.py --emit --strip` 出交接包与净化版正文；推草稿箱交给 `wechat-oa-draft-publish`

> 作者措辞五花八门时，可在第 4 步前跑 `--annotate` 把角色固化成 `<!-- role:x -->`，
> 之后无论怎么改写标题词，B6 都认得出。

---

## 十一、排错（先看症状，再决定动不动手）

**第一反应永远是**：`python scripts/typeset_check.py --fix 稿件.html`。能自动修的 5 类一次归零，剩下的 3 类会带行号和手改步骤。

| 症状 | 处理 |
|---|---|
| 报 `[B1]`~`[B8]` 某条 | 照输出里的「怎么改」；细则与 before/after 代码查 `@references/troubleshooting.md` |
| 脚本报 `EXIT 2` | 是**读文件/用法**问题，不是排版问题：路径不存在、指到文件夹、>32 MB、参数写错 |
| 输出乱码 / `UnicodeEncodeError` | v2.4.0 已内置编码自适应；自己写脚本调用时要带 `encoding="utf-8"` |
| 稿件是 GBK / 带 BOM | 已自动识别（UTF-8 → BOM → GB18030 → UTF-16），不用手转 |
| `--fix` 改坏了 | `Copy-Item 稿件.html.bak 稿件.html`（.bak 是改前原文） |
| 脚本说合规但真机难看 | 超出能力边界：脚本只管结构与配色，**真机必须自己预览** |
| 必留区块报缺失 | 要么把区块加回稿子，要么改 `fixed-blocks.json`；改配置前先问用户 |
| 报「待确认」但 EXIT 0 | 证据不足（如只命中「注意：」）：扫一眼即可，不用改；真要它判错就加 `<!-- role:x -->` 标注 |
| B6 认不出角色（作者换了词） | 卡片里写 `<!-- role:quote -->`，或 `--annotate` 固化；长期用词加进 `scripts/roles.json` |
| 准备发布 / 要交接 | `python scripts/handoff.py --emit --strip 稿件.html`；推草稿箱不在本技能范围 |
| 粘进微信出现空白段落 | 用 `--strip` 出的净化版（去注释 + 压空行），不要粘带注释的工作副本 |
| 检查器可疑地报/不报 | 先 `--explain <编号>` 看判据，再对 `test/run_all.py` 跑回归 |

⛔ **不要**为了让脚本通过去改判据、删夹具或放宽配额。规则松了，真机问题一点没少。

---

## 十二、降级与边界

| 情况 | 怎么办 |
|---|---|
| 用户明确说「只改排版」 | 不动内容，只调样式 |
| 需要推草稿箱 / 定时发布 | 先 `handoff.py --emit` 生成交接包（自检没过就 `ready=false`），再**转`wechat-oa-draft-publish`**；本技能不实现推送 |
| 用户给的是 Markdown | 先按第三节选组件，再把 Markdown 内容填进对应 section |
| 没有 Pillow | 封面处理无法自动完成，明确告知用户需手动裁图，**不要假装已处理** |
| 规范与用户新要求冲突 | **以用户最新要求为准**，并同步更新本技能与资料库正本 |

**红线：**

- ⛔ 不擅自改用户的配色与字号——要改先问
- ⛔ 不把红色用成常态——满篇红反而失去视觉冲击
- ⛔ 不用第三方查 IP 网站判断微信白名单问题（与排版无关，但同属公众号工作流常见坑）
- ⛔ 不承诺"排完就一定过审"

---

## 十三、文件索引

| 文件 | 位置 | 用途 |
|---|---|---|
| `style-floating.html` | `templates/` | **唯一弹性参照稿**，区块标了【固定】/【弹性】 |
| `fixed-blocks.json` | `scripts/` | **必留区块配置**（用户自己改） |
| `fixed_blocks_check.py` | `scripts/` | **必留区块校验器**（按配置校验，`--show` 看配置） |
| `typeset_check.py` | `scripts/` | **排版合规检查器（八类坏法 + `--fix` 自愈），每篇必跑** |
| `roles.json` | `scripts/` | **角色词表**（强/弱标记、底色、视觉指纹，可自行增补） |
| `handoff.py` | `scripts/` | **交付契约**：跑三个自检生成交接包，`--strip` 出可直接粘贴的净化版 |
| `fix_quotes.py` | `scripts/` | **标点检查/修复，`--check` 只检查** |
| `skillio.py` | `scripts/` | 共用 IO 层：编码识别、原子写、控制台编码降级（**不要绕过它直接 open**） |
| `troubleshooting.md` | `references/` | **排障手册**：八类坏法的原因 + before/after 修法 + 环境问题 FAQ |
| `typography-and-color.md` | `references/` | 字号/行距/配色/边框的判据、理由与边界情况（第一节二节的展开） |
| `writing-and-editing.md` | `references/` | 改写判例、常见病灶修法、简报专用要点（第九节的展开） |
| `convergence_spec.json` | `test/` | 检查器收敛矩阵规格（8 规则 × 52 格） |
| `run_all.py` | `test/` | 验证集入口，100 项断言，任一失败非零退出 |
| `ab_compare.py` | `test/` | A/B 增益对照（验优于裸模型） |
| `stability.py` | `test/` | 稳定性证据：判分器防 flaky、best-of-N 分布、黄金集回归 |
| `golden_expect.json` | `test/` | 黄金集基线（`--golden --update` 重录） |

改样式模板后必须跑：

```bash
python scripts/typeset_check.py --all && python test/run_all.py
```

**正本位置**：资料库 → 个人空间 → `公众号运营规范/`（用户明确指认正本在资料库，本技能是工作副本）。
正本更新后需同步本技能，并递增 `version`。
