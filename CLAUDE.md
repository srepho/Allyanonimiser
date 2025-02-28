# Development Guidelines for Allyanonimiser

## Build & Test Commands
```bash
# Install dependencies
pip install -e .
python -m spacy download en_core_web_lg

# Run tests
pytest tests/
pytest tests/test_analyzer.py -v  # Run specific test file

# Run examples
python example_usage.py
python example_consolidated.py

# Test pattern validation
python -c "from validators import test_pattern_against_examples; print(test_pattern_against_examples(pattern='YOUR_PATTERN', positive_examples=['EXAMPLE1'], negative_examples=['EXAMPLE2']))"
```

## Code Style Guidelines
- **Imports**: stdlib > third-party > local (alphabetical in each group)
- **Types**: Type hints required for all function parameters and returns
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_SNAKE_CASE for constants
- **Documentation**: Docstrings required with Args/Returns sections
- **Error Handling**: Return tuples of (is_valid, error_message) for validation functions
- **Pattern Definition**: Follow CustomPatternDefinition structure with proper validation
- **PII Handling**: Never log or print actual PII data, even during development

## Project Structure
Australian-focused PII detection and anonymization for insurance industry with modular, extensible architecture using Presidio and spaCy.

## Primary Interface
The main interface class is `Allyanonimiser`, which provides unified functionality for processing both long texts and emails. Use `create_allyanonimiser()` to get a pre-configured instance.

## Version Management

When updating the Allyanonimiser package version, make sure to update all version references in these files:

1. `/pyproject.toml`: Update `version = "X.Y.Z"` in the `[project]` section
2. `/allyanonimiser/__init__.py`: Update `__version__ = "X.Y.Z"` at the top
3. `/setup.py`: Update `version="X.Y.Z",` in the setup function
4. `/README.md`: 
   - Update version heading `## Version X.Y.Z - [Description]`
   - Update installation command `pip install allyanonimiser==X.Y.Z`
5. `/CHANGELOG.md`: Add new version entry at the top

## Testing with Conda

When testing packages, use conda to create test environments with specific Python versions:

```bash
# Create a Python 3.8+ environment for testing
conda create -n allytest python=3.8
conda activate allytest

# Install package in development mode
pip install -e .

# Install test dependencies
pip install -e ".[dev]"

# Or install specific version from PyPI for testing
conda activate allytest
pip install allyanonimiser==0.1.6
```

Note: Conda is already installed on the system, making it easier to create isolated test environments with different Python versions.

## Additional Test Commands

Always verify that example code runs properly after making changes:

```bash
# Run the example script
python example_usage.py

# Run specific test files
pytest tests/test_analyzer.py
pytest tests/test_anonymizer.py

# Run all tests
pytest tests/

# Run tests with coverage report
pytest --cov=allyanonimiser
```

## Release Process

Follow these steps when releasing a new version:

1. Update version numbers in all files
2. Update CHANGELOG.md with detailed changes
3. Run tests to ensure everything works
4. Build the package: `python -m build`
5. Upload to PyPI: `python -m twine upload dist/*`
6. Commit changes to GitHub
7. Create a new release on GitHub

## Package Structure

Key locations of important functionality:

- Main package interface: `/allyanonimiser/allyanonimiser.py`
- Analyzer implementation: `/allyanonimiser/enhanced_analyzer.py`
- Anonymizer implementation: `/allyanonimiser/enhanced_anonymizer.py`
- Pattern definitions:
  - `/allyanonimiser/patterns/au_patterns.py`: Australian-specific patterns
  - `/allyanonimiser/patterns/insurance_patterns.py`: Insurance-specific patterns
  - `/allyanonimiser/patterns/general_patterns.py`: General PII patterns
- Processing utilities: `/allyanonimiser/utils/long_text_processor.py`