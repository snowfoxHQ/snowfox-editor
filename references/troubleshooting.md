# 排障手册 · 每条报错怎么改（附可直接复制的代码）

> 这份文件解决一件事：**检查器报了问题，你照着改就行，不用回头翻规范。**
> 主文件 `SKILL.md` 讲「应该长什么样」，这里讲「报错了怎么办」。

---

## 一、先跑这一条（90% 的问题它能自己修）

```bash
python scripts/typeset_check.py --fix 稿件.html
```

它会自动处理 5 类：`B1` 微信剥离写法、`B2` 缺边框、`B3` 直角引号、`B6` 配色串用、`B8` 文末卡边框。
改完自动复检，退出码 0 就是干净了；原文件会留一份 `稿件.html.bak`，改坏了拷回来即可。

| 想干嘛 | 命令 |
|---|---|
| 先看它会改什么，不落盘 | `python scripts/typeset_check.py --fix --dry-run 稿件.html` |
| 只看问题，不动稿 | `python scripts/typeset_check.py 稿件.html` |
| 让机器读结果（Agent/CI） | `python scripts/typeset_check.py --json 稿件.html` |
| 查某条规则到底在管什么 | `python scripts/typeset_check.py --explain B7` |
| 不想留 .bak | 加 `--no-backup` |

**它不会自动修的 3 类，以及为什么**：

| 编号 | 为什么不敢自动修 |
|---|---|
| B4 结构损坏 | 少一个 `</section>` 有十几种补法，猜错会把整篇排版弄塌 |
| B5 外域资源 | 得先把图传到素材库拿到新链接，脚本变不出来 |
| B7 红底超配额 | 该降级哪张红卡是内容判断，不是排版判断 |

---

## 二、八类坏法逐条修法

### B1 · 微信剥离（`style` 标签 / `class` / `script` / `onclick`）

**为什么会报**：微信正文编辑器会把 `<style>`、`class`、`<script>`、行内事件全部过滤掉。写完看着好好的，一粘进后台样式就没了。

```html
<!-- ❌ 会被吃掉 -->
<style>.card{background:#F0F9F2}</style>
<section class="card" onclick="track()">…</section>

<!-- ✅ 内联，且不留 class / 事件 -->
<section style="background:#F0F9F2;border:1px solid #E3E8EF;border-radius:12px;">…</section>
```

**手改三步**：① 把 `<style>` 里的每条规则复制进对应标签的 `style=""`；② 删掉 `class="…"`；③ 删掉 `onclick` 等事件属性。
**注意**：`--fix` 能删 `class`，但**样式不会自动补**——class 里原本的样式要么已经在 inline 里，要么需要你按第三节抄一份。

---

### B2 · 有底色却没有整圈 border

**为什么会报**：卡片靠 1px 描边和浅底色分层，缺边框在真机上会和底板糊成一片；只写 `border-top` 也报，因为另外三边是空的。

```html
<!-- ❌ 缺边框 -->
<section style="background:#F0F9F2;padding:18px 20px;">…</section>

<!-- ❌ 只有上边线，同样算缺 -->
<section style="background:#F0F9F2;border-top:1px solid #E3E8EF;">…</section>

<!-- ✅ 内容级 1px -->
<section style="background:#F0F9F2;border:1px solid #E3E8EF;border-radius:12px;box-shadow:0 2px 10px rgba(31,45,61,0.08);padding:18px 20px;">…</section>
```

**合法例外**（报这几处就是脚本 bug，不是稿子问题）：
- `background:#F2F3F5` 底板 —— 承载全篇的容器，不是卡片
- `background:#282C34` 代码块 —— 功能性黑底
- 卡里有「本期看点」或「导读」—— 导读块**刻意无边框**（2026-10-13 用户确认）

---

### B3 · 直角引号「」

**为什么会报**：本号标点铁律，正文一律用中文双引号。

```html
❌ 所谓「主动记忆」        ✅ 所谓“主动记忆”
❌ 「外「内」外」          ✅ “外‘内’外”（嵌套内层用单引号）
```

**手改**：`python scripts/fix_quotes.py 稿件.html`；只想确认：加 `--check`。
**引号不配对时脚本会中止、不改文件**（返回 1），这时自己数一遍左右引号。

---

### B4 · 标签不配对 / 错位嵌套

**为什么会报**：微信对错位嵌套会整段吞样式，而且数量相等也可能错——所以用栈式校验，不是数个数。

```html
<!-- ❌ 错位：数量都是 1:1，但闭合顺序反了 -->
<section><div></section></div>

<!-- ✅ -->
<section><div></div></section>
```

**手改**：看报错行号，往上找最近的 `<section` / `<div`，确认「先开的后关」。
复制卡片时最常见：整块复制后只删了内容、忘了删闭合标签。

---

### B5 · 外域图片 / 外链 / 背景图

**为什么会报**：微信只显示自家图床，外域图是空白；外链会被拦。

```html
❌ <img src="https://example.com/a.png">
✅ <img src="https://mmbiz.qpic.cn/mmbiz_jpg/xxxx/640?wx_fmt=jpeg">

❌ style="background-image:url(https://example.com/bg.png)"
✅ 先上传素材库，再换成 mmbiz.qpic.cn 的链接

❌ <a href="https://github.com/xxx">仓库</a>
✅ <a href="https://mp.weixin.qq.com/s/xxxx">仓库</a>
```

**手改**：图片先传公众号素材库；外链改成公众号内链（短链会被微信自动改成长链，正常）。

---

### B6 · 配色串用（红/绿/蓝用错）

**为什么会报**：三色分工固定 —— **红=强调提醒 · 绿=分层收尾 · 蓝=结构规格**。

| 卡片里的角色词 | 必须是 | 常见错法 |
|---|---|---|
| `核心金句` / `最值得注意` / `注意：` | 红底 `#FDF3F2` | 做成绿底（历史上真出过一次） |
| `升华块` / `层名称` / `一句话职能` / `收尾金句` | 绿底 `#F0F9F2` | 做成红底（和上面搞反） |
| `规格项` / `参数说明` | 蓝底 `#F4F8FC` | 做成绿底 |

**手改**：把该 `section` 的 `background` 换成上表颜色即可；`--fix` 会自动换（弱证据除外）。

#### 判据是三值的（2026-10-18 起）

| 证据 | 例子 | 结果 |
|---|---|---|
| 显式标注 | `<!-- role:quote -->` | 判错（优先级最高，改了措辞也认） |
| 强角色词 | `核心金句` / `升华块` / `规格项` | 判错 |
| 视觉指纹 | `border-left: 4px solid #D93F2B` | 判错（与用词无关） |
| 通用汉语 | `注意：` / `最值得注意` | **只提醒**：列进「待确认」，不计退出码、不自动改色 |

⛔ 为什么分级：二值判定必然在「误报」和「漏报」之间二选一。
「注意：」这种通用汉语出现在论述段里就要求人家改红底，是典型误报。

#### 作者换了措辞，B6 认不出来（按推荐顺序）

1. 卡片里写 `<!-- role:quote -->` —— 微信不渲染注释，是工作副本的元信息
2. `python scripts/typeset_check.py --annotate 稿件.html` —— 把已判定的角色一次性固化（幂等）
3. 长期用词加进 `scripts/roles.json` —— `strong` 判错、`weak` 只提醒

⛔ `--annotate` 只给判得准的卡写标注：把猜测固化成事实比不标注更糟。

**两个已知边界**（不是 bug）：
- 卡片里**没有**这些角色词、也没有色条指纹 → B6 不管（没有判据就不猜）
- 「收尾金句」不会被当成「核心金句」——关键词是精确匹配的，升华块不会因为含「金句」二字被误判成红卡

---

### B7 · 红底超配额

**为什么会报**：红色是强调色，满篇红等于没有重点。配额随字数伸缩：

| 全文字数 | 红底上限 |
|---|---|
| ≤500 | 1 张 |
| ≤1000 | 2 张 |
| ≤2000 | 3 张 |
| >2000 | 4 张 |

**手改**：报错里会列出每张红卡的行号，挑最弱的那张：
- 金句 → 改成绿底（`#F0F9F2`）当分层卡，或直接删掉
- 提醒卡 → 合并进相邻正文段
- 文末① → 保留，它通常是最该留的那张

⛔ 不要靠删字数硬凑配额，也不要为了腾配额把真金句降级成普通段落。

---

### B8 · 封面级卡边框退化（报头 / 文末）

**为什么会报**：封面级区块是 2px，内容级是 1px。**B2 只看「有没有边框」，看不出「该 2px 写成 1px」**，所以单列 B8。

```html
❌ <section style="background:#F0F9F2;padding:20px 22px;">AI 对话已开通</section>
❌ <section style="background:#F0F9F2;border:1px solid #E3E8EF;">AI 对话已开通</section>
✅ <section style="background:#F0F9F2;border:2px solid #09B83E;">AI 对话已开通</section>
```

| 区块 | 档位 | 边框 |
|---|---|---|
| 报头（含 `by SnowFox`） | 封面级 | `border:2px solid #09B83E` |
| AI 对话 / 开源仓库 | 封面级 | `border:2px solid #09B83E` |
| 最值得深挖 | 封面级 | `border:2px solid #D93F2B` |
| 互动问句 | 封面级 | `border:2px solid #09B83E` |
| 事实来源 / 资料来源 | 内容级 | `border:1px solid #E3E8EF` |
| 升华 | 内容级 | `border:1px solid #E3E8EF` |

> 档位以 `references/typography-and-color.md` 的配色表为准：**升华是 1px，不是 2px**。

---

## 三、环境类问题（不是稿子的错）

### 输出是乱码 / 报 UnicodeEncodeError

**已修（v2.4.0）**：脚本检测到输出被管道捕获时自动转 UTF-8；真实控制台则保持系统编码、把 emoji 降级。
如果你在**自己写的脚本**里调这些工具，记得：

```python
subprocess.run(cmd, capture_output=True, text=True,
               encoding="utf-8", errors="replace",
               env=dict(os.environ, PYTHONIOENCODING="utf-8"))
```

### 稿件是 GBK / 带 BOM / 打不开

**已修（v2.4.0）**：自动依次尝试 UTF-8 → UTF-8 BOM → GB18030 → UTF-16。
全都失败时会给一条可执行命令，而不是 traceback：

```powershell
Get-Content '稿件.html' -Encoding Default | Set-Content '稿件.html' -Encoding UTF8
```

### `EXIT 2` 是什么意思

**读文件/用法出错**（不是排版不合规）。常见三种：
1. 路径不存在 / 指到了文件夹 → 检查路径
2. 文件 > 32 MB → 大概是把整站导出当成单篇稿了
3. 参数写错 → `python scripts/typeset_check.py --help`

### `--fix` 改坏了想回滚

```powershell
Copy-Item 稿件.html.bak 稿件.html
```
`.bak` 是**每次 --fix 之前**的原文（只保留最近一次）。

### 粘进微信后出现空白段落 / 格式错乱

**先换净化版再粘**（v2.5.0 起）：

```bash
python scripts/handoff.py --strip 稿件.html     # 生成 稿件.wechat.html
```

净化版会去掉 HTML 注释（含 `<!-- role:x -->` 标注与【固定】/【弹性】标记）、压掉空行、清行尾空格。
⛔ 别把带注释的工作副本直接粘进编辑器——注释在微信里不渲染，但可能造成空白段落。

### 要发布 / 要交接给别人

```bash
python scripts/handoff.py --emit --strip 稿件.html --title "标题" --digest "摘要" --cover 封面.jpg
```

产出 `稿件.handoff.json`：三个自检的退出码、标题/摘要/封面/作者，缺什么写进 `missing`。
- `ready=true` → EXIT 0；自检没过 → `ready=false` + EXIT 1，不会让没过的稿子蒙混出去
- **推草稿箱 / 定时发布不在本技能范围**，交接包里写明下一步交给 `wechat-oa-draft-publish`

### 脚本说合规，真机还是丑

**这不是 bug，是能力边界**：脚本只保证结构、配色、边框、字数这些**确定性规则**，不判断真机观感。
不同机型字号行距渲染有差异，**发布前必须自己手机预览一遍**——这一条脚本永远替代不了。

### Pillow 没装，封面裁不了

```bash
python -c "import PIL" || pip install pillow
```
装不上就明确告诉用户「需手动裁到 900×383」，⛔ 不要假装已处理。

---

## 四、反模式清单（照抄就会翻车）

| ❌ 别这样 | ✅ 应该这样 | 原因 |
|---|---|---|
| `class="card"` + `<style>` | 全部内联到 `style=""` | 微信过滤 |
| 18 个卡片全 2px 绿边 | 只有封面级区块用 2px | 层级要分档，全是粗边等于没有层级 |
| 满篇红底强调 | 按配额用红 | 满篇红 = 没重点 |
| 金句用绿底、升华用红底 | 金句红、升华绿 | 三色分工搞反 |
| 每段都加粗 | 一段 1-2 个关键词 | 加粗太多等于没加粗 |
| 首行缩进两格 | 段间距 22px、不缩进 | 微信阅读习惯 |
| `rgba(0,0,0,0.9)` 当正文色 | `#3F3F3F` | 真机上过黑、发脏 |
| 拿「3000 字」当一屏塞 30 张卡 | 字数÷150 算卡片数 | 密度跟着字数走 |
| 摘要直接截正文首句 | 重写一句带钩子的 | 首句常含小标题，截出来是乱麻 |
| 排完就说「一定过审」 | 只保证排版合规 | 过审是内容与账号问题 |
