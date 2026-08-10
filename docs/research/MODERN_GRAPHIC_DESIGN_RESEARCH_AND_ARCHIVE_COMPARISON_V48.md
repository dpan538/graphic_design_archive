# Modern Graphic Design History：研究定位、档案比较与验证路线（v48）

- 报告日期：**2026-08-08**
- 数据基线：**v48 candidate freeze**
- 发布边界：**候选冻结，不是正式公开发布层**
- 报告性质：内部研究与产品决策文件
- 官方资料访问日期：**2026-08-08**

> 本报告评估项目当前能够支持的现代平面设计史结论、TRACE 的方法价值、数据偏差、教育与 research-extended 路线，并与其他设计档案和文化遗产研究平台进行比较。报告不改变 v48 数据、关系或冻结状态。

## 1. 执行结论

项目目前最有防御力的定位不是“最大的平面设计图库”“完整的全球设计史”或“自动发现影响谱系”，而是：

> **一个版本化、权利敏感、证据受限、禁止自动推断的现代平面设计史研究索引。它不仅展示对象，也展示每一条关系如何形成、受什么限制，以及如何返回原始来源。**

推荐英文定位：

> **An evidence-bounded, rights-aware research index for modern graphic design history.**

项目可以进一步提出的方法性命题是：

> **现代平面设计史不是一条单一的风格谱系，而是一套由对象、媒介、流通、记录机构、元数据语言、权利制度、数字化政策和保存条件共同塑造的证据生态。**

这一定义比“复杂关系图”更接近真正的科研贡献。地铁图、树图、地图、圆形系统或动画本身不是学术创新；只有当它们帮助使用者区分来源事实、规范化描述、项目分类、不确定状态与历史解释时，才构成方法贡献。

当前应将项目描述为“**具有差异化潜力的可审计设计史研究基础设施**”，而不是已经被证明独有或领先的科研成果。其新颖性仍需通过文献比较、专家复核、关系准确率实验和用户研究验证。

## 2. v48 冻结身份与计数口径

v48 是用于 TRACE 可视化和界面验证的 candidate freeze。任何后续数据修改都必须建立新候选版本，不能原地更改冻结 JSON 或 SQLite。

| 指标 | v48 数值 | 正确解释 |
| --- | ---: | --- |
| 活跃主对象 | 15,923 | 通过当前冻结门禁并计入主层的对象 |
| 距 20,000 的缺口 | 4,077 | 扩展目标，不是科研质量指标 |
| TRACE 节点 | 97,889 | SQLite 图中的全部证据与结构节点 |
| **Total graph edges** | **255,695** | 全图边，包括研究树中的来源链、结构和辅助图边 |
| **Active-object relation memberships** | **126,822** | 直接映射到活跃对象、供 20 种公开关系统计使用的 membership |
| 活跃研究树 | 30 | 研究分组结构，不等于 30 条历史谱系 |
| Source verified | 12,952 | 当前证据层级，不能等同于外部独立学术鉴定 |
| Metadata supported | 2,971 | 有对象级元数据证据但证据层级较弱 |
| Review / authority hold | 4,425 | 与活跃总数隔离，不应混入默认统计 |
| TRACE auxiliary | 11 | 摄影/版画辅助旁支，`countEligible=false` |
| `influenced_by` | 0 | 没有达到显式文献证据阈值的历史影响边 |
| 保存的审计样本 | 200 / 200 pass | 冻结门禁结果，不等于总体准确率 100% |

### 2.1 两种边数必须永久分开

`255,695` 和 `126,822` 不能在界面、论文或新闻材料中都被简称为“Evidence relations”。推荐固定术语：

- **Total graph edges / 全部图边：255,695**；
- **Active-object relation memberships / 活跃对象关系 membership：126,822**。

活跃对象 membership 的关系族分布如下：

| 关系族 | 数量 | 占 126,822 |
| --- | ---: | ---: |
| Medium / context | 79,206 | 62.45% |
| Source / provenance | 31,288 | 24.67% |
| Time / place | 16,328 | 12.87% |
| Historical influence | 0 | 0% |

这些比例表示当前索引中记录关系的构成，不表示媒介、来源或地点在真实设计史中的重要性。

### 2.2 冻结证据

- Candidate JSON SHA-256：`b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`
- SQLite SHA-256：`ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`
- SQLite integrity：`ok`
- 冻结审计：55 PASS，0 HOLD
- 活跃层 unresolved geography：0
- authority-uncertain leakage：0
- active TRACE unlinked：0
- filename-as-title：0
- 历史影响边：0

详细冻结身份与门禁以 [v48 freeze receipt](../capture/PREFREEZE_CANDIDATE_V48_FREEZE_RECEIPT.md) 和 [v48 frozen baseline](../capture/PREFREEZE_CANDIDATE_V48_FROZEN.md) 为准。本报告日期统一为 2026-08-08；冻结动作的原始日期和 commit 以 receipt 为唯一事实来源。

## 3. 项目对现代平面设计史能够形成的总结

### 3.1 设计史首先是一种证据组织问题

当前语料能够连接对象、年代、地点、媒介、创作者、馆藏、来源和权利状态。这表明现代平面设计史不能只由少数风格标签、名家或代表图像组成；它同时由生产、流通、收藏、描述、数字化和再利用条件构成。

### 3.2 档案可见性不等于历史重要性

当前数据中的高频地区、年代、媒介和来源，首先反映馆藏供应、API 可用性、图片权利、编目密度和项目采集路径。它们可以支持“档案如何塑造可见历史”的研究，却不能直接证明某地区或年代的设计活动更重要。

### 3.3 记录关系不等于历史影响

`documented_by`、`associated_with_place`、`dated`、`created_by`、`part_of_collection`、`has_medium` 等关系回答的是不同的证据问题。共享地点、年代、媒介、视觉形式或集合都不足以产生 `influenced_by`。

v48 的零影响边是一项方法边界：它意味着系统没有越过证据阈值，而不是声称历史中不存在影响。

### 3.4 缺失与排除属于研究结果

Review、authority hold、未地图化地区、IMG00、source-hosted 图像、权利不确定和辅助旁支不应被隐藏。它们能够帮助研究者区分：

- 历史对象不存在；
- 对象没有被收藏；
- 对象没有被数字化；
- 对象存在但权利不允许展示；
- 来源存在但元数据不足；
- 当前项目尚未完成采集或权威控制。

这些状态不能互相替代。

## 4. TRACE 的已实现贡献与尚未证明的创新

### 4.1 已实现的方法贡献

1. **对象级回源**：关系可返回对象页、证据 URL 或原始馆藏页。
2. **类型化关系**：不同 predicate 具有各自的证据要求、允许陈述和禁止推断。
3. **显式反推断协议**：不从相似、共现、时间、地点或媒介自动建立影响。
4. **认识状态分层**：active、review/authority hold、auxiliary 不合并计数。
5. **权利与对象分离**：有对象记录不等于有本地图像展示权。
6. **版本冻结与哈希**：研究结论可以绑定到具体 JSON、SQLite、commit 和生成资产。
7. **同一证据模型的多视图**：对象、时间地理、媒介语境、来源树和表格降级使用同一冻结语义。

关系协议见 [TRACE taxonomy](../../frontend/src/components/archive/trace/trace-taxonomy.ts)，可视化边界见 [TRACE visualization decision](../system/TRACE_VISUALIZATION_V48_DECISION.md)。

### 4.2 尚不能当作已证明创新的内容

- 关系图、地铁图、时间轴、地球仪或径向图本身；
- 15,923 的对象规模；
- “全球”“演化”“扩散”类视觉叙事；
- 搜索、筛选或地图聚合的常规功能；
- 尚未经过用户研究的 no-inference 界面；
- 尚未与文化遗产本体互操作的自定义 TRACE vocabulary；
- 没有同行评议和双人编码验证的关系准确率。

因此不能使用“首个设计史关系图”“首个全球设计地图”或“已经重建设计影响网络”等宣传语。

## 5. 数据偏差与解释限制

| 偏差维度 | 当前证据 | 可能成因 | 可以研究 | 不可直接解释为 |
| --- | --- | --- | --- | --- |
| 来源集中 | 前五大来源 11,210 个对象，占 70.4% | 大型 API、开放元数据、批量可得性 | 馆藏供应如何塑造语料 | 这些机构收藏了全球最重要的设计 |
| 媒介集中 | `graphic object / other` 与 `poster` 合计 14,755，占 92.7% | 海报馆藏、分类便利、映射规则 | 编目词汇如何压缩媒介差异 | 平面设计历史有 92.7% 是海报/泛化对象 |
| 年代集中 | 1960 年以后 10,211，占 64.1%；1980 年代最高 | 数字化、保存、权利与来源批次 | 不同来源的年代可见性 | 1960 年后设计活动真实占比最高 |
| 地域集中 | 英国 3,256，占 20.45%；`Other regions` 5,901 | 来源结构、规范化粒度和聚合策略 | 地名标准化与来源地理偏差 | 英国在全球设计史中占 20.45% |
| Tree 集中 | 最大三个 tree 含 11,444 个 membership，占 71.9% | 研究包结构与来源规模 | 研究树如何组织注意力 | 三个主题代表 71.9% 的设计史 |
| 地图粒度 | 15,569 可按规范化地区映射；354 有意不精确映射 | Global/transnational、宽泛地区、历史地名 | 地理不确定性 | 点是生产坐标或真实传播路线 |
| 关系构成 | Medium/context 占 active memberships 62.45% | 对象类型与媒介字段密集 | 元数据结构差异 | 媒介是历史因果主轴 |
| 内部对象路由 | 约 2,585 个活跃 root 有当前项目对象页，其余主要返回官方来源 | 当前公开 surface 覆盖有限 | source-return 与内部阅读体验 | 每个对象已有同等深度的本地研究页 |
| 权利可见性 | 部分对象仅 source-hosted 或无本地图像 | 权利、服务稳定性、反盗链 | 可见性偏差 | 无图对象不重要或不存在 |
| 抽样验证 | 200/200 pass，且 18 条 LOC 修复被强制纳入 | 冻结门禁设计 | 已知高风险修复是否通过 | 对总体作 100% 准确率推断 |

### 5.1 特别严重的公开指标漂移

当前 About 页面硬编码 `active_source_count = 104` 和一组 coverage 百分比，而 v48 SQLite 的 distinct `source_name` 为 272；现有 coverage 文档又出现 18,312 等不同数字。它们可能分别在统计 provider、source record、source locator、captured row 或旧候选，但公开名称没有定义单位。

在以下项目统一之前，任何 source coverage 百分比都不应作为科研结论：

- 数据版本与 candidate/release 状态；
- 分子、分母和统计单位；
- SQL 或生成规则；
- 输入文件哈希；
- 生成时间；
- 旧指标的废止状态。

建议所有公开统计由一个版本化 `research-metrics.json` 自动生成，About、TRACE、Search、导出和论文表格只能读取这一来源。

### 5.2 可视化语言也可能制造过度推断

`Evolution`、`Development`、`Expansion`、`diffusion` 等标题即使附有免责声明，也容易让使用者把“当前语料随年代的变化”理解为真实历史演化。建议统一使用：

- `Recorded corpus coverage field`；
- `Archive observations through time`；
- `Time × geography distribution of indexed objects`。

未知的新关系也不应默认归入 `medium_context/documented`；未来候选版本应 fail closed，进入 review，直到 taxonomy 注册和审计完成。

## 6. 可声称与不可声称

| 可以公开声称 | 需要限定或不可声称 |
| --- | --- |
| v48 是包含 15,923 个活跃对象的 candidate freeze | v48 是正式发布或最终数据库 |
| 每个活跃对象都有已索引的 TRACE 证据路径 | 每条边都是历史影响或对象之间的真实传播 |
| 系统区分来源事实、规范化、分析、review 和未知 | 项目已经消除编目偏差或 authority 问题 |
| 系统可以研究当前语料的来源、年代、地域、媒介和权利结构 | 当前计数代表世界设计生产总量或重要性 |
| 当前没有达到证据要求的 `influenced_by` 边 | 历史上没有发生影响，或项目已重建影响谱系 |
| 地理视图展示对象级地区陈述的聚合 | 地图点是精确制作坐标、移动或扩散路径 |
| TRACE auxiliary 是不计数的语境旁支 | 摄影、版画或未来动画已被升级为主设计对象 |
| 冻结门禁和 200 个保存样本全部通过 | 数据整体准确率或代表性为 100% |
| 项目具有形成可审计研究基础设施的潜力 | 项目已被证明是独有、首创或领先平台 |

20,000 只能作为扩展容量目标，不能成为学术质量 KPI。任何新增对象都不能以降低对象级年份、地理、authority、图片、权利和 TRACE 标准为代价。

## 7. 设计档案与研究平台比较

下表比较的是不同机构的研究能力，不把它们简单视为商业“竞品”。

| 档案或平台 | 核心优势 | 教育 / research 模式 | MGD 应学习 | MGD 可形成的差异 |
| --- | --- | --- | --- | --- |
| [People’s Graphic Design Archive](https://peoplesgdarchive.org/about) | 众包、包容性历史；接收成品、过程材料、信件、文章与口述内容 | 社区发现、研究、贡献；提供 [Resources](https://peoplesgdarchive.org/resources) | 社区参与、去中心化采集、贡献者治理 | 对象级证据边、权利状态、冻结门禁与 no-inference 协议 |
| [AIGA Design Archives](https://designarchives.aiga.org/) | 自 1924 年以来的专业设计与竞赛档案；形式发现门槛低 | 按年份、颜色、格式、关键词和策展集合浏览 | 快速视觉发现、清楚的对象入口 | 解释专业正典和评选机制如何塑造可见历史，而不是复制正典 |
| [Letterform Archive Online Archive](https://letterformarchive.org/online-archive/) | 实物、图像、字体和印刷细节深度高 | [Education](https://letterformarchive.org/education/) 包括导览、工作坊、课程与研究访问 | 高质量对象阅读、专家教学、物质性描述 | 跨机构比较、来源审计、权利与不确定性教学；不能宣称取代实物研究 |
| [RIT Graphic Design Archive](https://www.rit.edu/carycollection/graphic-design-archive) / [Vignelli Center Research](https://www.rit.edu/vignellicenter/research) | 过程材料、设计师档案和美国现代主义教学资源深 | 实物研究、设计教育、实践回应 | 过程材料和设计劳动的保存 | 研究机构与设计师正典如何形成，并连接跨机构对象证据 |
| [University of Brighton Design Archives](https://blogs.brighton.ac.uk/brightondesignarchives/) | 档案层级、研究合作、设计史与博士训练 | 档案研究、数字人文、研究合作 | 语义结构、研究伙伴关系和研究者培养 | TRACE 的权利层、冻结审计、对象地理和反推断组合；不能把“关系网络”称为首创 |
| [Cooper Hewitt API](https://apidocs.cooperhewitt.org/api-home/) | 开放接口、facet、对象元数据和技术文档 | 数据探索、开发者复用 | 稳定公共 API、字段定义、开放数据实践 | 跨来源证据统一和不确定状态；当前项目在 API 成熟度上落后 |
| [Cooper Hewitt Open Source](https://www.cooperhewitt.org/open-source-at-cooper-hewitt/) | CC0 数据和开源实践边界较清楚 | 可复用数据与代码 | 许可、版本和开发者沟通 | 对第三方对象、图片和项目原创数据实行更细的权利分层 |
| [MoMA Collection Dataset](https://github.com/MuseumofModernArt/collection) | 版本化 CSV/JSON、CC0 元数据、引用与局限说明，图片权利分离 | 可下载数据研究和复算 | 公开数据发布、更新说明、局限与引用 | 关系级 provenance 和多来源图模型；当前项目缺 DOI 与正式数据许可 |
| [V&A Developer Platform](https://developers.vam.ac.uk/) | 搜索、API、IIIF、notebook 和方法警示完整 | [API docs](https://api.vam.ac.uk/docs) 与 [data exploration notebooks](https://developers.vam.ac.uk/notebooks/data-explorations/) | 开发者体验、可复现 notebook、API/IIIF 互操作 | 明确记录跨来源关系如何被允许或禁止；V&A 仍是技术基准而非弱竞品 |
| [Designing Britain](https://www.vads.ac.uk/customizations/collection/DCADB/pages/html/about.html) | 将数字对象组织成高等教育学习模块 | 理论、对象与项目 brief 结合 | 把档案数据变成明确学习任务 | 可用实时证据路径替代固定模块，但必须先形成教学设计 |
| [Smithsonian Learning Lab](https://learninglab.si.edu/about) | Discover–Create–Share，支持建立与分享集合 | 教师备课、个性化学习和课堂集合 | 研究集、教师工具和可分享学习包 | 近期先做 evidence packet，不必立即扩张为完整 LMS |

### 7.1 比较结论

MGD 不应在以下维度声称领先：

- 馆藏规模和机构权威；
- 原始实物与高分辨率图像；
- 公共 API、IIIF 和 notebook；
- 社区贡献机制；
- 完整课程、教师工具和实物教学；
- 正式数据许可、DOI 与长期保存。

可以防御的差异化来自以下能力的组合，而不是任何单项功能：

1. 跨机构对象级回源；
2. 类型化 TRACE 证据边和明确 no-inference；
3. 主对象、review、authority hold、auxiliary 分层；
4. candidate freeze、哈希、SQLite、样本和门禁；
5. 同一证据模型驱动对象、来源、媒介和时间地理视图；
6. 将证据缺席、图片权利和不可推断状态公开显示。

## 8. Education 与 research-extended 定位

项目方法论明确指出它不是 textbook、course 或 museum education platform。因此教育功能应作为 **evidence lab / teaching extension**，而不是重新定义整个项目。

### 8.1 移动端初次用户

移动端的首要任务是快速展示研究价值，不是一次呈现全部方法文本：

1. 0–15 秒：看见一个清楚的数据现象，以及“candidate freeze / evidence relationships / no inferred influence”。
2. 15–60 秒：触摸一个节点，看到对象标题、关系类型、证据状态和一句解释。
3. 1–3 分钟：展开一条证据边，理解来源记录了什么、项目没有推断什么。
4. 后续：进入对象、来源或复制引用。

About、来源长列表、方法与权利说明在移动端默认折叠。触摸优先于 hover，视觉复杂度可以保留，但信息必须按上下区域、逐层进入和 reduced-motion 路径组织。

### 8.2 学生和一般研究者

核心学习任务：

- 区分历史对象、馆藏记录和本项目的规范化表面；
- 返回对象的直接来源；
- 判断地点是对象地理、流通地点、机构地点还是创作者国籍；
- 区分 documented、analytical、review、unknown；
- 比较两个来源对同类对象的标题、媒介和创作者描述；
- 生成包含冻结版本和权利状态的引用。

### 8.3 桌面端高级研究者

目标工作流：

> 研究问题 → 搜索/筛选 → 聚合观察 → 对象 TRACE → 精确边账本 → 对象页 → 原始来源 → 引用/导出 → 保存可复现查询

现有系统覆盖了前七步的一部分；保存研究集、查询 manifest、逐对象/逐边引用、CSV/JSON 导出和 notebook 尚未形成闭环。

### 8.4 教师、图书馆员和档案工作者

应优先提供：

- 5–15 个对象组成的教学证据包；
- 可复用研究问题模板；
- 显示权利和不确定性的课堂材料；
- 对象、来源、关系、限制和引用清单导出；
- 比较不同机构编目词汇的活动。

### 8.5 五段式 TRACE 证据卡

每条关系应固定展示：

1. 来源记录；
2. 原始字段或证据文本；
3. 规范化关系；
4. 允许陈述；
5. 禁止推断。

这可直接把现有 taxonomy 中的 `evidenceRequirement`、`allowedAssertion` 和 `prohibitedInference` 转化为教学界面。

### 8.6 建议课程模块

| 模块 | 学习任务 | 可观察产出 |
| --- | --- | --- |
| 对象不是记录 | 比较对象、馆藏记录与项目表面 | 标出三者边界 |
| 返回来源 | 从聚合图追溯到官方对象页 | 完整来源路径 |
| 元数据与正典 | 比较来源的分类、标题和创作者字段 | 一份差异表 |
| 地理证据 | 区分制作、流通、馆藏和国籍 | 正确的地点主张 |
| 图片权利 | 比较 IMG00–IMG04 | 解释为何 URL 不等于展示权 |
| TRACE 与反推断 | 判断哪些关系成立 | 不制造虚假 influence |
| 数据偏差 | 分析来源、媒介、年代和地区集中 | 一段有边界的结论 |
| Research dossier | 选取 5–10 个对象形成论证 | 对象、边、来源、限制和引用齐全 |

该框架与 [ACRL Framework for Information Literacy](https://www.ala.org/acrl/standards/ilframework) 中的 contextual authority、information creation、research as inquiry、scholarship as conversation 和 strategic exploration 相容。

## 9. 研究问题

### 9.1 档案与正典

- 数字化政策和图片权利如何改变可见的设计史正典？
- 大型馆藏 API 是否会在聚合项目中获得不成比例的解释权？
- 哪些历史空白来自未收藏、未数字化、权利限制或项目采集不足？

### 9.2 元数据与分类

- 不同机构如何定义 poster、print、publication、graphic object 和 digital object？
- 跨馆归一化在哪些位置隐藏了原始分类制度差异？
- 同一对象的原始字段、规范化字段和研究分类之间有多大偏差？

### 9.3 时间与地理

- 对象地点、制作地点、流通地点、创作者地点和馆藏地点如何系统性分离？
- 当前年代和地区峰值在 provider-balanced 重采样后是否仍然存在？
- 历史地名、跨国对象和 transnational records 应如何显示而不伪造坐标？

### 9.4 TRACE 与使用者理解

- 显示“禁止推断”能否降低用户把共现或相似误判为影响的比例？
- 聚合视图、对象 TRACE 和来源页之间的往返能否提高引用准确率？
- 图形复杂性在哪个水平开始妨碍证据理解？

### 9.5 权利与可见性

- source-hosted、开放图像和无图记录在浏览、选择和引用上是否受到不同关注？
- 图片可见性是否会让学生高估某些对象的历史重要性？

## 10. 可复现实验路线

### Phase 0：科研一致性修复

1. 统一所有公开计数单位和术语。
2. 从冻结 manifest 自动生成 About、TRACE 和引用统计。
3. 将 `Evolution / Expansion` 改为 corpus coverage / archive observations。
4. 未登记 relation fail closed 到 review。
5. 为 candidate freeze、正式 release、代码、元数据和第三方图片建立清楚的引用与许可边界。

### Phase 1：关系和地理准确率

#### 关系审计

- 对 20 种关系进行分层抽样，目标约 600 条；稀有类型采用全量审核。
- 两位研究者独立判断 evidence URL、field、allowed assertion、confidence 和 prohibited inference。
- 报告 precision、Cohen’s κ 或 Krippendorff’s α。

#### 地理审计

- 按来源、地区和年代抽取约 400 个对象。
- 比较原始对象地点、规范化地区、历史地名映射与地图粒度。
- 单独检测馆藏所在地、搜索词和创作者国籍误用。

### Phase 2：语料偏差和稳健性

#### 来源移除实验

逐一移除主要 provider，重算：

- 地区 × 年代；
- medium；
- TRACE tree 排名；
- Jensen–Shannon divergence；
- Spearman rank correlation。

#### 平衡重采样

按地区、年代、来源族设置等额或加权配额，并进行 bootstrap。平衡后消失的峰值只能被解释为语料/来源效应。

#### 权利可见性实验

比较 IMG00、source-hosted 和开放图像对象的点击率、停留时间、保存率与引用率，测量图片权利如何影响历史注意力。

### Phase 3：搜索、教育与 HCI

#### 搜索金标准

建立跨语言、音译、历史地名、来源、权利和 relation 查询集，报告：

- Recall@50；
- nDCG@10；
- active/review/auxiliary 泄漏率；
- 对象和来源返回成功率；
- relation code 与自然语言查询一致性。

#### No-inference 用户实验

比较普通对象页、只有关系图的界面和带五段式证据卡的 TRACE 界面。任务包括寻找来源、判断地点证据和识别是否存在影响关系。主要结果：

- 正确率；
- 完成时间；
- 错误因果推断率；
- 自信度与正确率校准。

#### 教学研究

用 evidence-lab 模块进行前测/后测，评估学生区分 evidence、normalization、analysis 和 unknown 的能力。

### Phase 4：可复现发布

1. 从冻结 commit 和 LFS 对象进行 clean-room 重建。
2. 核对 JSON、SQLite、580 个 read-model 资产和 manifest 哈希。
3. 建立 DOI、`CITATION.cff`、`codemeta.json` 和正式 release notes。
4. 发布可执行 notebook、数据字典、查询 manifest 和偏差说明。
5. 定期检测 source URL 和 IIIF 路由存活率。

设计仍在迭代期间，视觉验证应使用固定、分层且不超过 **50 个页面/路由** 的代表性 fixture；不应为每一轮设计调整重新全量编译 15,923 个对象页。该 fixture 至少覆盖 active、review、auxiliary、无图、source-hosted、长标题、多语言和地图不可精确映射状态。

## 11. 评估指标

不得再用一个总 coverage 分数替代不同质量维度。

| 维度 | 推荐指标 |
| --- | --- |
| 数据完整性 | 冻结哈希、SQLite integrity、孤立节点、空 evidence、authority 泄漏、层级混入 |
| 证据质量 | relation precision、双人编码一致性、证据字段准确率、来源 URL 存活率 |
| 地理质量 | 对象地理 precision、历史地名覆盖、故意未地图化率、错误地点来源 |
| 代表性与偏差 | provider Top-k、HHI、地区/年代/媒介熵、来源移除后的分布变化 |
| 搜索 | Recall@50、nDCG@10、跨语言表现、层级泄漏、来源返回率 |
| 教育 | 证据状态识别率、错误影响推断率、引用完整率、前后测改善 |
| 可复现性 | clean-room 重建成功、资产哈希一致、查询 manifest 完整度 |
| 无障碍 | WCAG AA、键盘路径、屏幕阅读、非颜色编码、reduced motion、低数据模式 |
| 性能 | atlas 首载、单 shard 加载、触摸响应、动画帧稳定性、50-route 验收时间 |

建议未来验收目标，而非当前成绩：

- 90% 用户在三次操作内返回正确对象来源；
- 85% 学习者正确区分 documented、analytical、review 和 unknown；
- 错误把共现/相似判断为历史影响的比例低于 5%；
- 90% 导出引用包含对象 ID、来源、URL、冻结版本和权利状态；
- 移动端首次打开到第一次证据节点交互中位时间低于 60 秒；
- 桌面端完成“筛选—对象—边—来源—引用”中位时间低于 3 分钟。

## 12. 论文方向

### 12.1 方法论文

**Evidence Without Genealogy: An Audit-Bounded TRACE Model for a Distributed Graphic Design Archive**

结构：

1. 聚合界面如何压平来源、权利和不确定性；
2. 类型化关系及 no-inference 协议；
3. v48 candidate freeze、分层和 read-model 流程；
4. relation 与地理准确率；
5. 用户能否避免错误因果推断；
6. 对设计史、档案学和数字人文的意义。

### 12.2 档案与偏差论文

**The Archive Is Not the History: Measuring Provider, Rights and Cataloguing Bias in a Modern Graphic Design Index**

使用来源移除、平衡重采样、权利可见性和编目词汇差异实验。

### 12.3 设计史论文

研究数字化、馆藏政策、元数据和图像权利如何塑造“可被看见的现代平面设计史”，避免把语料数量写成设计生产事实。

### 12.4 HCI / 可视化论文

评估三视图、对象回溯、证据卡、不确定性与禁止推断呈现对理解准确率和误判率的影响。

### 12.5 教育论文

**Teaching Graphic Design History Through Provenance**：测试 evidence lab 是否改善视觉素养、信息素养、引用准确度和因果判断。

## 13. 展览与公共叙事方向

推荐主题：

> **How the Archive Makes Design History Visible / 档案如何使设计史可见**

建议顺序：

1. **Object**：我们看见了什么；
2. **Source**：谁保存、描述并数字化了它；
3. **Relation**：证据允许连接到哪里；
4. **Absence**：哪些内容因权利、语言、收藏和数字化不可见；
5. **No inferred influence**：相关、相似和共现不等于影响；
6. **Return**：返回原始馆藏并完成引用。

展览可以使用来源移除前后对照、权利不可见墙、不可精确地图化对象、review 队列和同一对象在不同机构中的分类差异。不要以“从 1800 到现在的全球扩散动画”作为主叙事，除非另有历史来源支持传播路径。

## 14. 互操作、伦理、引用与长期基础设施

### 14.1 互操作路线

- 以 [Linked Art](https://linked.art/model/) 对接文化遗产对象模型；
- 以 [W3C PROV-O](https://www.w3.org/TR/prov-o/) 表达采集、转换、审计和生成 provenance；
- 以 [IIIF Presentation API 3.0](https://iiif.io/api/presentation/3.0/) 提供可互操作对象、图像和序列；
- 发布字段字典、mapping decision 和转换损失说明，而不是只导出扁平 CSV。

### 14.2 伦理边界

- 继续禁止把馆藏地点、搜索词或创作者国籍替代对象地理；
- 对 Indigenous、殖民、政治宣传和社区材料同时参考 [CARE Principles](https://www.gida-global.org/careprinciples)，而不只追求 FAIR；
- [Local Contexts Labels](https://localcontexts.org/labels/about-the-labels/) 只能在相关社区决定后使用，项目不能自行分配；
- 社区纠错、撤回和敏感材料说明应进入长期计划。

### 14.3 无障碍边界

以 [WCAG 2.2](https://www.w3.org/TR/WCAG22/) AA 为最低标准：

- 图形不能只靠颜色；
- 完整键盘路径与可见焦点；
- 屏幕阅读标签和等价表格；
- 移动端触摸目标与触摸手势替代路径；
- `prefers-reduced-motion`；
- 低数据与无图形模式；
- 移动正文不低于 16px，桌面研究界面不低于 18px。

### 14.4 引用与许可

现有 APA、MLA、IEEE 项目级复制引用是起点，但正式科研发布仍需：

- 在引用中明确 `v48 candidate freeze`；
- 每对象、每边和每个查询的可复制引用；
- DOI 或其他持久标识符；
- `CITATION.cff` 与 `codemeta.json`；
- 区分代码许可、项目原创元数据许可和第三方对象/图片权利；
- 不把 GitHub URL 当作永久 DOI；
- 不将第三方图片权利用仓库许可证一并覆盖。

每次研究导出至少包含：

```text
freeze_version
candidate_or_release_status
git_commit
candidate_json_sha256
sqlite_sha256
query_and_filters
selected_object_ids
selected_edge_ids
generated_at
software_version
rights_and_uncertainty_notes
```

## 15. 发布前优先级

### P0：科研一致性阻断项

- 统一 255,695 total graph edges 与 126,822 active-object memberships 的名称；
- 清除 About 和 coverage 文档的统计单位冲突；
- 全站明确 v48 是 candidate freeze；
- 删除或重命名暗示真实演化、扩散和影响的标题；
- 未登记 relation fail closed；
- 保证 review、authority hold 和 auxiliary 不进入主层统计。

### P1：把潜在差异变成经过验证的贡献

- 完成双人 relation audit；
- 完成地理审计和 provider-ablation；
- 建立搜索金标准；
- 进行 no-inference 用户实验；
- 公开方法、抽样与误差，而不只公开通过门禁的结果。

### P2：Research-extended 闭环

- 五段式证据卡；
- 每对象/每边引用；
- 保存查询和研究集 manifest；
- evidence-lab 课程包；
- CSV/JSON/notebook 导出；
- “Other regions”可展开并保留原始地理粒度。

### P3：正式研究基础设施

- DOI、许可和正式 release；
- Linked Art / PROV-O / IIIF 对接；
- 社区纠错、撤回与贡献治理；
- 可复现 notebook 与长期 URL 健康监测；
- 外部设计史、档案学、图书馆学和 HCI 同行评议。

## 16. 最终定位

项目真正的竞争力不应被总结为“有三张复杂图”，而应被总结为：

> **把现代平面设计史的视觉探索约束在对象级来源、权利状态、明确的不确定性、分层审计和可复算版本之内，并使用户能够看见一条关系为什么成立、为什么不能被升级为历史影响。**

如果后续实验能够证明这种界面显著提高来源返回、引用准确度和证据判断，同时降低错误因果推断，那么项目才可以从“有差异化潜力的研究基础设施”升级为具有实证支持的方法贡献。

## 17. 主要官方参考链接

以下官方页面均按本报告统一访问日期 2026-08-08 记录：

- People’s Graphic Design Archive: https://peoplesgdarchive.org/about
- PGDA Resources: https://peoplesgdarchive.org/resources
- AIGA Design Archives: https://designarchives.aiga.org/
- Letterform Archive Online Archive: https://letterformarchive.org/online-archive/
- Letterform Archive Education: https://letterformarchive.org/education/
- RIT Graphic Design Archive: https://www.rit.edu/carycollection/graphic-design-archive
- Vignelli Center Research: https://www.rit.edu/vignellicenter/research
- University of Brighton Design Archives: https://blogs.brighton.ac.uk/brightondesignarchives/
- Cooper Hewitt API: https://apidocs.cooperhewitt.org/api-home/
- Cooper Hewitt Open Source: https://www.cooperhewitt.org/open-source-at-cooper-hewitt/
- MoMA Collection Dataset: https://github.com/MuseumofModernArt/collection
- V&A Developer Platform: https://developers.vam.ac.uk/
- V&A API Documentation: https://api.vam.ac.uk/docs
- V&A Data Exploration Notebooks: https://developers.vam.ac.uk/notebooks/data-explorations/
- Designing Britain: https://www.vads.ac.uk/customizations/collection/DCADB/pages/html/about.html
- Smithsonian Learning Lab: https://learninglab.si.edu/about
- ACRL Framework for Information Literacy: https://www.ala.org/acrl/standards/ilframework
- Linked Art Model: https://linked.art/model/
- W3C PROV-O: https://www.w3.org/TR/prov-o/
- IIIF Presentation API 3.0: https://iiif.io/api/presentation/3.0/
- CARE Principles: https://www.gida-global.org/careprinciples
- Local Contexts Labels: https://localcontexts.org/labels/about-the-labels/
- WCAG 2.2: https://www.w3.org/TR/WCAG22/

## 18. 项目内部证据文件

- [Methodology v0](../methodology/Methodology_v0.md)
- [Coverage Assessment](../system/COVERAGE_ASSESSMENT.md)
- [Regional Coverage Framework](../system/REGIONAL_COVERAGE_FRAMEWORK.md)
- [Surface Field Contract](../system/SURFACE_FIELD_CONTRACT_v1.md)
- [TRACE Visualization Decision](../system/TRACE_VISUALIZATION_V48_DECISION.md)
- [TRACE Visualization Implementation](../system/TRACE_VISUALIZATION_V48_IMPLEMENTATION.md)
- [TRACE Reference Study](../system/TRACE_VISUALIZATION_V48_REFERENCE_STUDY.md)
- [v48 Frozen Baseline](../capture/PREFREEZE_CANDIDATE_V48_FROZEN.md)
- [v48 Freeze Receipt](../capture/PREFREEZE_CANDIDATE_V48_FREEZE_RECEIPT.md)
- [TRACE taxonomy](../../frontend/src/components/archive/trace/trace-taxonomy.ts)
- [TRACE type contract](../../frontend/src/components/archive/trace/trace-types.ts)
