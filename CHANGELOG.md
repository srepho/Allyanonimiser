# Changelog

## 0.1.6 (2025-02-28)

### Changed
- Optimized pattern detection performance for long documents
- Enhanced accuracy of Australian TFN and Medicare patterns
- Improved handling of edge cases in insurance pattern detection
- Bug fixes in enhanced_analyzer.py for certain pattern matches

### Fixed
- Fixed performance issues when processing large claim notes
- Resolved pattern matching inconsistencies in insurance_patterns.py
- Fixed detection issues with Australian formats in au_patterns.py
- Improved compatibility with different spaCy model versions

## 0.1.5 (2025-02-28)

### Added
- Greatly expanded pattern sets for more comprehensive PII detection
- Enhanced Australian-specific patterns for TFNs, Medicare numbers, phone numbers, addresses
- Added insurance-specific patterns for policy numbers, claim references, and vehicle identifiers
- Improved detection of general patterns such as person names, email addresses, dates, monetary amounts
- Fixed detection rates for common PII in example claim notes

### Changed
- Updated README badges to point to correct GitHub repository
- Improved pattern matching precision for Australian contexts
- Enhanced regex patterns for more accurate entity detection

## 0.1.4 (2025-02-28)

### Added
- Functional implementation of EnhancedAnalyzer with regex-based PII detection
- Added RecognizerResult class to represent detected PII entities
- Implemented anonymization functionality with multiple operator types (replace, mask, redact, hash)
- Enhanced pattern files with comprehensive patterns for Australian PII, insurance information, and general entities
- Added text segmentation and PII detection scoring in long_text_processor
- Implemented the process method in Allyanonimiser for one-step analysis and anonymization

### Changed
- Updated README with detailed description of new features
- Fixed badge URLs in README to point to correct GitHub repository
- Made minimal processing work without relying on external packages
- Improved documentation with examples of using the new functionality

## 0.1.3 (2025-02-28)

### Added
- Enhanced factory functions to accept custom patterns parameter
- Improved flexibility in function parameters with better default values
- More robust pattern creation from examples

### Changed
- Made API more flexible and customizable
- Improved handling of different pattern types
- Further enhanced code structure to avoid import issues

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