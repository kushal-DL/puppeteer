# File Discovery & Input Catalog Pattern

## Problem Statement

The current `core_runner.py` architecture has a critical limitation:

```python
# Current approach: single hardcoded INPUT_PATH
def _read_raw_export(raw_path: str) -> DataFrame:
    """Read raw input with ORC preferred and JSON fallback."""
    df = spark.read.format("orc").load(raw_path)
    return df
```

**Real-world scenarios that break this:**

1. **Multiple files in same S3 bucket**
   - Raw data ingested hourly → 24 files/day in `s3://raw-data/expenses/2026-04-09/`
   - Core expects ONE path, but needs to discover and load which hourly partition(s)?

2. **Multiple source files required for one pass**
   - Pass 1: Need both `expenses/*.orc` AND `expense_metadata/*.orc` to join
   - Can't pass two `INPUT_PATH` args; doesn't scale to N sources

3. **Multiple S3 buckets**
   - Expenses in `s3://raw-expenses-prod/`
   - Travel codes in `s3://reference-data-prod/`
   - Policy rules in `s3://business-rules-prod/`
   - How do we instruct core_runner where to find each?

**Current behavior:** Passes only fail at runtime when `INPUT_PATH` is wrong. No way for strategy to influence file selection.

---

## Proposed Solution: Input Catalog Pattern

**Principle:** Move file discovery responsibility to the strategy layer. `core_runner` remains dumb and orchestrates reading; strategy contains all domain knowledge.

### Architecture

```python
# BaseStrategy interface gets new method:

@abstractmethod
def get_input_catalog(self, pass_id: int) -> InputCatalog:
    """
    Return a catalog describing which files/buckets to load for this pass.
    
    The strategy owns the logic: which partitions, which buckets, which format.
    core_runner is relegated to mechanical reading + union logic.
    """
```

### InputCatalog Data Structure

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class DataFormat(Enum):
    ORC = "orc"
    JSON = "json"
    PARQUET = "parquet"
    CSV = "csv"

@dataclass
class DataSourceSpec:
    """Defines a single data source to read."""
    name: str  # e.g., "primary_expenses", "reference_codes", "policy_rules"
    path: str  # e.g., "s3://raw-expenses-prod/2026-04-09/hourly-11/"
    format: DataFormat = DataFormat.ORC
    required: bool = True  # Fail if this file not found?
    allow_empty: bool = False  # OK if file has 0 rows?
    schema_validation: Dict[str, str] | None = None  # optional: {"col": "type"}
    options: Dict[str, Any] | None = None  # format-specific read options

@dataclass
class InputCatalog:
    """Catalog of all files to load for a single pass."""
    pass_id: int
    sources: List[DataSourceSpec]
    union_strategy: str = "concat"  # "concat" (union all) or "cogroup" (call strategy.union_sources())
```

### Updated core_runner Logic

```python
def _load_inputs_from_catalog(spark: SparkSession, catalog: InputCatalog) -> Dict[str, DataFrame]:
    """
    Generic loader: read all sources in catalog, return dict keyed by source.name
    """
    loaded = {}
    for source_spec in catalog.sources:
        try:
            df = _read_source(spark, source_spec)
            loaded[source_spec.name] = df
            print(f"[CATALOG] Loaded '{source_spec.name}' from {source_spec.path}; rows={df.count()}")
        except FileNotFoundError as e:
            if source_spec.required:
                raise ValueError(f"Required source '{source_spec.name}' not found") from e
            else:
                print(f"[CATALOG] Optional source '{source_spec.name}' missing; continuing")
                loaded[source_spec.name] = None
    
    # Merge all into single DataFrame (strategy can customize merge logic)
    if catalog.union_strategy == "concat":
        non_null_dfs = [df for df in loaded.values() if df is not None]
        if not non_null_dfs:
            raise ValueError("All input sources were empty/missing")
        return non_null_dfs[0] if len(non_null_dfs) == 1 else non_null_dfs[0].unionByName(*non_null_dfs[1:])
    elif catalog.union_strategy == "cogroup":
        return strategy.union_sources(loaded)  # Delegate join logic to strategy


def _read_source(spark: SparkSession, spec: DataSourceSpec) -> DataFrame:
    """
    Generic reader: ORC → JSON fallback, per-format options support.
    """
    format_name = spec.format.value
    options = spec.options or {}
    
    try:
        if spec.format == DataFormat.ORC:
            return spark.read.format("orc").options(options).load(spec.path)
        elif spec.format == DataFormat.JSON:
            return spark.read.format("json").options(options).load(spec.path)
        elif spec.format == DataFormat.PARQUET:
            return spark.read.format("parquet").options(options).load(spec.path)
        else:
            raise ValueError(f"Unsupported format: {spec.format}")
    except Exception as read_error:
        if spec.format == DataFormat.ORC:
            print(f"[CATALOG] ORC read failed; falling back to JSON: {read_error}")
            return spark.read.format("json").options(options).load(spec.path)
        raise


# In main orchestration loop:
if __name__ == "__main__":
    strategy = _load_strategy(args["STRATEGY_MODULE"])
    pass_id = int(args["PASS_ID"])
    output_path = args["OUTPUT_PATH"]
    context = optional_args.get("CONTEXT_PATH", "")

    # NEW: Strategy provides input catalog, core_runner reads it
    catalog = strategy.get_input_catalog(pass_id)
    loaded_sources = _load_inputs_from_catalog(spark, catalog)
    
    # If multiple sources → strategy decides merge logic
    if len(loaded_sources) == 1:
        input_df = loaded_sources[0]
    else:
        input_df = strategy.union_sources(loaded_sources)
    
    # Rest of pipeline unchanged
    prefilter_sql = strategy.get_prefilter_sql(pass_id)
    if prefilter_sql:
        input_df = input_df.filter(F.expr(prefilter_sql))
    
    output_dfs = strategy.apply_transform(spark=spark, df=input_df, pass_id=pass_id, context=context)
    
    if output_dfs:
        _write_outputs(output_dfs, output_path, pass_id)

    job.commit()
```

---

## Example: Expense Strategy Implementation

```python
class ExpenseStrategy(BaseStrategy):
    
    def get_input_catalog(self, pass_id: int) -> InputCatalog:
        """
        Expense strategy: load from multiple sources depending on pass.
        """
        if pass_id == 1:
            # Pass 1: Load expense records + metadata
            return InputCatalog(
                pass_id=1,
                sources=[
                    DataSourceSpec(
                        name="expense_records",
                        path="s3://raw-expenses-prod/2026-04-09/",  # Glob: multiple hourly partitions
                        format=DataFormat.ORC,
                        required=True,
                    ),
                    DataSourceSpec(
                        name="expense_metadata",
                        path="s3://reference-data-prod/expense_metadata/",
                        format=DataFormat.ORC,
                        required=True,
                    ),
                ],
                union_strategy="cogroup",  # Delegate join logic to union_sources()
            )
        
        elif pass_id == 2:
            # Pass 2: Load enriched data from Pass 1 + policy rules
            return InputCatalog(
                pass_id=2,
                sources=[
                    DataSourceSpec(
                        name="pass1_enriched",
                        path="s3://pipeline-artifacts/pass1_output/",
                        format=DataFormat.PARQUET,
                        required=True,
                    ),
                    DataSourceSpec(
                        name="policy_rules",
                        path="s3://business-rules-prod/policy_rules/2026-04-09/",
                        format=DataFormat.JSON,
                        required=True,
                    ),
                ],
                union_strategy="cogroup",
            )
    
    def union_sources(self, sources: Dict[str, DataFrame]) -> DataFrame:
        """
        Strategy-specific logic for joining multiple sources.
        core_runner doesn't need to know HOW to join; it delegates.
        """
        expense_df = sources["expense_records"]
        metadata_df = sources["expense_metadata"]
        
        # Domain-specific join logic
        joined = expense_df.join(
            metadata_df,
            on="expenseId",
            how="left",
        )
        return joined
```

---

## Migration Path (Backwards Compatible)

### Phase 1: Add new interface, keep old INPUT_PATH
```python
# core_runner still accepts INPUT_PATH as before
# But if strategy has get_input_catalog(), use it instead
if hasattr(strategy, 'get_input_catalog'):
    catalog = strategy.get_input_catalog(pass_id)
    input_df = _load_inputs_from_catalog(spark, catalog)
else:
    # Fallback: use legacy INPUT_PATH
    input_df = _read_raw_export(args["INPUT_PATH"])
```

### Phase 2: Mandate get_input_catalog() in BaseStrategy
All new strategies must implement it; old ones get deprecation warning.

### Phase 3: Remove INPUT_PATH from job args entirely
Only catalog-driven input is allowed.

---

## Benefits

| Aspect | Current | With Catalog Pattern |
|--------|---------|----------------------|
| **Multiple files** | ❌ Breaks (path is singular) | ✅ List N sources in catalog |
| **Multiple buckets** | ❌ Must hard-code in strategy | ✅ Each source.path can be different bucket |
| **File discovery logic** | ❌ Buried in job config | ✅ Strategy owns it, testable, versionable |
| **Schema validation** | ❌ None | ✅ Optional per-source validation |
| **Format flexibility** | ⚠️ ORC + JSON fallback only | ✅ ORC/JSON/Parquet/CSV, per-source |
| **core_runner complexity** | Simple | Simple (still dumb, just more flexible) |
| **Observability** | Low (just a file path) | High (catalog logged, source-by-source) |
| **Testability** | Hard (mocking paths) | Easy (mock strategy.get_input_catalog()) |

---

## Testing Strategy

```python
# tests/unit/test_input_catalog.py

def test_expense_strategy_pass1_catalog():
    """Validate that expense strategy declares correct sources."""
    strategy = ExpenseStrategy()
    catalog = strategy.get_input_catalog(pass_id=1)
    
    assert len(catalog.sources) == 2
    assert catalog.sources[0].name == "expense_records"
    assert catalog.sources[0].required == True
    
    assert catalog.sources[1].name == "expense_metadata"
    assert catalog.union_strategy == "cogroup"

def test_core_runner_multi_source_union():
    """Validate core_runner correctly union's multiple DataFrames."""
    source1 = spark.createDataFrame([(1, "a")], "id INT, val STRING")
    source2 = spark.createDataFrame([(2, "b")], "id INT, val STRING")
    
    sources = {"s1": source1, "s2": source2}
    result = _load_inputs_from_catalog_test(sources, union_strategy="concat")
    
    assert result.count() == 2
```

---

## References

- **Strategy Pattern:** Encapsulates domain logic; core_runner remains generic
- **Separation of Concerns:** File discovery (strategy) vs. file mechanics (core_runner)
- **YAML Manifest Pattern:** Similar to Kubernetes Pod specs—data catalog is declarative
