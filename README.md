# Snowfox编辑 · 公众号排版技能

> 微信公众号正文排版与编辑技能包 v2.5.0 · 作者 SnowFox

## 一句话

本号只有**一套样式（悬浮卡片）**，板块数按字数自动算，必留区块按账号配置——不预设、不拆分、不硬套。

## 怎么装

把整个 `snowfox-editor` 文件夹放进：

```
~/.workbuddy/skills/snowfox-editor/
```

（Windows：`C:\Users\<用户名>\.workbuddy\skills\snowfox-editor\`）

目录必须叫 `snowfox-editor`，且与 `SKILL.md` 平级。

## 文件结构

```
snowfox-editor/
├── SKILL.md                           主文件（13 节，触发词与规则都在这）
├── QC-REPORT.md                       质检报告（100 项断言实跑记录）
├── references/
│   ├── troubleshooting.md             排障手册：每条报错的原因 + 改法 + 代码
│   ├── typography-and-color.md        字号/配色/边框判据与理由
│   └── writing-and-editing.md         改写判例、病灶修法、简报要点
├── scripts/
│   ├── typeset_check.py               排版合规检查器（8 类坏法 + --fix 自愈）
│   ├── roles.json                     角色词表（强/弱标记、底色、视觉指纹）
│   ├── handoff.py                     交付契约：交接包 + --strip 粘贴前净化
│   ├── skillio.py                     共用 IO：编码识别 / 原子写 / 控制台降级
│   ├── fix_quotes.py                  引号检查/修复
│   ├── fixed-blocks.json              必留区块配置（按账号改这个）
│   └── fixed_blocks_check.py          必留区块校验器
├── templates/
│   └── style-floating.html            唯一弹性参照稿
└── test/
    ├── run_all.py                     验证集入口（100 项断言）
    ├── ab_compare.py                  A/B 增益对照
    ├── stability.py                   稳定性：防 flaky / best-of-N 分布 / 黄金集
    ├── golden_expect.json             黄金集基线
    ├── convergence_spec.json          收敛矩阵规格（8 规则 × 52 格）
    └── convergence_matrix.py          收敛验收工具
```

## 日常怎么用

| 你说 | 会做什么 |
|---|---|
| 排版 / 按公众号规范排 | 判断稿型 → 整套复制参照稿 → 只改中文 → 按公式调板块数 → 三重自检 |
| 用悬浮样式 / 卡片式排版 | 同上，整篇用悬浮样式 |
| 给我一张金句卡 | 分块调用，直接给成品 HTML，不反问 |
| 这张卡换成悬浮的 | 补 `border-radius:12px` + `box-shadow` |
| 检查排版 | 只跑脚本，不改稿 |
| 自动修一下 | `typeset_check.py --fix`，改前留 `.bak`，改完复检 |
| 必留区块改成 XX | 改 `scripts/fixed-blocks.json` |

## 三个自检（交付前都要 EXIT 0）

```bash
cd ~/.workbuddy/skills/snowfox-editor

python scripts/typeset_check.py --fix 稿件.html  # 排版八类；能修的自动修，改前留 .bak
python scripts/fix_quotes.py --check 稿件.html   # 标点（禁直角引号）
python scripts/fixed_blocks_check.py 稿件.html   # 必留区块（按配置）
```

检查器会报告：**字数 / 卡片数 / 红底配额 / 建议卡片数**，按建议值增删弹性卡即可。

每条违规都带 **行号 + 为什么 + 怎么改 + 能否自动修**：

```
[B8] 第 38 行 · 文末卡「AI 对话已开通」有底色但没有 border（2px 封面级）
     为什么：文末引导卡是封面级 2px 描边，退化后视觉层级塌掉。
     怎么改：补 border: 2px solid #09B83E
     自动修：python scripts/typeset_check.py --fix <稿>
```

自动修覆盖 **B1/B2/B3/B6/B8**；**B4 结构 / B5 外域资源 / B7 红底配额**必须手工
（B4 补标签会猜错位置、B5 得先传素材库、B7 是内容取舍）。

不想落盘先预演：`--fix --dry-run`；想给机器读：`--json`；想知道某条规则在管什么：`--explain B7`。
改坏了回滚：`Copy-Item 稿件.html.bak 稿件.html`。

## 作者换了措辞怎么办（B6 三值判定）

微信不允许 class，角色只能靠内容与视觉推断。判据分四级证据：

| 证据 | 例子 | 判定 |
|---|---|---|
| 显式标注 | `<!-- role:quote -->` | 判错（改了措辞也认） |
| 强角色词 | 核心金句 / 升华块 / 规格项 | 判错 |
| 视觉指纹 | 左侧 4px 红（绿）色条 | 判错（与用词无关） |
| 通用汉语 | 「注意：」 | **只提醒**，不计退出码、不自动改色 |

```bash
python scripts/typeset_check.py --roles 稿件.html      # 看当前词表（强/弱分别列）
python scripts/typeset_check.py --annotate 稿件.html   # 把已判定的角色固化成注释（幂等）
```

- 自己的习惯用词直接加进 `scripts/roles.json`（`strong` 判错 / `weak` 只提醒）
- `--annotate` 只给「判得准」的卡写标注，**不会把猜测固化成事实**

## 准备发布

```bash
python scripts/handoff.py --emit --strip 稿件.html \
       --title "标题" --digest "摘要" --cover 封面.jpg
```

生成 `稿件.handoff.json`（三个自检的退出码 + 标题/摘要/封面/作者，缺什么写进 `missing`）
与 `稿件.wechat.html`（去注释、压空行，可直接粘进微信编辑器）。
**推草稿箱不在这个技能里**——交接包写明下一步交给 `wechat-oa-draft-publish`。
自检没过时 `ready=false` 且退出码 1，不会让没过的稿子蒙混出去。

## 排障

遇到看不懂的报错，先看 `references/troubleshooting.md`——八类坏法逐条给了 before/after 代码，
环境类问题（编码、大文件、EXIT 2、Pillow 缺失、真机与脚本不一致）也在里面。

## 板块数自适应

```
可重复卡片数 = 全文字数 ÷ 150，取整，最少 2 张
红底配额     = ≤500字→1 张 · ≤1000字→2 张 · ≤2000字→3 张 · >2000字→4 张
```

**固定骨架**（永不可删）：底板 · 报头 · 导语 · 升华 · 事实来源 · 开源仓库 · AI 对话
**弹性内容**（按公式增删）：胶囊栏目标 · 白卡 · 绿卡 · 红卡 · 蓝卡 · 提醒卡

## 必留区块配置

改 `scripts/fixed-blocks.json` 的 `required` 数组：

```json
"required": ["board", "masthead", "lede", "subtitle", "ai_chat"]
```

可用 key：`board` 底板 · `masthead` 报头 · `lede` 导语 · `subtitle` 升华 · `reminder` 提醒卡
· `deep_dive` 文末① · `interact` 文末② · `repo` 文末③ · `ai_chat` 文末④

查看当前配置：`python scripts/fixed_blocks_check.py --show`

## 配色铁律

| 底色 | 语义 | 边框 |
|---|---|---|
| `#FDF3F2` 红 | 金句 / 提醒 / 封面红卡 | 金句1px+左4px红 · 文末卡2px红 |
| `#F0F9F2` 绿 | 分层 / 升华 / 报头 / 文末绿卡 | 内容1px灰 · 封面2px绿 |
| `#F4F8FC` 蓝 | 规格卡（浅蓝底） | 1px 灰 |
| `#FFFFFF` 白 | 资讯卡 / 事实来源 | 1px 灰 |
| 无边框 | **导读块（刻意）** · 底板 `#F2F3F5` · 代码块 `#282C34` | — |

## 跑一遍验证

```bash
python test/run_all.py              # 100 项断言，应全绿
python test/convergence_matrix.py --spec test/convergence_spec.json --audit scripts/typeset_check.py
python test/ab_compare.py           # A/B 增益（应 ≥20%）
python test/stability.py            # 判分器防 flaky + 黄金集回归
python test/stability.py --candidates <候选稿目录>   # best-of-N 分布（均值/σ/最好）
```

## 环境要求

- Python 3.9+，**零第三方依赖**（纯标准库），Windows / macOS / Linux 均可跑
- 稿件编码自适应：UTF-8 / UTF-8 BOM / GBK(GB18030) / UTF-16 都能读
- 输出编码自适应：管道里强制 UTF-8，真实控制台保持系统编码并把 emoji 降级成 `[OK]`/`[X]`
- 可选：Pillow（只用于封面裁图，缺了会明确告知，不会假装处理）
