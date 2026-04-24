# Installation

Allyanonimiser can be installed using pip with various installation options depending on your needs.

## Prerequisites

- Python 3.12 or 3.13 (spaCy does not yet ship cp314 wheels)
- A spaCy language model (recommended)

## Basic Installation

Install the core package from PyPI:

```bash
pip install allyanonimiser==3.4.0
```

## Installation Options

Allyanonimiser offers several installation options to meet different needs:

### With Stream Processing Support

For processing very large files with memory-efficient streaming:

```bash
pip install "allyanonimiser[stream]==3.4.0"
```

### With LLM Integration

For advanced pattern generation using language models:

```bash
pip install "allyanonimiser[llm]==3.4.0"
```

### Complete Installation

To install all optional dependencies:

```bash
pip install "allyanonimiser[stream,llm]==3.4.0"
```

## Installing a spaCy Language Model

Allyanonimiser uses spaCy for NER (PERSON, LOCATION, ORG). Two models are
supported; pattern-based detection (TFN, ABN, MEDICARE, AU_PHONE, EMAIL,
dates, etc.) is identical with either one.

### Default: small model

```bash
python -m spacy download en_core_web_sm   # 44 MB, fast
```

This is what `create_allyanonimiser()` loads by default in v3.3+. It's
the right choice for serverless deployments (Azure Functions, Lambda)
and for pipelines where pattern PII (TFN, ABN, etc.) is the primary
concern.

### Optional: large model (higher NER accuracy)

```bash
python -m spacy download en_core_web_lg   # 587 MB, ~1.5 GB resident
```

Pass it explicitly when you need higher recall on names, places, and
organisations:

```python
from allyanonimiser import create_allyanonimiser, SPACY_MODEL_ACCURATE

ally = create_allyanonimiser(spacy_model=SPACY_MODEL_ACCURATE)
```

### Choosing a spaCy model

| | `SPACY_MODEL_FAST` (`en_core_web_sm`) | `SPACY_MODEL_ACCURATE` (`en_core_web_lg`) |
|---|---|---|
| Default in v3.3+? | yes | no |
| Download / disk | 44 MB | 587 MB |
| Resident memory | ~200 MB | ~1.5 GB |
| Cold start | ~0.5s | 2 – 5s |
| Pattern detection | identical | identical |
| `PERSON` recall | ~80% on insurance text | ~92% |
| `LOCATION`, `ORG` recall | noticeably worse | high |

Pass `spacy_model=None` to disable spaCy entirely — pattern detection
keeps working.

## Development Installation

If you're contributing to the project, install in development mode:

```bash
# Clone the repository
git clone https://github.com/srepho/Allyanonimiser.git
cd Allyanonimiser

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Verifying Installation

To verify that Allyanonimiser was installed correctly, run:

```python
import allyanonimiser
print(allyanonimiser.__version__)
```

This should print the current version of Allyanonimiser (e.g., `3.4.0`).