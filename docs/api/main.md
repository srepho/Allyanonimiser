# Main API Reference

This page documents the main API of the Allyanonimiser package.

## Main Classes and Functions

### `create_allyanonimiser`

```python
def create_allyanonimiser(pattern_filepath=None, settings_path=None):
    """
    Create an Allyanonimiser instance with all patterns pre-configured.
    
    Args:
        pattern_filepath: Optional path to a JSON file with pattern definitions
        settings_path: Optional path to a settings file (JSON or YAML)
        
    Returns:
        Allyanonimiser instance
    """
```

This is the primary factory function for creating an Allyanonimiser instance.

**Example:**
```python
from allyanonimiser import create_allyanonimiser

# Create with default settings
ally = create_allyanonimiser()

# Create with custom patterns
ally = create_allyanonimiser(pattern_filepath="my_patterns.json")

# Create with custom settings
ally = create_allyanonimiser(settings_path="my_settings.yaml")
```

### `Allyanonimiser` Class

The main class that provides a unified interface for PII detection and anonymization.

```python
class Allyanonimiser:
    """
    Main class for PII detection and anonymization with comprehensive configuration options.
    """
```

#### Key Methods

##### `analyze`

```python
def analyze(self, text, config=None):
    """
    Analyze text to detect PII entities.
    
    Args:
        text (str): The text to analyze
        config (AnalysisConfig, optional): Configuration for analysis
        
    Returns:
        List of detected entities
    """
```

##### `anonymize`

```python
def anonymize(self, text, operators=None, config=None):
    """
    Anonymize text by replacing detected PII entities.
    
    Args:
        text (str): The text to anonymize
        operators (dict, optional): Mapping of entity types to operators
        config (AnonymizationConfig, optional): Configuration for anonymization
        
    Returns:
        Dict containing anonymized text and metadata
    """
```

##### `process`

```python
def process(self, text, analysis_config=None, anonymization_config=None):
    """
    Process text by analyzing and anonymizing in one step.
    
    Args:
        text (str): The text to process
        analysis_config (AnalysisConfig, optional): Configuration for analysis
        anonymization_config (AnonymizationConfig, optional): Configuration for anonymization
        
    Returns:
        Dict containing analysis results and anonymized text
    """
```

##### `add_pattern`

```python
def add_pattern(self, pattern_definition):
    """
    Add a custom pattern to the analyzer.
    
    Args:
        pattern_definition (dict or CustomPatternDefinition): The pattern to add
        
    Returns:
        None
    """
```

##### `create_pattern_from_examples`

```python
def create_pattern_from_examples(self, entity_type, examples, context=None, name=None, 
                                pattern_type="regex", generalization_level="none"):
    """
    Create and add a pattern from example strings.
    
    Args:
        entity_type (str): Entity type this pattern detects
        examples (List[str]): List of example strings to generate pattern from
        context (List[str], optional): List of context words
        name (str, optional): Name for the pattern
        pattern_type (str, optional): Type of pattern to create - "regex" or "spacy"
        generalization_level (str, optional): Level of pattern generalization
        
    Returns:
        CustomPatternDefinition: The created pattern definition
    """
```

##### `process_dataframe`

```python
def process_dataframe(self, df, column, operation="anonymize", output_column=None, 
                     operators=None, config=None, batch_size=100, num_workers=1):
    """
    Process a pandas DataFrame by analyzing or anonymizing a text column.
    
    Args:
        df (pandas.DataFrame): DataFrame to process
        column (str): Name of the column containing text
        operation (str, optional): Operation to perform - "analyze" or "anonymize"
        output_column (str, optional): Name of the output column
        operators (dict, optional): Entity type to operator mapping
        config (AnonymizationConfig, optional): Configuration for anonymization
        batch_size (int, optional): Batch size for processing
        num_workers (int, optional): Number of parallel workers
        
    Returns:
        pandas.DataFrame: Processed DataFrame
    """
```

##### `export_config`

```python
def export_config(self, filepath, format="json"):
    """
    Export current configuration to a file.
    
    Args:
        filepath (str): Path to save the configuration
        format (str, optional): Format - "json" or "yaml"
        
    Returns:
        None
    """
```

### `AnalysisConfig` Class

Configuration object for the analysis process.

```python
class AnalysisConfig:
    """
    Configuration for the analysis process.
    """
    
    def __init__(self, active_entity_types=None, min_score_threshold=0.5, context_words=None):
        """
        Initialize configuration with optional parameters.
        
        Args:
            active_entity_types (List[str], optional): Entity types to detect
            min_score_threshold (float, optional): Minimum confidence score
            context_words (Dict[str, List[str]], optional): Additional context words
        """
```

### `AnonymizationConfig` Class

Configuration object for the anonymization process.

```python
class AnonymizationConfig:
    """
    Configuration for the anonymization process.
    """
    
    def __init__(self, operators=None, age_bracket_size=5, mask_char="*", 
                redaction_text="[REDACTED]", hash_algorithm="sha256", 
                hash_length=8, encryption_key=None):
        """
        Initialize configuration with optional parameters.
        
        Args:
            operators (Dict[str, Union[str, callable]], optional): Entity type to operator mapping
            age_bracket_size (int, optional): Size of age brackets
            mask_char (str, optional): Character to use for masking
            redaction_text (str, optional): Text to use for redaction
            hash_algorithm (str, optional): Hashing algorithm to use
            hash_length (int, optional): Length of hash output
            encryption_key (str, optional): Key for encryption
        """
```

## Pattern Related Classes

### `CustomPatternDefinition` Class

```python
class CustomPatternDefinition:
    """
    Definition of a custom pattern for detecting entities.
    """
    
    def __init__(self, entity_type, patterns, context=None, name=None, 
                 score=0.65, language="en", description=None):
        """
        Initialize a custom pattern definition.
        
        Args:
            entity_type (str): Entity type this pattern detects
            patterns (List[str]): List of regex patterns or spaCy patterns
            context (List[str], optional): List of context words
            name (str, optional): Name for the pattern
            score (float, optional): Confidence score threshold
            language (str, optional): Language code
            description (str, optional): Description of the pattern
        """
```

### `PatternManager` Class

```python
class PatternManager:
    """
    Manages pattern definitions and provides pattern registry functionality.
    """
```

## Utility Functions

### Pattern Generation

```python
def create_pattern_from_examples(entity_type, examples, context=None, name=None, 
                               pattern_type="regex", generalization_level="none"):
    """
    Create a custom pattern definition from examples with optional generalization.
    
    Args:
        entity_type (str): Entity type this pattern detects
        examples (List[str]): List of example strings to generate pattern from
        context (List[str], optional): List of context words
        name (str, optional): Name for the pattern
        pattern_type (str, optional): Type of pattern to create - "regex" or "spacy"
        generalization_level (str, optional): Level of pattern generalization
        
    Returns:
        CustomPatternDefinition: A pattern definition that can be added to an analyzer
    """
```

### Pattern Validation

```python
def test_pattern_against_examples(pattern, positive_examples, negative_examples=None):
    """
    Test a regex pattern against example strings.
    
    Args:
        pattern (str): Regex pattern to test
        positive_examples (List[str]): Examples that should match
        negative_examples (List[str], optional): Examples that should not match
        
    Returns:
        Dict: Results of the test with is_valid flag and diagnostic message
    """
```

## See Also

For more detailed API documentation on specific components:

- [Analyzer API](analyzer.md) - Documentation for the EnhancedAnalyzer class
- [Anonymizer API](anonymizer.md) - Documentation for the EnhancedAnonymizer class
- [Pattern Manager API](pattern-manager.md) - Documentation for pattern management classes
- [Utilities API](utilities.md) - Documentation for utility functions