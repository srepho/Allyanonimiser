# Changelog

## 2.2.0 (2025-07-21)

### Added
- **Robust Detection System**: Enhanced validation and context-aware detection to reduce false positives
- **Overlapping Entity Resolution**: Smart handling of overlapping entities prevents text corruption during anonymization
- **Automatic Pattern Loading**: All default patterns (Australian, Insurance, General) now load automatically on initialization
- **Context Analyzer**: New `context_analyzer.py` module for context-aware entity detection
- **Entity Validators**: New `validators.py` module with validation functions for various entity types
- **Comprehensive Test Suite**: Added test files for robust detection, overlapping entities, and multiple entity masking

### Fixed
- **Medicare Number Detection**: Fixed Medicare number detection and validation for numbers starting with 2-6
- **Date False Positives**: "NSW 2000" and similar state+postcode combinations no longer detected as dates
- **Phone Number Detection**: Improved detection of Australian service numbers (1300, 1800, 13xx)
- **Overlapping Entity Handling**: Fixed text corruption when entities overlap (e.g., Medicare number containing postcode)
- **Pattern Conflicts**: Resolved conflicts between TFN, ABN, and ACN patterns by making them context-specific

### Enhanced
- **False Positive Filtering**: Added filtering for common false positives (street names as PERSON, abbreviations as ORGANIZATION)
- **Entity Priority System**: Implemented priority-based resolution for overlapping entities
- **Date Validation**: Enhanced date validation to avoid phone number prefixes and Medicare numbers
- **Multiple Entity Masking**: Improved support for simultaneous masking of multiple entity types with different operators

## 2.1.0 (2025-03-03)

### Added
- NSW legacy driver's license pattern support (licenses issued until 1990)
- Comprehensive pattern reference table in documentation
- Enhanced pattern management examples in README

### Fixed
- Fixed package build with proper dependency specifications
- Added missing dependencies in pyproject.toml (pandas, tqdm)
- Updated documentation with clearer pattern examples

## 2.0.0 (2025-03-30)

### Added
- Comprehensive reporting system with rich visualization capabilities:
  - Added `AnonymizationReport` class for tracking statistics and metrics
  - Added `ReportingManager` class for handling report sessions
  - Added integration with Jupyter notebooks for rich visualizations
  - Added multiple export formats (HTML, JSON, CSV) for report sharing
  - Added detailed entity type tracking and distribution analysis
  - Added performance metrics tracking for anonymization operations
  - Added document-level statistics and batch reporting features
  - Added visual charts for entity distribution and operator usage
  - Created example scripts demonstrating reporting capabilities

### Enhanced
- Integrated reporting system with existing functionality:
  - Added reporting to anonymize(), process(), and process_files() methods
  - Added report display capabilities for Jupyter notebook environments
  - Added methods to start, retrieve, and finalize reports
  - Added automated reporting for batch operations
  - Improved reporting of anonymization effectiveness with rate metrics
  - Enhanced documentation with comprehensive reporting examples
  - Added test suite for reporting functionality

## 1.2.0 (2025-03-29)

### Added
- Stream processing for very large files with Polars integration:
  - Implemented `StreamProcessor` class for memory-efficient processing
  - Added chunk-by-chunk processing with minimal memory footprint
  - Created streaming file reader for multi-gigabyte CSV files
  - Added streaming API for custom chunk processing
  - Added comprehensive error handling for stream processing failures
  - Implemented graceful fallbacks when Polars is not available
  - Added adaptive chunk sizing based on data volume
  - Added example script (`example_stream_processing.py`) demonstrating stream processing

### Improved
- Enhanced memory efficiency when processing multi-gigabyte datasets
- Added streaming progress bars for better user feedback
- Updated documentation with comprehensive stream processing examples
- Added tests for stream processing functionality

## 1.1.0 (2025-03-28)

### Added
- Simplified API with unified interface methods for common operations:
  - Added `manage_acronyms(action, data, ...)` to replace multiple acronym methods
  - Added `manage_patterns(action, data, ...)` to replace multiple pattern methods
  - Added unified `process_dataframe(operation, ...)` to consolidate DataFrame methods
- Added configuration objects for improved parameter organization:
  - `AnalysisConfig` for grouping analysis parameters
  - `AnonymizationConfig` for grouping anonymization parameters
- Added stream processing for very large files with Polars integration:
  - Implemented `StreamProcessor` class for memory-efficient processing
  - Added chunk-by-chunk processing with minimal memory footprint
  - Created streaming file reader for multi-gigabyte CSV files
  - Added streaming API for custom chunk processing
  - Added comprehensive error handling for stream processing failures
  - Implemented graceful fallbacks when Polars is not available
  - Added adaptive chunk sizing based on data volume
  - Added example script (`example_stream_processing.py`) demonstrating stream processing
- Created new example script (`example_simplified_api.py`) demonstrating the simplified API
- Maintained backward compatibility with deprecated method support
- Added comprehensive docstrings for all new methods

### Improved
- Reduced total public API method count while preserving all functionality
- Consolidated parameter handling for better code organization
- Enhanced code maintainability and reduced duplication
- Simplified pattern and acronym management workflows
- Optimized large file processing with adaptive chunk sizing
- Enhanced memory efficiency when processing multi-gigabyte datasets
- Added streaming progress bars for better user feedback

## 1.0.0 (2025-03-27)

### Breaking Changes
- Removed legacy analyzer factory functions (`create_au_analyzer`, `create_insurance_analyzer`, `create_au_insurance_analyzer`)
- Added cleaner `create_analyzer()` function as the main entry point
- Increased major version number to indicate production readiness
- Removed backward compatibility with 0.x versions
- Streamlined and simplified internal implementation
- Improved documentation and examples with clearer API usage

## 0.3.3 (2025-03-27)

### Changed
- Updated minimum Python version requirement to 3.10+
- Added support for Python 3.11 and 3.12
- Removed support for Python 3.8 and 3.9 due to dependency requirements (particularly NumPy 2.0+)
- Updated GitHub Actions workflows to test on Python 3.10-3.12 only

### Fixed
- Fixed circular import issues in the insurance module
- Enhanced batch processing capabilities for better performance
- Addressed compatibility issues with newer NumPy (2.0+) requirements
- Fixed package build and CI/CD processes
- Improved documentation for Python version requirements

## 0.3.2 (2025-03-25)

### Added
- Configuration export/import functionality for sharing settings between users
- Added `export_config()` method to export settings to JSON or YAML files
- Enhanced settings manager with functions to create shareable configurations
- Added support for exporting and importing configuration files
- Created example_export_config.py demonstrating configuration sharing
- Added comprehensive test suite for configuration export functionality
- Added PyArrow integration for improved DataFrame performance
- Graceful fallback for environments without PyArrow installed
- Configurable PyArrow usage through settings with sensible defaults

### Enhanced 
- Modified DataFrameProcessor class to utilize PyArrow when available
- Updated README with comprehensive documentation on configuration sharing
- Improved error handling in configuration import/export

## 0.3.1 (2025-03-20)

### Added
- DataFrameProcessor class for efficient pandas DataFrame processing
- Batch processing for handling large DataFrames with optimized memory usage
- Multi-processing capabilities for improved performance
- Comprehensive DataFrame anonymization functionality
- Statistical analysis tools for entity detection results
- Progress tracking with tqdm for long-running operations
- Extended main interface with DataFrame convenience methods
- Added example_dataframe.py demonstrating DataFrame processing

### Enhanced
- Added pandas dependency to package requirements
- Implemented test suite for DataFrame processing
- Added documentation for DataFrame processing in README
- Optimized entity detection algorithms for batched data

## 0.3.0 (2025-03-10)

### Added
- Comprehensive custom pattern creation and management functionality
- PatternManager class for handling pattern collections and application
- PatternRegistry class for saving and loading patterns
- Enhanced CustomPatternDefinition with serialization capabilities
- Support for creating patterns from examples with different generalization levels
- Added pattern creation helpers in main interface
- Implemented pattern persistence with JSON storage
- Added example script demonstrating custom pattern usage

### Enhanced
- Improved entity type metadata for custom patterns
- Enhanced pattern explanation capabilities
- Extended public API with pattern management methods
- Improved pattern testing and validation support

## 0.2.2 (2025-02-28)

### Added
- Integrated spaCy's NER system for more accurate PERSON entity detection
- Added entity type mapping between spaCy NER and custom entity types
- Improved detection of names with contextual understanding

### Fixed
- Reduced false positives by prioritizing spaCy NER results over pattern matching for PERSON entities
- Fixed issues with conflicting entity types for the same text span
- Addressed false positives for phrases like "Ref Number" being detected as PERSON entities
- Added proper entity type resolution with configurable prioritization rules

## 0.2.1 (2025-02-28)

### Fixed
- Fixed import issue with `create_simple_generalized_regex` function in package
- Corrected relative vs. absolute imports in pattern generation functionality
- Added missing pattern generation functions to package structure
- Fixed syntax errors in regex pattern matchers

## 0.2.0 (2025-02-28)

### Added
- Implemented multi-level pattern generalization system with four levels of flexibility
- Added intelligent format detection for common patterns (dates, emails, phone numbers)
- Created prefix/suffix analysis and character class recognition algorithms
- Added `generalization_level` parameter to `create_pattern_from_examples`
- Added comprehensive docstrings with detailed examples
- Created example script `example_advanced_pattern_generation.py`
- Exposed additional pattern generation helper functions

### Enhanced
- Improved pattern matching capability for variations of examples
- Made generated patterns more flexible with character classes
- Enabled automatic detection of common format patterns

### Fixed
- Fixed imports in the pattern generator modules
- Improved error handling in pattern generation functions
- Fixed path issues in the pattern creation utility functions

## 0.1.8 (2025-02-28)

### Added
- Improved package structure for better organization
- Added clearer examples for custom pattern creation
- Enhanced documentation for pattern validation
- Additional utility functions for pattern registry management

### Fixed
- Resolved installation issues on certain platforms
- Improved compatibility with different Python versions

## 0.1.7 (2025-02-28)

### Fixed
- Fixed text mangling issue in anonymizer by separating entity collection from replacement
- Improved handling of overlapping entities during anonymization
- Enhanced text replacement algorithm to maintain correct positions

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