"""
Utility for processing long text fields in insurance documents.
Provides functions for text segmentation, paragraph analysis, and context detection.
"""

import re
from typing import List, Dict, Any, Tuple, Optional, Set
import spacy
from spacy.tokens import Doc, Span

class LongTextProcessor:
    """
    Processor for analyzing long text fields such as emails, claim notes, and reports.
    Provides methods for segmenting text, analyzing paragraphs, and detecting context.
    """
    
    def __init__(self, nlp=None):
        """
        Initialize the long text processor.
        
        Args:
            nlp: Optional spaCy language model
        """
        if nlp is None:
            # Load a larger, more accurate spaCy model
            try:
                self.nlp = spacy.load("en_core_web_lg")
            except OSError:
                # Fallback to smaller model if large model not available
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    # Fallback to small model if core model not available
                    self.nlp = spacy.load("en")
        else:
            self.nlp = nlp
            
        # Common insurance-specific section headers
        self.section_headers = {
            "claim": [
                "claim details", "claim summary", "claim information", "incident details", 
                "incident description", "incident summary", "accident details",
                "event details", "loss details", "damage details"
            ],
            "policy": [
                "policy details", "policy information", "policy summary", "coverage details",
                "insurance details", "policy schedule", "policy coverage"
            ],
            "customer": [
                "customer details", "client details", "customer information", "client information",
                "insured details", "policyholder details", "personal details", "contact details"
            ],
            "vehicle": [
                "vehicle details", "vehicle information", "car details", "automobile details",
                "vehicle damage", "vehicle inspection", "vehicle assessment"
            ],
            "property": [
                "property details", "property information", "home details", "building details",
                "property damage", "property assessment", "building inspection"
            ],
            "medical": [
                "medical details", "medical information", "medical assessment", "medical report",
                "injury details", "treatment details", "health information", "clinical notes"
            ],
            "financial": [
                "payment details", "financial details", "premium details", "payment information",
                "billing details", "invoice details", "quote details", "excess details", "settlement details"
            ],
            "communication": [
                "communication log", "call notes", "phone call", "conversation notes",
                "email correspondence", "message log", "communication summary"
            ]
        }
        
        # Insurance-specific terminology by domain
        self.domain_terminology = {
            "motor": [
                "vehicle", "car", "automotive", "motor", "automobile", "crash", "collision",
                "driver", "passenger", "registration", "rego", "license", "licence", "vin",
                "make", "model", "repair", "mechanic", "workshop", "panel beater", "tow", "smash"
            ],
            "home": [
                "property", "building", "house", "home", "residence", "dwelling", "structural",
                "contents", "theft", "burglary", "flood", "fire", "storm", "water damage", "roof"
            ],
            "health": [
                "medical", "health", "treatment", "diagnosis", "patient", "doctor", "hospital",
                "clinic", "specialist", "procedure", "medicare", "surgery", "consultation", "referral"
            ],
            "liability": [
                "liability", "responsible", "fault", "negligence", "duty of care", "third party",
                "injury", "damage", "compensation", "public liability", "professional indemnity"
            ],
            "business": [
                "business", "commercial", "company", "enterprise", "operation", "employer",
                "employee", "workplace", "staff", "business interruption", "equipment", "premises"
            ]
        }
    
    def segment_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Segment long text into meaningful parts.
        
        Args:
            text: Long text to segment
            
        Returns:
            List of dictionaries with segment information
        """
        # Process text with spaCy for basic linguistic features
        doc = self.nlp(text)
        
        # Detect paragraph boundaries
        paragraphs = self._detect_paragraphs(text)
        
        # Process each paragraph
        segments = []
        
        for i, (start, end) in enumerate(paragraphs):
            paragraph_text = text[start:end].strip()
            
            # Skip empty paragraphs
            if not paragraph_text:
                continue
            
            # Determine if this paragraph is a section header
            section_type = self._detect_section_header(paragraph_text)
            
            # Process paragraph content
            paragraph_doc = doc[start:end]
            
            # Detect domain terminology
            domains = self._detect_domains(paragraph_text)
            
            # Create segment object
            segment = {
                "id": i,
                "start": start,
                "end": end,
                "text": paragraph_text,
                "is_header": section_type is not None,
                "section_type": section_type,
                "domains": domains,
                "length": len(paragraph_text)
            }
            
            segments.append(segment)
        
        return segments
    
    def _detect_paragraphs(self, text: str) -> List[Tuple[int, int]]:
        """
        Detect paragraph boundaries in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of (start, end) tuples for paragraphs
        """
        # Simple paragraph detection based on line breaks
        paragraph_spans = []
        current_start = 0
        
        # Split by double line breaks first (preferred paragraph separator)
        double_breaks = re.split(r'\n\s*\n', text)
        
        current_pos = 0
        for paragraph in double_breaks:
            # Skip empty paragraphs
            if not paragraph.strip():
                current_pos += len(paragraph) + 2  # +2 for the double newline
                continue
            
            # Further split by single line breaks if the paragraph is very long
            if len(paragraph) > 500:
                single_breaks = re.split(r'\n', paragraph)
                for sub_para in single_breaks:
                    if not sub_para.strip():
                        current_pos += len(sub_para) + 1  # +1 for the newline
                        continue
                        
                    para_start = current_pos
                    current_pos += len(sub_para) + 1  # +1 for the newline
                    paragraph_spans.append((para_start, current_pos - 1))
            else:
                para_start = current_pos
                current_pos += len(paragraph) + 2  # +2 for the double newline
                paragraph_spans.append((para_start, current_pos - 2))
        
        return paragraph_spans
    
    def _detect_section_header(self, text: str) -> Optional[str]:
        """
        Detect if text is a section header and determine type.
        
        Args:
            text: Text to analyze
            
        Returns:
            Section type or None if not a header
        """
        # Clean and lowercase the text for matching
        clean_text = text.strip().lower()
        
        # Check if it's short enough to be a header
        if len(clean_text) > 100:
            return None
        
        # Check if it ends with a colon (common for headers)
        is_header_format = clean_text.endswith(':') or clean_text.endswith('-') or clean_text.isupper()
        
        # Check against known section headers
        for section_type, headers in self.section_headers.items():
            for header in headers:
                if header in clean_text or clean_text in header:
                    return section_type
        
        # If it looks like a header but doesn't match known types, return generic type
        if is_header_format:
            return "other"
            
        return None
    
    def _detect_domains(self, text: str) -> List[str]:
        """
        Detect insurance domains relevant to text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of relevant domains
        """
        text_lower = text.lower()
        domains = []
        
        for domain, terms in self.domain_terminology.items():
            # Count how many domain-specific terms appear in the text
            term_count = sum(1 for term in terms if term in text_lower)
            
            # If enough terms appear, consider this domain relevant
            if term_count >= 2:
                domains.append(domain)
        
        return domains
    
    def detect_pii_context(self, text: str, pii_type: str) -> float:
        """
        Detect how likely a text is to contain a specific type of PII.
        
        Args:
            text: Text to analyze
            pii_type: Type of PII to check for
            
        Returns:
            Context score from 0.0 to 1.0
        """
        # Map of PII types to relevant context terms
        pii_context_terms = {
            "PERSON": ["name", "person", "individual", "customer", "client", "insured", "claimant", "driver"],
            "EMAIL": ["email", "e-mail", "contact", "correspondence", "electronic", "message"],
            "PHONE": ["phone", "telephone", "mobile", "cell", "contact", "call", "number"],
            "ADDRESS": ["address", "location", "residence", "property", "street", "suburb", "postal"],
            "TFN": ["tax", "taxation", "file", "tfn", "number"],
            "MEDICARE": ["medicare", "health", "medical", "card", "insurance", "number"],
            "LICENSE": ["license", "licence", "driver", "driving", "card", "identification"],
            "BANK_ACCOUNT": ["bank", "account", "bsb", "financial", "transfer", "payment", "deposit"],
            "POLICY_NUMBER": ["policy", "insurance", "cover", "coverage", "number", "reference"],
            "CLAIM_NUMBER": ["claim", "reference", "number", "case", "incident", "lodgement"],
            "VEHICLE_REGO": ["registration", "rego", "vehicle", "car", "automobile", "plate", "number"],
            "VIN": ["vin", "vehicle", "identification", "chassis", "number", "manufacture"]
        }
        
        # Get the relevant context terms for this PII type
        context_terms = pii_context_terms.get(pii_type.upper(), [])
        
        if not context_terms:
            return 0.0
        
        # Count how many context terms appear in the text
        text_lower = text.lower()
        term_count = sum(1 for term in context_terms if term in text_lower)
        
        # Calculate a score based on term frequency
        max_score = min(len(context_terms), 5)  # Cap at 5 terms for 100% score
        score = min(1.0, term_count / max_score)
        
        return score
    
    def extract_pii_rich_segments(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract segments of text likely to contain PII.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of segments with PII likelihood scores
        """
        # First segment the text
        segments = self.segment_text(text)
        
        # Evaluate each segment for PII likelihood
        for segment in segments:
            segment_text = segment["text"]
            
            # Calculate PII likelihood for various PII types
            pii_scores = {}
            for pii_type in ["PERSON", "EMAIL", "PHONE", "ADDRESS", "TFN", "MEDICARE", 
                           "LICENSE", "BANK_ACCOUNT", "POLICY_NUMBER", "CLAIM_NUMBER", 
                           "VEHICLE_REGO", "VIN"]:
                pii_scores[pii_type] = self.detect_pii_context(segment_text, pii_type)
            
            # Add overall PII score (average of individual scores)
            overall_score = sum(pii_scores.values()) / len(pii_scores)
            
            # Add scores to segment
            segment["pii_scores"] = pii_scores
            segment["pii_likelihood"] = overall_score
        
        # Sort segments by PII likelihood (highest first)
        segments.sort(key=lambda s: s["pii_likelihood"], reverse=True)
        
        return segments
    
    def extract_entities_by_type(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities by type using spaCy's named entity recognition.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping entity types to entity texts
        """
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            
            entities[ent.label_].append(ent.text)
        
        return entities
    
    def analyze_claim_notes(self, text: str) -> Dict[str, Any]:
        """
        Analyze claim notes to extract structured information.
        
        Args:
            text: Claim notes text
            
        Returns:
            Dictionary with structured information
        """
        # Segment the text
        segments = self.segment_text(text)
        
        # Extract entities
        entities = self.extract_entities_by_type(text)
        
        # Get PII-rich segments
        pii_segments = self.extract_pii_rich_segments(text)
        
        # Identify key segments by section type
        section_segments = {}
        for segment in segments:
            section_type = segment.get("section_type")
            if section_type:
                if section_type not in section_segments:
                    section_segments[section_type] = []
                section_segments[section_type].append(segment)
        
        # Identify incident description
        incident_segments = section_segments.get("claim", [])
        incident_description = " ".join([s["text"] for s in incident_segments]) if incident_segments else ""
        
        # Extract communication segments
        communication_segments = section_segments.get("communication", [])
        
        return {
            "segments": segments,
            "entities": entities,
            "pii_segments": pii_segments[:5],  # Top 5 PII-rich segments
            "section_segments": section_segments,
            "incident_description": incident_description,
            "communication_segments": communication_segments
        }

def segment_long_text(text: str) -> List[Dict[str, Any]]:
    """
    Utility function to segment long text.
    
    Args:
        text: Text to segment
        
    Returns:
        List of text segments
    """
    processor = LongTextProcessor()
    return processor.segment_text(text)

def extract_pii_rich_segments(text: str) -> List[Dict[str, Any]]:
    """
    Utility function to extract segments likely to contain PII.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of segments with PII likelihood scores
    """
    processor = LongTextProcessor()
    return processor.extract_pii_rich_segments(text)

def analyze_claim_notes(text: str) -> Dict[str, Any]:
    """
    Utility function to analyze insurance claim notes.
    
    Args:
        text: Claim notes text
        
    Returns:
        Dictionary with structured information
    """
    processor = LongTextProcessor()
    return processor.analyze_claim_notes(text)