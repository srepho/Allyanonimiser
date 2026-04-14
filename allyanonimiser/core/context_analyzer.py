"""
Context-aware analysis for improving entity detection accuracy.
"""

import re
from typing import List, Dict, Tuple, Optional

class ContextAnalyzer:
    """Analyzes context around entities to improve detection accuracy."""
    
    def __init__(self):
        # Define context patterns that help identify entity types
        self.context_patterns = {
            'AU_MEDICARE': {
                'before': [r'medicare\s*(?:number|#|:)?\s*$', r'health\s+card\s*(?:number|#|:)?\s*$'],
                'after': [r'^\s*(?:for|is|was)']
            },
            'AU_TFN': {
                'before': [r'(?:tfn|tax\s+file\s+number)\s*(?:#|:)?\s*$'],
                'after': []
            },
            'AU_ABN': {
                'before': [r'(?:abn|australian\s+business\s+number)\s*(?:#|:)?\s*$'],
                'after': []
            },
            'AU_PHONE': {
                'before': [r'(?:phone|ph|tel|telephone|mobile|mob|contact)\s*(?:number|#|:)?\s*$'],
                'after': []
            },
            'INSURANCE_POLICY_NUMBER': {
                'before': [r'policy\s*(?:number|#|:)?\s*$'],
                'after': []
            },
            'INSURANCE_CLAIM_NUMBER': {
                'before': [r'claim\s*(?:number|#|:)?\s*$'],
                'after': []
            },
            'DATE_OF_BIRTH': {
                'before': [r'(?:dob|date\s+of\s+birth|birth\s+date)\s*(?:#|:)?\s*$'],
                'after': []
            },
            'AU_POSTCODE': {
                'before': [r'(?:postcode|post\s+code|zip)\s*(?:#|:)?\s*$'],
                'after': [],
                'within': [r'\b(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s+\d{4}\b']
            },
            'EMAIL_ADDRESS': {
                'before': [r'(?:email|e-mail)\s*(?:address)?\s*(?:#|:)?\s*$'],
                'after': []
            }
        }
        
        # Context words that suggest specific entity types
        self.context_keywords = {
            'AU_MEDICARE': ['medicare', 'health card', 'medical'],
            'AU_TFN': ['tfn', 'tax file', 'tax number'],
            'AU_ABN': ['abn', 'business number', 'australian business'],
            'AU_ACN': ['acn', 'company number', 'australian company'],
            'AU_PHONE': ['phone', 'mobile', 'contact', 'call', 'tel', 'ph'],
            'AU_DRIVERS_LICENSE': ['license', 'licence', 'driver', 'driving'],
            'AU_POSTCODE': ['postcode', 'postal', 'zip'],
            'VEHICLE_REGISTRATION': ['rego', 'registration', 'vehicle', 'car'],
            'DATE_OF_BIRTH': ['dob', 'birth', 'born'],
            'INSURANCE_POLICY_NUMBER': ['policy', 'insurance'],
            'INSURANCE_CLAIM_NUMBER': ['claim', 'case'],
            'EMAIL_ADDRESS': ['email', 'mail'],
            'AU_BSB_ACCOUNT': ['bsb', 'account', 'bank']
        }
    
    def get_context_window(self, text: str, start: int, end: int, window_size: int = 50) -> Tuple[str, str]:
        """
        Get context before and after an entity.
        
        Args:
            text: The full text
            start: Start position of entity
            end: End position of entity
            window_size: Number of characters to include in context
            
        Returns:
            (context_before, context_after)
        """
        # Get context before
        context_start = max(0, start - window_size)
        context_before = text[context_start:start].lower().strip()
        
        # Get context after
        context_end = min(len(text), end + window_size)
        context_after = text[end:context_end].lower().strip()
        
        return context_before, context_after
    
    def analyze_context(self, text: str, entity_type: str, start: int, end: int) -> Dict[str, any]:
        """
        Analyze the context around an entity to determine if it's correctly identified.
        
        Args:
            text: The full text
            entity_type: The detected entity type
            start: Start position of entity
            end: End position of entity
            
        Returns:
            Dictionary with context analysis results
        """
        entity_text = text[start:end]
        context_before, context_after = self.get_context_window(text, start, end)
        
        # Check if entity type has defined context patterns
        if entity_type in self.context_patterns:
            patterns = self.context_patterns[entity_type]
            
            # Check before patterns
            before_match = any(re.search(pattern, context_before, re.IGNORECASE) 
                             for pattern in patterns.get('before', []))
            
            # Check after patterns
            after_match = any(re.search(pattern, context_after, re.IGNORECASE) 
                            for pattern in patterns.get('after', []))
            
            # Check within patterns (full entity with context)
            full_context = context_before + ' ' + entity_text + ' ' + context_after
            within_match = any(re.search(pattern, full_context, re.IGNORECASE) 
                             for pattern in patterns.get('within', []))
            
            pattern_match = before_match or after_match or within_match
        else:
            pattern_match = False
        
        # Check for context keywords
        if entity_type in self.context_keywords:
            keywords = self.context_keywords[entity_type]
            keyword_found = any(keyword in context_before or keyword in context_after 
                              for keyword in keywords)
        else:
            keyword_found = False
        
        # Calculate confidence based on context
        confidence_boost = 0.0
        if pattern_match:
            confidence_boost += 0.2
        if keyword_found:
            confidence_boost += 0.1
        
        return {
            'entity_text': entity_text,
            'context_before': context_before,
            'context_after': context_after,
            'pattern_match': pattern_match,
            'keyword_found': keyword_found,
            'confidence_boost': confidence_boost,
            'suggested_entity_type': self.suggest_entity_type(entity_text, context_before, context_after)
        }
    
    def suggest_entity_type(self, entity_text: str, context_before: str, context_after: str) -> Optional[str]:
        """
        Suggest the most likely entity type based on context.
        
        Args:
            entity_text: The entity text
            context_before: Context before the entity
            context_after: Context after the entity
            
        Returns:
            Suggested entity type or None
        """
        full_context = context_before + ' ' + context_after
        
        # Check each entity type's patterns
        best_match = None
        best_score = 0
        
        for entity_type, patterns in self.context_patterns.items():
            score = 0
            
            # Check before patterns
            if any(re.search(pattern, context_before, re.IGNORECASE) 
                  for pattern in patterns.get('before', [])):
                score += 2
            
            # Check keywords
            if entity_type in self.context_keywords:
                keyword_count = sum(1 for keyword in self.context_keywords[entity_type] 
                                  if keyword in full_context)
                score += keyword_count
            
            if score > best_score:
                best_score = score
                best_match = entity_type
        
        return best_match if best_score > 0 else None
    
    def is_likely_false_positive(self, text: str, entity_type: str, start: int, end: int) -> bool:
        """
        Check if an entity is likely a false positive based on context.
        
        Args:
            text: The full text
            entity_type: The detected entity type
            start: Start position of entity
            end: End position of entity
            
        Returns:
            True if likely false positive, False otherwise
        """
        entity_text = text[start:end]
        context_before, context_after = self.get_context_window(text, start, end, window_size=30)
        
        # Check for common false positive patterns
        false_positive_patterns = {
            'DATE': [
                # NSW 2000 (state + postcode)
                r'(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s*$',
                # Part of phone number
                r'(?:phone|mobile|contact|ph|tel)[\s:]*$',
                # Part of Medicare number
                r'medicare[\s:]*$'
            ],
            'NUMBER': [
                # Just a hash symbol
                r'#\s*$',
                # Words containing "quarter", "half", etc.
                r'(?:quarter|half|third)\s+panel',
            ],
            'PERSON': [
                # Street names
                r'(?:lives?\s+(?:at|on)|address)[\s:]*\d+\s*$',
                # Policy/claim numbers
                r'(?:policy|claim)[\s#:]*$'
            ]
        }
        
        if entity_type in false_positive_patterns:
            patterns = false_positive_patterns[entity_type]
            if any(re.search(pattern, context_before, re.IGNORECASE) for pattern in patterns):
                return True
        
        # Additional checks for specific entity types
        if entity_type == 'DATE' and entity_text in ['NSW 2000', 'VIC 3000', 'QLD 4000']:
            return True
        
        if entity_type == 'NUMBER' and entity_text == '#':
            return True
        
        return False