"""
Specialized analyzer for medical reports in insurance claims.
Provides functionality for extracting structured information from medical documents.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set
import spacy

from ..utils.long_text_processor import LongTextProcessor
from ..enhanced_analyzer import EnhancedAnalyzer
from .. import create_au_insurance_analyzer

class MedicalReportAnalyzer:
    """
    Specialized analyzer for extracting structured information from medical reports.
    Identifies medical terminology, treatments, diagnoses, and PII in medical contexts.
    """
    
    def __init__(self, analyzer=None, nlp=None):
        """
        Initialize the medical report analyzer.
        
        Args:
            analyzer: Optional EnhancedAnalyzer instance
            nlp: Optional spaCy language model
        """
        self.analyzer = analyzer or create_au_insurance_analyzer()
        self.text_processor = LongTextProcessor(nlp=nlp)
        
        # Common medical report section headers
        self.section_headers = {
            "patient_info": [
                "patient information", "patient details", "demographics", "personal information",
                "patient demographics", "patient data"
            ],
            "clinical_history": [
                "clinical history", "medical history", "past medical history", "history", 
                "past history", "clinical background", "background"
            ],
            "examination": [
                "examination", "physical examination", "physical assessment", "clinical examination",
                "assessment", "observations", "findings", "clinical findings"
            ],
            "diagnosis": [
                "diagnosis", "diagnoses", "diagnostic impression", "impression", "conclusion",
                "diagnostic summary", "clinical impression"
            ],
            "treatment": [
                "treatment", "treatment plan", "management", "therapeutic plan", "therapy",
                "intervention", "procedure", "surgical procedure", "medical management"
            ],
            "medication": [
                "medication", "medications", "drugs", "prescriptions", "drug therapy",
                "pharmaceutical therapy", "medical therapy", "current medications"
            ],
            "investigation": [
                "investigation", "investigations", "tests", "laboratory", "imaging",
                "pathology", "diagnostic tests", "radiology", "test results"
            ],
            "prognosis": [
                "prognosis", "outlook", "expected outcome", "follow-up", "follow up",
                "rehabilitation", "recovery", "anticipated progress"
            ]
        }
        
        # Common medical terminology
        self.medical_terminology = {
            "conditions": [
                "fracture", "sprain", "strain", "contusion", "laceration", "concussion",
                "whiplash", "herniation", "rupture", "tear", "dislocation", "subluxation",
                "tendinitis", "bursitis", "arthritis", "osteoarthritis", "spondylosis",
                "spondylolisthesis", "stenosis", "neuropathy", "radiculopathy", "myalgia",
                "neuralgia", "migraine", "hypertension", "diabetes", "asthma"
            ],
            "anatomy": [
                "cervical", "thoracic", "lumbar", "sacral", "spine", "vertebra", "disc",
                "shoulder", "rotator cuff", "humerus", "elbow", "radius", "ulna", "wrist",
                "carpal", "hand", "finger", "phalange", "hip", "femur", "knee", "patella",
                "tibia", "fibula", "ankle", "foot", "cranium", "skull", "rib", "clavicle",
                "scapula", "pelvis", "joint", "ligament", "tendon", "muscle", "nerve"
            ],
            "procedures": [
                "x-ray", "mri", "ct scan", "ultrasound", "surgery", "operation", "arthroscopy",
                "discectomy", "laminectomy", "fusion", "reduction", "fixation", "immobilization",
                "cast", "splint", "brace", "injection", "aspiration", "physiotherapy", "rehabilitation",
                "therapy", "assessment", "examination", "consultation"
            ],
            "medications": [
                "analgesic", "painkiller", "nsaid", "steroid", "anti-inflammatory", "opioid",
                "muscle relaxant", "sedative", "antibiotic", "antidepressant", "gabapentin",
                "pregabalin", "tramadol", "oxycodone", "paracetamol", "ibuprofen", "naproxen",
                "diclofenac", "codeine", "morphine", "fentanyl", "amitriptyline"
            ]
        }
        
        # Common medical report patterns
        self.patterns = {
            "patient_id": r'(?:patient|case|medical)\s*(?:id|number|#)(?:[:-])?\s*([A-Z0-9]{5,12})',
            "medicare_number": r'(?:medicare|health\s+insurance)\s*(?:number|#)(?:[:-])?\s*(\d{4}[ -]?\d{5}[ -]?\d{1,2}|\d{10,11})',
            "medical_provider": r'(?:doctor|physician|specialist|surgeon|practitioner|provider)(?:[:-])?\s*(?:Dr\.?|Professor|Prof\.|MD)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
            "hospital": r'(?:hospital|medical\s+center|clinic|facility)(?:[:-])?\s*([A-Z][a-zA-Z\s&\'\-]+)',
            "date_of_consultation": r'(?:date\s+of|consultation\s+date|examination\s+date|assessment\s+date)(?:[:-])?\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})',
            "date_of_injury": r'(?:date\s+of\s+injury|injury\s+date|accident\s+date|incident\s+date)(?:[:-])?\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})',
            "diagnosis_code": r'(?:diagnosis\s+code|diagnostic\s+code|icd)(?:[:-])?\s*([A-Z]\d{2}(?:\.\d{1,2})?)',
            "procedure_code": r'(?:procedure\s+code|cpt|service\s+code)(?:[:-])?\s*(\d{5}(?:-\d{2})?)'
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze medical report text to extract structured information.
        
        Args:
            text: Medical report text
            
        Returns:
            Dictionary with extracted information
        """
        # Segment the text into sections
        segments = self.text_processor.segment_text(text)
        
        # Extract specific information using regex patterns
        extracted_info = self._extract_specific_information(text)
        
        # Identify sections based on headers
        sections = self._identify_sections(segments)
        
        # Extract patient information
        patient_info = self._extract_patient_info(text, sections)
        
        # Extract clinical information
        clinical_info = self._extract_clinical_info(text, sections)
        
        # Extract diagnosis information
        diagnosis_info = self._extract_diagnosis_info(text, sections)
        
        # Extract treatment information
        treatment_info = self._extract_treatment_info(text, sections)
        
        # Detect medical terminology
        medical_terms = self._detect_medical_terminology(text)
        
        # Detect PII entities
        pii_entities = self._detect_pii_entities(text)
        
        # Get PII-rich segments
        pii_segments = self.text_processor.extract_pii_rich_segments(text)
        
        # Combine all analyses
        result = {
            "extracted_info": extracted_info,
            "sections": sections,
            "patient_info": patient_info,
            "clinical_info": clinical_info,
            "diagnosis_info": diagnosis_info,
            "treatment_info": treatment_info,
            "medical_terms": medical_terms,
            "pii_entities": pii_entities,
            "pii_segments": pii_segments[:3]  # Top 3 PII-rich segments
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
    
    def _identify_sections(self, segments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify sections in the medical report.
        
        Args:
            segments: List of text segments
            
        Returns:
            Dictionary mapping section types to segments
        """
        section_segments = {}
        current_section = None
        
        for segment in segments:
            # Check if this segment is a header
            if segment.get("is_header", False):
                section_text = segment["text"].lower()
                
                # Determine section type based on header text
                found_section = False
                for section_type, headers in self.section_headers.items():
                    if any(header in section_text for header in headers):
                        current_section = section_type
                        found_section = True
                        
                        # Initialize this section if not already present
                        if current_section not in section_segments:
                            section_segments[current_section] = []
                        
                        break
                
                if not found_section:
                    current_section = "other"
                    if current_section not in section_segments:
                        section_segments[current_section] = []
            
            # Add this segment to the current section
            if current_section:
                section_segments[current_section].append(segment)
        
        return section_segments
    
    def _extract_patient_info(self, text: str, sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract patient information from the report."""
        patient_info = {}
        
        # Extract from patient_info section if present
        if "patient_info" in sections:
            section_text = " ".join([s["text"] for s in sections["patient_info"]])
            
            # Extract specific fields using regex
            patterns = {
                "name": r'(?:name|patient)(?:[:-])?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
                "age": r'(?:age|years old)(?:[:-])?\s*(\d{1,3})',
                "gender": r'(?:gender|sex)(?:[:-])?\s*(male|female|non-binary|transgender|other)',
                "dob": r'(?:date of birth|dob|born)(?:[:-])?\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})',
                "address": r'(?:address|residence)(?:[:-])?\s*([^,\n]+(,[^,\n]+){1,4})',
                "contact": r'(?:contact|phone|telephone)(?:[:-])?\s*((?:\+?61|0)\s*\d(?:[ \.-]?\d{2,4}){2,4})'
            }
            
            for field, pattern in patterns.items():
                matches = re.search(pattern, section_text, re.IGNORECASE)
                if matches:
                    patient_info[field] = matches.group(1).strip()
        
        # Also try to extract from the entire text for key identifiers
        if "name" not in patient_info:
            name_match = re.search(r'(?:Patient(?:\s+Name)?|Name)(?:[:-])?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', text, re.IGNORECASE)
            if name_match:
                patient_info["name"] = name_match.group(1).strip()
        
        # Try to extract Medicare number if not found in extracted_info
        if "medicare_number" not in patient_info:
            medicare_match = re.search(r'(?:Medicare|Health\s+Insurance)(?:[:-])?\s*(\d{4}[ -]?\d{5}[ -]?\d{1,2}|\d{10,11})', text, re.IGNORECASE)
            if medicare_match:
                patient_info["medicare_number"] = medicare_match.group(1).strip()
        
        return patient_info
    
    def _extract_clinical_info(self, text: str, sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract clinical information from the report."""
        clinical_info = {}
        
        # Extract from clinical_history and examination sections if present
        for section_type in ["clinical_history", "examination"]:
            if section_type in sections:
                section_text = " ".join([s["text"] for s in sections[section_type]])
                clinical_info[section_type] = section_text
        
        # Extract specific clinical fields
        injury_match = re.search(r'(?:injury|presenting complaint|chief complaint|reason for visit)(?:[:-])?\s*([^.]+)', text, re.IGNORECASE)
        if injury_match:
            clinical_info["injury_description"] = injury_match.group(1).strip()
        
        mechanism_match = re.search(r'(?:mechanism of injury|how the injury occurred|how it happened)(?:[:-])?\s*([^.]+)', text, re.IGNORECASE)
        if mechanism_match:
            clinical_info["mechanism_of_injury"] = mechanism_match.group(1).strip()
        
        return clinical_info
    
    def _extract_diagnosis_info(self, text: str, sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract diagnosis information from the report."""
        diagnosis_info = {}
        
        # Extract from diagnosis section if present
        if "diagnosis" in sections:
            section_text = " ".join([s["text"] for s in sections["diagnosis"]])
            diagnosis_info["diagnosis_text"] = section_text
            
            # Try to extract specific diagnoses
            # Look for numbered or bulleted lists
            diagnosis_items = re.findall(r'(?:^|\n)(?:\d+\.|\*|-)\s*([^\n]+)', section_text)
            if diagnosis_items:
                diagnosis_info["diagnoses"] = diagnosis_items
            else:
                # Try to split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', section_text)
                if sentences:
                    diagnosis_info["diagnoses"] = sentences
        
        # Try to extract ICD codes
        icd_codes = re.findall(r'(?:ICD-10|ICD)(?:-)?(?:CM)?\s*(?:code|diagnosis)?\s*(?:[:-])?\s*([A-Z]\d{2}(?:\.\d{1,2})?)', text, re.IGNORECASE)
        if icd_codes:
            diagnosis_info["icd_codes"] = icd_codes
        
        return diagnosis_info
    
    def _extract_treatment_info(self, text: str, sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract treatment information from the report."""
        treatment_info = {}
        
        # Extract from treatment and medication sections if present
        for section_type in ["treatment", "medication"]:
            if section_type in sections:
                section_text = " ".join([s["text"] for s in sections[section_type]])
                treatment_info[section_type] = section_text
        
        # Try to extract specific treatments
        treatment_patterns = {
            "medications": r'(?:medications?|drugs?|prescriptions?)(?:[:-])?\s*([^.]+)',
            "procedures": r'(?:procedures?|surgeries?|operations?)(?:[:-])?\s*([^.]+)',
            "therapy": r'(?:therapy|physiotherapy|physical therapy|rehabilitation)(?:[:-])?\s*([^.]+)',
            "followup": r'(?:follow[ -]?up|review|subsequent visit)(?:[:-])?\s*([^.]+)'
        }
        
        for treatment_type, pattern in treatment_patterns.items():
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                treatment_info[treatment_type] = matches.group(1).strip()
        
        # Try to extract medication list
        medication_items = re.findall(r'(?:^|\n)(?:\d+\.|\*|-)\s*([^\n]+\b(?:mg|mcg|mL|tablet|capsule|patch|injection|daily|twice|BID|TID|QID)\b[^\n]*)', text, re.IGNORECASE)
        if medication_items:
            treatment_info["medication_list"] = medication_items
        
        return treatment_info
    
    def _detect_medical_terminology(self, text: str) -> Dict[str, List[str]]:
        """Detect medical terminology in the report."""
        text_lower = text.lower()
        detected_terms = {}
        
        for category, terms in self.medical_terminology.items():
            detected = []
            for term in terms:
                if term in text_lower:
                    # Find all instances with word boundaries
                    matches = re.findall(r'\b' + re.escape(term) + r'\b', text_lower)
                    if matches:
                        detected.append(term)
            
            if detected:
                detected_terms[category] = detected
        
        return detected_terms
    
    def _detect_pii_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Detect PII entities in the report."""
        results = self.analyzer.analyze(text)
        
        # Group by entity type
        entities_by_type = {}
        for result in results:
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
    
    def extract_suitability_for_work(self, text: str) -> Dict[str, Any]:
        """
        Extract information about suitability for work or return to work.
        Useful for workers' compensation claims.
        
        Args:
            text: Medical report text
            
        Returns:
            Dictionary with work capacity information
        """
        work_info = {}
        
        # Patterns for work capacity assessment
        patterns = {
            "work_capacity": r'(?:work capacity|fitness for work|work fitness)(?:[:-])?\s*([^.]+)',
            "return_date": r'(?:return to work|RTW|resume work)(?:[:-])?\s*(?:on|date|from)?\s*(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4})',
            "restrictions": r'(?:restrictions|limitations|modified duties)(?:[:-])?\s*([^.]+)',
            "hours": r'(?:reduced hours|part-time|full-time)(?:[:-])?\s*([^.]+)',
            "duration": r'(?:duration|period|timeframe)(?:[:-])?\s*([^.]+)'
        }
        
        for info_type, pattern in patterns.items():
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                work_info[info_type] = matches.group(1).strip()
        
        # Determine overall work status
        status_patterns = {
            "fit_for_work": r'\b(?:fit for work|can resume|can return)\b',
            "unfit_for_work": r'\b(?:unfit for work|not fit|cannot resume|cannot return|unable to work)\b',
            "modified_duties": r'\b(?:modified duties|restricted duties|light duties|alternative duties)\b',
            "gradual_return": r'\b(?:gradual return|graduated return|staged return|phased return)\b'
        }
        
        for status, pattern in status_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                work_info["work_status"] = status
                break
        
        return work_info
    
    def extract_impairment_assessment(self, text: str) -> Dict[str, Any]:
        """
        Extract impairment assessment information.
        Useful for permanent impairment claims.
        
        Args:
            text: Medical report text
            
        Returns:
            Dictionary with impairment information
        """
        impairment_info = {}
        
        # Patterns for impairment assessment
        patterns = {
            "impairment_rating": r'(?:impairment|disability|WPI|whole person impairment)(?:[:-])?\s*(\d{1,3}(?:\.\d{1,2})?\s*\%)',
            "assessment_guide": r'(?:assessed according to|assessed using|based on|as per)(?:[:-])?\s*([^.]+)',
            "body_part": r'(?:impairment of|disability of|injury to)(?:[:-])?\s*([^.]+)',
            "permanent": r'(?:permanent|long-term|chronic|ongoing)(?:[:-])?\s*([^.]+)'
        }
        
        for info_type, pattern in patterns.items():
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                impairment_info[info_type] = matches.group(1).strip()
        
        # Try to extract specific percentage ratings
        percentage_matches = re.findall(r'(\d{1,2}(?:\.\d{1,2})?\s*\%)\s*(?:impairment|disability|WPI|loss)', text, re.IGNORECASE)
        if percentage_matches:
            impairment_info["percentage_ratings"] = percentage_matches
        
        return impairment_info
    
    def anonymize_medical_report(self, text: str) -> Dict[str, Any]:
        """
        Anonymize a medical report while preserving its structure.
        
        Args:
            text: Medical report text
            
        Returns:
            Dictionary with anonymized text and details
        """
        from ..enhanced_anonymizer import EnhancedAnonymizer
        
        # Create anonymizer
        anonymizer = EnhancedAnonymizer(analyzer=self.analyzer)
        
        # Define anonymization operators for medical context
        operators = {
            "PERSON": "replace",
            "AU_PHONE": "mask",
            "AU_MEDICARE": "redact",
            "AU_TFN": "redact",
            "AU_DRIVERS_LICENSE": "hash",
            "AU_BSB_ACCOUNT": "mask",
            "AU_ADDRESS": "replace",
            "EMAIL_ADDRESS": "mask",
            "DATE": {"type": "replace", "new_value": "<DATE>"},
            "AU_POSTCODE": "mask",
            "MEDICARE_PROVIDER_NUMBER": "hash",
            "MEDICAL_RECORD_NUMBER": "hash"
        }
        
        # Anonymize the text
        anonymized = anonymizer.anonymize(
            text=text,
            operators=operators
        )
        
        # Extract sections from the anonymized text
        try:
            anonymized_segments = self.text_processor.segment_text(anonymized["text"])
            anonymized_sections = self._identify_sections(anonymized_segments)
        except Exception:
            anonymized_sections = {}
        
        return {
            "anonymized_text": anonymized["text"],
            "entities_found": anonymized["items"],
            "anonymized_sections": anonymized_sections
        }

# Helper function for directly analyzing medical reports
def analyze_medical_report(text: str) -> Dict[str, Any]:
    """
    Analyze a medical report using the MedicalReportAnalyzer.
    
    Args:
        text: Medical report text
        
    Returns:
        Dictionary with structured information
    """
    analyzer = MedicalReportAnalyzer()
    return analyzer.analyze(text)