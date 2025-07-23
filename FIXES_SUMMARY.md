# Summary of Detection Fixes

## Issues Fixed

### 1. BSB and Account Number Detection
**Problem**: "BSB : 062-000 Account Number : 1617 8029" was not detecting BSB or Account Number.

**Solution**: 
- Split `AU_BSB_ACCOUNT` into two separate entity types: `AU_BSB` and `AU_ACCOUNT_NUMBER`
- Added patterns with capturing groups to handle labeled formats like "BSB : 062-000"
- Added patterns for "Account Number : 1617 8029" format

### 2. Organization Detection  
**Problem**: "Payee Name : Right2Drive Pty Ltd" was not being detected as an organization.

**Solution**:
- Updated organization patterns to include alphanumeric characters (not just letters)
- Added specific patterns for Australian company suffixes (Pty Ltd, Limited)
- Added patterns to capture organizations after labels like "Payee Name :"

### 3. NAME_CONSULTANT Pattern
**Problem**: "Diary Assigned To : Bruno Aloi" was not being detected.

**Solution**:
- Created new `NAME_CONSULTANT` entity type in insurance patterns
- Added patterns for "Assigned To :", "Consultant :", "Agent :", etc.
- **IMPORTANT**: Patterns now correctly capture just the name without trailing words like "Subject"

### 4. False Positive PERSON Detection
**Problem**: Common words like "Balance Outstanding", "Await", "Repairer Unreachable" were being detected as PERSON.

**Solution**:
- Added comprehensive false positive word list in spaCy analyzer
- Enhanced filtering to skip words that are clearly not names
- Added checks for entire phrases that shouldn't be names

### 5. PERSON Boundary Issues
**Problem**: "John Smith Subject" was capturing "Subject" as part of the person name.

**Solution**:
- Added stop word detection for words that shouldn't be part of names
- Implemented trimming logic to remove stop words from the end of detected names
- Properly recalculated entity boundaries after trimming

### 6. NAME_CONSULTANT Boundary Issues
**Problem**: "Bruno Aloi Subject" was including "Subject" in the NAME_CONSULTANT detection.

**Solution**:
- Added positive lookahead assertions to stop capture before common trailing words
- Patterns now stop before words like: Subject, Re, Regarding, For, About, Status, Case, Date, Time, Matter, Issue, Type, Category
- Example: "Assigned To : Bruno Aloi Subject" now correctly captures just "Bruno Aloi"

## Files Modified

1. `/allyanonimiser/patterns/au_patterns.py`
   - Split BSB and Account patterns
   - Added better pattern matching with capturing groups

2. `/allyanonimiser/patterns/insurance_patterns.py`
   - Added NAME_CONSULTANT entity type and patterns

3. `/allyanonimiser/patterns/general_patterns.py`
   - Enhanced ORGANIZATION patterns to include alphanumeric characters
   - Added Australian company suffix patterns

4. `/allyanonimiser/enhanced_analyzer.py`
   - Enhanced spaCy false positive filtering
   - Added boundary correction for PERSON entities
   - Improved stop word detection and trimming

## Test Results

All reported issues are now fixed:
- ✓ BSB detection: "062-000" correctly identified as AU_BSB
- ✓ Account Number: "1617 8029" correctly identified as AU_ACCOUNT_NUMBER  
- ✓ Organization: "Right2Drive Pty Ltd" correctly identified as ORGANIZATION
- ✓ Consultant Name: "Bruno Aloi" detected by NAME_CONSULTANT pattern
- ✓ False Positives: Words like "Await", "Drop" no longer detected as PERSON
- ✓ Boundary Issues: "John Smith Subject" now only captures "John Smith"

## Additional Fixes (Latest Update)

### 7. Enhanced PERSON False Positive Detection
**Problem**: Many non-names were being flagged as PERSON entities.

**Solution**:
- Expanded false positive word list to include 100+ common words
- Added categories: status words, action words, business terms, service terms, document terms, time terms, quality terms
- Examples of words now filtered: "await", "repairs", "balance", "outstanding", "update", "review", etc.

### 8. LOCATION False Positive Detection
**Problem**: Words like "Await" and "Repairs" were being detected as LOCATION.

**Solution**:
- Added comprehensive LOCATION false positive filtering
- Filters action words, status words, business terms, department terms
- Checks for single-word patterns that clearly aren't locations
- Maintains detection of real locations (Sydney, Melbourne, etc.)

### 9. Vehicle Registration Pattern Refinement
**Problem**: VEHICLE_REGISTRATION pattern was too broad, matching any uppercase words.

**Solution**:
- Refined patterns to require alphanumeric combinations
- Added exclusion for state abbreviations (NSW, VIC, etc.)
- Added common registration formats (ABC123, 123ABC, etc.)
- Reduced false positives from all-caps text

## Remaining Considerations

1. Some entities may be detected multiple times by different patterns (e.g., both PERSON and NAME_CONSULTANT). This is expected behavior as they serve different purposes.

2. Continue monitoring for new false positive patterns in production use.

3. Consider adding context-aware detection to further reduce false positives.