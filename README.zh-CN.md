# MaritimeSQLBench

[English](README.md) | [简体中文](README.zh-CN.md)

MaritimeSQLBench 是论文 **《SCDS: Data Synthesis with Structural Priors via Large Language Models for Text-to-SQL》** 的海事领域 Text-to-SQL 测评基准。测评集包含 585 条中文自然语言问题及对应的 PostgreSQL 参考 SQL，覆盖船舶、港口、航运指数和海事监管等场景。

可执行 benchmark 数据包经过确定性脱敏和一致性校验。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `evaluation_data_anonymized.json` | 585 条脱敏问题-SQL 数据，以及涉及表和难度元数据。 |
| `schema_anonymized.py` | Python 字典，包含类 DDL 结构、字段注释、枚举值和脱敏样例。 |
| `data/` | 16 张表的 UTF-8 CSV 数据及包含行数、校验和与快照时间的 manifest。 |
| `database/` | 可执行 PostgreSQL DDL、DDL 生成器和 CSV 装载器。 |
| `benchmark.py` | 黄金 Schema 上下文、执行准确率评测和发布校验工具。 |
| `model_inference.py` | OpenAI-compatible 模型调用器，生成按 `question_id` 对齐的预测 SQL。 |
| `run_benchmark.py` | 一键完成 Docker 建库、数据装载、模型推理和 EX 计算。 |
| `compose.yaml` | 本地 PostgreSQL 16 容器配置。 |
| `scds_prompts.py` | 意图发现、IR 构建、SQL 实例化、问题生成和推理构造的提示词定义。 |
| `CITATION.cff` | benchmark 发布版本的引用元数据。 |
| `README.md` | 英文主文档。 |
| `LICENSE` | 本次发布的多许可证总览。 |
| `LICENSE-CODE` | `LICENSE` 所列软件文件适用的 MIT 许可证。 |
| `LICENSE-DATA` | `LICENSE` 所列数据、Schema、提示词和文档适用的 CC BY 4.0 许可证。 |

`data/manifest.json` 是 `database/load_data.py` 使用的机器可读数据包清单，记录发布版本、固定快照时间、16 个 CSV 文件名、逻辑行数与列数、SHA-256 校验值，以及校验摘要。装载器会据此在导入前核对数据包。

## 数据统计

当前公开的测评集包含 585 条数据。

| 难度 | 定义 | 数量 | 占比 |
| --- | --- | ---: | ---: |
| 简单 | 基础过滤、字段投影或简单聚合 | 212 | 36.24% |
| 中等 | 双表 JOIN 加聚合，或包含子查询、时间窗口的基础查询 | 316 | 54.02% |
| 复杂 | 多表 JOIN、窗口函数、UNION、分组聚合或组合时间范围逻辑 | 57 | 9.74% |
| **总计** |  | **585** | **100%** |

本仓库公开 16 张 Schema 表，585 条测评数据实际引用全部 16 张表。

根据 `data/manifest.json`，16 表可执行数据包总计包含 17,406 行数据。

## 记录格式

测评 JSON 文件顶层为数组，每条记录包含以下字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `query` | string | 中文自然语言问题。 |
| `question_id` | string | 稳定题目标识，也是预测提交的连接键。 |
| `sql` | string | 脱敏后的 PostgreSQL 参考 SQL。 |
| `table_names` | string[] | SQL 引用的完整表名。 |
| `difficulty` | string | `简单`、`中等` 或 `复杂`。 |
| `difficulty_score` | integer | 0 至 7 的结构难度分数。 |
| `difficulty_reasons` | string[] | 与分数相关的结构因素，可以为空。 |

格式示例：

```json
{
  "question_id": "msb_0001",
  "query": "海岳荷花的设计航速是多少？",
  "sql": "SELECT speed FROM maritime.vessel_reference WHERE name_cn LIKE '%海岳荷花%' LIMIT 1;",
  "table_names": ["maritime.vessel_reference"],
  "difficulty": "简单",
  "difficulty_score": 0,
  "difficulty_reasons": []
}
```

`schema_anonymized.py` 用于向模型提供黄金 Schema 上下文，不是数据库迁移脚本。实际建库使用 `database/schema.sql`。当前 585 条 SQL 不包含空间运算，因此可执行快照将说明性 `geography` 列存为 `text`，模型上下文仍保留其领域类型说明。

## 读取测评数据与 Schema

```python
import json

from schema_anonymized import schema_dict

with open("evaluation_data_anonymized.json", encoding="utf-8") as file:
  examples = json.load(file)

print(len(examples))  # 585
print(examples[0]["query"])
print(schema_dict[examples[0]["table_names"][0]])
```

参考 SQL 使用 PostgreSQL 方言，Schema 描述还包含与 PostGIS 相关的类型。

## 本地执行与测评

前置条件：

- Python 3.10+。
- 若走 Docker 流程，需要 Docker Engine/Desktop 和 Compose v2。
- 主机环境的 `PATH` 中需要有 `psql`，因为 `database/load_data.py` 会直接调用它。

在 macOS 上：

```bash
brew install libpq
export PATH="$(brew --prefix libpq)/bin:$PATH"
```

默认流程使用 Docker 管理 PostgreSQL 16。

警告：`docker compose down -v` 会删除本项目的 benchmark volume。默认的 `python run_benchmark.py ...` 流程也会重建这份 Docker 数据库，除非显式传入 `--reuse-database`。

```bash
python -m pip install -r requirements.txt
docker compose down -v
docker compose up -d --wait
python database/load_data.py \
  --database-url postgresql://benchmark_admin:benchmark_local_only@localhost:54320/maritime_benchmark \
  --data-dir data
```

如果使用原生 PostgreSQL 16，请跳过上面的 Docker 命令。先预创建一个空数据库，以及一个有权限创建所需 schema 和表的角色，然后用你的数据库 URL 运行装载器。若 `psql` 不在 `PATH` 中，可额外传入 `--psql /path/to/psql`。

```bash
python -m pip install -r requirements.txt
python database/load_data.py \
  --database-url postgresql://your_role:your_password@localhost:5432/your_database \
  --data-dir data
```

预测文件是仅含 `question_id` 和 `sql` 的 JSON 数组。运行 EX：

```bash
python benchmark.py evaluate \
  --predictions predictions.json \
  --database-url postgresql://benchmark_admin:benchmark_local_only@localhost:54320/maritime_benchmark \
  --snapshot-as-of 2026-10-13T14:00:00+08:00 \
  --output evaluation_report.json
```

评测固定使用上述快照时间和 `Asia/Shanghai` 数据库会话时区，对黄金 SQL 和预测 SQL 对称替换 `NOW()`、`CURRENT_DATE` 与 `CURRENT_TIMESTAMP`。黄金 SQL 含 `ORDER BY` 时按行顺序比较，否则按保留重复行的多重集比较。`NULL`、精确数值和时间类型经过类型化规范；缺失预测、执行错误和超时均计为错误。

### 一键模型评测

`scds_prompts.py` 是论文数据合成流程的提示词定义，不负责调用待测模型。实际模型接入在 `model_inference.py`，支持 OpenAI 及兼容 `/chat/completions` 的服务。API Key 只从环境变量读取：

```bash
export MODEL_API_KEY="your-api-key"
python run_benchmark.py --model gpt-4.1-mini --workers 4
```

使用本地或其他兼容服务：

```bash
export MODEL_API_KEY="your-api-key"
export MODEL_BASE_URL="http://localhost:8000/v1"
python run_benchmark.py --model your-model-name --workers 4
```

仅使用可信端点。该服务会收到 API Key、每条自然语言问题，以及该题所需的 Schema 上下文；不会收到参考 SQL 或执行结果。

该命令默认清理 benchmark Docker 卷、完成数据库初始化与装载、逐题向模型发送自然语言问题及该题所需的黄金 Schema、保存 `predictions.json`，并生成用于 EX 评测的 `evaluation_report.json`。`--limit N` 会将预测生成和 EX 评测都限制到前 `N` 题，报告分母也变为 `N`。`--resume` 应与中断前相同的模型、端点和预测文件配合使用，只补齐缺失或空的 SQL。`--reuse-database` 会保留当前 Docker volume 并跳过 CSV 重载。`--workers` 控制并发模型请求数，默认值为 1；也可通过 `MODEL_WORKERS` 设置。并发值应根据模型服务的限流策略调整。

若已有预测文件，可跳过模型调用：

```bash
python run_benchmark.py --predictions predictions.json
```

## 脱敏说明

公开 Schema 和测评集使用确定性替换规则生成：

- SQL、表元数据、字典键、DDL 和注释中的内部数据库限定名统一替换为中性的 `maritime`。
- 可识别船名、公司名、IMO、MMSI、业务 UUID 和源记录样例替换为脱敏值。
- 同一源实体在自然语言问题和 SQL 中始终映射为同一脱敏实体。
- 内部序列名、失效对象引用和复制索引后缀已规范化。
- 公开港口、国家、航线节点、特殊区域和海区的标量坐标统一保留到小数点后 1 位，量级约为 10 公里，实际距离分辨率会随纬度变化。
- 可执行数据包中的船舶位置和相关时间经过脱敏或重建，不适用于现实世界推断。
- 原始几何字段和未被使用的复合位置字符串已从公开数据包中移除。
- 为保持 benchmark 语义，船型及事件类别、公开地理名称、公开港口代码等标准领域词汇予以保留。其中部分公开名称和代码可与外部资料关联。
- 原始值与发布值之间的保密映射不随仓库发布。
- 数据包已针对固定快照完成适配和校验，保证全部参考 SQL 获得有效非空结果。

脱敏会改变 SQL 中的数据库字面量。公开的参考问题与 SQL 仍保留 benchmark 语义配对，但 SQL 不能直接查询原始数据库。

`data/manifest.json` 中汇总的残留检查能力有限，不能排除重新识别风险。

## 评测范围与限制

执行准确率（Execution Accuracy，EX）是主要 Text-to-SQL 指标，同时使用执行错误率作为补充指标。发布校验已确认 585 条黄金查询全部执行成功且结果非空，黄金 SQL 作为预测提交时 EX=100%。

## 引用

benchmark 的引用元数据见 `CITATION.cff`。截至本次发布，论文尚未分配 DOI、卷期或文章号。正式发表后应更新以下条目：

```bibtex
@article{zhang2026structure,
  author  = {Zhang, Haoyu and Zou, Yingqi and Wang, Xiangyu and Wang, Shaohan and Zhang, Zijian},
  title   = {SCDS: Data Synthesis with Structural Priors via Large Language Models for Text-to-SQL},
  year    = {2026},
  note    = {Manuscript; publication metadata pending}
}
```

## 许可证

本仓库采用多许可证发布。总览见 `LICENSE`，MIT 条款见 `LICENSE-CODE`，CC BY 4.0 条款见 `LICENSE-DATA`。

- `LICENSE-CODE`（MIT）适用于 `benchmark.py`、`model_inference.py`、`run_benchmark.py`、`database/generate_schema.py`、`database/load_data.py`、`tests/`、`compose.yaml` 和 `requirements.txt`。
- `LICENSE-DATA`（CC BY 4.0）适用于 `evaluation_data_anonymized.json`、`data/`、`schema_anonymized.py`、`database/schema.sql`、`scds_prompts.py`、`README.md`、`README.zh-CN.md` 和 `CITATION.cff`。
- `results/` 下的生成模型输出，以及本地预测/报告文件，不随本次发布分发，除非另有明确说明，否则不在上述许可范围内。

本次发布所需授权已经确认。第三方材料如有，其权利和许可证仍归各自权利人所有。
