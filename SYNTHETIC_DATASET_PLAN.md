# Synthetic Dataset Generation Plan for Allyanonimiser

## Executive Summary
Plan to generate a comprehensive synthetic dataset using LLMs (Claude, Gemini, ChatGPT) to improve PII detection and anonymization capabilities in Allyanonimiser, with a focus on Australian insurance industry contexts.

## 1. Objectives

### Primary Goals
- **Improve Detection Accuracy**: Create diverse examples to catch edge cases
- **Reduce False Positives**: Generate negative examples that look like PII but aren't
- **Enhance Pattern Coverage**: Cover all 38+ entity types with realistic variations
- **Test Robustness**: Include challenging, ambiguous, and overlapping cases

### Secondary Goals
- Build benchmark dataset for regression testing
- Create training data for potential ML-based improvements
- Generate documentation examples
- Enable community contributions

## 2. Dataset Structure

### 2.1 Core Components
```
synthetic_dataset/
├── positive_examples/     # True PII examples
│   ├── australian/        # AU-specific entities
│   ├── insurance/         # Insurance-specific
│   ├── general/           # General PII
│   └── edge_cases/        # Challenging examples
├── negative_examples/     # Non-PII that might trigger false positives
├── contextual_examples/   # PII in realistic contexts
├── overlapping_examples/  # Multiple overlapping entities
└── metadata/              # Dataset documentation and stats
```

### 2.2 Data Format
```json
{
  "id": "uuid",
  "text": "Customer John Smith (TFN: 123 456 789) called about policy POL-123456",
  "entities": [
    {
      "type": "PERSON",
      "start": 9,
      "end": 19,
      "text": "John Smith",
      "confidence": 0.95
    },
    {
      "type": "AU_TFN",
      "start": 26,
      "end": 37,
      "text": "123 456 789",
      "confidence": 1.0
    }
  ],
  "context": "insurance_claim",
  "difficulty": "easy|medium|hard",
  "source": "claude-3.5|gpt-4|gemini-pro",
  "timestamp": "2024-08-14T10:00:00Z"
}
```

## 3. Generation Strategy

### 3.1 Multi-Model Approach
Use different models for different strengths:

**Claude 3.5 Sonnet**
- Complex insurance scenarios
- Australian cultural context
- Nuanced edge cases
- Multi-entity interactions

**GPT-4/GPT-4o**
- Diverse name generation
- International formats
- Creative variations
- Business contexts

**Gemini Pro**
- Structured data formats
- Technical documentation
- Medical/healthcare contexts
- Validation and verification

### 3.2 Prompt Engineering

#### Base Prompt Template
```python
SYSTEM_PROMPT = """You are a data generation specialist creating realistic synthetic examples 
for PII detection testing in the Australian insurance industry. Generate diverse, realistic 
examples that include the specified entity types while maintaining natural language flow."""

GENERATION_PROMPT = """Generate {num_examples} realistic text examples containing {entity_types}.
Context: {context}
Requirements:
- Mix formal and informal language
- Include Australian spelling and terminology
- Vary entity formats (e.g., TFN with/without spaces)
- Include surrounding context that makes sense
- Some examples should have multiple entities
- Some should be edge cases or challenging to detect

Output as JSON array with 'text' and 'entities' fields."""
```

### 3.3 Entity-Specific Generation

#### Phase 1: Core Australian Entities
- **AU_TFN**: Various formats (XXX XXX XXX, XXX-XXX-XXX, XXXXXXXXX)
- **AU_MEDICARE**: With/without IRN, spaces, reference codes
- **AU_PHONE**: Mobile, landline, 1300/1800 numbers
- **AU_DRIVERS_LICENSE**: All state formats
- **AU_ADDRESS**: Urban, rural, PO boxes, unit numbers

#### Phase 2: Insurance-Specific
- **INSURANCE_POLICY_NUMBER**: Different insurer formats
- **INSURANCE_CLAIM_NUMBER**: Various prefixes and structures
- **NAME_CONSULTANT**: With titles, departments, roles
- **VEHICLE_DETAILS**: Make, model, year combinations
- **INCIDENT_DATE**: Various date formats and contexts

#### Phase 3: Edge Cases
- Names that are also common words (e.g., "Mark", "Rose")
- Addresses with business names
- Policy numbers that look like phone numbers
- Dates that could be postcodes (e.g., "2024")
- Medicare numbers in different contexts

### 3.4 Negative Example Generation
Generate text that might trigger false positives:
- Product codes that resemble policy numbers
- Reference numbers that aren't PII
- Business names that include person names
- Technical terms with number patterns
- Lorem ipsum with realistic-looking numbers

## 4. Implementation Plan

### 4.1 Generation Pipeline
```python
class SyntheticDataGenerator:
    def __init__(self, models=['claude', 'gpt4', 'gemini']):
        self.models = self._initialize_models(models)
        self.validator = PIIValidator()
        
    async def generate_batch(self, 
                            entity_types: List[str],
                            count: int = 100,
                            context: str = 'insurance'):
        # 1. Distribute generation across models
        # 2. Validate generated examples
        # 3. Balance positive/negative ratio
        # 4. Ensure diversity metrics are met
        # 5. Save with metadata
        pass
        
    def validate_example(self, example):
        # Check entity boundaries are correct
        # Verify no real PII accidentally included
        # Ensure text is grammatically correct
        # Validate Australian formats
        pass
```

### 4.2 Quality Assurance
- **Automated Validation**: Check format compliance
- **Cross-Model Verification**: Use one model to verify another's output
- **Human Review**: Sample 5% for manual verification
- **Diversity Metrics**: Ensure variety in patterns
- **Coverage Analysis**: Track which patterns are well-represented

### 4.3 Progressive Enhancement
1. **Baseline Dataset** (Week 1-2)
   - 1000 examples per entity type
   - Basic positive/negative examples
   - Simple contexts

2. **Contextual Enhancement** (Week 3-4)
   - Add insurance-specific contexts
   - Include multi-entity examples
   - Add conversation/email formats

3. **Edge Case Addition** (Week 5-6)
   - Challenging detection scenarios
   - Overlapping entities
   - Ambiguous cases

4. **Adversarial Examples** (Week 7-8)
   - Deliberately tricky cases
   - Common false positive triggers
   - Format variations

## 5. Dataset Usage

### 5.1 Testing & Validation
```python
def test_with_synthetic_data():
    dataset = load_synthetic_dataset()
    
    for example in dataset:
        detected = ally.analyze(example['text'])
        expected = example['entities']
        
        # Calculate metrics
        precision = calculate_precision(detected, expected)
        recall = calculate_recall(detected, expected)
        f1_score = calculate_f1(precision, recall)
```

### 5.2 Pattern Improvement
- Identify patterns with low performance
- Generate additional examples for problem areas
- Refine regex patterns based on failures
- Add new patterns for uncovered cases

### 5.3 Documentation Examples
- Use clean, validated examples in README
- Create interactive examples for documentation
- Generate test cases for CI/CD

## 6. Cost Optimization

### 6.1 API Usage Strategy
- **Batch Generation**: Group similar requests
- **Caching**: Store and reuse similar examples
- **Model Selection**: Use cheaper models for simple cases
- **Prompt Optimization**: Minimize token usage

### 6.2 Estimated Costs
```
Target: 50,000 synthetic examples

Claude 3.5 Sonnet (20,000 examples):
- ~2M tokens @ $3/1M input, $15/1M output = ~$50

GPT-4o (20,000 examples):
- ~2M tokens @ $5/1M input, $15/1M output = ~$40

Gemini Pro (10,000 examples):
- ~1M tokens @ $0.50/1M = ~$5

Total Estimated Cost: ~$95-$150
```

## 7. Technical Architecture

### 7.1 Generation Service
```python
# synthetic_generator.py
class LLMPool:
    def __init__(self):
        self.claude = anthropic.Client()
        self.openai = openai.Client()
        self.gemini = genai.Client()
        
    async def generate_parallel(self, prompts):
        # Distribute prompts across models
        # Handle rate limits
        # Retry failed requests
        pass

class DatasetBuilder:
    def __init__(self, output_dir='synthetic_dataset'):
        self.generator = LLMPool()
        self.output_dir = output_dir
        
    def build_dataset(self, config):
        # Generate examples
        # Validate quality
        # Save to structured format
        # Generate metadata and stats
        pass
```

### 7.2 Validation Framework
```python
class SyntheticDataValidator:
    def validate_entity_accuracy(self, example):
        # Check entity boundaries
        # Verify entity types
        # Ensure no overlaps unless intended
        pass
        
    def validate_text_quality(self, text):
        # Grammar checking
        # Readability score
        # Context appropriateness
        pass
        
    def validate_australian_formats(self, entity):
        # TFN checksum
        # Medicare number format
        # Phone number validity
        # Postcode ranges
        pass
```

## 8. Evaluation Metrics

### 8.1 Dataset Quality Metrics
- **Coverage**: % of entity types with >100 examples
- **Diversity**: Unique patterns per entity type
- **Balance**: Positive/negative example ratio
- **Difficulty Distribution**: Easy/medium/hard split
- **Context Variety**: Number of unique contexts

### 8.2 Model Performance Metrics
- **Precision**: Correct detections / total detections
- **Recall**: Correct detections / total actual entities
- **F1 Score**: Harmonic mean of precision and recall
- **False Positive Rate**: Incorrect detections / total non-entities
- **Processing Speed**: Entities detected per second

## 9. Integration with Allyanonimiser

### 9.1 New Module Structure
```
allyanonimiser/
├── synthetic/
│   ├── __init__.py
│   ├── generator.py        # LLM generation logic
│   ├── validator.py        # Quality validation
│   ├── dataset.py          # Dataset management
│   └── benchmarks.py       # Performance testing
```

### 9.2 CLI Commands
```bash
# Generate synthetic data
ally-synthetic generate --entity-types AU_TFN,AU_MEDICARE --count 1000

# Validate existing dataset
ally-synthetic validate dataset.json

# Run benchmarks
ally-synthetic benchmark --dataset synthetic_dataset/

# Export for training
ally-synthetic export --format spacy --output training_data/
```

## 10. Timeline & Milestones

### Month 1: Foundation
- Week 1-2: Set up LLM integrations
- Week 3-4: Create generation pipeline

### Month 2: Generation
- Week 5-6: Generate core dataset
- Week 7-8: Add edge cases and adversarial examples

### Month 3: Integration
- Week 9-10: Build validation framework
- Week 11-12: Integrate with Allyanonimiser and document

## 11. Future Enhancements

### 11.1 Community Contributions
- Allow users to submit examples
- Crowdsource validation
- Share datasets publicly

### 11.2 Active Learning
- Identify failure cases in production
- Generate similar examples automatically
- Continuously improve patterns

### 11.3 Multi-language Support
- Extend to other English-speaking countries
- Add support for other languages
- Handle code-switching scenarios

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Accidental real PII | High | Validation, scanning, human review |
| Model hallucinations | Medium | Cross-validation, fact-checking |
| Cost overruns | Low | Budget limits, batching, caching |
| Bias in generation | Medium | Multiple models, diversity metrics |
| Format drift | Low | Regular validation against real data |

## 13. Success Criteria

- [ ] 50,000+ high-quality synthetic examples
- [ ] Coverage of all 38 entity types
- [ ] 95%+ validation accuracy
- [ ] 10% improvement in detection F1 score
- [ ] <5% false positive rate
- [ ] Documentation and examples updated
- [ ] Community adoption and contributions

## 14. Next Steps

1. **Review and approve plan**
2. **Set up API credentials for LLMs**
3. **Create initial prototype generator**
4. **Generate small test batch (100 examples)**
5. **Validate approach and adjust**
6. **Scale up generation**
7. **Integrate with main package**
8. **Document and release**

---

## Appendix A: Example Prompts

### A.1 Australian Phone Number Generation
```
Generate 20 examples of Australian phone numbers in natural context.
Include: mobile (04xx), landline (02, 03, 07, 08), and service numbers (1300, 1800).
Vary formats: (02) 9xxx xxxx, 02-9xxx-xxxx, 0412 345 678, 0412345678.
Each should be in a sentence like you'd find in insurance documents.
```

### A.2 Insurance Claim Context
```
Create 10 insurance claim descriptions that naturally include:
- A person's name
- A claim number (format: CLM-XXXXXXX or C-XXXXXX)
- An incident date
- A location in Australia
- Optional: phone number, policy number, vehicle details

Make them realistic for motor, home, or liability insurance.
```

### A.3 Edge Case Generation
```
Generate 15 challenging examples that might confuse PII detection:
- Names that are also common words (Mark, Rose, Hope)
- Numbers that could be dates or postcodes (2024, 3000)
- Business names containing person names (John's Plumbing)
- Product codes resembling policy numbers
- Addresses with unit/level numbers

Include whether each should be detected as PII or not.
```

## Appendix B: Validation Checklist

- [ ] No real PII included
- [ ] Entity boundaries correct
- [ ] Australian spelling/format
- [ ] Natural language flow
- [ ] Appropriate context
- [ ] Correct entity type labels
- [ ] No inappropriate content
- [ ] Balanced difficulty levels
- [ ] Sufficient diversity
- [ ] Cross-model agreement

---

*Document created: 2024-08-14*
*Last updated: 2024-08-14*
*Status: DRAFT - Pending Review*