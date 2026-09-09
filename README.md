# MaritimeSQLBench

[English](README.md) | [简体中文](README.zh-CN.md)

MaritimeSQLBench is a domain-specific Text-to-SQL benchmark accompanying the manuscript **"Structure-Constrained Data Synthesis for Domain-Specific Text-to-SQL."** The evaluation set contains 585 Chinese natural-language questions paired with PostgreSQL reference queries for maritime scenarios involving vessels, ports, shipping indices, and maritime regulation.

> **Release status:** This initial release publishes the anonymized schema context for 10 tables. The anonymized evaluation set will be released in a later repository version after the remaining review and release procedures are complete.

The current release does not contain evaluation question-SQL pairs, the source database, table contents, query results, model outputs, or training data.

## Files

| File | Description |
| --- | --- |
| `schema_anonymized.py` | Python dictionary containing DDL-like schema descriptions, field comments, categorical values, and synthetic examples for the 10 tables released at this stage. |
| `README.zh-CN.md` | Chinese documentation. |
| `LICENSE` | Creative Commons Attribution 4.0 International notice. |

The evaluation data, source files, and confidential anonymization mappings are intentionally excluded from this release.

## Planned Evaluation-Set Release

The following statistics describe the 585-example evaluation set. The corresponding anonymized JSON file is **not included in the current release** and is planned for a later version.

| Difficulty | Description | Examples | Share |
| --- | --- | ---: | ---: |
| Simple (`简单`) | Basic filtering, projection, or simple aggregation | 212 | 36.23% |
| Moderate (`中等`) | Two-table joins with aggregation, or basic queries with subqueries/time windows | 316 | 54.02% |
| Challenging (`复杂`) | Multi-table joins, window functions, unions, grouped aggregation, or combined time-range logic | 57 | 9.74% |
| **Total** |  | **585** | **100%** |

At this stage, this repository releases the 10 schema tables referenced by the forthcoming evaluation pairs.

The forthcoming evaluation data includes a `difficulty_score` ranging from 0 to 7. The release documentation does not define an exact scoring formula, so the score must not be interpreted as a calibrated or linear measure. `difficulty_reasons` records the structural signals associated with each assigned score.

## Planned Record Format

When released, the evaluation JSON file will be a top-level array in which each record contains:

| Field | Type | Description |
| --- | --- | --- |
| `query` | string | Chinese natural-language question. |
| `sql` | string | Anonymized PostgreSQL reference query. |
| `table_names` | string[] | Fully qualified tables referenced by the query. |
| `difficulty` | string | One of `简单`, `中等`, or `复杂`. |
| `difficulty_score` | integer | Structural difficulty score from 0 to 7. |
| `difficulty_reasons` | string[] | Structural factors associated with the score; may be empty. |

Illustrative format:

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

## Schema Coverage

The 10 currently released tables describe vessel master data, vessel dynamics, vessel events, current voyage state, ports and berths, port efficiency, and shipping indices.

The following 10 tables are available in the current schema release and occur in the 585 reference queries planned for a later release:

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

`schema_anonymized.py` is model context, not a production migration. Its SQL strings include comments, parent partition declarations, PostGIS types, and descriptive sample blocks. They are provided to communicate schema semantics and are not guaranteed to execute as a standalone database deployment.

## Loading the Schema

```python
from schema_anonymized import schema_dict

print(len(schema_dict))  # 10
print(schema_dict["maritime.vessel_reference"])
```

The schema descriptions use PostgreSQL syntax and include PostGIS-related types.

## Anonymization

The public schema was produced with deterministic replacement rules. The same rules have also been applied to the evaluation set being prepared for a later release:

- The internal database/schema qualifier was replaced with the neutral `maritime` qualifier in SQL, table metadata, dictionary keys, DDL, and comments.
- Identifiable vessel names, company names, IMO values, MMSI values, operational UUIDs, and record-derived examples were replaced with synthetic values.
- The same source entity maps to the same synthetic entity across natural-language questions and SQL.
- Internal sequence names, stale object references, and copied index-name suffixes were normalized.
- Public domain terminology and standard domain codes, including vessel/event categories, geographic names, and public port codes, were retained where they are necessary to preserve task semantics.
- The confidential source-to-synthetic mapping is not distributed.

Anonymization changes database literals. Therefore, the reference SQL in the forthcoming evaluation release will be structurally aligned with the questions but will not be intended to run against the original source database.

## Evaluation Scope and Limitations

Execution accuracy (EX) is the primary Text-to-SQL metric, with execution error rate reported as an additional metric. This repository alone cannot reproduce those metrics because it does not distribute an executable database snapshot or expected query-result sets.

The current schema-only release is suitable for:

- schema linking research and prompt construction;
- analysis of maritime database structure and field semantics;
- preparation of Text-to-SQL systems for the later evaluation-set release.

It is not yet possible to evaluate systems on MaritimeSQLBench using this release alone. The evaluation pairs are planned for a later version. The underlying database, generated training set, sampling scripts, model checkpoints, and model outputs are also not included.

## Citation

The manuscript has no assigned DOI, volume, issue, or article number at the time of this release. Update the following entry after publication:

```bibtex
@article{zhang2026structure,
  author  = {Zhang, Haoyu and Zou, Yingqi and Wang, Xiangyu and Wang, Shaohan and Zhang, Zijian},
  title   = {Structure-Constrained Data Synthesis for Domain-Specific Text-to-SQL},
  year    = {2026},
  note    = {Manuscript; publication metadata pending}
}
```

## License

Unless otherwise noted, the released anonymized schema and repository documentation are licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). Reusers must provide appropriate attribution, link to the license, and indicate whether changes were made. The license status of future release artifacts will be stated when those artifacts are published.

The license applies only to rights that the licensors are authorized to grant. Before public release, repository maintainers should confirm that all required institutional approvals for publishing the derived benchmark have been obtained.
