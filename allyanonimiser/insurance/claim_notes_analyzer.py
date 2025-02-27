"""
Specialized analyzer for insurance claim notes.
Provides functionality for extracting structured information from free-text claim notes.
"""

from typing import Dict, List, Any, Optional
import re
import spacy
from ..utils.long_text_processor import LongTextProcessor
from ..enhanced_analyzer import EnhancedAnalyzer
from .. import create_au_insurance_analyzer

class ClaimNotesAnalyzer:
    """
    Specialized analyzer for extracting structured information from claim notes.
    Focuses on common claim note sections and insurance-specific context.
    """
    
    def __init__(self, analyzer=None, nlp=None):
        """
        Initialize the claim notes analyzer.
        
        Args:
            analyzer: Optional EnhancedAnalyzer instance
            nlp: Optional spaCy language model
        """
        self.analyzer = analyzer or create_au_insurance_analyzer()
        self.text_processor = LongTextProcessor(nlp=nlp)
        
        # Patterns for extracting specific claim information
        self.patterns = {
            "claim_number": r'(?:claim|reference|ref).*?(?:number|#|\:)?\s*([A-Za-z]{0,3}[-]?[0-9]{4,10})',
            "policy_number": r'(?:policy|insurance).*?(?:number|#|\:)?\s*([A-Za-z0-9]{2,5}[-]?[A-Za-z0-9]{4,10})',
            "incident_date": r'(?:incident|accident|event|loss).*?(?:date|occurred).*?([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            "incident_location": r'(?:location|at|in).*?(?:of|the).*?(?:incident|accident|event|collision|crash).*?(?:at|in|near)\s*([A-Za-z0-9\s\.,]+(?:Road|Street|St|Rd|Avenue|Ave|Highway|Hwy|Lane|Drive|Dr|Court|Ct|Place|Pl|Crescent|Cr|Boulevard|Blvd))',
            "amount": r'(?:amount|total|sum|cost|quote|estimate).*?(?:of|\:|\$)\s*(?:\$)?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)',
            "third_party": r'(?:third\s+party|tp|other\s+party|other\s+driver).*?(?:details|name|is|was)?\s*(?:\:)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            "insurer": r'(?:insurer|insurance|company|provider).*?(?:is|with|through|name)?\s*(?:\:)?\s*([A-Z][a-z]*(?:\s[A-Z][a-z]*){0,2}\s+(?:Insurance|Mutual|Assurance|Underwriters|Limited|Ltd))'
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze claim notes text to extract structured information.
        
        Args:
            text: Claim notes text
            
        Returns:
            Dictionary with extracted information
        """
        # Process text using LongTextProcessor
        base_analysis = self.text_processor.analyze_claim_notes(text)
        
        # Extract specific claim information using regex patterns
        extracted_info = self._extract_specific_information(text)
        
        # Detect entities using EnhancedAnalyzer
        entities = self._detect_entities(text)
        
        # Identify the main incident description
        incident_description = self._extract_incident_description(text, base_analysis)
        
        # Identify action items and next steps
        action_items = self._extract_action_items(text)
        
        # Combine all analyses
        result = {
            **base_analysis,
            "extracted_info": extracted_info,
            "entities": entities,
            "incident_description": incident_description,
            "action_items": action_items
        }
        
        return result
    
    def _extract_specific_information(self, text: str) -> Dict[str, Any]:
        """Extract specific information using regex patterns."""
        results = {}
        
        for info_type, pattern in self.patterns.items():
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                results[info_type] = matches.group(1).strip()
        
        return results
    
    def _detect_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Detect entities using the enhanced analyzer."""
        analysis_results = self.analyzer.analyze(text)
        
        # Group by entity type
        entities_by_type = {}
        for result in analysis_results:
            entity_type = result.entity_type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            
            entities_by_type[entity_type].append({
                "text": text[result.start:result.end],
                "start": result.start,
                "end": result.end,
                "score": result.score
            })
        
        return entities_by_type
    
    def _extract_incident_description(self, text: str, base_analysis: Dict[str, Any]) -> str:
        """Extract the main incident description."""
        # Try to get incident description from claim section
        if "section_segments" in base_analysis and "claim" in base_analysis["section_segments"]:
            claim_segments = base_analysis["section_segments"]["claim"]
            if claim_segments:
                return " ".join([s["text"] for s in claim_segments])
        
        # Fall back to regex-based extraction
        incident_patterns = [
            r'(?:Incident|Accident|Event|Loss)\s+(?:Details|Description)\s*\:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'(?:what|how)(?:\s+did)?(?:\s+the)?(?:\s+incident|accident|event|collision|crash)(?:\s+occur|\s+happen)(?:\?|:|\.)?\s*([^\n]+(?:\n[^\n]+)*)',
            r'(?:describe|details\s+of)(?:\s+the)?(?:\s+incident|accident|event|collision|crash)(?:\?|:|\.)?\s*([^\n]+(?:\n[^\n]+)*)'
        ]
        
        for pattern in incident_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(1).strip()
        
        # If no specific incident description found, return empty string
        return ""
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items and next steps."""
        action_items = []
        
        # Look for sections with action items, next steps, or to-do lists
        action_patterns = [
            r'(?:Action|Next Steps|To Do|Follow Up)s?\s*\:?\s*\n((?:\s*\d+\.\s*[^\n]+\n)+)',
            r'(?:Action|Next Steps|To Do|Follow Up)s?\s*\:?\s*\n((?:\s*-\s*[^\n]+\n)+)',
            r'(?:We will|I will|Please|Customer to)\s+([^\.\n]+\.)'
        ]
        
        for pattern in action_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                action_text = match.group(1).strip()
                
                # Split into individual actions if it's a list
                if re.search(r'^\s*\d+\.', action_text, re.MULTILINE) or re.search(r'^\s*-', action_text, re.MULTILINE):
                    for line in action_text.split('\n'):
                        if line.strip():
                            # Remove list markers
                            clean_line = re.sub(r'^\s*\d+\.\s*|\s*-\s*', '', line).strip()
                            if clean_line:
                                action_items.append(clean_line)
                else:
                    action_items.append(action_text)
        
        return action_items
    
    def extract_customer_details(self, text: str) -> Dict[str, Any]:
        """Extract customer details from claim notes."""
        customer_details = {}
        
        # Common patterns for customer details
        detail_patterns = {
            "name": r'(?:customer|client|insured|policyholder|claimant)(?:\s+name)?\s*(?:\:|is|-)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
            "phone": r'(?:phone|telephone|mobile|contact)(?:\s+number)?\s*(?:\:|is|-)?\s*((?:\+?61|0)\s*\d(?:[ \.-]?\d{2,4}){2,4})',
            "email": r'(?:email|e-mail)(?:\s+address)?\s*(?:\:|is|-)?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            "dob": r'(?:date\s+of\s+birth|dob|born)(?:\s+date)?\s*(?:\:|is|-)?\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})',
            "address": r'(?:address|residence|lives\s+at)(?:\s+is)?\s*(?:\:|-)?\s*([^,\n]+(,[^,\n]+){1,4})'
        }
        
        for detail_type, pattern in detail_patterns.items():
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                customer_details[detail_type] = matches.group(1).strip()
        
        # Get additional customer details from entity detection
        entities = self._detect_entities(text)
        
        # Map entity types to customer detail fields
        entity_mapping = {
            "PERSON": "name_entities",
            "AU_PHONE": "phone_entities",
            "EMAIL_ADDRESS": "email_entities",
            "AU_ADDRESS": "address_entities",
            "AU_DRIVERS_LICENSE": "license_entities",
            "AU_MEDICARE": "medicare_entities",
            "AU_TFN": "tfn_entities"
        }
        
        for entity_type, field_name in entity_mapping.items():
            if entity_type in entities:
                customer_details[field_name] = entities[entity_type]
        
        return customer_details
    
    def categorize_claim(self, text: str) -> Dict[str, Any]:
        """
        Categorize the claim based on its content.
        
        Returns information about the claim type, severity, and complexity.
        """
        # Analyze domains using the text processor
        segments = self.text_processor.segment_text(text)
        domains = []
        for segment in segments:
            if "domains" in segment:
                domains.extend(segment["domains"])
        
        # Count domain occurrences
        domain_counts = {}
        for domain in domains:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Determine primary domain (most frequently mentioned)
        primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0] if domain_counts else None
        
        # Check for severity indicators
        severity_indicators = {
            "high": ["severe", "significant", "major", "extensive", "serious", "high", "totaled", "wrote off", "hospital", "injury", "ambulance", "emergency"],
            "medium": ["moderate", "partial", "damage", "repair", "treatment", "medical", "attention"],
            "low": ["minor", "small", "slight", "minimal", "cosmetic", "scratch", "dent"]
        }
        
        severity_scores = {level: 0 for level in severity_indicators}
        for level, terms in severity_indicators.items():
            for term in terms:
                matches = re.findall(r'\b' + term + r'\b', text.lower())
                severity_scores[level] += len(matches)
        
        highest_severity = max(severity_scores.items(), key=lambda x: x[1])[0] if any(severity_scores.values()) else "unknown"
        
        # Estimate complexity based on number of parties, action items, and entities
        action_items = self._extract_action_items(text)
        entities = self._detect_entities(text)
        
        complexity_factors = {
            "action_items": len(action_items),
            "entity_types": len(entities),
            "third_party_involved": 1 if "third_party" in self._extract_specific_information(text) else 0
        }
        
        complexity_score = sum(complexity_factors.values())
        complexity = "high" if complexity_score >= 8 else "medium" if complexity_score >= 4 else "low"
        
        return {
            "primary_domain": primary_domain,
            "domains": list(domain_counts.keys()),
            "severity": highest_severity,
            "complexity": complexity,
            "complexity_factors": complexity_factors
        }

# Helper function for accessing the analyzer directly
def analyze_claim_note(text: str) -> Dict[str, Any]:
    """
    Analyze a claim note using the ClaimNotesAnalyzer.
    
    Args:
        text: Claim note text
        
    Returns:
        Structured analysis of the claim note
    """
    analyzer = ClaimNotesAnalyzer()
    return analyzer.analyze(text)