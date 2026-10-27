# MaritimeSQLBench

[English](README.md) | [简体中文](README.zh-CN.md)

MaritimeSQLBench is a domain-specific Text-to-SQL benchmark accompanying the manuscript **"SCDS: Data Synthesis with Structural Priors via Large Language Models for Text-to-SQL."** The evaluation set contains 585 Chinese natural-language questions paired with PostgreSQL reference queries for maritime scenarios involving vessels, ports, shipping indices, and maritime regulation.

The executable benchmark package has undergone deterministic anonymization and consistency validation.

## Training Data

[Download training data](https://github.com/K-zhy/maritimeSQLbench/releases/download/bird-training-data-v1.0/bird_syn_with_cot.jsonl.gz).

## Files

| File | Description |
| --- | --- |
| `evaluation_data_anonymized.json` | 585 anonymized question-SQL pairs with table and difficulty metadata. |
| `schema_anonymized.py` | Python dictionary containing DDL-like schema descriptions, field comments, categorical values, and anonymized examples. |
| `data/` | UTF-8 CSV data for 16 tables plus a manifest with row counts, checksums, and snapshot time. |
| `database/` | Executable PostgreSQL DDL, its generator, and the CSV loader. |
| `benchmark.py` | Gold schema context, execution-accuracy evaluation, and release-validation utilities. |
| `model_inference.py` | OpenAI-compatible model client that produces SQL keyed by `question_id`. |
| `run_benchmark.py` | One-command Docker setup, data loading, model inference, and EX evaluation. |
| `compose.yaml` | Local PostgreSQL 16 container configuration. |
| `scds_prompts.py` | Prompt definitions for intent discovery, IR construction, SQL instantiation, question generation, and reasoning construction. |
| `CITATION.cff` | Citation metadata for the benchmark release. |
| `README.zh-CN.md` | Chinese documentation. |
| `LICENSE` | Multi-license overview for the release. |
| `LICENSE-CODE` | MIT license for the software files listed in `LICENSE`. |
| `LICENSE-DATA` | CC BY 4.0 license for the data, schema, prompts, and documentation files listed in `LICENSE`. |

`data/manifest.json` is the machine-readable package inventory used by `database/load_data.py`. It records the release version, fixed snapshot timestamp, 16 CSV file names, logical row and column counts, SHA-256 digests, and validation summaries. The loader uses it to verify the package before loading data.

## Dataset Statistics

The released evaluation set contains 585 examples.

| Difficulty | Description | Examples | Share |
| --- | --- | ---: | ---: |
| Simple (`简单`) | Basic filtering, projection, or simple aggregation | 212 | 36.24% |
| Moderate (`中等`) | Two-table joins with aggregation, or basic queries with subqueries/time windows | 316 | 54.02% |
| Challenging (`复杂`) | Multi-table joins, window functions, unions, grouped aggregation, or combined time-range logic | 57 | 9.74% |
| **Total** |  | **585** | **100%** |

This repository publishes 16 schema tables, and the 585 evaluation examples reference all 16 tables.

According to `data/manifest.json`, the executable 16-table package contains 17,406 total rows.

## Record Format

The evaluation JSON file is a top-level array in which each record contains:

| Field | Type | Description |
| --- | --- | --- |
| `query` | string | Chinese natural-language question. |
| `question_id` | string | Stable question identifier and prediction submission key. |
| `sql` | string | Anonymized PostgreSQL reference query. |
| `table_names` | string[] | Fully qualified tables referenced by the query. |
| `difficulty` | string | One of `简单`, `中等`, or `复杂`. |
| `difficulty_score` | integer | Structural difficulty score from 0 to 7. |
| `difficulty_reasons` | string[] | Structural factors associated with the score; may be empty. |

Illustrative format:

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

`schema_anonymized.py` provides gold schema context and is not a database migration. Use `database/schema.sql` to create the executable database. The current 585 queries contain no spatial operations, so the executable snapshot stores descriptive `geography` columns as `text` while retaining their domain types in model context.

## Reading Evaluation Data and Schema

```python
import json

from schema_anonymized import schema_dict

with open("evaluation_data_anonymized.json", encoding="utf-8") as file:
  examples = json.load(file)

print(len(examples))  # 585
print(examples[0]["query"])
print(schema_dict[examples[0]["table_names"][0]])
```

The reference SQL uses PostgreSQL syntax. The schema descriptions also include PostGIS-related types.

## Local Execution and Evaluation

Prerequisites:

- Python 3.10+.
- For the Docker flow, Docker Engine/Desktop with Compose v2.
- `psql` on the host `PATH`, because `database/load_data.py` invokes it directly.

On macOS:

```bash
brew install libpq
export PATH="$(brew --prefix libpq)/bin:$PATH"
```

Docker is the default PostgreSQL 16 flow.

Warning: `docker compose down -v` deletes this project's benchmark volume. The default `python run_benchmark.py ...` flow also rebuilds the Docker-managed database unless `--reuse-database` is set.

```bash
python -m pip install -r requirements.txt
docker compose down -v
docker compose up -d --wait
python database/load_data.py \
  --database-url postgresql://benchmark_admin:benchmark_local_only@localhost:54320/maritime_benchmark \
  --data-dir data
```

For a native PostgreSQL 16 installation, skip the Docker commands above. Pre-create an empty database and a role with permission to create the required schema and tables, then run the loader against your database URL. Add `--psql /path/to/psql` if `psql` is not available on `PATH`.

```bash
python -m pip install -r requirements.txt
python database/load_data.py \
  --database-url postgresql://your_role:your_password@localhost:5432/your_database \
  --data-dir data
```

A prediction file is a JSON array containing only `question_id` and `sql`. Run EX with:

```bash
python benchmark.py evaluate \
  --predictions predictions.json \
  --database-url postgresql://benchmark_admin:benchmark_local_only@localhost:54320/maritime_benchmark \
  --snapshot-as-of 2026-10-13T14:00:00+08:00 \
  --output evaluation_report.json
```

Evaluation uses the fixed snapshot time above and the `Asia/Shanghai` database session time zone, and symmetrically replaces `NOW()`, `CURRENT_DATE`, and `CURRENT_TIMESTAMP` in gold and predicted SQL. Queries with `ORDER BY` are compared in row order; other results use multiset comparison with duplicates retained. `NULL`, exact numerics, and temporal values are type-normalized. Missing predictions, execution errors, and timeouts are incorrect.

### One-Command Model Evaluation

`scds_prompts.py` defines the manuscript's data-synthesis prompts; it does not invoke the model under evaluation. Runtime model integration is implemented in `model_inference.py` and supports OpenAI and compatible `/chat/completions` services. The API key is read only from an environment variable:

```bash
export MODEL_API_KEY="your-api-key"
python run_benchmark.py --model gpt-4.1-mini --workers 4
```

For a local or other compatible endpoint:

```bash
export MODEL_API_KEY="your-api-key"
export MODEL_BASE_URL="http://localhost:8000/v1"
python run_benchmark.py --model your-model-name --workers 4
```

Use a trusted endpoint only. It receives the API key, each question, and the required schema context. Gold SQL and execution results are not sent.

By default, this command recreates the benchmark Docker volume, sets up and loads the database, sends each question and its required gold schema to the model, writes `predictions.json`, and produces `evaluation_report.json` for EX evaluation. `--limit N` restricts model generation and EX evaluation to the first `N` examples, and the reported denominator also becomes `N`. `--resume` should be used with the same model, endpoint, and predictions file as the interrupted run; it fills only missing or empty SQL entries. `--reuse-database` keeps the current Docker volume and skips CSV reload. `--workers` controls concurrent model requests and defaults to 1; it can also be set with `MODEL_WORKERS`. Choose a value within the provider's rate limits.

To evaluate an existing submission without calling a model:

```bash
python run_benchmark.py --predictions predictions.json
```

## Anonymization

The public schema and evaluation set were produced with deterministic replacement rules:

- The internal database/schema qualifier was replaced with the neutral `maritime` qualifier in SQL, table metadata, dictionary keys, DDL, and comments.
- Identifiable vessel names, company names, IMO values, MMSI values, operational UUIDs, and record-derived examples were replaced with anonymized values.
- The same source entity maps to the same anonymized entity across natural-language questions and SQL.
- Internal sequence names, stale object references, and copied index-name suffixes were normalized.
- Public port, country, route-node, special-region, and sea-area scalar coordinates were rounded to 1 decimal place (roughly 10 km order, latitude-dependent).
- Vessel positions and relevant times in the executable package were anonymized or reconstructed and are not suitable for real-world inference.
- Original geometry fields and unused composite location strings were removed from the public package.
- Public domain terminology and standard domain codes, including vessel/event categories, geographic names, and public port codes, were retained where needed to preserve benchmark semantics. Some public names and codes can still be linked with external sources.
- The confidential mapping between source and released values is not distributed.
- The package was adapted to the fixed snapshot and validated so every reference query returns a meaningful nonempty result.

Anonymization changes database literals. The released question-SQL pairs preserve benchmark semantics, but the SQL does not run against the original source database.

The residual check summarized in `data/manifest.json` is limited and cannot rule out re-identification risk.

## Evaluation Scope and Limitations

Execution accuracy (EX) is the primary Text-to-SQL metric, with execution error rate reported as an additional metric. Release validation confirmed that all 585 gold queries execute successfully with nonempty results, and using the gold SQL as predictions yields EX=100%.

## Citation

Use `CITATION.cff` for benchmark citation metadata. The manuscript has no assigned DOI, volume, issue, or article number at the time of this release. Update the following entry after publication:

```bibtex
@article{zhang2026structure,
  author  = {Zhang, Haoyu and Zou, Yingqi and Wang, Xiangyu and Wang, Shaohan and Zhang, Zijian},
  title   = {SCDS: Data Synthesis with Structural Priors via Large Language Models for Text-to-SQL},
  year    = {2026},
  note    = {Manuscript; publication metadata pending}
}
```

## License

This repository is a multi-license distribution. See `LICENSE` for the overview, `LICENSE-CODE` for the MIT terms, and `LICENSE-DATA` for the CC BY 4.0 terms.

- `LICENSE-CODE` (MIT) applies to `benchmark.py`, `model_inference.py`, `run_benchmark.py`, `database/generate_schema.py`, `database/load_data.py`, `tests/`, `compose.yaml`, and `requirements.txt`.
- `LICENSE-DATA` (CC BY 4.0) applies to `evaluation_data_anonymized.json`, `data/`, `schema_anonymized.py`, `database/schema.sql`, `scds_prompts.py`, `README.md`, `README.zh-CN.md`, and `CITATION.cff`.
- Generated model outputs under `results/` and local prediction/report files are not distributed with this release and are not covered unless explicitly stated otherwise.

Authorization for this release has been confirmed. Third-party materials, if any, retain their own rights and licenses.
