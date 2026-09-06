# 移动端整改方案 v1（2026-09-06，仅方案，不含代码）

依据：FRONTEND_DESIGN_DECISION.md §4a（移动端独立代码路径）、§5（视觉系统）、§7b/§7c/§7d/§7e（对象页、索引、搜索、首页）、§7（About 段落顺序）；以及本轮桌面端已定型的视觉语言："一张邮票纸"——实色色板承载被裁切的超大数字、LINE Seed 800 标题、墨线轮廓、pills、小线描标记；单一对比规则（色板混 8% 纸色、深色上纸色字 / 浅色上墨色字、数字同色 90%、1.5px 软化轮廓）；全站字号下限 17px；只用 v49 冻结数字；缺失即省略或 "Not recorded"。

## 1. 现状（已验证，读自 worktree 源码）

| 页面 | 移动端树 | 数据来源 | 状态 |
| --- | --- | --- | --- |
| 首页 `/` | `app/home/mobile/HomeMobile.tsx` | `lib/content.ts` 常量（含 v49 年份分层数据） | 四段纯文本堆叠，无任何图形，与桌面"胶片"脱节 |
| 索引 `/directory` | `app/directory/mobile/*` | `/api/index/v1` 真实 catalogue | 结构成立（列表优先、控制行、底部抽屉），但视觉仍是早期语言 |
| 搜索 `/search` | `app/search/mobile/*` | **设计 fixture**（`lib/fixture.ts` 合成记录 + 本地 `suggestFor`） | 数量与结果都不是真的；System suggests 是本地静态版 |
| 对象页 `/surfaces/[id]` | `app/surfaces/[id]/mobile/*` | 真实 sealed projection（page.tsx 解析后传入） | 单列阅读成立；层头 03/04/05 仍是旧语言，视觉层三态已接 §3d |
| About `/about` | **无移动端树**，单树 + `@media` 断点 | `about/content.ts` | 违反 §4a（移动端不是断点回流） |
| TRACE 系列 | 服务端返回 desktop-required 提示 | — | 维持（§4a：移动端不提供 TRACE） |
| 导航 | `SiteNav variant="mobile"`：MGDA · Index · Search · About | — | 维持 |

桌面端 Search 本轮已接入真实 API（`app/search/lib/live.ts`：结果、精确计数、游标翻页、真实字典与年份范围、共享 guidance 端点）。这些 hook 位于 `lib/`，按 §4a 是移动端唯一允许共享的层。

## 2. 目标与不变原则

1. 移动端是独立代码路径：每页 `mobile/` 自己的组件与 CSS；只共享 `lib/`（取数、DTO、纯函数）。不复用桌面 JSX 或 module.css。
2. 视觉语言同源不同形：邮票纸的色板、裁切数字、pills、线描标记在 390px 上重新排版，而不是缩小桌面版。
3. 数据只能来自真实 API 与冻结清单：搜索接 `/api/search/v1`；首页数字读生成的 status/manifest；对象页与索引保持现有真实来源。
4. 字号下限 17px；触控目标 ≥ 44px；折叠内容默认折叠；阅读页无滚动动画；无渐变、阴影、毛玻璃（Exploration 图片的例外只在桌面）。
5. 移动端范围仍是"阅读与查找"：首页、索引、搜索、对象页、About（含 Source）。TRACE 三个视图不在移动端。

## 3. 分页方案

### 3.1 首页（新设计）

桌面首页是四段：01 Identity 胶片 · 02 Contribution · 03 Enter · 04 Research status。移动端保留四段与顺序，但每段换成"邮票纸"的竖排形式：

- **01 Identity**：一块满宽色板（深色，纸色字），标题用 LINE Seed 800 两行（`IDENTITY_HEADLINE_LEAD` + accent 色字），下方一句 `IDENTITY_TAGLINE_SETTLED`；不做桌面的滚动驱动网格与文字变形，改为一枚静态小线描标记（同 About 的段首标记）。
- **02 Contribution**：账本改成 2×2 色板格，每格一个被裁切的超大数字（7,995 public · 15,923 canonical · 93 geographies · 1800–2026 期间），标签 17px 大写字距；数字全部来自 `CONTRIBUTION_LEDGER` 与 status-v49 清单，不手打。年份分层图（`YEAR_TIERS`，227 年）压缩为按十年的细条图（23 条），"public / held" 两色并列，图例文字 17px；这是桌面 Identity 图的移动端替身，不再逐年。
- **03 Enter the archive**：两块可点的色板 Index、Search（各带一行动词与一枚线描标记）；TRACE 作为第三块但不可点，右上角 pill "Desktop"，一行说明 "Three research views on desktop."（沿用 §4a 的 address-disabled 语义，不给死链）。
- **04 Research status**：一段正文 + 指向 About 内 Source 段落的锚链接（移动端 Source 折叠在 About 中）。

### 3.2 索引（部分重设计）

保留：列表优先、单行控制条（Filter · 切片 · 数量）、底部抽屉手风琴、按年分组、每页 200 后"show the next"、真实 `/api/index/v1`。

改动：

- 年份分组头改为色板行：左侧被裁切的十年数字（例如 "196"）+ 右侧记录数，色板颜色取该组主题主色的软化版；行内条目保持墨色。
- 条目行统一为：标题（17px 加粗）· 地名（as recorded）· 年份；主题用 pill，最多两枚，其余 "+n"。
- 控制条数量字用数字面（`--font-num`），切片与筛选计数用 pill；Filter 按钮 44px 高。
- 底部抽屉：五个手风琴段（Place · Year · Order · Theme · Visual）的头部显示当前值 pill；Place 改为可搜索列表（145 个 as-recorded 地名）；Visual 过滤沿用"interim"文案（§3c）。
- 空态与错误态文案沿用桌面（不出现 "Unknown"）。

### 3.3 对象页（重设计）

保留：服务端设备分流、单列、§3d 三种视觉模式（可显示图片 / 一句话 + "View at source" / 仅引用，从不出现空框）、返回瓦片与 "Object record" 面包屑、回到顶部。

改动：

- 头部改为色板：眼眉 "MGDA record"，标题 LINE Seed 800（最大两行，超出截断到三行），身份行（surfaceId · type · date · place）17px；色板颜色按对象主要主题取色，无主题则用墨色板。
- 层头 03/04/05 改成与 About 一致的"段首标记"：小色块 + 裁切数字 + 名称，取消现在的 `--l-*` 色条。
- 目录元数据用两列定义表（label 17px 大写字距 / 值 17px），缺项省略。
- 描述段默认展开前 6 行，其余折叠（"fold by default"）。
- Source · Citation · Provenance 默认折叠；引用格式提供一键复制；来源查看器链接为 44px 全宽按钮。
- 底部固定条（可选，见 §6 问题 4）：Top · Index · View at source。

### 3.4 About（新建移动端树）

新建 `app/about/mobile/`，内容从 `about/content.ts` 共享。段落顺序固定（§7）：Overview / Project · Methodology · Claim boundaries · Citation · Design research · Source · Rights & permissions。

- 每段一块满宽色板：裁切的段号数字 + 段标题 + 一枚线描标记；正文在纸面上，默认只展开每段的引导句，其余折叠（"More"/"Less" 44px）。
- Source 段落在移动端折叠桌面 `/source` 的三部分（provenance · rights / licence · source register）；register 用可搜索列表而非表格。
- Citation 段提供复制按钮；Rights 段以 pill 标注许可类型。
- 最后一段翻纸（黄色板配墨底），与桌面一致。

### 3.5 搜索（接入真实 API）

- 移动端 ticket 换用 `lib/live.ts` 的 `useLiveSearch / useSearchFacets / useSearchGuidance`；删除对 `runSearch`、`suggestFor`、fixture 字典的依赖。
- 结果行：标题 · 日期 · 地点 · 类型，一枚匹配等级 pill（Perfect / Partial）；翻页改为"show the next 25"（游标），不用页码。
- System suggests 用服务端 v2 结果：一段 note + 最多两枚 token；标签仍为 "System suggests"。
- 筛选：底部抽屉（与索引同构件语言，但各自实现）；字典与年份范围来自 `/api/search/v1/facets`。
- 关闭 = history.back()；URL 同步走 history API（本轮已修桌面的双窗口问题，移动端同样处理）。

### 3.6 导航

MGDA · Index · Search · About 四项，44px 触控；当前页高亮用 1.5px 下划轮廓；无 hover 显示逻辑。

## 4. 视觉细节调整清单（390px 基线，430px 复核）

| 项 | 规格 |
| --- | --- |
| 字阶 | 标题 40/44 LINE Seed 800；段标题 28/32；正文 17/26；标签 17 大写 0.08em；数字面 17 |
| 色板 | 满宽出血到安全区；色混 8% 纸色；裁切数字同色 90%，字号 120–160，超出板边裁切 |
| 轮廓与 pill | 1.5px 软化轮廓；pill 高 32，内距 0 12，17px |
| 间距 | 段间 40 · 块间 24 · 行间 12；板内距 20 |
| 触控 | 所有控件 ≥ 44px；列表行整行可点 |
| 动效 | 无滚动动画；折叠展开 160ms；尊重 reduced-motion |
| 安全区 | `env(safe-area-inset-*)` 应用于顶栏、底部固定条 |
| 图片 | 仅可显示图片才出现，`max-width:100%`，附来源与许可；否则一句话 + 动作，绝不空框 |
| 颜色 | 站点自有色（sky / coral / yellow / green / teal / night），无渐变无阴影 |

## 5. 数据与 API 接入清单

| 页面 | 端点 / 来源 | 备注 |
| --- | --- | --- |
| 首页 | `src/data/status-v49.json`（年份分层、总数）、`home/lib/content.ts` | 数字来自生成清单，不手打 |
| 索引 | `GET /api/index/v1` | 已接入，不改契约 |
| 搜索 | `GET /api/search/v1`、`GET /api/search/v1/facets`、`POST /api/system-suggestions/v1`（v2 请求） | 移动端新接 |
| 对象页 | sealed projection（page.tsx） | 已接入 |
| About | `about/content.ts` + Source 内容 | 共享 lib |

## 6. 需要你决定的问题

1. 首页移动端是否保留年份分层图（十年条形版），还是只留四格数字？
2. 对象页头部色板按主题取色，还是全站统一一种色（如 sky）？
3. About 移动端把 Source 折叠进去（§4a 现行地图）还是保留独立 `/source` 移动页？
4. 对象页要不要底部固定操作条（Top · Index · View at source）？
5. 搜索移动端的筛选：底部抽屉（与索引同形）还是 ticket 内展开？
6. TRACE 在首页移动端：不可点色板 + "Desktop" pill，还是完全不出现？

## 7. 顺序与验收

按轮推进，每轮先给冻结态截图（390×844、430×932），你确认后再进入下一轮；不 stage、不 commit，除非你明确指示。

- M1 搜索接真实 API + 导航（最小风险，先把假数据清掉）
- M2 首页移动端
- M3 对象页移动端
- M4 About 移动端树（含 Source 折叠）
- M5 索引局部重设计 + 全站视觉细节收口

每轮验收：设备分流测试（移动端树不引入桌面树；`SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT = 0`）；浏览器最小字号检查 ≥ 17px；触控目标 ≥ 44px；数量与真实 API 一致（搜索、索引）；`?view=mobile` 与真实 UA 两种进入方式；截图清单登记到 `docs/qa/screenshots`。
