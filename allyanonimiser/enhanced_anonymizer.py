"""
Enhanced anonymizer for PII data anonymization.
"""

class EnhancedAnonymizer:
    """
    Enhanced anonymizer for PII data anonymization.
    This is a wrapper around Presidio Anonymizer with additional functionality.
    """
    def __init__(self, analyzer=None):
        self.analyzer = analyzer
    
    def anonymize(self, text, operators=None, language="en"):
        """
        Anonymize PII entities in text.
        
        Args:
            text: The text to anonymize
            operators: Dict of entity_type to anonymization operator
                       (e.g. "PERSON": "replace", "PHONE": "mask")
            language: The language of the text (default: en)
            
        Returns:
            Dict with anonymized text and other metadata
        """
        if not self.analyzer:
            return {"text": text, "items": []}
            
        # Get the entities from the analyzer
        results = self.analyzer.analyze(text, language)
        
        # Default operators if none provided
        if not operators:
            operators = {}
            
        # Keep track of replacements
        replacements = []
        anonymized_text = text
        
        # Collect all entities first
        anonymization_entities = []
        for result in results:
            entity_type = result.entity_type
            start = result.start
            end = result.end
            
            # Get the original text
            original = text[start:end]
            
            # Determine operator
            operator = operators.get(entity_type, "replace")
            
            # Apply anonymization based on operator
            if operator == "replace":
                replacement = f"<{entity_type}>"
            elif operator == "mask":
                replacement = "*" * len(original)
            elif operator == "redact":
                replacement = "[REDACTED]"
            elif operator == "hash":
                replacement = f"HASH-{hash(original) % 1000000:06d}"
            else:
                replacement = f"<{entity_type}>"
            
            # Add to entities list
            anonymization_entities.append({
                "entity_type": entity_type,
                "start": start,
                "end": end,
                "original": original,
                "replacement": replacement
            })
        
        # Sort entities by start position in reverse order to process from end to start
        anonymization_entities.sort(key=lambda x: x["start"], reverse=True)
        
        # Apply replacements from end to start to maintain correct offsets
        for entity in anonymization_entities:
            start = entity["start"]
            end = entity["end"]
            replacement = entity["replacement"]
            
            # Replace in the text
            anonymized_text = anonymized_text[:start] + replacement + anonymized_text[end:]
            
            # Add to replacements list
            replacements.append(entity)
        
        return {
            "text": anonymized_text,
            "items": replacements
        }