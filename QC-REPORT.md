# QC 报告 · Snowfox编辑 v2.5.2

质检结论与实跑记录。所有数字来自实跑，未跑的项标注「未执行」。

## 当前版本（v2.5.2）实跑结果

```
python test/run_all.py                  → 100 项 100 通过 0 失败
python test/convergence_matrix.py …     → 8 规则 / 52 格，无孤儿格无漂移
python test/ab_compare.py               → A 组 0 违规 / B 组 2 类，增益 100%
python test/stability.py                → 防 flaky 通过 + 黄金集 3/3 一致
python scripts/typeset_check.py --all   → 全库合规
```

复核方式：改样式模板或判据后，重跑上面五条命令即可复现本报告。

## 检查器能力摘要

- 八类坏法 B1-B8，每条违规输出：行号 + 为什么 + 怎么改 + 能否自动修
- `--fix` 自动修 B1/B2/B3/B6/B8（改前留 `.bak`，幂等）；B4/B5/B7 手改
- B6 三值判定：显式标注 `<!-- role:x -->` / 强角色词 / 左 4px 色条 → 判错；通用词 → 只提醒
- 词表外置 `scripts/roles.json`；`--annotate` 把判定结果固化成注释（幂等，只写判得准的）
- 输入编码自适应（UTF-8 / BOM / GB18030 / UTF-16）；输出编码自适应（管道强制 UTF-8，TTY 降级 emoji）
- 写盘原子写 + `.bak`；>32MB / 含 NUL 的文件明确拒绝，返回 EXIT 2 而不是 traceback

## 已知限制

1. B6 不是真语义理解：既无标注、无色条、又改了措辞的卡片认不出（微信禁 class 的固有代价）
2. 弱证据只提醒不拦截，待确认列表需要人扫一眼
3. 不校验真机观感，必须用户自己预览
4. 不覆盖发布链路：只出交接包，推送交给 `wechat-oa-draft-publish`
5. B5 白名单是前缀匹配，微信新增官方域名需手工扩
6. 跨模型压测未做：现有证据是判分器防 flaky + 单模型 best-of-N + 黄金集
7. 黄金集基线按文件名存，同名不同内容的稿子会误判
8. `.bak` 只保留最近一次

## 历史版本

各版本的变更明细与修复记录见 `CHANGELOG.md`。
