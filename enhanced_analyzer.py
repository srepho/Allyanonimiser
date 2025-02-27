"""
Enhanced analyzer that extends Presidio's analyzer with custom pattern support.
Provides unified processing for all text types (emails, claim notes, medical reports, etc.).
"""

from typing import List, Dict, Optional, Union, Any, Tuple, Set, Iterable
import re
import logging
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngine

from .pattern_manager import PatternManager, CustomPatternDefinition
from .utils.spacy_helpers import load_spacy_model
from .utils.long_text_processor import LongTextProcessor

class EnhancedAnalyzer:
    """
    Enhanced analyzer that extends Presidio's AnalyzerEngine with custom pattern support.
    Combines results from both Presidio's built-in recognizers and custom spaCy patterns.
    Provides unified processing for all text types.
    """
    
    def __init__(
        self,
        pattern_manager: Optional[PatternManager] = None,
        registry: Optional[RecognizerRegistry] = None,
        nlp_engine: Optional[NlpEngine] = None,
        patterns: Optional[List[Union[Dict[str, Any], CustomPatternDefinition]]] = None,
        language: str = "en",
        spacy_model: Optional[str] = None,
        nlp = None,
        log_analysis_results: bool = False
    ):
        """
        Initialize the EnhancedAnalyzer.
        
        Args:
            pattern_manager: Initialized PatternManager
            registry: Presidio RecognizerRegistry
            nlp_engine: Presidio NlpEngine
            patterns: List of pattern definitions to use
            language: Language code
            spacy_model: Name of spaCy model to load
            nlp: Pre-loaded spaCy NLP pipeline
            log_analysis_results: Whether to log analysis results
        """
        # Initialize pattern manager
        self.pattern_manager = pattern_manager or PatternManager(patterns=patterns or [])
        
        # Load spaCy model if not provided
        self.nlp = nlp or load_spacy_model(spacy_model)
        
        # Initialize text processor for long texts, emails, etc.
        self.text_processor = LongTextProcessor(self.nlp)
        
        # Initialize registry if not provided
        if registry is None:
            registry = RecognizerRegistry()
            registry.load_predefined_recognizers(languages=[language])
            
            # Add custom recognizers
            for pattern in self.pattern_manager.get_patterns():
                recognizer = self.pattern_manager.pattern_to_recognizer(pattern)
                registry.add_recognizer(recognizer)
        
        self.registry = registry
        self.language = language
        self.log_analysis_results = log_analysis_results
        
        # Initialize analyzer engine
        self.analyzer_engine = AnalyzerEngine(
            registry=registry, 
            nlp_engine=nlp_engine,
            supported_languages=[language]
        )
    
    def add_pattern(self, pattern: Union[Dict[str, Any], CustomPatternDefinition]) -> None:
        """
        Add a pattern to the analyzer.
        
        Args:
            pattern: Pattern definition to add
        """
        if not pattern:
            logging.warning("Attempted to add empty pattern")
            return
            
        # Add to pattern manager
        self.pattern_manager.add_pattern(pattern)
        
        # Create and add recognizer
        recognizer = self.pattern_manager.pattern_to_recognizer(pattern)
        self.registry.add_recognizer(recognizer)
        
        # Update analyzer engine with the new registry
        self.analyzer_engine = AnalyzerEngine(
            registry=self.registry,
            nlp_engine=self.analyzer_engine.nlp_engine,
            supported_languages=[self.language]
        )
    
    def analyze(
        self, 
        text: str, 
        language: Optional[str] = None,
        score_threshold: float = 0.3,
        entities: Optional[List[str]] = None,
        return_decision_process: bool = False,
        ad_hoc_recognizers: Optional[List[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyze text for PII entities.
        
        Args:
            text: Text to analyze
            language: Language of the text
            score_threshold: Minimum confidence score for results
            entities: Specific entities to look for
            return_decision_process: Whether to include decision process in results
            ad_hoc_recognizers: Additional recognizers to use for this analysis only
            
        Returns:
            List of detected entities with details
        """
        if not text:
            return []
        
        # Use specified language or default
        lang = language or self.language
        
        # Get Presidio results
        analyzer_results = self.analyzer_engine.analyze(
            text=text,
            language=lang,
            entities=entities,
            score_threshold=score_threshold,
            return_decision_process=return_decision_process,
            ad_hoc_recognizers=ad_hoc_recognizers
        )
        
        # Convert to serializable format
        results = []
        for result in analyzer_results:
            result_dict = {
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
                "text": text[result.start:result.end],
                "recognizer": result.recognition_metadata['recognizer'] if result.recognition_metadata else None
            }
            
            # Add decision factors if requested
            if return_decision_process and hasattr(result, "analysis_explanation"):
                result_dict["decision_factors"] = result.analysis_explanation
                
            results.append(result_dict)
            
        if self.log_analysis_results and results:
            logging.info(f"Found {len(results)} entities in text: {results}")
            
        return results
        
    def process_text(self, text: str, language: str = None) -> Dict[str, Any]:
        """
        Unified method to process any type of text, automatically detecting content type.
        
        This method provides a simplified interface for processing any text by:
        1. Detecting the content type (email, claim note, medical report, etc.)
        2. Applying the appropriate processing based on content type
        3. Returning a standardized result structure
        
        Args:
            text: The text to process
            language: Language of the text (defaults to language set during initialization)
            
        Returns:
            Dictionary containing:
            - content_type: Detected type of content
            - entities: List of detected entities
            - structured_data: Any structured information extracted (headers, subject, etc.)
            - segments: Content divided into logical segments with PII likelihood scores
        """
        # Use specified language or default
        lang = language or self.language
        
        # Detect content type
        content_type = self._detect_content_type(text)
        
        # Basic entity detection
        entities = self.analyze(text, language=lang)
        
        # Initialize result structure
        result = {
            "content_type": content_type,
            "entities": entities,
            "structured_data": {},
            "segments": []
        }
        
        # Process based on content type
        if content_type == "email":
            return self._process_email(text, result)
        elif content_type == "claim_note":
            return self._process_claim_note(text, result)
        elif content_type == "medical_report":
            return self._process_medical_report(text, result)
        else:
            # Generic processing for unknown content types
            return self._process_generic(text, result)
    
    def _detect_content_type(self, text: str) -> str:
        """
        Detect the type of content in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            String identifying the content type: "email", "claim_note", "medical_report", or "generic"
        """
        # Check for email patterns
        email_patterns = [
            r"^From:.*?$",
            r"^To:.*?$", 
            r"^Subject:.*?$",
            r"^Date:.*?$",
            r"^Cc:.*?$",
            r"^Bcc:.*?$"
        ]
        
        email_header_matches = sum(1 for p in email_patterns if re.search(p, text, re.MULTILINE))
        if email_header_matches >= 2:
            return "email"
            
        # Check for claim note patterns
        claim_patterns = [
            r"claim\s+(?:number|reference|ref|#)",
            r"policy\s+(?:number|#)",
            r"incident\s+(?:date|description)",
            r"insured(?:'s)?\s+(?:name|details)"
        ]
        
        claim_matches = sum(1 for p in claim_patterns if re.search(p, text, re.IGNORECASE))
        if claim_matches >= 2:
            return "claim_note"
            
        # Check for medical report patterns
        medical_patterns = [
            r"(?:patient|diagnosis|symptoms|treatment|medication|doctor|physician|hospital)",
            r"(?:medical|clinical|healthcare|patient) (?:record|report|assessment|evaluation)",
            r"(?:medical history|family history|allergies|medications)"
        ]
        
        medical_matches = sum(1 for p in medical_patterns if re.search(p, text, re.IGNORECASE))
        if medical_matches >= 2:
            return "medical_report"
            
        # Default to generic
        return "generic"
    
    def _process_email(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process email content."""
        import email
        from email.parser import Parser
        from email.policy import default
        
        # Parse email
        try:
            message = email.message_from_string(text, policy=default)
            result["structured_data"]["headers"] = dict(message.items())
            result["structured_data"]["subject"] = message.get("Subject", "")
            result["structured_data"]["from"] = message.get("From", "")
            result["structured_data"]["to"] = message.get("To", "")
            
            # Extract body
            body = ""
            if message.is_multipart():
                for part in message.get_payload():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload()
            else:
                body = message.get_payload()
                
            result["structured_data"]["body"] = body
            
            # Process segments with the long text processor
            segments = self.text_processor.split_into_paragraphs(body)
            result["segments"] = [
                {
                    "text": seg,
                    "pii_likelihood": self._calculate_pii_likelihood(seg, self.analyze(seg))
                }
                for seg in segments if seg.strip()
            ]
            
        except Exception as e:
            logging.warning(f"Error parsing email: {str(e)}")
            # Fall back to generic processing
            return self._process_generic(text, result)
            
        return result
    
    def _process_claim_note(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process insurance claim notes."""
        # Extract common insurance claim fields
        patterns = {
            "claim_number": r"(?:claim|reference)\s*(?:number|ref|#)?:?\s*([A-Z0-9-]+)",
            "policy_number": r"policy\s*(?:number|#)?:?\s*([A-Z0-9-]+)",
            "incident_date": r"(?:incident|event|accident)\s*date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "customer_name": r"(?:customer|insured|claimant)(?:'s)?\s*name:?\s*([A-Za-z\s]+)",
        }
        
        # Extract structured data
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["structured_data"][key] = match.group(1).strip()
        
        # Extract incident description
        incident_pattern = r"(?:incident|accident)\s*description:?\s*(.*?)(?:\n\n|\r\n\r\n|$)"
        match = re.search(incident_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            result["structured_data"]["incident_description"] = match.group(1).strip()
        
        # Process segments with the long text processor
        segments = self.text_processor.split_into_paragraphs(text)
        result["segments"] = [
            {
                "text": seg,
                "pii_likelihood": self._calculate_pii_likelihood(seg, self.analyze(seg))
            }
            for seg in segments if seg.strip()
        ]
        
        return result
        
    def _process_medical_report(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process medical report content."""
        # Extract common medical report fields
        patterns = {
            "patient_name": r"(?:patient|name):?\s*([A-Za-z\s]+)",
            "dob": r"(?:dob|date\s*of\s*birth):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "medicare": r"(?:medicare)(?:\s*(?:number|#))?:?\s*(\d{4}\s*\d{5}\s*\d{1})",
        }
        
        # Extract structured data
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["structured_data"][key] = match.group(1).strip()
        
        # Extract assessment/diagnosis
        assessment_pattern = r"(?:assessment|diagnosis|impression):?\s*(.*?)(?:\n\n|\r\n\r\n|$)"
        match = re.search(assessment_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            result["structured_data"]["assessment"] = match.group(1).strip()
            
        # Extract treatment plan
        treatment_pattern = r"(?:treatment|plan|recommendation):?\s*(.*?)(?:\n\n|\r\n\r\n|$)"
        match = re.search(treatment_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            result["structured_data"]["treatment_plan"] = match.group(1).strip()
        
        # Process segments with the long text processor
        segments = self.text_processor.split_into_paragraphs(text)
        result["segments"] = [
            {
                "text": seg,
                "pii_likelihood": self._calculate_pii_likelihood(seg, self.analyze(seg))
            }
            for seg in segments if seg.strip()
        ]
        
        return result
    
    def _process_generic(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process generic text content."""
        # Process segments with the long text processor
        segments = self.text_processor.split_into_paragraphs(text)
        result["segments"] = [
            {
                "text": seg,
                "pii_likelihood": self._calculate_pii_likelihood(seg, self.analyze(seg))
            }
            for seg in segments if seg.strip()
        ]
        
        return result
    
    def _calculate_pii_likelihood(self, text: str, entities: List[Dict[str, Any]]) -> float:
        """
        Calculate the likelihood that a text segment contains PII.
        
        Args:
            text: Text segment
            entities: Detected entities in the segment
            
        Returns:
            Score between 0 and 1 indicating PII likelihood
        """
        if not text or not entities:
            return 0.0
            
        # Basic calculation - percentage of text covered by entities
        text_length = len(text)
        if text_length == 0:
            return 0.0
            
        # Count non-overlapping characters in entities
        entity_chars = set()
        for entity in entities:
            for i in range(entity["start"], entity["end"]):
                entity_chars.add(i)
                
        # Calculate coverage
        coverage = len(entity_chars) / text_length
        
        # Calculate average score of entities
        avg_score = sum(entity["score"] for entity in entities) / len(entities) if entities else 0
        
        # Combine coverage and score
        return 0.7 * coverage + 0.3 * avg_score