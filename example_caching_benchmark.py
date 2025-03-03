"""
Example script demonstrating the performance benefits of caching in Allyanonimiser.

This example demonstrates:
1. Setting up caching with different configurations
2. Benchmarking repeated text analysis with and without caching
3. Analyzing cache hit rates and memory usage
4. Performance optimization for production scenarios
"""
import time
import sys
import gc
import pandas as pd
import numpy as np
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig

# Set random seed for reproducibility
np.random.seed(42)

# ----- Helper functions -----
def get_memory_usage():
    """Estimate memory usage of the current process in MB."""
    import os
    import psutil
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # Convert to MB

def generate_sample_data(unique_samples=100, duplications=10, similarity_factor=0.8):
    """
    Generate a dataset with controlled repetition and similarity for benchmarking.
    
    Args:
        unique_samples: Number of unique base texts to generate
        duplications: How many times each unique text appears (with minor variations)
        similarity_factor: How similar variations are to the original (0-1)
    
    Returns:
        List of sample texts
    """
    # Base templates with PII
    templates = [
        "Customer {name} called about policy {policy}. They can be reached at {email}.",
        "Claim {claim} was submitted by {name} ({dob}). Contact: {phone}.",
        "Policy {policy} holder {name} reported an incident at {address}.",
        "Driver {name} with license {license} was involved in accident on {date}."
    ]
    
    # Sample data for PII elements
    names = [
        "John Smith", "Jane Doe", "Robert Johnson", "Maria Garcia", 
        "Michael Chen", "Sarah Williams", "David Brown", "Emma Davis"
    ]
    emails = [
        "john.smith@example.com", "jane.doe@email.org", "robert.j@company.net",
        "maria.garcia@business.com", "m.chen@tech.co", "sarah.w@insurance.com"
    ]
    phones = [
        "0412 345 678", "(02) 9876 5432", "+61 3 8765 4321", 
        "0499 876 543", "03-9876-5432", "0455 555 555"
    ]
    addresses = [
        "123 Main Street, Sydney NSW 2000",
        "456 Queen Avenue, Melbourne VIC 3000",
        "789 King Road, Brisbane QLD 4000",
        "101 Park Lane, Perth WA 6000"
    ]
    policies = [f"POL-{np.random.randint(10000, 99999)}" for _ in range(20)]
    claims = [f"CL-{np.random.randint(10000, 99999)}" for _ in range(20)]
    
    # Generate unique base samples
    base_samples = []
    for _ in range(unique_samples):
        template = np.random.choice(templates)
        text = template.format(
            name=np.random.choice(names),
            email=np.random.choice(emails),
            phone=np.random.choice(phones),
            address=np.random.choice(addresses),
            policy=np.random.choice(policies),
            claim=np.random.choice(claims),
            dob=f"{np.random.randint(1, 28)}/{np.random.randint(1, 12)}/{np.random.randint(1950, 2000)}",
            license=f"{np.random.randint(100000, 999999)}",
            date=f"{np.random.randint(1, 28)}/{np.random.randint(1, 12)}/2024"
        )
        base_samples.append(text)
    
    # Create variations and duplications
    all_samples = []
    for base_text in base_samples:
        # Add exact duplicates
        exact_copies = max(1, int(duplications * (1 - similarity_factor)))
        all_samples.extend([base_text] * exact_copies)
        
        # Add similar variations
        variations_count = duplications - exact_copies
        for _ in range(variations_count):
            # Add random whitespace or punctuation variations
            if np.random.random() < 0.5:
                # Add extra spaces or different punctuation
                variation = base_text.replace(". ", ".  ").replace(", ", " , ")
            else:
                # Change capitalization or add a prefix/suffix
                variation = base_text + " Please process this request."
                
            all_samples.append(variation)
    
    # Shuffle the samples
    np.random.shuffle(all_samples)
    return all_samples

# ----- Benchmark function -----
def benchmark_with_caching(samples, enable_caching=True, cache_size=10000, show_progress=True):
    """
    Benchmark the performance impact of caching.
    
    Args:
        samples: List of text samples to analyze
        enable_caching: Whether to enable result caching
        cache_size: Maximum cache size
        show_progress: Whether to show progress during benchmark
        
    Returns:
        Dictionary with benchmark results
    """
    # Create analyzer with specified caching settings
    ally = create_allyanonimiser(enable_caching=enable_caching, max_cache_size=cache_size)
    
    # Configure for consistent detection settings
    analysis_config = AnalysisConfig(
        active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "ADDRESS"],
        min_score_threshold=0.7
    )
    
    start_memory = get_memory_usage()
    start_time = time.time()
    total_entities = 0
    
    # Process all samples
    for i, sample in enumerate(samples):
        if show_progress and i % 100 == 0:
            print(f"Processing sample {i}/{len(samples)}...")
            
        result = ally.analyze(sample, 
                              active_entity_types=analysis_config.active_entity_types,
                              min_score_threshold=analysis_config.min_score_threshold)
        total_entities += len(result)
    
    end_time = time.time()
    end_memory = get_memory_usage()
    
    # Get cache statistics if available
    cache_stats = {}
    if enable_caching and hasattr(ally.analyzer, 'get_cache_statistics'):
        cache_stats = ally.analyzer.get_cache_statistics()
    
    return {
        "caching_enabled": enable_caching,
        "processing_time": end_time - start_time,
        "entities_found": total_entities,
        "memory_usage_mb": end_memory - start_memory,
        "samples_processed": len(samples),
        "cache_stats": cache_stats
    }

# ----- Main benchmark script -----
print("=== Caching Performance Benchmark ===")

# Generate sample data
print("\nGenerating sample data...")
num_unique = 200
repetitions = 15
total_samples = num_unique * repetitions
samples = generate_sample_data(unique_samples=num_unique, duplications=repetitions)
print(f"Created {len(samples)} samples with ~{num_unique} unique texts")

# Perform benchmark with caching disabled
print("\n1. Running benchmark WITHOUT caching...")
no_cache_results = benchmark_with_caching(samples, enable_caching=False)

# Clear memory between tests
gc.collect()

# Perform benchmark with caching enabled
print("\n2. Running benchmark WITH caching...")
cache_results = benchmark_with_caching(samples, enable_caching=True)

# Compare results
speedup = no_cache_results["processing_time"] / cache_results["processing_time"]
memory_ratio = cache_results["memory_usage_mb"] / max(0.1, no_cache_results["memory_usage_mb"])

print("\n=== Benchmark Results ===")
print(f"Total samples processed: {len(samples)}")
print(f"Unique texts: ~{num_unique}")
print(f"Repetition factor: {repetitions}")

print("\nPerformance Comparison:")
print(f"WITHOUT caching: {no_cache_results['processing_time']:.2f} seconds")
print(f"WITH caching:    {cache_results['processing_time']:.2f} seconds")
print(f"Speedup factor:  {speedup:.2f}x")

print("\nMemory Usage:")
print(f"WITHOUT caching: {no_cache_results['memory_usage_mb']:.2f} MB")
print(f"WITH caching:    {cache_results['memory_usage_mb']:.2f} MB")
print(f"Memory ratio:    {memory_ratio:.2f}x")

if 'cache_stats' in cache_results and cache_results['cache_stats']:
    stats = cache_results['cache_stats']
    print("\nCache Statistics:")
    print(f"Cache hits:     {stats.get('cache_hits', 0)}")
    print(f"Cache misses:   {stats.get('cache_misses', 0)}")
    print(f"Hit rate:       {stats.get('hit_rate', 0):.2%}")
    print(f"Result cache:   {stats.get('result_cache_size', 0)} entries")
    print(f"Pattern cache:  {stats.get('pattern_cache_size', 0)} entries")
    print(f"SpaCy cache:    {stats.get('spacy_cache_size', 0)} entries")

# ----- Advanced benchmark: Testing different cache sizes -----
print("\n=== Advanced Benchmark: Cache Size Optimization ===")

# Test different cache sizes
cache_sizes = [100, 500, 1000, 5000, 10000]
results = []

for size in cache_sizes:
    print(f"\nTesting cache size: {size}...")
    # Clear memory
    gc.collect()
    
    # Run benchmark
    result = benchmark_with_caching(samples, enable_caching=True, cache_size=size, show_progress=False)
    
    # Save result
    results.append({
        "cache_size": size,
        "processing_time": result["processing_time"],
        "memory_usage_mb": result["memory_usage_mb"],
        "hit_rate": result["cache_stats"].get("hit_rate", 0) if "cache_stats" in result else 0
    })

# Format results as DataFrame
results_df = pd.DataFrame(results)
print("\nCache Size Optimization Results:")
print(results_df)

# Find optimal cache size (highest hit rate with reasonable memory usage)
best_size = results_df.loc[results_df["hit_rate"].idxmax()]["cache_size"]
print(f"\nOptimal cache size for this workload: {best_size}")

# ----- Production recommendations -----
print("\n=== Production Recommendations ===")
print("1. For batch processing of similar texts, enable caching for 2-10x speedup")
print("2. For memory-constrained environments, use a smaller cache size (500-1000 entries)")
print("3. For real-time web services with repetitive queries, maximize the cache size")
print("4. For completely unique texts with no repetition, disable caching to save memory")
print("5. Monitor hit rate in production to adjust cache size dynamically")

# When processing repeating data, the ideal cache size depends on:
# - The number of unique text patterns in your data
# - Available memory
# - Performance requirements
print(f"\nFor this dataset (~{num_unique} unique patterns), the ideal cache size is: {best_size}")
print("Your production data patterns may differ, so monitor and adjust accordingly.")