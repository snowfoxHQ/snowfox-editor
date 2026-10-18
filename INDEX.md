# Snowfox编辑 · 资料库索引

技能包 v2.5.0 · 全部文件都在这个文件夹里

> 平台页：https://skillhub.cn/skills/indiv-snowfox/snowfox-editor
> 仓库：https://github.com/snowfoxHQ/snowfox-editor

## 怎么装

把 `snowfox-editor` 整个文件夹放进 `~/.workbuddy/skills/`（即 `snowfox-editor/` 与 `SKILL.md` 平级）。

## 文件在哪

| 文件 | 用途 |
|---|---|
| SKILL.md（主文件） | 触发词、全部规则、流程——**先看这个** |
| README.md（说明文档） | 快速上手、目录结构、常用提示词 |
| QC-REPORT.md（质检报告） | 100 项断言实跑记录、已知限制 |
| CHANGELOG.md（变更记录） | 每个版本改了什么，发版时复制到 SkillHub「变更说明」 |
| LICENSE.md / NOTICE.md | Apache-2.0 全文与归属声明 |
| 排障手册 | 每条报错的原因 + 改法 + before/after 代码 + 环境 FAQ |
| 字号配色边框判据 | 字号/行距/配色/边框的原理与边界 |
| 写作与编辑细则 | 改写判例、常见病灶修法、简报要点 |
| 唯一弹性参照稿 | `style-floating.html`，照着增删区块 |
| 必留区块配置 | `fixed-blocks.json`，**每个账号改这个** |
| typeset_check.py | 排版合规检查器（8 类坏法 + `--fix` 自愈 + 角色三值判定） |
| roles.json | 角色词表（强/弱标记、底色、视觉指纹，可增补） |
| handoff.py | 交付契约：交接包 + `--strip` 粘贴前净化 |
| skillio.py | 共用 IO（编码识别 / 原子写 / 控制台降级） |
| fix_quotes.py | 引号检查/修复 |
| fixed_blocks_check.py | 必留区块校验器 |
| run_all.py | 验证集（100 项断言） |
| ab_compare.py | A/B 增益对照 |
| stability.py / golden_expect.json | 稳定性证据（防 flaky / best-of-N / 黄金集） |
| convergence_matrix.py / convergence_spec.json | 收敛验收工具与规格（8 规则 × 52 格） |

## 三句话用法

1. **一套样式** —— 本号只有悬浮卡片样式，不分简报/长文模板
2. **板块数自动算** —— `字数 ÷ 150`，不预设、不硬套
3. **必留区块可配置** —— 改 `fixed-blocks.json`，不同账号自己定

## 交付前三重自检

```bash
python scripts/typeset_check.py --fix 稿件.html  # 排版 + 字数 + 红底配额 + 文末边框（可自愈）
python scripts/fix_quotes.py --check 稿件.html   # 标点
python scripts/fixed_blocks_check.py 稿件.html  # 必留区块
```

三个都要退出码 0。自动修覆盖 B1/B2/B3/B6/B8，B4/B5/B7 按报错手改（每类都有行号与 before/after）。

## 注

- 「弹性参照稿」「必留区块配置」各有一份标了「重复项」的，那是上传时的重复，可删
- `snowfox-editor-v2.3.0.zip` 是完整打包版，解压即用
