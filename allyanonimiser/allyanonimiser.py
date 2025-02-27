"""
Main interface for the Allyanonimiser package.
"""

from .enhanced_analyzer import EnhancedAnalyzer
from .enhanced_anonymizer import EnhancedAnonymizer
from .utils.long_text_processor import (
    analyze_claim_notes,
    extract_pii_rich_segments,
    segment_long_text
)

class Allyanonimiser:
    """
    Main interface for PII detection and anonymization of mixed content.
    This class provides a unified interface for processing different types of content.
    """
    def __init__(self, analyzer=None, anonymizer=None):
        self.analyzer = analyzer or EnhancedAnalyzer()
        self.anonymizer = anonymizer or EnhancedAnonymizer(analyzer=self.analyzer)
    
    def analyze(self, text, language="en"):
        """
        Analyze text to detect PII entities.
        
        Args:
            text: The text to analyze
            language: The language of the text (default: en)
            
        Returns:
            List of detected entities
        """
        return self.analyzer.analyze(text, language)
    
    def anonymize(self, text, operators=None, language="en"):
        """
        Anonymize PII entities in text.
        
        Args:
            text: The text to anonymize
            operators: Dict of entity_type to anonymization operator
            language: The language of the text (default: en)
            
        Returns:
            Dict with anonymized text and other metadata
        """
        return self.anonymizer.anonymize(text, operators, language)
    
    def process(self, text, language="en"):
        """
        Process text with automatic content type detection.
        
        Args:
            text: The text to process
            language: The language of the text (default: en)
            
        Returns:
            Dict with analysis, anonymized text, and other metadata
        """
        # Detect content type based on the text
        content_type = self._detect_content_type(text)
        
        # Analyze the text
        analysis_results = self.analyze(text, language)
        
        # Anonymize the text
        anonymized_results = self.anonymize(text, language=language)
        
        # Get PII-rich segments
        segments = extract_pii_rich_segments(text)
        
        # Add anonymized versions of segments
        for segment in segments:
            segment_text = segment['text']
            anonymized_segment = self.anonymize(segment_text, language=language)
            segment['anonymized'] = anonymized_segment['text']
        
        # Create structured data based on content type
        structured_data = self._extract_structured_data(text, content_type, analysis_results)
        
        return {
            'content_type': content_type,
            'analysis': {
                'entities': [
                    {
                        'entity_type': result.entity_type,
                        'start': result.start,
                        'end': result.end,
                        'text': text[result.start:result.end],
                        'score': result.score
                    }
                    for result in analysis_results
                ]
            },
            'anonymized': anonymized_results['text'],
            'segments': segments,
            'structured_data': structured_data
        }
    
    def _detect_content_type(self, text):
        """
        Detect the type of content.
        
        Args:
            text: The text to analyze
            
        Returns:
            String indicating the content type
        """
        # Simple heuristics for content type detection
        lower_text = text.lower()
        
        if 'from:' in lower_text and 'to:' in lower_text and 'subject:' in lower_text:
            return 'email'
        elif 'claim' in lower_text and 'policy' in lower_text and ('vehicle' in lower_text or 'accident' in lower_text):
            return 'claim_note'
        elif 'patient' in lower_text and ('assessment' in lower_text or 'diagnosis' in lower_text or 'treatment' in lower_text):
            return 'medical_report'
        else:
            return 'generic_text'
    
    def _extract_structured_data(self, text, content_type, analysis_results):
        """
        Extract structured data based on content type.
        
        Args:
            text: The text to analyze
            content_type: The detected content type
            analysis_results: Results from the analyzer
            
        Returns:
            Dict with structured data
        """
        structured_data = {}
        
        if content_type == 'email':
            # Extract email metadata
            from_match = re.search(r'From: (.+?)\n', text, re.IGNORECASE)
            to_match = re.search(r'To: (.+?)\n', text, re.IGNORECASE)
            subject_match = re.search(r'Subject: (.+?)\n', text, re.IGNORECASE)
            
            if from_match:
                structured_data['from'] = from_match.group(1).strip()
            if to_match:
                structured_data['to'] = to_match.group(1).strip()
            if subject_match:
                structured_data['subject'] = subject_match.group(1).strip()
                
        elif content_type == 'claim_note':
            # Extract claim note metadata
            claim_number_match = re.search(r'Claim (?:Number|#): (.+?)\n', text, re.IGNORECASE)
            policy_match = re.search(r'Policy (?:Number|#): (.+?)\n', text, re.IGNORECASE)
            customer_match = re.search(r'Customer: (.+?)\n', text, re.IGNORECASE)
            
            if claim_number_match:
                structured_data['claim_number'] = claim_number_match.group(1).strip()
            if policy_match:
                structured_data['policy_number'] = policy_match.group(1).strip()
            if customer_match:
                structured_data['customer'] = customer_match.group(1).strip()
                
        elif content_type == 'medical_report':
            # Extract medical report metadata
            patient_match = re.search(r'Patient:?\s+(.+?)\n', text, re.IGNORECASE)
            dob_match = re.search(r'DOB:?\s+(.+?)\n', text, re.IGNORECASE)
            doctor_match = re.search(r'Dr\.?\s+(.+?)\n', text, re.IGNORECASE)
            
            if patient_match:
                structured_data['patient'] = patient_match.group(1).strip()
            if dob_match:
                structured_data['dob'] = dob_match.group(1).strip()
            if doctor_match:
                structured_data['doctor'] = doctor_match.group(1).strip()
        
        return structured_data

import re