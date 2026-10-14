template_analysis = """
## Role
You are a data analysis expert specializing in "business-perspective enumeration."

Your task is:
Based on a given SQL Template, a Database Schema, and an Example SQL, propose exactly **3** unique business observation objectives: exactly one **Simple**, one **Moderate**, and one **Challenging** objective.

## Input Data
SQL Template: {template}
Database Schema: {schema}
example SQL: {example}

---

## Core Principle: Scenario Discovery

- SQL Template Description:
  - The template preserves the data-source graph, table aliases, JOIN sequence and predicates, nesting boundaries, and the presence and position of structural operators such as GROUP BY, ORDER BY, and LIMIT.
  - Generated objectives may change clause-level semantics only within the slots already exposed by the template.
  - Do not require adding, removing, or moving a JOIN, subquery boundary, GROUP BY, ORDER BY, or LIMIT operator.
  - **Innovation & Non-Duplication:** Your proposed business objective **MUST NOT** be the same as or highly similar to the provided `Example SQL`. You must explore a different business angle, customer segment, or operational scenario while staying within the constraints of the SQL Template.

- Your task is not to repeat the template conditions, but to **select reasonable, realistic, and executable specific values for these WHERE columns based on the Schema**, thereby forming a complete and actionable business query objective.

---

## ⚠️ Key Mandatory Constraints (Must be followed)

### 1. Explicit WHERE Values (Placeholders Forbidden)

- For every column appearing in the WHERE clause of the SQL template:
  - You must explicitly specify a [specific value] in the business observation objective.
  - This value must come from the Schema's:
    - Enumerated example values.
    - Realistic values within the legal range.
    - Example values provided in Schema comments.

- ❌ Vague expressions are strictly prohibited:
  - "A certain / A type of / A certain range"
  - "Specific value / Designated value / Reasonable value / Specified"
  - "[val] / Any value / Variable value" — You must determine specific database values; this is crucial.

- ✅ Correct Examples:
  - "school_metro = 'urban'"
  - "poverty_level IN ('high poverty', 'highest poverty')"
  - "school_state = 'CA'"

> If a tier cannot be represented using legal values and the retained template structure, keep its position in the three-object output, set `is_feasible` to false, set `target` to null, and explain the reason. Do not invent a value or alter the topology.

---

### 2. Clause Semantic Requirements

- You need to determine:
  - Within the business cohort defined by the current template + specific WHERE values:
  - Which fields in the Schema are worth observing as dimensions?
- You may choose the projected columns, filters, aggregation expressions, grouping keys, and ordering expressions only when the corresponding slots exist in the template.
- You must not introduce a structural operator that is absent from the template or remove one that is present.

---

## Difficulty Classification (Based on the premise of determined WHERE values)
 **Required coverage:** Output exactly one objective from each tier below, in the order Simple, Moderate, Challenging.
### Simple
- Within the scope of the [specific business cohort] defined by the WHERE clause in the template.
- Directly observe basic attributes of a single business entity.
- Or related attributes reachable through JOINs.
- Do not introduce aggregation, grouping, sorting, or cross-record calculation logic.

### Moderate·
- Based on the business cohort with determined WHERE values.
- Use grouping, sorting, or limited aggregation.
- Characterize structural features or comparative relationships.
- Do not involve ratios, proportions, or explicit numerator/denominator calculations.

### Challenging
- Use the [entire business cohort] defined by the WHERE clause in the template as the overall denominator.
- Explicitly introduce a sub-group that meets additional conditions.
- Describe the proportion or position of the sub-group within the whole through ratios, percentages, or implicit numerator/denominator relationships.

---

## Business Relevance Requirements

- The business observation objectives you generate must:
  - Highly align with the business domain of the Schema.
  - Reflect valuable concerns or metrics in real-world business scenarios.
- Avoid objectives that are abstract, vague, non-executable, or "complex for the sake of complexity."

---

## Output Format (Strict JSON)

Only JSON output is allowed; no explanatory text is permitted.

[
  {{ "difficulty": "Simple", "is_feasible": true, "reason": null, "target": "Business observation objective with explicit filter values" }},
  {{ "difficulty": "Moderate", "is_feasible": true, "reason": null, "target": "Business observation objective with explicit filter values" }},
  {{ "difficulty": "Challenging", "is_feasible": true, "reason": null, "target": "Business observation objective with explicit filter values" }}
]

"""

template_anlysis = template_analysis



IR = """
## Role
You are a rigorous [Database Query Specification Designer].
Your task is to convert the three natural-language query targets into three SQL-executable semi-structured Intermediate Representations (IRs). This is a semantic-planning stage. Do not instantiate SQL in this stage.

The system uses a semi-frozen SQL template:
- The data-source graph, table aliases, JOIN sequence and predicates, nesting boundaries, and the presence and position of structural operators are fixed.
- Clause-local semantic expressions may be represented by slots such as SELECT_CLAUSE, WHERE_CLAUSE, GROUP_BY_CLAUSE, and ORDER_BY_CLAUSE.
- Structural operators that are absent from the template must not be introduced.

You must:

- Keep all retained structural elements unchanged.
- Specify the semantic content for existing clause slots based on the Target and Schema.

- WHERE columns are not pre-fixed; you may introduce necessary filtering conditions derived from the Target.

- All selected fields and filtering conditions must come from the provided Schema.

---

## Input Data
- Query Targets (three Business Blueprints ordered Simple, Moderate, Challenging): {target}
- SQL Template (Join + Where Backbone): {template}
- Database Schema: {schema}
- Example Filled SQL: {example}
---

## Core Principles (Execution Accuracy)

### 1. Target Fidelity
- The IR must strictly and completely implement the business semantics described in the Target.
- Do not omit any conditions, observation dimensions, or calculation goals implied in the Target.

### 2. Template Awareness
- You must preserve the data-source graph, aliases, JOIN sequence and predicates, nesting boundaries, and the presence and position of GROUP BY, ORDER BY, and LIMIT.
- SELECT, WHERE, grouping keys, ordering expressions, and other clause-local slots must be specified based on the Target.
- Do not add, remove, or move a structural operator.
- All columns must belong to the tables included in the template.


### 3. Schema Compliance
Table and column names must exist in the Schema.

Values must be:

Real example values from the Schema,

Enumerated values,

Or reasonably inferable values under field type constraints.

Forbidden vague expressions:

"certain"

"any"

"specified"

"[val]"

"reasonable value"

### 4. Principle of Minimality and Necessity (No Overreach)
- Use a grouping, ordering, or limit requirement only when both the Target requires it and the corresponding structural operator or slot exists in the template.
- If a Target cannot be represented by the retained template structure, set `sql_feasibility_check.is_feasible` to false instead of changing the topology.
- Every semantic decision must be logically derived from the Target.

### 5. Downstream SQL Executability Requirements
The IR must provide enough unambiguous information for the downstream assembler to produce an executable, placeholder-free SQL query.

Literal-planning rules:
  - Strings must be quoted.
  - Dates must follow YYYY-MM-DD format.
  - Numbers must not be quoted.

---

## 💡 Example Reference Logic (learning from the benchmark)

- **Structural Benchmark**: The `example SQL` demonstrates a successful implementation of the template. Use it to understand how to:
  - Extract realistic values from the Schema to replace [val].
  - Construct the SELECT and GROUP BY clauses to match the business complexity.
- **Reference, Don't Copy**: 
  - The `example SQL` is a reference for **format and depth**, not content.
  - The IR must be driven by the current `{{target}}`, not by the content of `{{example}}`.
  - If the `{{target}}` implies a different business focus than the `{{example}}`, prioritize the `{{target}}`.
- **Consistency**: Ensure the "granularity" of your generated IR (e.g., the choice of dimensions in `required_columns`) is consistent with the professional level shown in the `example SQL`.
---

## IR Design Requirements (For Unique SQL Reconstruction)

You must explicitly decompose the Target into the following structured elements:

### 1. query_intent
- LIST: Returns a list of detailed records.
- VALUE: Returns a single numerical value (e.g., total count, ratio, a specific value).
- SUMMARY: Returns grouped summary results.

### 2. filter_logic (Filtering Logic - Completing WHERE values only)
  - You may introduce necessary filtering conditions.

  - Each condition must specify:
    - table
    - column
    - operator
    - value
  - The value must be an executable literal.


### 3. required_columns (Result Fields - Defining the SELECT clause)
For each output field, specify:
   - table
   - column (or EXPR if calculated)
   - aggregation (NONE / COUNT / SUM / AVG / MIN / MAX)
If a calculated field is required:
  - Use "EXPR" as column,
  - Define its structure in calc_spec.
### 4. aggregation_spec (Aggregation and Grouping)
- type: NONE / SINGLE_AGG / GROUP_AGG.
- group_by: Fill only when type is GROUP_AGG; otherwise, must be [].

### 5. ordering_spec (Sorting)
- Fill only if the Target implies sorting; otherwise, must be null.
- Content: {{ column: "table.column|EXPR", direction: "ASC|DESC" }}.

### 6. limit_spec (Limit)
- Fill only if the Target explicitly implies a Top/Single result; otherwise, must be null.

### 7. result_cardinality
- SINGLE_VALUE / MULTI_ROW.

### 8. sql_feasibility_check
- is_feasible: true/false.
- reason: Briefly state the reason.

### 9. filled_template_sql (Traceability Field)
- In this semantic-planning stage, this field must be `null`.
- The downstream SQL-instantiation stage will populate it with the concrete executable SQL for traceability.


### 10. calc_spec (Optional, required only if required_columns contains EXPR)
- Use a strict structure to describe the calculation expression for unique reconstruction:
  - op: "DIVIDE|MULTIPLY|SUBTRACT|ADD|CASE_WHEN".
  - args: Array of sub-expressions.
  - numerator/denominator (if it's a ratio).
  - case_when (if it's a conditional count/ratio).

---

## Output Format (Strict JSON)
Only JSON output is allowed; no explanatory text is permitted. Output exactly three objects in the order Simple, Moderate, Challenging.
[
  {{
    "difficulty": "Simple",
    "query_intent": "LIST",
    "filter_logic": [
      {{
        "table": "table_name",
        "column": "column_name",
        "operator": "=",
        "value": "real_literal_value"
      }}
    ],
    "required_columns": [
      {{
        "table": "table_name",
        "column": "column_name",
        "aggregation": "NONE"
      }}
    ],
    "aggregation_spec": {{
      "type": "NONE",
      "group_by": []
    }},
    "ordering_spec": null,
    "limit_spec": null,
    "result_cardinality": "MULTI_ROW",
    "sql_feasibility_check": {{
      "is_feasible": true,
      "reason": "supported by schema and template"
    }},
    "calc_spec": null,
    "filled_template_sql": null
  }},
  {{
    "difficulty": "Moderate",
    "query_intent": "SUMMARY",
    "filter_logic": [
      {{
        "table": "table_name",
        "column": "column_name",
        "operator": "=",
        "value": "real_literal_value"
      }}
    ],
    "required_columns": [
      {{
        "table": "table_name",
        "column": "grouping_column",
        "aggregation": "NONE"
      }},
      {{
        "table": "table_name",
        "column": "metric_column",
        "aggregation": "COUNT"
      }}
    ],
    "aggregation_spec": {{
      "type": "GROUP_AGG",
      "group_by": ["table_name.grouping_column"]
    }},
    "ordering_spec": null,
    "limit_spec": null,
    "result_cardinality": "MULTI_ROW",
    "sql_feasibility_check": {{
      "is_feasible": true,
      "reason": "supported by schema and template"
    }},
    "calc_spec": null,
    "filled_template_sql": null
  }},
  {{
    "difficulty": "Challenging",
    "query_intent": "VALUE",
    "filter_logic": [],
    "required_columns": [
      {{
        "table": "table_name",
        "column": "EXPR",
        "aggregation": "NONE"
      }}
    ],
    "aggregation_spec": {{
      "type": "SINGLE_AGG",
      "group_by": []
    }},
    "ordering_spec": null,
    "limit_spec": null,
    "result_cardinality": "SINGLE_VALUE",
    "sql_feasibility_check": {{
      "is_feasible": true,
      "reason": "supported by schema and retained template structure"
    }},
    "calc_spec": {{
      "op": "DIVIDE",
      "args": [
        {{
          "aggregation": "COUNT",
          "filter_logic": ["additional subgroup condition"]
        }},
        {{
          "aggregation": "COUNT",
          "filter_logic": ["overall cohort conditions"]
        }}
      ]
    }},
    "filled_template_sql": null
  }}
]

"""
 

modified_target_prompt = """
## Role
You are a rigorous [SQL Assembler].
Your task is to instantiate exactly three directly executable SQLite queries from the three IR objects, preserving the retained SQL-template topology exactly.

You must strictly follow the declarations in the IR and must not infer, supplement, or modify any business logic not explicitly provided in the IR.

---

## Input Data

- **SQL Template (Join + Where Backbone):** `{template}`  
  Description:
  - The data-source graph, aliases, JOIN sequence and predicates, nesting boundaries, and the presence and position of structural operators are fixed.
  - Replace only the clause-local slots that occur in the template.
  - Do not add, remove, or move a JOIN, subquery boundary, GROUP BY, ORDER BY, or LIMIT operator.

- **Semi-structured Query Specification (IR):** `{IR}`  
  Description:
  - The IR is the single source of truth.
  - The IR explicitly provides:
    - `filter_logic` (used to fill values in the `WHERE` clause)
    - `required_columns` (used to construct the `SELECT` clause)
    - `aggregation_spec` (whether `GROUP BY` is needed)
    - `ordering_spec` (whether `ORDER BY` is needed)
    - `limit_spec` (whether `LIMIT` is needed)

- **Database Schema:** `{schema}`

---

## Absolute Rules (Mechanized Synthesis / Zero Inference)

### 1. IR is the Single Source of Truth
- Every field appearing in the `SELECT` clause must come from `IR.required_columns`.
- Every value in the `WHERE` clause must come from `IR.filter_logic`.
- Grouping keys, ordering expressions, and limit values can be filled only when the corresponding operator or slot exists in the template and is explicitly specified by the IR.
- If `IR.sql_feasibility_check.is_feasible = false`:
  - Do not fabricate or repair SQL.
  - Set `filled_template_sql` to null for that object.

---

### 2. Template Constraints (Unbreakable)
- ❌ Do not modify the data-source graph, aliases, JOIN sequence or predicates, nesting boundaries, or the presence and position of structural operators.
- ❌ Do not introduce tables not present in the template.
- ✅ Replace only existing semantic slots with expressions declared in the IR.

---

### 3. Clause Synthesis Rules

#### 3.1 SELECT Clause (`[SELECT_CLAUSE]`)
Construct strictly from IR.required_columns.
Each field must follow:
- table_alias.column
- or AGG_FUNC(table_alias.column) when aggregation ≠ NONE
- or the expression defined in calc_spec (if column = EXPR)

Rules:
- Use the exact table aliases defined in the template (e.g., T1, T2).
- Separate fields using commas.
No additional fields beyond IR.


#### 3.2 WHERE Clause (Value Filling)
Construct strictly from IR.filter_logic.

For each condition:
- Use exact table alias
- Use exact column
- Use exact operator
- Use exact value

Rules:
-  Join multiple conditions using AND
-  Preserve logical structure as implied by IR
-  Strings must use single quotes 'value'
-  Dates must follow YYYY-MM-DD
-  Numbers must not be quoted
-  No placeholders may remain

#### 3.3 GROUP BY Clause
- Fill a GROUP BY slot if and only if the template contains that slot and `IR.aggregation_spec.type = GROUP_AGG`:
  - The `GROUP BY` fields must include all non-aggregated columns in the `SELECT` clause.
- Do not add or remove the GROUP BY operator itself.

#### 3.4 ORDER BY Clause
- Fill only an existing ORDER BY slot and only if `IR.ordering_spec` exists.
- Must strictly use the column and sort direction (`ASC` / `DESC`) specified in the IR.
- Do not add or remove the ORDER BY operator itself.

#### 3.5 LIMIT Clause
- Fill only an existing LIMIT slot and only if `IR.limit_spec ≠ null`.
- The `LIMIT` value must be exactly consistent with the IR.
- Do not add or remove the LIMIT operator itself.

---

### 4. Zero Placeholder Residue
- The final SQL must not contain:
  - `[SELECT_CLAUSE]`
  - `[WHERE_CLAUSE]`
  - `[val]`
  - `{{ }}`
  - Or any other unreplaced template placeholders.

---

## Assembly Workflow (Must be Followed)

1. **SELECT Mapping** - Map `IR.required_columns` → `SELECT` expression list.

2. **WHERE Mapping** - Map `IR.filter_logic` → Fill values into the template's `WHERE` clause.

3. **Aggregation Processing** - Fill an existing grouping slot according to `IR.aggregation_spec`.

4. **Ordering and Limiting** - Fill existing ordering and limit slots based on `IR.ordering_spec` / `limit_spec`.

5. **Final Integration** - Inject all generated fragments into the template.
   - Ensure the SQL syntax is complete and executable.

6. **Verification** - All table names / column names / aliases must be consistent with the Schema and template, and all retained structural elements must match the template exactly.

7. **Traceability Update** - Populate the corresponding IR object's `filled_template_sql` field with the assembled SQL. Runtime execution validation occurs after this stage and is not simulated here.

---

## Output Format (Strict JSON)
Only JSON output is allowed; no explanatory text is permitted. Output exactly three objects in the order Simple, Moderate, Challenging.

[
  {{
    "difficulty": "Simple",
    "filled_template_sql": "The complete executable SQLite SQL for the Simple IR"
  }},
  {{
    "difficulty": "Moderate",
    "filled_template_sql": "The complete executable SQLite SQL for the Moderate IR"
  }},
  {{
    "difficulty": "Challenging",
    "filled_template_sql": "The complete executable SQLite SQL for the Challenging IR"
  }}
]

"""

sql_generation_prompt = modified_target_prompt


execution_validation_spec = {
  "stage": "between_sql_instantiation_and_question_generation",
  "dialect": "SQLite",
  "timeout_seconds": 15,
  "retain_only_if_execution_succeeds": True,
  "preserve_sql_text_for_downstream_stages": True,
  "note": (
    "Execution success checks runtime validity, schema compatibility, and "
    "termination only; it does not prove semantic equivalence to the intent."
  ),
}


query_generation_prompt = """
# Role
You are a [Strict] SQL → Natural Language Query (NL Query) Translation Expert.
Your sole task is to translate a given SQL query into a **natural language question that a real user would likely ask**.

Your highest priority goal is:
**Zero Semantic Drift** (The natural language question must be business-semantically equivalent to the SQL).

---

# Input Data
- Execution-validated SQL candidates: {sql_generation}
- Database Schema: {schema}

Only candidates that executed successfully within the external 15-second timeout may be provided to this prompt. Do not process null, infeasible, timed-out, or failed candidates.

---

# Core Principles (Must be Strictly Followed)

## 0️⃣ SQL is the Single Source of Truth (Highest Priority)
- Each SQL candidate has already passed external execution validation and must remain byte-for-byte unchanged.
- The **conditions, calculation logic, statistical objects, granularity, sorting, and limits** appearing in the SQL are the only facts allowed to be expressed.
- The natural language question must **faithfully "translate" the meaning of the SQL** and must not:
  - Infer business meanings not explicitly expressed in the SQL.
  - Automatically "correct" or "optimize" the SQL logic.
  - Upgrade record-level granularity into entity-level semantics without an explicit grouping or deduplication operation.

---

## 1️⃣ Semantic Equivalence (Must Cover Item by Item)
The generated natural language question **must explicitly cover all semantic elements of the SQL**, including:

- Filtering conditions (all restrictions in the WHERE clause).
- Granularity of statistical objects (e.g., entity level, event level, transaction level, relationship level, or raw-record level).
- Aggregation and calculation meanings:
  - COUNT → quantity / frequency / number of records.
  - SUM → total amount / total quantity.
  - AVG → average value.
  - Ratio → proportion / percentage.
- Grouping dimensions (business classification methods corresponding to GROUP BY).
- Sorting rules (metrics and direction of ORDER BY).
- Quantity limits (LIMIT / Top N).

⚠️ **If the SQL calculation logic is at the "record level" rather than the "entity level," the NLQ must maintain this logic and must not upgrade it.**

---

## 2️⃣ Granularity Consistency (Strong Constraint)
When generating questions, explicitly determine whether the SQL operates at entity, event, transaction, relationship, or raw-record granularity from its FROM/JOIN structure and aggregation keys.

❌ Do not upgrade a record count into an entity count, or an event-level statistic into an entity-level statistic, unless the SQL explicitly performs the required grouping or deduplication.

---

## 3️⃣ User Perspective + Colloquialism (Without Breaking Semantics)
- The language should align with the questioning habits of real business users—natural and colloquial.
- You may use phrases like:
  - "I'd like to know..."
  - "Can you help me look at..."
  - "I want to calculate..."
- **But only on the premise that it does not change the statistical logic or boundaries of the SQL.**

---

## 4️⃣ Zero SQL Trace (Expression Level)
- Do not include the following in the question:
  - Table names or field names.
  - Engineering terms like "SQL," "database," or "query."
- You must convert field names into accurate business meaning descriptions:
  - Use the column descriptions and table semantics in the provided Schema.

---

## 5️⃣ No Semantic Enhancement or Weakening
- Do not automatically interpret:
  - `COUNT(*)` as a count of business entities unless the SQL operates at that entity granularity.
  - "LIMIT N" as "the last N days" (unless the SQL has an explicit time filter).
- Do not add:
  - Time ranges.
  - Deduplication assumptions.
  - Causal or trend descriptions.

---

## 6️⃣ Output Format (Strict)
- Output only a JSON array.
- Output exactly one object for each supplied execution-validated SQL candidate, preserving candidate order and difficulty label. Execution filtering may result in fewer than three candidates.
- Each element must contain exactly three fields:
  - "difficulty": Preserve the corresponding Simple / Moderate / Challenging label.
  - "sql": Output the SQL from {sql_generation} exactly as is, without modifying any characters.
  - "query": The natural language question strictly equivalent to that SQL.
- Prohibit the output of:
  - Markdown formatting.
  - Comments.
  - Explanatory text.
  - Redundant fields.


Output Format (Strict JSON)
Important Hint: Output the raw JSON array directly! Prohibit the use of any Markdown code block tags (such as json), and do not include any explanatory text.

[
    {{
    "difficulty": "Simple",
        "sql": "<SQL statement>",
        "query": "<final query corresponding to the SQL>"
    }},
    {{
    "difficulty": "Moderate",
        "sql": "<SQL statement>",
        "query": "<final query corresponding to the SQL>"
    }},
    {{
    "difficulty": "Challenging",
        "sql": "<SQL statement>",
        "query": "<final query corresponding to the SQL>"
    }}
]

"""





cot_prompt = """
    You are an expert data scientist and SQL reasoning assistant.

    You are given:
    - A database schema
    - A natural language question
    - The execution-validated SQL query that semantically anchors the question
    {cot_seq}
    Here is the execution-validated SQL query:
    ```sql
    {sql}
    ```
    Your task is to read the database schema and the natural language question, then produce:

    1. A detailed, step-by-step reasoning process that explains how to derive the SQL query from the schema and the question.
    2. The same execution-validated SQL query, reproduced without changing any character.

    Important instructions:
        - The reasoning must be fully self-contained and must be written as if you are deriving the SQL from scratch.
        - The reasoning MUST NOT mention or imply the existence of ground truth, a provided answer, or a correction process.
        - Do NOT fix, modify, optimize, normalize, or compare the SQL.
        - Do NOT mention correctness verification, supervision, evaluation, or comparison.
        - The reasoning should only describe how the SQL logically follows from the schema and the question.

    The validated SQL is the semantic anchor.
      - Explain its observable operations without referring to it as a reference or ground-truth answer.
      - It MUST NOT be evaluated, criticized, compared, corrected, or optimized.
      - Every reasoning step must remain consistent with its tables, joins, filters, aggregations, grouping, ordering, and limits.
    Reasoning Style Constraint:
        Your reasoning must be written as a genuine from-scratch derivation process.
        Assume that you have only been given the database schema and the natural language question.
        You must reason forward step by step, introducing tables, columns, joins, filters, and aggregations only when they become logically necessary.
        Do not use language that suggests hindsight, prior knowledge, correction, optimization, or alignment with any existing SQL.
        The reasoning should read naturally as an initial analytical process, not as an explanation of a known or pre-existing solution.


    Your final answer must strictly follow this format:
    [Detailed reasoning steps]

    ```sql
    [Final correct SQL query]
    ```
    Do NOT include comments inside the SQL block.
    Reproduce the validated SQL exactly. If the question and SQL appear inconsistent, do not repair either artifact; report no reasoning output for that item so it can be excluded upstream.
"""
    