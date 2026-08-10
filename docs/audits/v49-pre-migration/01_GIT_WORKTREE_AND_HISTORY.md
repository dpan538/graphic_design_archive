# A1 — Git、worktree、history、LFS 与仓库治理审计

## 审计声明

- **独立范围：** Git/worktree/branch/remote-tracking refs/ancestry、Git LFS、Git 对象规模、历史大 blob、当前树重复 blob、tracked generated evidence、许可证与第三方内容边界、公共仓库治理风险。
- **唯一输出：** `docs/audits/v49-pre-migration/01_GIT_WORKTREE_AND_HISTORY.md`。
- **审计 worktree：** `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`。
- **受保护 worktree：** `/Users/jarlgiovanni/Desktop/modern_GD_history`；本审计只读取 Git 元数据和路径状态，没有修改其文件、索引或 refs。
- **状态：PARTIAL。** refs、worktree、LFS、对象大小和当前重复 blob 清点完成；完整 `git fsck --unreachable` 因长期无输出按子任务健康规则中止，历史 secret-path 命令也不能证明内容安全。两个缺口均明确移交最终 Git/security gate，未伪装为 PASS。

## Evidence commands

以下均为只读意图命令；没有读取或打印 secret 值。`repo` 与 `main` 是任务专用变量，不使用 `$HOME` 或未解析删除目标。

```sh
repo=/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform
main=/Users/jarlgiovanni/Desktop/modern_GD_history

git -C "$repo" rev-parse --show-toplevel
git -C "$repo" rev-parse HEAD
git -C "$repo" branch --show-current
git -C "$repo" status --short --branch
git -C "$repo" remote -v
git -C "$repo" worktree list --porcelain
git -C "$repo" merge-base --is-ancestor 0404c7f96f9189f576c4c5b1368061e4082e436b HEAD

git -C "$main" rev-parse HEAD
git -C "$main" diff --name-status HEAD | shasum -a 256
git -C "$main" diff --cached --name-only | wc -l

git -C "$repo" count-objects -vH
git -C "$repo" for-each-ref --sort=refname \
  --format='%(refname)%09%(objectname)%09%(upstream:short)%09%(upstream:track)' \
  refs/heads refs/remotes refs/tags
git -C "$repo" branch --all --verbose --verbose
git -C "$repo" tag --list --format='%(refname:short)%09%(objectname)%09%(creatordate:iso8601)'
git -C "$repo" rev-list --left-right --count main...origin/main
git -C "$repo" rev-list --left-right --count \
  refactor/v49-data-platform...origin/refactor/v49-data-platform

git -C "$repo" rev-list --objects --all |
  git -C "$repo" cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)'
git -C "$repo" ls-tree -r -l HEAD

git -C "$repo" lfs version
git -C "$repo" lfs ls-files --all --long
git -C "$repo" lfs ls-files --long
git -C "$repo" log --all --oneline -- .gitattributes
git -C "$repo" show HEAD:.gitattributes
git -C "$repo" check-attr -a -- .

git -C "$repo" status --porcelain=v2 --branch --untracked-files=normal
git -C "$repo" ls-files --others --exclude-standard | wc -l
git -C "$repo" ls-files -ci --exclude-standard | wc -l
git -C "$repo" ls-files
git -C "$repo" grep -n -i -E \
  'third[- ]party|copyright|license|licence|attribution|rights' -- \
  LICENSE FRONTEND_DESIGN_LICENSE.md README.md ARCHITECTURE.md docs/adr docs/architecture
```

两条非成功检查也属于证据，不应从回执中省略：

```sh
# 对象库约 4.4 GiB；连续数分钟无输出后按健康规则 Ctrl-C，exit 130。
git -C "$repo" fsck --no-reflogs --unreachable --no-progress

# lfs status 内部尝试 update-index --refresh；sandbox 拒绝，exit 128，索引未改变。
git -C "$repo" lfs status

# 只读残留进程检查被 sandbox 拒绝；主任务必须在最终阶段运行授权的全局扫描。
ps -axo pid=,etime=,state=,command= | rg 'git fsck|git-fsck'
```

历史敏感路径枚举误含宽 pathspec `.`，因此只得到全历史路径列表，不能用来声称“无 secret”；没有打开任何命中文件或输出变量值。该失败结论移交 A10：

```sh
git -C "$repo" log --all --name-only --pretty=format: -- . \
  ':glob:**/.env*' ':glob:**/*secret*' ':glob:**/*credential*' \
  ':glob:**/*.pem' ':glob:**/*.p12' ':glob:**/*.pfx' ':glob:**/*.key'
```

## Measured results

### 1. 固定分支、远端跟踪与 ancestry

| 测量 | 结果 | 状态 |
|---|---|---|
| 本地 HEAD | `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720` | PASS |
| 当前 branch | `refactor/v49-data-platform` | PASS |
| 本地 remote-tracking ref | `origin/refactor/v49-data-platform` 同为 `f076ca3…` | PASS |
| target branch divergence | `0 0` | PASS |
| 冻结 checkpoint ancestry | `0404c7f96f9189f576c4c5b1368061e4082e436b` 是 HEAD 祖先，exit 0 | PASS |
| live remote SHA | 由主任务入口/收尾 `ls-remote` gate 负责；A1 没有重复网络访问 | PARTIAL（A1） |
| 初始 cleanliness | 主任务在创建 audit 文件前确认；A1 首次观察时仅见本任务并发生成的 `?? docs/audits/` | PASS（共享任务态） |

`origin` 的 fetch/push URL 均为 `git@github.com:dpan538/graphic_design_archive.git`。本地共有 9 个 branch refs、6 个实际 remote branch refs（另有 `origin/HEAD` symref）、0 个 tag。没有 release tag 可作为冻结身份；v49 架构必须继续以 immutable manifest SHA 与 release ID 为权威，不能把 branch/tag 名当内容身份。

本地 `main` 位于 `7ef26d66b6ad671fdcc5e11bfa831699a39426bc`，相对 `origin/main` 为 `0 5`，即只落后 5 个提交、没有本地独有提交。其 tracked path/status fingerprint 以 `git diff --name-status HEAD | shasum -a 256` 重算为：

```text
57ecff59270460a769b743781ecd09ca191b867201991a260785985689f6d568
```

与任务基线相同。A1 未执行 main 的 checkout、restore、add、commit、clean 或文件读取。

### 2. Worktree 总账

共发现 8 个 registered worktrees：

| path | branch / state | HEAD | 结论 |
|---|---|---|---|
| `/Users/jarlgiovanni/Desktop/modern_GD_history` | `main` | `7ef26d6` | 受保护脏 main；KEEP_ACTIVE，禁止触碰 |
| `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform` | `refactor/v49-data-platform` | `f076ca3` | 当前长期 worktree；KEEP_ACTIVE |
| `/private/tmp/modern-gd-v47-data-expansion` | `codex/v47-data-expansion` | `f2cf492` | Git 标记 prunable；DELETE_CANDIDATE 仅指 worktree metadata，须先确认 owner |
| `/private/tmp/modern-gd-v48-freeze-clean` | `codex/v48-freeze-staging` | `f2cf492` | Git 标记 prunable；同上 |
| `/private/tmp/modern-gd-v48-main-transfer` | `codex/v48-main-transfer` | `592c765` | Git 标记 prunable；同上 |
| `/private/tmp/modern-gd-v48-trace-round2` | `codex/v48-trace-visualization-round2` | `6b4a60e` | registered；保留待 owner 判定 |
| `/private/tmp/modern-gd-v48-trace-visualization` | `codex/v48-trace-visualization` | `6b4a60e` | registered；保留待 owner 判定 |
| `/private/tmp/modern-gd-v48-visual-analytics` | detached | `0404c7f` | 冻结 recovery reference；ARCHIVE_READ_ONLY |

风险：三个 prunable 元数据项增加 branch/worktree 误判概率；两个 TRACE worktree 位于同一 commit，且 round2 branch 跟踪同一个 `origin/codex/v48-trace-visualization`，容易把本地实验 branch 当独立远端发布。建议由后续 cleanup 任务在 owner 确认后使用精确路径执行 `git worktree prune --dry-run`、再单独授权清理；本轮未 prune。

### 3. Git 对象库与历史大 blob

`git count-objects -vH`：

| 指标 | 数值 |
|---|---:|
| loose object count | 2,945 |
| loose size | 2.96 GiB |
| packed objects | 14,994 |
| pack count / size | 2 / 1.46 GiB |
| prune-packable | 1,023 |
| reported garbage | 1 item / 64 bytes |

garbage path 为 common Git dir 下当前 worktree metadata 的 `.../.git/worktrees/modern_GD_history_v49_data_platform/refs`。本轮没有删除、prune、gc 或 repack。

对所有 reachable refs 的对象 header 扫描得到：

| 指标 | 数值 |
|---|---:|
| historical unique blob objects | 14,693 |
| historical logical blob bytes | 22,053,618,952 bytes（约 20.54 GiB） |
| blobs ≥ 10 MiB | 105 |
| blobs ≥ 50 MiB | 84 |
| blobs ≥ 100 MiB | 78 |

最大的历史对象均为迭代中间数据库/投影，而非源码。最高 30 余项包括：

- `data/prefreeze_candidate_v37.sqlite` — 420,622,336 bytes；
- `data/prefreeze_candidate_v35.sqlite` — 420,319,232 bytes；
- `data/prefreeze_candidate_v45.sqlite`、`v38.sqlite` — 419,733,504 bytes；
- 大量 `data/prefreeze_candidate_v9…v43.sqlite` — 191–420 MB；
- `generated/public_surfaces_20k_candidate_v1.json` — 208,147,367 bytes；
- `generated/public_surfaces_20k_candidate_v2.json` — 202,205,955 bytes；
- 多版 `generated/public_surfaces_prefreeze_candidate_v*.json` — 约 190 MB。

这些对象已进入 reachable history；普通删除提交不会减小 clone/history 或消除公共历史暴露。是否需要 `git filter-repo`/LFS history migration 是独立、高风险仓库治理决策，绝不能在脏 main 或本轮执行。冻结 v48 数据不因仓库瘦身目标而允许改写。

完整 blob 内容校验没有完成：`git fsck --unreachable` 被中止。因此本节证明“路径、OID、对象类型、对象大小与 ref 可达枚举”，不证明每个对象 payload 都已重新解压并校验。

### 4. 当前 HEAD 的 tracked 与重复 blob

| 指标 | 数值 |
|---|---:|
| tracked entries | 3,419 |
| tracked logical Git bytes（LFS pointer 按 134 B） | 827,240,344 |
| unique Git blob OIDs | 3,249 |
| duplicate OID groups | 113 |
| additional paths sharing an OID | 170 |
| redundant checkout logical bytes | 276,206,239 |
| current blobs ≥10 / ≥50 / ≥100 MiB | 9 / 4 / 0 |

最大重复组是同一 90,895,254-byte Search/prototype projection OID `7efcc956…` 的四个路径：

- `data/public_surface_mock_v0.json`；
- `frontend/public/data/public_surface_mock_v0.json`；
- `frontend/src/data/public_surface_mock_v0.json`；
- `generated/public_surfaces_v1.json`。

Git 对象库只存一份 OID，但 checkout 和不同 runtime import path 形成约 272.7 MB 的额外文件占用与多权威风险。Search 必须保持 derived projection；四路径不得被解释为四个 canonical 数据库。后续 frontend/data decoupling 应选择一个 release-pinned artifact，通过 manifest/repository contract 消除其余 runtime copies；本轮不删除。

其它重复证据包括：

- 32 个 source-capture JSON 路径共享 3-byte blob；
- 15 个 Commons capture 路径共享 26-byte blob；
- QA 中多组扩展名不同或 round 不同但 OID 完全相同的 screenshot；
- `docs/qa/screenshots/round10-mobile-menu-icon-only.jpg`、`round7-mobile-icon-menu.png`、`round8…jpg`、`round9…jpg` 四路径共享同一 OID，表明扩展名不能证明 MIME；
- `round10-mobile-region-stack-before-swipe.jpg` 与 `after-swipe.jpg` OID 完全相同，无法作为手势变化证据。

截图语义与 MIME 的最终判定属于 A9；A1 只证明 Git blob identity。

### 5. Tracked generated evidence 与 ignored/untracked

当前顶层 tracked 路径分布：`data/` 2,060、`frontend/` 764、`docs/` 314、`scripts/` 197、`reports/` 28、`generated/` 16、`db/` 16、`prompts/` 11、`project-assets/` 2，另有顶层规范/许可证文件。

按路径语义匹配至少有：

- `generated/` 16 个 tracked 文件；
- `frontend/**/qa-screenshots` 或 screenshot 路径 65 个；
- `docs/**/screenshots` 60 个。

“generated” 或“screenshot”不自动等于可删除。冻结回执、manifest、可复核 QA evidence 可以是 ARCHIVE_READ_ONLY；可重建 runtime copy 才能进入 GENERATED_REPRODUCIBLE/DELETE_CANDIDATE。路径级分类由 A2/A9 总账完成。

A1 测量时 `git ls-files -ci --exclude-standard` 为 0，即没有已经 tracked 且同时命中当前 ignore 规则的路径。`git ls-files --others --exclude-standard` 当时为 3，均位于本任务并发创建的 `docs/audits/`；该瞬时数量会随其它 audit agent 输出增长，不能当最终 untracked 数。

### 6. Git LFS

- Git LFS 可用：`git-lfs/3.7.1`。
- `.gitattributes` 有 6 个精确 LFS 路径规则：v46/v47/v48 的 JSON 与 SQLite 各一项。
- 当前 HEAD 有 4 个 LFS pointer：v46、v48 的 JSON 与 SQLite；Git tree pointer blob 均为 134 bytes。
- v47 两个规则仍在 `.gitattributes`，但对应路径不在当前 HEAD；属于历史兼容还是 stale rule 尚未有 owner decision。
- `git lfs ls-files --all --long` 发现同一路径的历史 LFS OID 版本；这说明 path 不是 immutable identity，发布引用必须使用 manifest SHA/LFS object OID。

冻结 v48 的当前 LFS object IDs 与正式 freeze hash 一致：

- `data/prefreeze_candidate_v48.sqlite` → `ef190d00…`；
- `generated/public_surfaces_prefreeze_candidate_v48.json` → `b16bb015…`。

本轮没有 fetch、checkout、prune 或迁移 LFS object。`git lfs status` 作为状态命令却内部调用 `git update-index --refresh`，sandbox 以 exit 128 拒绝；之后 porcelain status 仍显示 staged 0 和仅 audit 输出，因此没有索引变更。

### 7. License、第三方内容与公共仓库边界

发现：

- `LICENSE`：MIT，声明覆盖源码；
- `FRONTEND_DESIGN_LICENSE.md`：frontend original visual design 为保留权利的个人设计许可；
- `README.md`：明确 screenshots 不属于 MIT、第三方 catalogue descriptions/images/archive materials 仍受原 owner 条款约束，GitHub backup 不等于 rights clearance；
- `frontend/package.json` 与 `frontend/package-lock.json` 存在，但当前树没有独立 `NOTICE`、`THIRD_PARTY_LICENSES` 或 machine-readable SBOM；
- `data/` 含大量第三方 provider capture/raw record；路径存在不能证明再发布许可；A1 没有打开第三方 payload 或判断其具体权利。

因此根 MIT 文件不能被理解为给 `data/`、`reports/`、截图、frontend visual design 或 provider content 统一授权。公共仓库/机器发布在 promotion 前需要 artifact-level license/rights inventory，并与 rights/visual registry gate 对接。缺少该 inventory 是发布 P0，不是删除这些研究证据的理由。

历史敏感路径扫描在 A1 中不具证明力：命令 pathspec 过宽，只生成了路径名且输出被截断。没有输出 secret 内容，但也不能据此声称历史无 secret。A10 必须使用路径模式加 secret-value redaction 扫描 Git history；任何命中只记录路径、commit 和变量名，不记录值。

## Findings and priorities

| ID | Priority | finding / affected paths | risk | recommended action | gate |
|---|---|---|---|---|---|
| A1-01 | P0 | 第三方/provider data 与截图没有统一 artifact-level license inventory；`data/**`, `reports/**`, `docs/qa/**`, `frontend/**/qa-screenshots/**` | 根 MIT 被错误外推；rights-held 内容进入机器发布 | 建立 release-scoped rights/license inventory；unknown/conflict/stale 默认 citation/link only | FREEZE/PROMOTION |
| A1-02 | P0 | reachable history 有 78 个 ≥100 MiB blob，主要为 legacy SQLite/JSON；远端可达性和公开内容合规未逐 blob 判定 | clone/push 脆弱；普通删除不能撤销历史暴露；候选数据可能被误认正式发布 | 独立 remote-reachability + rights/security review；决定保留 archive refs、LFS history migration 或经单独授权的 history rewrite | repository hygiene / PROMOTION；不直接阻塞 DDL 设计 |
| A1-03 | P1 | 四份相同 90.9 MB Search/prototype projection散落于 data/frontend/generated | runtime 多权威、checkout 浪费、数据更新要求多处同步 | v49 repository contract 生效后保留单一 release-pinned artifact；其余列 DELETE_CANDIDATE，先验证 consumers | migration/frontend gate |
| A1-04 | P1 | 3 个 prunable worktree metadata；2 个 TRACE worktree 同 commit/共享 upstream | branch owner 与恢复边界混淆 | owner 确认后先 `git worktree prune --dry-run`，独立 cleanup 执行 | repository hygiene |
| A1-05 | P1 | object DB 2.96 GiB loose + 1.46 GiB packs，1,023 prune-packable，1 个 64-byte garbage item | 本地性能/备份成本；手工 gc 可能破坏恢复线索 | 完成 refs/archive policy 后再授权 gc；保留 before/after object receipts | repository hygiene |
| A1-06 | P1 | 113 duplicate OID groups、170 extra paths、276,206,239 checkout bytes | 重复 evidence、错误 authority、QA 假阳性 | A2/A9 ledger 按 recovery reference 分类；只列候选，不直接删除 | cleanup/freeze evidence |
| A1-07 | P1 | 完整 fsck 未完成 | 尚未证明所有 payload 可解压/校验 | 在独占磁盘窗口运行 `git fsck --full --no-reflogs`，有进度/PID与时限回执 | final repository freeze |
| A1-08 | P1 | 历史 secret-path/value audit 在 A1 不完整 | 不能证明 public history 无 credential | A10 执行 redacted secret scanner；命中不得打印 value | security/promotion |
| A1-09 | P2 | `.gitattributes` 保留 v47 缺席路径；当前无 tag | stale policy/人工发现成本；tag 也不足以替代 manifest | 确认历史 checkout 需要后保留或单独清理；发布仍以 manifest SHA 为准 | hygiene/documentation |

Priority totals：**P0 2 / P1 6 / P2 1**。P0 均是 freeze/promotion 仓库治理阻塞；A1 没有发现必须靠猜测才能继续 physical DDL 设计的 Git-level identity blocker。

## Cleanup classifications contributed by A1

| classification | path/class | reason / recovery reference | deletion risk |
|---|---|---|---|
| KEEP_ACTIVE | v49 worktree、branch、`.gitattributes`、root licenses | 当前架构与 LFS checkout control | 高；不得删除 |
| ARCHIVE_READ_ONLY | `0404c7f` detached recovery worktree reference、v48 LFS objects、冻结相关 refs | checkpoint/hash recovery | 极高 |
| MIGRATE | 单一 Search/read projection consumer contract | 从四份 runtime copies 迁到 release-pinned repository | 高，需 consumer graph |
| GENERATED_REPRODUCIBLE | 只有已有 generator+input+hash receipt 的非冻结 projection 才适用 | 不能从目录名推断 | 中/未知 |
| DELETE_CANDIDATE | 3 个 prunable worktree metadata、经验证无 consumer 的重复 projection copies、已确认 stale 的属性规则 | Git OID/commit 可恢复；仍须 owner/consumer gate | 中至高 |
| HOLD_UNKNOWN | legacy large blobs、第三方 raw/capture、重复 QA、v47 LFS rules | authority/rights/recovery用途未逐项闭合 | 高；当前禁止删除 |

## Recommended action sequence

1. 在 physical schema 工作前，把 repository hygiene gate 写入 acceptance matrix：remote race、main fingerprint、changed-file allowlist、LFS availability、frozen object hash、无 tracked cache、无未分类大 blob进入 release。
2. 在 freeze/promotion 前完成 artifact-level rights/license inventory、redacted history secret scan 和独占窗口 full fsck；任何未知项保持 HOLD_UNKNOWN/link-only。
3. 在 frontend repository contract 落地后，单独执行 duplicate consumer graph 与 cleanup plan；所有删除都以精确路径、OID、owner、recovery commit 和恢复测试为前置条件。

## Actions explicitly not performed

- 没有修改或读取脏 main 的工作文件内容；没有 add、commit、push、fetch、merge、rebase、checkout、restore、reset、clean、prune、gc 或 repack。
- 没有删除 prunable worktree metadata、large blob、duplicate file、LFS object、generated artifact 或 QA screenshot。
- 没有改写 Git history、迁移 LFS history、创建 tag/branch/PR 或改变 remote。
- 没有运行 npm、Next、TypeScript、PostgreSQL、Docker、浏览器、数据生成/导出或下载第三方图片。
- 没有读取 `.env`/credential 内容或打印 secret 值。
- 没有将路径重复、扩展名或 API 可访问性解释为 rights 结论。

## Unfinished items and handoff

- **完整 object integrity：PARTIAL。** 长时 `git fsck` 已中止且 session 退出；由最终 repository freeze 独占窗口重跑。
- **live remote SHA：PARTIAL（A1）。** 依赖主任务入口和 push 前后的 `git ls-remote` race gate。
- **history secret audit：PARTIAL。** 移交 A10，必须 redacted。
- **第三方 license completeness：PARTIAL。** 根许可证边界已查明；dependency/provider artifact 逐项许可移交 A6/A10。
- **逐 blob remote-public reachability：PARTIAL。** 本报告证明 refs 可达历史，不证明每个 local ref 已推送到公共 remote。

## Residual processes

A1 启动的所有 shell sessions 均已退出。长时 `git fsck` 以 Ctrl-C/exit 130 中止，不再占用 session；其它 Git/LFS/blob scans 均 exit 0，`git lfs status` exit 128 后也已退出。sandbox 拒绝 `ps`（operation not permitted），因此全系统 residual process 的最终证明必须由主任务授权扫描完成。A1 没有启动 Node、Next、TypeScript、PostgreSQL、Docker、browser automation 或数据生成进程。
