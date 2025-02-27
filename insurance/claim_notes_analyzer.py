"""
Specialized analyzer for insurance claim notes.
Provides functionality for extracting structured information from free-text claim notes.
"""

from typing import Dict, List, Any, Optional
import re
import spacy

from ..utils.long_text_processor import LongTextProcessor
from ..enhanced_analyzer import EnhancedAnalyzer
from ..patterns.insurance_patterns import get_insurance_pattern_definitions
from ..patterns.au_patterns import get_au_pattern_definitions

class ClaimNotesAnalyzer:
    """
    Specialized analyzer for extracting structured information from claim notes.
    Focuses on common claim note sections and insurance-specific context.
    """
    
    def __init__(self, analyzer=None, nlp=None):
        """
        Initialize the ClaimNotesAnalyzer.
        
        Args:
            analyzer: Pre-configured analyzer to use
            nlp: Pre-loaded spaCy NLP pipeline
        """
        if analyzer is None:
            # Create our own analyzer without importing create_au_insurance_analyzer
            insurance_patterns = get_insurance_pattern_definitions()
            au_patterns = get_au_pattern_definitions()
            combined_patterns = au_patterns + insurance_patterns
            analyzer = EnhancedAnalyzer(patterns=combined_patterns, language="en")
            
        self.analyzer = analyzer
        self.nlp = nlp or spacy.load("en_core_web_lg")
        self.text_processor = LongTextProcessor(self.nlp)
    
    def analyze(self, claim_note: str) -> Dict[str, Any]:
        """
        Analyze a claim note to extract structured information.
        
        Args:
            claim_note: Raw claim note text
            
        Returns:
            Dictionary containing structured information from the claim note
        """
        # Process the claim note into segments
        segments = self.text_processor.split_into_paragraphs(claim_note)
        
        # Initialize structure for results
        result = {
            "claim_number": None,
            "policy_number": None,
            "customer_name": None,
            "incident_date": None,
            "incident_description": None,
            "customer_details": {},
            "vehicle_details": {},
            "assessment_details": {},
            "action_items": [],
            "pii_segments": [],
            "section_segments": {
                "claim": [],
                "customer": [],
                "vehicle": [],
                "incident": [],
                "assessment": [],
                "action": []
            }
        }
        
        # Extract key information
        self._extract_claim_details(claim_note, result)
        self._extract_customer_details(claim_note, result)
        self._extract_vehicle_details(claim_note, result)
        self._extract_incident_details(claim_note, result)
        
        # Process segments for PII likelihood
        for segment in segments:
            entities = self.analyzer.analyze(segment)
            pii_likelihood = self._calculate_pii_likelihood(segment, entities)
            
            segment_data = {
                "text": segment,
                "pii_likelihood": pii_likelihood,
                "pii_scores": self._get_pii_type_scores(entities)
            }
            
            result["pii_segments"].append(segment_data)
            
            # Categorize segment by section
            self._categorize_segment(segment, segment_data, result)
        
        # Sort PII segments by likelihood
        result["pii_segments"] = sorted(
            result["pii_segments"], 
            key=lambda x: x["pii_likelihood"], 
            reverse=True
        )
        
        return result
    
    def _extract_claim_details(self, text: str, result: Dict[str, Any]) -> None:
        """Extract claim-related details."""
        # Claim number
        claim_patterns = [
            r"(?:claim|reference)\s*(?:number|ref|#)?:?\s*([A-Z0-9-]+)",
            r"(?:claim|ref)\s*#?\s*([A-Z0-9-]+)"
        ]
        
        for pattern in claim_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not result["claim_number"]:
                result["claim_number"] = match.group(1).strip()
        
        # Policy number
        policy_patterns = [
            r"policy\s*(?:number|#)?:?\s*([A-Z0-9-]+)",
            r"policy\s*#?\s*([A-Z0-9-]+)"
        ]
        
        for pattern in policy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not result["policy_number"]:
                result["policy_number"] = match.group(1).strip()
    
    def _extract_customer_details(self, text: str, result: Dict[str, Any]) -> None:
        """Extract customer-related details."""
        # Customer name
        name_patterns = [
            r"(?:customer|insured|claimant)(?:'s)?\s*name:?\s*([A-Za-z\s]+)",
            r"name:?\s*([A-Za-z\s]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not result["customer_name"]:
                result["customer_name"] = match.group(1).strip()
        
        # Look for customer details section
        customer_section = re.search(
            r"(?:customer|insured|claimant)\s*details:?(.*?)(?:\n\n|\r\n\r\n|$)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if customer_section:
            section_text = customer_section.group(1).strip()
            
            # Extract structured details
            detail_patterns = {
                "dob": r"(?:dob|date\s*of\s*birth):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                "phone": r"(?:phone|mobile|tel):?\s*([\d\s]+)",
                "email": r"(?:email|e-mail):?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                "address": r"(?:address|location):?\s*([^\n]+)",
                "tfn": r"(?:tfn|tax\s*file\s*number):?\s*([\d\s]+)",
                "medicare": r"(?:medicare)(?:\s*(?:number|#))?:?\s*(\d{4}\s*\d{5}\s*\d{1})",
                "license": r"(?:license|licence|driver'?s\s*licen[cs]e):?\s*([A-Z0-9\s]+)"
            }
            
            for key, pattern in detail_patterns.items():
                match = re.search(pattern, section_text, re.IGNORECASE)
                if match:
                    result["customer_details"][key] = match.group(1).strip()
    
    def _extract_vehicle_details(self, text: str, result: Dict[str, Any]) -> None:
        """Extract vehicle-related details."""
        # Look for vehicle details section
        vehicle_section = re.search(
            r"(?:vehicle|car)\s*(?:details|information|assessment):?(.*?)(?:\n\n|\r\n\r\n|$)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if vehicle_section:
            section_text = vehicle_section.group(1).strip()
            
            # Extract structured details
            detail_patterns = {
                "make": r"(?:make|manufacturer):?\s*([A-Za-z]+)",
                "model": r"(?:model):?\s*([A-Za-z0-9\s]+)",
                "registration": r"(?:registration|rego):?\s*([A-Z0-9-]+)",
                "vin": r"(?:vin|vehicle\s*identification\s*number):?\s*([A-Z0-9]+)",
                "year": r"(?:year):?\s*(\d{4})"
            }
            
            for key, pattern in detail_patterns.items():
                match = re.search(pattern, section_text, re.IGNORECASE)
                if match:
                    result["vehicle_details"][key] = match.group(1).strip()
        
        # If vehicle section wasn't found, search in full text
        if not result["vehicle_details"]:
            # Registration
            reg_match = re.search(
                r"(?:registration|rego):?\s*([A-Z0-9-]+)",
                text,
                re.IGNORECASE
            )
            if reg_match:
                result["vehicle_details"]["registration"] = reg_match.group(1).strip()
            
            # VIN
            vin_match = re.search(
                r"(?:vin|vehicle\s*identification\s*number):?\s*([A-Z0-9]+)",
                text,
                re.IGNORECASE
            )
            if vin_match:
                result["vehicle_details"]["vin"] = vin_match.group(1).strip()
            
            # Make and model
            make_model_match = re.search(
                r"(?:vehicle|car)?:?\s*(?:a|his|her)?\s*([A-Za-z]+)\s+([A-Za-z0-9\s]+)(?:\s*\(\d{4}\))?",
                text,
                re.IGNORECASE
            )
            if make_model_match:
                result["vehicle_details"]["make"] = make_model_match.group(1).strip()
                result["vehicle_details"]["model"] = make_model_match.group(2).strip()
    
    def _extract_incident_details(self, text: str, result: Dict[str, Any]) -> None:
        """Extract incident-related details."""
        # Incident date
        date_patterns = [
            r"(?:incident|event|accident)\s*date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"occurred\s*on\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not result["incident_date"]:
                result["incident_date"] = match.group(1).strip()
        
        # Incident description
        description_patterns = [
            r"(?:incident|accident)\s*description:?\s*(.*?)(?:\n\n|\r\n\r\n|$)",
            r"(?:reported|called|report).*?(?:that|regarding|about|stating|advised)\s+(.*?)(?:\n\n|\r\n\r\n|$)"
        ]
        
        for pattern in description_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match and not result["incident_description"]:
                result["incident_description"] = match.group(1).strip()
    
    def _categorize_segment(self, segment: str, segment_data: Dict[str, Any], 
                           result: Dict[str, Any]) -> None:
        """Categorize a segment by its content."""
        # Prepare segment data for section categorization
        segment_info = {
            "text": segment,
            "pii_likelihood": segment_data["pii_likelihood"]
        }
        
        # Define section keywords
        section_keywords = {
            "claim": ["claim", "reference", "policy", "number"],
            "customer": ["customer", "insured", "name", "phone", "email", "address"],
            "vehicle": ["vehicle", "car", "registration", "rego", "vin", "make", "model"],
            "incident": ["incident", "accident", "occurred", "collision", "damage"],
            "assessment": ["assessment", "inspection", "damage", "repair", "quote"],
            "action": ["action", "approved", "processed", "follow-up", "next steps"]
        }
        
        # Check segment against each section's keywords
        segment_lower = segment.lower()
        for section, keywords in section_keywords.items():
            if any(keyword in segment_lower for keyword in keywords):
                result["section_segments"][section].append(segment_info)
    
    def _calculate_pii_likelihood(self, text: str, entities: List[Dict[str, Any]]) -> float:
        """Calculate likelihood of PII presence in a segment."""
        if not text or not entities:
            return 0.0
            
        # Calculate percentage of text covered by entities
        text_length = len(text)
        entity_chars = set()
        
        for entity in entities:
            for i in range(entity["start"], entity["end"]):
                entity_chars.add(i)
        
        # Coverage as percentage of text
        coverage = len(entity_chars) / text_length
        
        # Calculate average score
        avg_score = sum(entity["score"] for entity in entities) / len(entities)
        
        # Combine coverage and score
        return 0.7 * coverage + 0.3 * avg_score
    
    def _get_pii_type_scores(self, entities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get scores by PII type."""
        type_scores = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            if entity_type not in type_scores:
                type_scores[entity_type] = 0.0
            
            type_scores[entity_type] += entity["score"]
        
        # Average scores if multiple entities of same type
        for entity_type in type_scores:
            count = sum(1 for entity in entities if entity["entity_type"] == entity_type)
            type_scores[entity_type] /= count
        
        return type_scores


def analyze_claim_note(claim_note: str) -> Dict[str, Any]:
    """
    Analyze a claim note to extract structured information (convenience function).
    
    Args:
        claim_note: Raw claim note text
        
    Returns:
        Dictionary containing structured information from the claim note
    """
    # Create our own analyzer without importing create_au_insurance_analyzer
    insurance_patterns = get_insurance_pattern_definitions()
    au_patterns = get_au_pattern_definitions()
    combined_patterns = au_patterns + insurance_patterns
    analyzer = EnhancedAnalyzer(patterns=combined_patterns, language="en")
    
    claim_analyzer = ClaimNotesAnalyzer(analyzer=analyzer)
    return claim_analyzer.analyze(claim_note)