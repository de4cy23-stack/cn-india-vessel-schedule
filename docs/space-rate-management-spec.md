# 船期、运价与配舱管理模块：产品与开发规格（MVP）

> 状态：需求与数据模型设计，**并非已实现的功能**。
> 集成目标：在现有 CN-India Vessel Schedule Aggregator 中扩展业务管理，不改变现有 /search 与 /schedules 的语义。
> 数据来源：2026 年实际配舱工作簿的结构性分析；**不上传原始工作簿、提单号、客户、实际价格或敏感记录**。

## 1. 用户目标和原则

从“查某港到某港有哪些船期”，延伸到“这班船有哪些可用舱位、什么箱型/重量要求、对应什么运价、已经配给哪些业务、依据是哪个附件”。

以宁波、上海出口至印度航线为首批使用场景，其他港口可扩展。优先满足货代内部操作：少点表单、多用表格、能粘贴 Excel、支持批量修改。不要把它做成需要逐字段手工录入的复杂 ERP。

**务必区分四个概念：**
1. 物理船舶的名义 TEU 容量（可选参考数据，来源和更新时间必填）。
2. 某船司某航线某航次的可售/配额 TEU（可能分代理、约号、起运港、箱型）。
3. 本公司/代理实际分到的可用配额（实际经营限制）。
4. 配舱记录实际占用的 TEU 和总 VGM 重量（随订舱状态变更）。

这些数值不能互相推算。例如“50 TEU”可能是某次代理/合同配额，并不意味着整艘船仅有 50 TEU。无来源的总船容不允许自动填充。

## 2. 现有代码基线

- 后端：FastAPI + Pydantic；前端：backend/app/static/index.html。
- 已有模型：Schedule、ScheduleLeg、CarrierInfo、ScheduleSearchResponse。
- 已有接口：/search、/schedules、/ports、/carriers。
- 已有 Schedule 字段包含 carrier、carrier_code、origin、destination、vessel、voyage、service、etd、eta、direct、legs 和 source。
- 目前没有业务数据库、运价存储、舱位管理、文件导入或订舱占用状态。
- 新业务表建议做独立 package、数据库模型和路由；复用港口别名、船司代码及船期适配器。
- 查船期 API 返回的是航线信息，不是商业配额。**空的舱位/重量字段应显示“未录入”，不得默认 0、无限制或自动等于船舶载重。**

## 3. 业务层级与唯一性

建议层级：
- Carrier（船司）：如 HPL、WHL、HAL、RCL、SKR、COSCO、TSL、ECON。
- CarrierService（船司航线）：船司 + 航线代码，例如 HPL-TPI、WHL-CI6、WHL-CI2；代码只在所属船司内唯一。
- Sailing（班次/航次）：船司 + Service + 船名/IMO（可空）+ 航次 + 起运港 + ETD；可含中转腿、ETA 和挂靠港。
- Allocation（实际可用舱位额度）：一个 Sailing 下可能对应多个代理、约号、销售渠道、POL、POD、箱型和分配额度。
- RateCard（生效期间的报价）：船司/代理/约号、航线、POL、POD/最终目的地、箱型、重量区间、币种、运价及附加费。
- BookingAllocation（订单占用）：工作卡/订单编号 + 订舱号/MBL + 具体 Allocation + 箱型数量 + VGM + 状态。
- Attachment/SourceDocument（证据）：关联报价、配额、船期或订单的来源文件及文本摘录。
- ChangeLog（审计）：字段前后值、操作者、时间、原因、来源。

不同船司可以共用同一艘物理船、同一航次；不能仅凭 vessel+voyage 就把两个船司的不同商业配额合并。直达/中转在 Sailing/legs 层记录；同一船名航次也可能经不同 POL/POD 形成不同销售航线。

### 3.1 推荐字段

| 模型 | 必填字段 | 关键可选字段 |
| --- | --- | --- |
| CarrierService | carrier_id、service_code | display_name、active、transshipment_pattern |
| Sailing | carrier_id、vessel、voyage、pol、etd | service_id、pod、final_destination、eta、direct、transshipment_ports、source |
| Allocation | sailing_id、supplier/agent、status | contract_no、pol、pod、total_teu、total_vgm_tons、min_commitment_teu、max_single_container_vgm_tons、equipment_limits_json、unit/notes、valid_until |
| RateCard | carrier_id、pol、pod、equipment、currency、valid_from、valid_to、amount、direction | service_id、sailing_id、agent_id、contract_no、weight_from_tons、weight_to_tons、fee_items、payment_term、free_time_days、source_document_id |
| BookingAllocation | allocation_id、workcard_no、booking_no、equipment_counts、status | mbl_no、operator、customer_ref、vgm_kg、notes、last_changed_at |
| SourceDocument | filename、mime_type、sha256、storage_key、uploaded_at、uploaded_by | parsed_text、source_type、parser_version、document_date、validation_state |
| VesselReference | vessel_name、capacity_teu、source、as_of | imo、deadweight_tons、operator |

将无法确认的数据保留为空，并保留来源原文。避免把代理备注里的散文说明擅自转成硬性限制。

## 4. 箱型与 TEU 计算

- 20GP、20FR 等标准 20 英尺基础 TEU=1；40GP、40HQ、40FR 等标准 40 英尺基础 TEU=2。
- **箱量和 TEU 分开存**：1×20GP + 1×40HQ = 2 个箱，3 TEU。
- “45G1”是 ISO 箱型尺寸代码，不应简单因为以“45”开头就当作 45 英尺箱；需通过设备映射表识别其实际尺寸。
- 45 英尺、超限框架箱、冷箱、电箱、特种货等须由船司规则配置 TEU/舱位占用系数与是否允许，不可盲目套普通箱计算。
- 支持 1X20GP、1*40HQ、2X40'HQ、40HQ*8、1X20GP+1X40HC、6X20GP: 等常见输入的解析预览，无法解析时保留原字符串并提示人工确认。
- 单票可拆多个箱型行，每行记录 count、equipment_type、vgm_kg_per_container（可选）；实际总 VGM 必须有单位且支持公斤/吨换算。
- 被取消、拒舱、释放的订舱不占有效配额；已提交、待确认和已确认的占用规则须通过状态机明确，防止重复预占。
- 并发修改时用事务、版本号或行级锁防止超配。

## 5. 重量限制不能只有一个“重量”字段

建议规则引擎支持：
1. 航次/代理总 VGM 上限（吨），与 TEU 并行检查。
2. 单箱 VGM 上限，可按 20GP/40HQ/特殊箱分别设置。
3. 某箱型是否允许、某箱型最大箱数。
4. 每票最大 VGM、超重柜附加费和阶梯区间。
5. 起运港、目的港、中转港、码头、拖车/铁路等特定限制。
6. 来源、适用起止日期、强限制/软提醒、需要人工审批。

系统只在数据明确且有效期内才显示“校验通过”；缺少规则时显示“限制待核对”。禁止把各船司不同重量条件合并成一个统一阈值。

## 6. 运价管理

价格维度：船司、服务代码、代理/订舱渠道、约号、POL、POD、最终目的地、直达/中转、ETD/有效期、箱型、重量区间、买价/卖价、币种、结算条款。

- 基本海运费与附加费分拆存储：海运费、拥挤费、重柜附加费、驳船费、其他特殊费用。
- 可表示固定金额/箱、按 TEU、按票、按吨、百分比及“需询价”。
- 保留报价原文及附件；识别到“2600/2800”这种未指明箱型顺序的报价时，不能自动假定 20GP/40HQ，应标记待确认。
- 费用可配置预付/到付，支持免用箱期限与说明。
- 报价匹配优先级：明确指定订舱 > 航次指定 > 航线+港口+箱型+有效期 > 船司/代理常规报价。相同优先级冲突时展示多个选项，不自动任意覆盖。
- 价格未生效、过期、缺币种、缺箱型等一律不能显示为“确定有效报价”。
- 首版不自动换汇，不把不同币种直接相加。
- 区分“报价”和“订单锁价”，历史订单不会因新报价覆盖而被悄悄改价。

## 7. 附件与导入：人工确认优先

### 7.1 支持的类型

- MVP：.xls、.xlsx、.csv 的结构化预览和映射导入；PDF、图片、EML 支持安全上传与关联，但识别结果需要人工确认。
- 后续：PDF 文字层抽取、邮件附件解析；扫描件/OCR 仅作辅助建议，不能静默落库。
- 不应依赖船司官方 API 提供运价与配额；这些主要来自人工、代理通知和合同附件。

### 7.2 导入工作流

上传文件 → SHA-256 去重与存档 → 识别工作表/数据区域 → 匹配船司模板 → 预览原始行 → 展示字段映射和疑点 → 用户确认/调整 → 事务性导入 → 回传成功/跳过/需人工处理计数 → 可回滚与审计。

- 每个 Sheet 可有独立 mapping profile。相同文件内不同船司页面不能假定列布局一致。
- 表头、分段标题、合并单元格、自由文本备注、混合日期格式与运价信息需要分别处理。
- 日期既可能是 Excel 序列日期，也可能是 10.8、11.03、2026-11-09 等短日期；未明确年份时依据上下文推断且提示复核。
- 对可疑数字（币种不明的价格、质量单位不明的数字、无出处的 TEU 上限）不自动补齐。
- 从附件得到的建议字段带 confidence 和 original_text，在用户确认前不修改正式报价/配额。
- 同一文件重复上传不能重复占用舱位；同一订单行重复导入使用稳定 business key 实现幂等。

### 7.3 已观察到的工作簿结构（仅结构，不含私人业务数据）

工作簿有 ECON、HAL、RCL、SKR、WHL、TAIZHOU COSCO、TSL、HPL 八个标签：

| Sheet | 常见数据布局与风险 | 导入方式 |
| --- | --- | --- |
| ECON | 日期、经办人、单号、船名航次、POL/POD、箱量、品名、Weight；标题行还写 TEU、总吨和报价条件 | 分段识别标题约束 + 逐订单行；单位待确认 |
| HAL | 订舱号、船名航次、日期、箱量、POD、操作人，重量经常在自由文本里 | 标准行导入 + 自由重量备注复核 |
| RCL | 多个船期分段、报价备注和重复表头；日期有小数形式 | 先识别航次分组，不把备注当订单 |
| SKR | 船名航次、目的港、箱量、操作人；分段标题含码头/价格 | 分段模板 + 自由文本来源 |
| WHL | 一部分是传统配舱表，一部分含航线代码和转港代码，不能用同一字段映射 | 两个独立区域的 mapping profiles |
| TAIZHOU COSCO | 含约号、订舱号、POL/POD、箱型及“标箱数”列；标箱数可能与箱量存在不一致 | 自动重新计算 TEU 并标记冲突，不能依赖现有标箱列 |
| TSL | 以自然语言备忘船期/报价，没有完整订单表头 | 作为待确认线索导入，不强制形成订单 |
| HPL | 规则化主提单号、S/O、箱型、服务代码、目的港；备注含超重加费和免用箱等 | 结构化导入 + 备注规则审核 |

**注意：以上属于真实工作样本的结构抽象；不要将原始文件、业务编号、客户姓名、真实费用、箱量分配或重量明细提交到公共仓库。**

## 8. 界面与日常工作流

首屏建议采用“Excel 密度”的可编辑表格，而非一张船一张卡、反复打开表单。

**主导航**：船期查询｜舱位看板｜运价表｜配舱清单｜附件箱

- 筛选：起运港、目的港、日期段、船司、航线代码、船名航次、代理、约号、箱型、状态。
- 主表每行一条“某船司某航次某配额”，常显列：船司、航线、船名航次、POL/POD、ETD、额度 TEU、已用 TEU、剩余 TEU、总 VGM 上限、已用 VGM、剩余 VGM、20GP 价格、40HQ 价格、资料状态。
- 允许列显示隐藏、粘贴多行、批量选中、快捷筛选、导出 Excel。
- 点击一行，右侧抽屉显示“订舱明细｜运价版本｜重量限制｜原始附件｜更新记录”。
- 查询到的外部船期可以一键“加入内部管理”，但不可自动生成不存在的配额或价格。
- 警示颜色区分：已超配（错误）、临近上限（警告）、来源待确认（提醒）、未提供规则（灰色未知）；未知不能被渲染为绿色成功。
- 某船共享在不同船司的可售舱位应显示为独立商业记录，不可跨船司扣减。

## 9. MVP 技术方案

后端：
- 在 backend/app 下新增 commercial 子包：db、entities、schemas、routes、rules、importers、attachments。
- 使用 SQLAlchemy 2.x + SQLite 作为本地单机 MVP（后续可切 PostgreSQL），加入 Alembic 迁移。
- 路由统一挂载 /commercial；保持现有 /search、/schedules 向后兼容。
- 文件存放到配置的非 Git 工作目录；数据库只存 storage_key、hash、metadata。服务端严格控制路径、类型、大小、下载权限；禁止遍历路径、恶意宏执行。
- 导入采用“先预览、后确认”；后台解析失败不影响正常船期查询。
- 商务数据要求操作者权限和审计，不建议在公开互联网匿名提供写接口。

初始 API 草案：
- GET /commercial/sailings：本地管理班次查询与聚合。
- POST /commercial/sailings/import-from-schedule：导入选中的 API 船期，不导入空想配额。
- GET/POST/PATCH /commercial/allocations：额度与限制维护。
- POST /commercial/allocations/{id}/check：按箱型、数量、VGM 计算占用并返回阻断/警告/未知规则。
- GET/POST/PATCH /commercial/rates：报价与版本管理。
- POST /commercial/bookings、PATCH /commercial/bookings/{id}：订舱与状态机。
- POST /commercial/imports/preview：文件预解析与分 Sheet 映射，不写业务表。
- POST /commercial/imports/{id}/confirm：接受人工修改后的字段，幂等入库。
- GET /commercial/documents/{id}：受控下载原附件。
- GET /commercial/audit：按业务实体查询版本和变更。

前端先用现有静态 HTML + JS 快速验证交互，必要时再拆 React。禁止把复杂字段分散到十几个必填的独立弹窗。

## 10. 状态与计算示例（均为虚构示例）

- 某代理对某航次分得 12 TEU、150 吨，1×20GP + 1×40HQ 占用 3 TEU；剩余 9 TEU。
- 两票分别 20 吨与 40 吨 VGM，占用 60 吨；若总限 150 吨，剩余 90 吨。
- 若再提交 10 TEU，应阻止已确认占用越过 12 TEU；可保存草稿并标识超限。
- 重量上限未知，不可显示“重量通过”；报价缺币种，不可显示有效价。
- 舱位确认后取消需释放占用；再次导入相同订单不得二次扣减。
- 同船同航次但两个不同 carrier/service，不自动合并配额和报价。

## 11. 验收测试

1. 船司航线代码只在所属船司内唯一，同名船/同航次不会跨船司误合并。
2. 20GP=1、40HQ=2，混合箱型正确累加；非标准箱型需要规则映射。
3. 限额同时检查 TEU、总重量、单柜重量、箱型允许性；未知规则清楚显示为未知。
4. 重量同时支持公斤/吨，绝不静默混用。
5. 改变订单状态释放/预占舱位，重复请求和并发请求不造成超配或双扣。
6. 运价按有效期、POD、箱型和重量区间匹配；冲突、过期、缺币种展示提示。
7. 8 种 Excel Sheet 布局可分别映射，混合标题、备注和空行不形成假订单。
8. 非表格备注只生成待确认建议，不能直接当作已确认配额/运价。
9. 重复文件/重复订舱行导入幂等，可查看来源与差异；导入可回滚。
10. PDF/EML 文件上传可关联，但不能假装已准确解析。
11. 旧船期接口及前端页面保持正常，现有 pytest 通过；新增商业模块单元/API 测试。
12. GitHub 仓库内不能出现原始工作簿、客户资料、正式报价、凭证和上传的附件。

## 12. 开发拆分建议

**阶段 A：可信底座**
- 设计数据库 + 数据迁移 + 核心实体 + TEU/重量规则 + 后端 CRUD 和测试。
- 用手工录入的虚构测试数据呈现舱位可用量。

**阶段 B：Excel 高效导入**
- 支持 .xls/.xlsx 多 Sheet、区域预览、模板映射、批量粘贴、确认导入和去重。
- 优先解决混合箱型、非标准日期、分段标题和自由文本备注。

**阶段 C：运价与附件**
- 多币种、重量阶梯、费用拆分、报价版本和附件追溯。
- PDF/EML 先上传关联、后做可校验的文本抽取。

**阶段 D：船期联动与体验**
- 现有 /search 一键转内部 Sailing、看板筛选、临近阈值提示、按船司/航线对比。
- 如有稳定 API 再扩展自动更新，并记录手工覆盖的优先级。

## 13. 重要未决事项（开发时以可配置项处理，不阻断 MVP）

- 配额是否“必须订满”的最小保证，与“最多可订”的上限要分开记录。
- 重量约束究竟是总货重、总 VGM 还是单箱 VGM；未确认时不可互换。
- 运价的“2600/2800”对应何种箱型、是否包含附加费，需要来源确认。
- 同一代理跨 POL/POD 或多个航次可否共享额度，默认不共享。
- 特种箱/45 英尺箱占用 TEU 的船司特殊规则。
- 哪些订单状态算预占、哪些算实际占用，需要可配置的状态机。
- 是否按用户、团队和客户细分权限及价格可见性，首版至少限制写权限。
