# Migrating from v2.x

v3.0 restructured the package into layered modules (`core/`, `io/`, `patterns/`, `utils/`) and replaced the stringly-typed management methods with explicit ones. This page covers everything needed to move a v2.x integration to v3.x.


### Import path changes

```python
# v2.x
from allyanonimiser.enhanced_analyzer import EnhancedAnalyzer
from allyanonimiser.dataframe_processor import DataFrameProcessor
from allyanonimiser.validators import validate_regex

# v3.0
from allyanonimiser.core.analyzer import EnhancedAnalyzer
from allyanonimiser.io.dataframe_processor import DataFrameProcessor
from allyanonimiser.core.validators import validate_regex

# Top-level imports still work for the main API:
from allyanonimiser import create_allyanonimiser, EnhancedAnalyzer, DataFrameProcessor
```

### API changes

```python
# v2.x — stringly-typed
ally.manage_acronyms(action="add", data={"TPD": "Total and Permanent Disability"})
ally.manage_acronyms(action="get")
ally.manage_acronyms(action="remove", data=["TPD"])
ally.manage_patterns(action="create_from_examples", entity_type="MY_ID", examples=[...])
ally.manage_patterns(action="load", filepath="patterns.json")

# v3.0 — explicit methods
ally.add_acronyms({"TPD": "Total and Permanent Disability"})
ally.get_acronyms()
ally.remove_acronyms(["TPD"])
ally.create_pattern_from_examples(entity_type="MY_ID", examples=[...])
ally.load_patterns("patterns.json")
```

### Removed

- `setup.py` — use `pyproject.toml`
- `generators/` module (was stubs only)
- `InsuranceEmailAnalyzer`, `MedicalReportAnalyzer` (were stubs only)
- All deprecated wrapper methods (`set_acronym_dictionary`, `create_dataframe_processor`, etc.)

### New: Configurable entity priority

```python
from allyanonimiser.core.anonymizer import EnhancedAnonymizer, DEFAULT_ENTITY_PRIORITY

# Override priorities for your use case
custom_priority = {**DEFAULT_ENTITY_PRIORITY, "MY_CUSTOM_TYPE": 95}
anonymizer = EnhancedAnonymizer(analyzer=analyzer, entity_priority=custom_priority)
```

