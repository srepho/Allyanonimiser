# Changelog

All notable changes to the Allyanonimiser project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Australian-specific PII detection patterns
- Insurance-specific PII detection patterns
- Long text processing utilities
- Domain-specific analyzers for claim notes, emails, and medical reports
- Enhanced analyzer and anonymizer with customizable patterns
- Unified `Allyanonimiser` interface for processing mixed content
- Australian synthetic data generator
- LLM augmenter for creating challenging datasets

## [0.1.1] - 2025-02-28

### Fixed
- Fixed package structure to properly support imports
- Moved all modules into the proper package hierarchy
- Ensured correct relative imports across the package
- Added example script using absolute imports
- Improved import reliability for pip-installed packages

## [0.1.0] - 2025-02-28

### Added
- First official release with complete core functionality
- Australian-specific PII patterns:
  - TFN (Tax File Number)
  - Medicare numbers
  - Driver's licenses for all states/territories
  - BSB and account numbers
  - Australian addresses
  - Australian phone numbers
- Insurance-specific patterns:
  - Policy numbers
  - Claim references
  - Vehicle registrations
  - VINs
- Long text processing capabilities:
  - Text segmentation
  - Section detection
  - PII context detection
- Domain-specific analyzers:
  - Claim notes analyzer
  - Insurance email analyzer
  - Medical report analyzer
- Synthetic data generation:
  - Australian person profiles
  - Insurance claims
  - Document generation with annotations
- Consolidated interface with content-type autodetection
- Basic file processing functionality