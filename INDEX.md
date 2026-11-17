# Snowfox编辑 · 文件索引

公众号排版技能包 v2.5.3 · 作者 SnowFox
平台页：https://skillhub.cn/skills/indiv-snowfox/snowfox-editor · 仓库：https://github.com/snowfoxHQ/snowfox-editor

## 安装

把 `snowfox-editor` 整个文件夹放进 `~/.workbuddy/skills/`（目录名必须是 `snowfox-editor`，与 `SKILL.md` 平级）。

## 文件说明

| 文件 | 用途 |
|---|---|
| SKILL.md | 主文件：触发词、全部规则、流程，**先看这个** |
| README.md | 快速上手与常用命令 |
| QC-REPORT.md | 质检报告（100 项断言实跑结果与已知限制） |
| CHANGELOG.md | 每个版本改了什么 |
| LICENSE.md / NOTICE.md | Apache-2.0 全文与归属声明 |
| templates/style-floating.html | 唯一弹性参照稿，照着增删区块 |
| scripts/typeset_check.py | 排版检查器（8 类坏法 + `--fix` 自愈） |
| scripts/fix_quotes.py | 引号检查/修复 |
| scripts/fixed_blocks_check.py + fixed-blocks.json | 必留区块校验 + 配置（按账号改） |
| scripts/roles.json | 角色词表（可增补） |
| scripts/handoff.py | 交付契约：交接包 + `--strip` 净化版 |
| scripts/skillio.py | 共用 IO（编码识别/原子写/控制台降级） |
| references/troubleshooting.md | 排障手册：每条报错的原因 + 改法 + 代码 |
| references/typography-and-color.md | 字号/配色/边框判据 |
| references/writing-and-editing.md | 改写判例、病灶修法 |
| test/run_all.py | 验证集入口（100 项断言） |

## 三句话用法

1. 只有一套样式（悬浮卡片），不分简报/长文模板
2. 卡片数 = 字数 ÷ 150，自动算
3. 必留区块改 `fixed-blocks.json`，不同账号自己定

## 交付前自检（都要退出码 0）

```bash
python scripts/typeset_check.py --fix 稿件.html  # 排版八类，能修的自动修
python scripts/fix_quotes.py --check 稿件.html   # 标点
python scripts/fixed_blocks_check.py 稿件.html   # 必留区块
```
