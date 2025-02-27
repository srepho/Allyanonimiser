# Changelog

## 0.1.2 (2025-02-28)

### Fixed
- Fixed circular import issue between `__init__.py` and `insurance/claim_notes_analyzer.py`
- Restructured imports to ensure factory functions are defined before they are used
- Moved the import of insurance modules below the factory function definitions

## 0.1.1 (2025-02-25)

### Fixed
- Fixed package structure to work when installed from PyPI
- Fixed relative imports to use proper dot notation
- Added missing `__init__.py` files

## 0.1.0 (2025-02-15)

### Added
- Initial release
- Support for Australian PII detection
- Specialized analyzers for insurance claim notes, emails, and medical reports
- Integration with Presidio and spaCy
- Custom pattern registry and validation