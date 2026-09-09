# MaritimeSQLBench

[English](README.md) | [简体中文](README.zh-CN.md)

MaritimeSQLBench 是论文 **《Structure-Constrained Data Synthesis for Domain-Specific Text-to-SQL》** 的海事领域 Text-to-SQL 测评基准。测评集包含 585 条中文自然语言问题及对应的 PostgreSQL 参考 SQL，覆盖船舶、港口、航运指数和海事监管等场景。

> **发布状态：** 本次首期先公开 10 张表的脱敏 Schema 上下文。脱敏测评集将在完成剩余审核与发布流程后，于后续仓库版本中公开。

当前版本不包含测评问题-SQL 数据、源数据库、表内数据、查询结果、模型输出或训练数据。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `schema_anonymized.py` | Python 字典，包含现阶段公开的 10 张表的类 DDL 结构、字段注释、枚举值和合成样例。 |
| `README.md` | 英文主文档。 |
| `LICENSE` | Creative Commons 署名 4.0 国际许可说明。 |

测评数据、源文件及保密脱敏映射均不包含在本次发布中。

## 后续测评集发布计划

以下是 585 条测评数据的统计信息。相应的脱敏 JSON 文件**不包含在当前版本中**，计划在后续版本发布。

| 难度 | 定义 | 数量 | 占比 |
| --- | --- | ---: | ---: |
| 简单 | 基础过滤、字段投影或简单聚合 | 212 | 36.23% |
| 中等 | 双表 JOIN 加聚合，或包含子查询、时间窗口的基础查询 | 316 | 54.02% |
| 复杂 | 多表 JOIN、窗口函数、UNION、分组聚合或组合时间范围逻辑 | 57 | 9.74% |
| **总计** |  | **585** | **100%** |

现阶段本仓库先公开后续测评数据实际引用的 10 张 Schema 表。

后续发布的测评数据中，`difficulty_score` 取值为 0 至 7。发布文档未定义该分数的精确计算公式，因此不应将其解释为经过标定或线性的难度量表。`difficulty_reasons` 记录与分数相关的 SQL 结构因素。

## 计划发布的记录格式

测评 JSON 发布后，文件顶层为数组，每条记录包含以下字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `query` | string | 中文自然语言问题。 |
| `sql` | string | 脱敏后的 PostgreSQL 参考 SQL。 |
| `table_names` | string[] | SQL 引用的完整表名。 |
| `difficulty` | string | `简单`、`中等` 或 `复杂`。 |
| `difficulty_score` | integer | 0 至 7 的结构难度分数。 |
| `difficulty_reasons` | string[] | 与分数相关的结构因素，可以为空。 |

格式示例：

```json
{
  "query": "海岳荷花的设计航速是多少？",
  "sql": "SELECT speed FROM maritime.vessel_reference WHERE name_cn LIKE '%海岳荷花%' LIMIT 1;",
  "table_names": ["maritime.vessel_reference"],
  "difficulty": "简单",
  "difficulty_score": 0,
  "difficulty_reasons": []
}
```

## Schema 范围

现阶段公开的 10 张表覆盖船舶主数据、船舶动态、船舶事件、当前航次状态、港口与泊位、港口效率和航运指数。

当前 Schema 已公开以下 10 张表，它们也是计划后续发布的 585 条参考 SQL 实际使用的表：

```text
maritime.vessel_reference
maritime.vessel_state_history
maritime.vessel_event_log
maritime.vessel_current_state
maritime.index_observation
maritime.index_catalog
maritime.port_reference
maritime.berth_reference
maritime.port_efficiency_snapshot
maritime.port_efficiency_baseline
```

`schema_anonymized.py` 用于向模型提供 Schema 上下文，不是生产数据库迁移脚本。其中的 SQL 字符串包含注释、分区父表声明、PostGIS 类型和说明性样例块，不保证能够作为独立数据库部署脚本直接执行。

## 加载 Schema

```python
from schema_anonymized import schema_dict

print(len(schema_dict))  # 10
print(schema_dict["maritime.vessel_reference"])
```

Schema 描述使用 PostgreSQL 方言，并包含与 PostGIS 相关的类型。

## 脱敏说明

公开 Schema 使用确定性替换规则生成；正在准备后续发布的测评集也使用相同规则：

- SQL、表元数据、字典键、DDL 和注释中的内部数据库限定名统一替换为中性的 `maritime`。
- 可识别船名、公司名、IMO、MMSI、业务 UUID 和源记录样例替换为合成值。
- 同一源实体在自然语言问题和 SQL 中始终映射为同一合成实体。
- 内部序列名、失效对象引用和复制索引后缀已规范化。
- 为保持任务语义，船型及事件类别、公开地理名称、公开港口代码等标准领域词汇予以保留。
- 原始值与合成值之间的保密映射不随仓库发布。

脱敏会改变 SQL 中的数据库字面量。因此，后续发布的参考 SQL 将与问题在结构和语义上保持对应，但不能用于直接查询原始数据库。

## 评测范围与限制

执行准确率（Execution Accuracy，EX）是主要 Text-to-SQL 指标，同时使用执行错误率作为补充指标。本仓库没有提供可执行数据库快照或预期查询结果，因此仅凭当前文件无法复现这些指标。

当前仅包含 Schema 的版本适合用于：

- Schema Linking 研究和提示词构建；
- 海事数据库结构与字段语义分析；
- 为后续测评集发布准备 Text-to-SQL 系统。

仅凭当前版本尚不能在 MaritimeSQLBench 上开展正式测评。问题-SQL 数据计划在后续版本发布。底层数据库、合成训练集、采样脚本、模型检查点和模型输出也不包含在本仓库中。

## 引用

截至本次发布，论文尚未分配 DOI、卷期或文章号。正式发表后应更新以下条目：

```bibtex
@article{zhang2026structure,
  author  = {Zhang, Haoyu and Zou, Yingqi and Wang, Xiangyu and Wang, Shaohan and Zhang, Zijian},
  title   = {Structure-Constrained Data Synthesis for Domain-Specific Text-to-SQL},
  year    = {2026},
  note    = {Manuscript; publication metadata pending}
}
```

## 许可证

除非另有说明，本次发布的脱敏 Schema 和仓库文档采用 [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) 许可。复用者需要提供适当署名、附上许可证链接，并说明是否进行了修改。后续发布文件的许可状态将在相应文件正式发布时说明。

该许可证只覆盖许可方有权授予的权利。正式公开仓库前，维护者仍应确认已取得发布该衍生测评集所需的单位审批与授权。
