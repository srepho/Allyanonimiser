"""
Example script demonstrating optimized DataFrame processing with the Allyanonimiser API.

This example demonstrates:
1. PyArrow integration for performance
2. Adaptive batch sizing
3. Multi-column processing in a single pass
4. Benchmarking different configurations
"""
import pandas as pd
import numpy as np
import time
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig

# Create allyanonimiser instance
ally = create_allyanonimiser()

# Generate a sample DataFrame with different volumes of text
def create_test_dataframe(rows=1000, avg_text_length=200):
    """Create a synthetic DataFrame with varying text lengths for testing."""
    print(f"Creating test DataFrame with {rows} rows...")
    
    # Sample names to include as PII
    names = [
        "John Smith", "Jane Doe", "Robert Johnson", "Maria Garcia", 
        "Michael Chen", "Sarah Williams", "David Brown", "Emma Davis"
    ]
    
    # Sample emails to include as PII
    emails = [
        "john.smith@example.com", "jane.doe@email.org", "robert.j@company.net",
        "maria.garcia@business.com", "m.chen@tech.co", "sarah.w@insurance.com"
    ]
    
    # Sample phone numbers to include as PII
    phones = [
        "0412 345 678", "(02) 9876 5432", "+61 3 8765 4321", 
        "0499 876 543", "03-9876-5432", "0455 555 555"
    ]
    
    # Sample addresses to include as PII
    addresses = [
        "123 Main Street, Sydney NSW 2000",
        "456 Queen Avenue, Melbourne VIC 3000",
        "789 King Road, Brisbane QLD 4000",
        "101 Park Lane, Perth WA 6000"
    ]
    
    # Sample policy and claim numbers
    policy_numbers = [f"POL-{np.random.randint(10000, 99999)}" for _ in range(20)]
    claim_numbers = [f"CL-{np.random.randint(10000, 99999)}" for _ in range(20)]
    
    # Generate text data
    def generate_text(min_len, max_len):
        """Generate a text with random PII elements."""
        # Base text templates
        templates = [
            "Customer contacted us regarding {claim}. {name} reported an incident on {date}. " +
            "They can be reached at {email} or {phone}. Customer lives at {address}.",
            
            "Policy {policy} holder {name} called about claim {claim}. " +
            "Contact details: {phone}, {email}. Address: {address}.",
            
            "Incident report from {name} ({email}). Customer called from {phone} " +
            "regarding damage at {address}. Policy number {policy}, claim {claim}.",
            
            "Interview with {name} conducted on {date} regarding claim {claim}. " +
            "They reported the incident at {address}. Contact: {email}, {phone}."
        ]
        
        # Select a random template
        text = np.random.choice(templates)
        
        # Fill in PII information
        text = text.format(
            name=np.random.choice(names),
            email=np.random.choice(emails),
            phone=np.random.choice(phones),
            address=np.random.choice(addresses),
            policy=np.random.choice(policy_numbers),
            claim=np.random.choice(claim_numbers),
            date=f"{np.random.randint(1, 28)}/{np.random.randint(1, 12)}/{np.random.randint(2020, 2025)}"
        )
        
        # Add filler text to reach desired length
        target_len = np.random.randint(min_len, max_len)
        if len(text) < target_len:
            filler = "The customer provided additional context about their situation. " * ((target_len - len(text)) // 50 + 1)
            text += " " + filler
            
        return text[:max_len]
    
    # Generate three columns with different text characteristics
    short_texts = [generate_text(50, 150) for _ in range(rows)]
    medium_texts = [generate_text(200, 500) for _ in range(rows)]
    long_texts = [generate_text(800, 1500) for _ in range(rows)]
    
    # Create DataFrame
    df = pd.DataFrame({
        "id": range(1, rows + 1),
        "short_note": short_texts,
        "medium_note": medium_texts,
        "long_note": long_texts
    })
    
    return df

# Create a test DataFrame
df_test = create_test_dataframe(rows=5000, avg_text_length=300)
print(f"DataFrame created with {len(df_test)} rows and columns: {df_test.columns.tolist()}")
print(f"Sample row (short_note):\n{df_test.iloc[0]['short_note']}\n")

# 1. Basic processing example
print("\n=== Basic DataFrame Processing ===")
start_time = time.time()
result = ally.process_dataframe(
    df_test,
    text_columns=["short_note"],
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
    min_score_threshold=0.7,
    progress_bar=True
)
basic_time = time.time() - start_time

print(f"Basic processing completed in {basic_time:.2f} seconds")
print(f"Entities found: {len(result['entities'])}")
print("Entity type distribution:")
print(result['entities']['entity_type'].value_counts())

# 2. Process with PyArrow optimization
print("\n=== PyArrow Optimized Processing ===")
start_time = time.time()
result_arrow = ally.process_dataframe(
    df_test,
    text_columns=["short_note"],
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
    min_score_threshold=0.7,
    use_pyarrow=True,
    adaptive_batch_size=True,
    progress_bar=True
)
arrow_time = time.time() - start_time

print(f"PyArrow processing completed in {arrow_time:.2f} seconds")
print(f"Speedup factor: {basic_time / arrow_time:.2f}x")
print(f"Entities found: {len(result_arrow['entities'])}")

# 3. Multi-column processing
print("\n=== Multi-Column Processing with PyArrow and Parallel Execution ===")
start_time = time.time()
result_multi = ally.process_dataframe(
    df_test,
    text_columns=["short_note", "medium_note", "long_note"],
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "ADDRESS"],
    min_score_threshold=0.7,
    use_pyarrow=True,
    adaptive_batch_size=True,
    n_workers=4,  # Use 4 worker processes for parallel execution
    progress_bar=True
)
multi_time = time.time() - start_time

print(f"Multi-column processing completed in {multi_time:.2f} seconds")
entities_per_column = result_multi['entities'].groupby('column').size()
print("Entities per column:")
print(entities_per_column)

# 4. Anonymize with custom operators
print("\n=== Anonymizing with Custom Operators ===")

# Define a custom operator for policy numbers
def custom_policy_operator(text, entity_data):
    """Custom operator that preserves prefix but masks numbers with hash symbols."""
    import re
    if not text:
        return "<POLICY>"
    
    match = re.match(r'(POL)-(\d+)', text)
    if match:
        prefix = match.group(1)
        return f"{prefix}-######"
    
    return "<POLICY>"

# Register the custom operator
ally.anonymizer.register_custom_operator("POLICY_NUMBER", custom_policy_operator)

# Create pattern for policy numbers
ally.manage_patterns(
    action="create_from_examples",
    entity_type="POLICY_NUMBER",
    examples=["POL-12345", "POL-67890", "POL-54321"],
    context=["policy"]
)

# Use custom operator in DataFrame processing
start_time = time.time()
result_custom = ally.process_dataframe(
    df_test.head(10),  # Just process a small sample
    text_columns=["medium_note"],
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "POLICY_NUMBER"],
    operators={
        "PERSON": "replace",           # Replace with <PERSON>
        "EMAIL_ADDRESS": "mask",       # Replace with ***@***
        "PHONE_NUMBER": "redact",      # Replace with [REDACTED]
        "POLICY_NUMBER": "custom"      # Use our custom operator
    },
    min_score_threshold=0.7,
    use_pyarrow=True,
    progress_bar=False
)
custom_time = time.time() - start_time

print(f"Custom operator processing completed in {custom_time:.2f} seconds")
print("\nSample anonymized text:")
for i, row in result_custom['dataframe'].head(1).iterrows():
    print(f"Original: {df_test.loc[i, 'medium_note'][:100]}...")
    print(f"Anonymized: {row['medium_note_anonymized'][:100]}...")

# 5. Performance Optimization Summary
print("\n=== Performance Optimization Summary ===")
print("Processing times for different configurations:")
print(f"1. Basic processing:                 {basic_time:.2f} seconds")
print(f"2. PyArrow optimization:             {arrow_time:.2f} seconds (Speedup: {basic_time / arrow_time:.2f}x)")
print(f"3. Multi-column with parallelism:    {multi_time:.2f} seconds")
print(f"4. Custom operator anonymization:    {custom_time:.2f} seconds")

print("\nRecommendations for large DataFrame processing:")
print("1. Always enable PyArrow with: use_pyarrow=True")
print("2. Enable adaptive batch sizing with: adaptive_batch_size=True")
print("3. Use parallel processing with: n_workers=[CPU_COUNT]")
print("4. Process multiple columns in a single call when possible")
print("5. For memory-constrained environments, process one column at a time")