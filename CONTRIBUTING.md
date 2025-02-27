# Contributing to Allyanonimiser

Thank you for your interest in contributing to Allyanonimiser! This guide will help you get started with the contribution process.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project and everyone participating in it is governed by the [Allyanonimiser Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your changes
5. Make your changes and commit them
6. Push to your fork and submit a pull request

## Development Environment

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/allyanonimiser.git
cd allyanonimiser

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode with all dependencies
pip install -e ".[dev]"

# Install the required spaCy model
python -m spacy download en_core_web_lg
```

## Submitting Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them with clear, descriptive commit messages:
   ```bash
   git commit -m "Add feature: brief description of the feature"
   ```

3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Submit a pull request through the GitHub interface.

## Coding Standards

We follow these coding standards:

- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Use [mypy](http://mypy-lang.org/) for type checking

Run the following commands to check your code:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type check
mypy .
```

### Code Style Guidelines

- **Imports**: stdlib > third-party > local (alphabetical in each group)
- **Types**: Type hints required for all function parameters and returns
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_SNAKE_CASE for constants
- **Documentation**: Docstrings required with Args/Returns sections

## Testing

Write tests for all new features and bug fixes. Run the tests with pytest:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=allyanonimiser

# Run a specific test file
pytest tests/test_analyzer.py
```

## Documentation

- Add docstrings to all functions, methods, and classes
- Update the README.md with any new features or changes in usage
- For significant changes, update the documentation in the docs directory

## Issue Reporting

- Use the GitHub issue tracker to report bugs or suggest features
- Check existing issues before creating a new one
- Provide as much information as possible when reporting bugs
- For bugs, include steps to reproduce, expected behavior, and actual behavior

Thank you for contributing to Allyanonimiser!