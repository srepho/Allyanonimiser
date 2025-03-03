# Installation

Allyanonimiser can be installed using pip with various installation options depending on your needs.

## Prerequisites

- Python 3.10 or higher
- A spaCy language model (recommended)

## Basic Installation

Install the core package from PyPI:

```bash
pip install allyanonimiser==2.1.0
```

## Installation Options

Allyanonimiser offers several installation options to meet different needs:

### With Stream Processing Support

For processing very large files with memory-efficient streaming:

```bash
pip install "allyanonimiser[stream]==2.1.0"
```

### With LLM Integration

For advanced pattern generation using language models:

```bash
pip install "allyanonimiser[llm]==2.1.0"
```

### Complete Installation

To install all optional dependencies:

```bash
pip install "allyanonimiser[stream,llm]==2.1.0"
```

## Installing spaCy Language Models

For optimal performance, install a spaCy language model:

```bash
# Install the comprehensive language model (recommended)
python -m spacy download en_core_web_lg

# OR install the smaller model if you have limited resources
python -m spacy download en_core_web_sm
```

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

This should print the current version of Allyanonimiser (e.g., `2.1.0`).