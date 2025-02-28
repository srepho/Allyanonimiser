from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Test text with multiple entity types
test_text = """
From: john.smith@example.com
To: insurance@company.com.au
Subject: Claim for policy POL-12345678

Dear Sir/Madam,

I'm writing about my car accident on 15/05/2023. My policy number is POL-12345678 
and my claim reference is CL-987654. The vehicle registration is ABC123.

My phone number is 0412 345 678 and my address is 123 Main St, Sydney NSW 2000.

My Tax File Number is 123 456 789 and Medicare number is 2123 45678 1.

Please call me if you need more information.

Regards,
John Smith
"""

print("Default analysis (all entity types):")
results = ally.analyze(test_text)
for result in results:
    print(f"- {result.entity_type}: {result.text} (Score: {result.score})")

print("\nAnalysis with only specific entity types:")
active_types = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
filtered_results = ally.analyze(test_text, active_entity_types=active_types)
for result in filtered_results:
    print(f"- {result.entity_type}: {result.text} (Score: {result.score})")

print("\nAdjusting scores:")
score_adjustments = {"PERSON": 0.1, "EMAIL_ADDRESS": -0.1}
adjusted_results = ally.analyze(test_text, score_adjustment=score_adjustments)
for result in adjusted_results:
    if result.entity_type in ["PERSON", "EMAIL_ADDRESS"]:
        print(f"- {result.entity_type}: {result.text} (Score: {result.score})")

print("\nExplaining an entity detection:")
results = ally.analyze(test_text)
if results:
    person_entities = [r for r in results if r.entity_type == "PERSON"]
    if person_entities:
        person_entity = person_entities[0]
        entity_dict = {
            'entity_type': person_entity.entity_type,
            'start': person_entity.start,
            'end': person_entity.end,
            'text': person_entity.text,
            'score': person_entity.score
        }
        explanation = ally.explain_entity(test_text, entity_dict)
        print(f"Entity: {explanation['entity_type']} - {explanation['matched_text']}")
        print(f"Confidence: {explanation['confidence_score']}")
        print(f"Description: {explanation['metadata']['description']}")
        print(f"Detection method: {explanation['match_details']['detection_method']}")
