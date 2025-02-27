"""
Main interface for the Allyanonimiser package.

This module provides a unified interface for PII detection and anonymization
of mixed content types (emails, claim notes, reports, etc.) regardless of source.
"""

import os
from typing import Dict, List, Any, Optional, Union, Callable

from .enhanced_analyzer import EnhancedAnalyzer
from .enhanced_anonymizer import EnhancedAnonymizer
from .utils.long_text_processor import (
    analyze_claim_notes,
    extract_pii_rich_segments,
    segment_long_text
)
from .insurance.claim_notes_analyzer import analyze_claim_note
from .insurance.email_analyzer import InsuranceEmailAnalyzer


class Allyanonimiser:
    """
    Main interface for PII detection and anonymization of mixed content.
    
    This class provides a single entry point for processing various types of content
    including emails, claim notes, medical reports, and other free text documents.
    It automatically detects the content type when possible and applies the appropriate
    processing strategy.
    """
    
    def __init__(
        self,
        analyzer: Optional[EnhancedAnalyzer] = None,
        anonymizer: Optional[EnhancedAnonymizer] = None,
        content_processors: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize the Allyanonimiser.
        
        Args:
            analyzer: Optional EnhancedAnalyzer instance
            anonymizer: Optional EnhancedAnonymizer instance
            content_processors: Optional dictionary mapping content types to processor functions
        """
        from . import create_au_insurance_analyzer
        
        self.analyzer = analyzer or create_au_insurance_analyzer()
        self.anonymizer = anonymizer or EnhancedAnonymizer(analyzer=self.analyzer)
        
        # Default content processors
        self.email_analyzer = InsuranceEmailAnalyzer()
        
        # Register content type processors
        self.content_processors = {
            "email": self._process_email,
            "claim_note": self._process_claim_note,
            "medical_report": self._process_medical_report,
            "generic": self._process_generic_text
        }
        
        # Override with user-provided processors if any
        if content_processors:
            self.content_processors.update(content_processors)
        
        # Content type detection patterns
        self.content_type_patterns = {
            "email": [
                r"^From:.*$",
                r"^To:.*$",
                r"^Subject:.*$",
                r"^Cc:.*$",
                r"^Bcc:.*$",
                r"^Sent:.*$",
                r"^Received:.*$"
            ],
            "claim_note": [
                r"(?:Claim|Reference)\s*(?:Number|#|ID|No)[:\s]+",
                r"(?:Policy|Insurance)\s*(?:Number|#|ID|No)[:\s]+",
                r"(?:Incident|Accident|Event)\s*(?:Details|Summary|Description)[:\s]+",
                r"(?:Insured|Customer|Client)\s*(?:Details|Information)[:\s]+"
            ],
            "medical_report": [
                r"(?:Patient|Medical|Health)\s*(?:Record|Report|Summary|Assessment)[:\s]+",
                r"(?:Diagnosis|Treatment|Prognosis|Medication|Prescription)[:\s]+",
                r"(?:Doctor|Physician|Specialist|Consultant|Clinician)[:\s]+",
                r"(?:Hospital|Clinic|Medical Center|Surgery|Practice)[:\s]+"
            ]
        }
    
    def process(
        self, 
        text: str, 
        content_type: Optional[str] = None,
        anonymize: bool = True,
        operators: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process text for PII detection and optional anonymization.
        
        Args:
            text: Text to process
            content_type: Optional content type override ("email", "claim_note", "medical_report", "generic")
            anonymize: Whether to anonymize the text
            operators: Optional custom anonymization operators
            
        Returns:
            Dictionary with analysis results and anonymized text if requested
        """
        # Detect content type if not provided
        if content_type is None:
            content_type = self._detect_content_type(text)
        
        # Process according to content type
        if content_type in self.content_processors:
            processor = self.content_processors[content_type]
            results = processor(text)
        else:
            # Fall back to generic processor
            results = self._process_generic_text(text)
        
        # Add basic entity detection results
        if "entities" not in results:
            entities = self.analyzer.analyze(text)
            results["entities"] = [
                {
                    "entity_type": entity.entity_type,
                    "text": text[entity.start:entity.end],
                    "start": entity.start,
                    "end": entity.end,
                    "score": entity.score
                }
                for entity in entities
            ]
        
        # Anonymize if requested
        if anonymize:
            # Default operators if not provided
            if operators is None:
                operators = {
                    "PERSON": "replace",
                    "AU_PHONE": "mask",
                    "AU_MEDICARE": "redact",
                    "AU_TFN": "redact",
                    "AU_DRIVERS_LICENSE": "hash",
                    "AU_BSB_ACCOUNT": "mask",
                    "AU_ADDRESS": "replace",
                    "EMAIL_ADDRESS": "mask",
                    "VEHICLE_REGISTRATION": "replace",
                    "VEHICLE_VIN": "hash",
                    "INSURANCE_POLICY_NUMBER": "replace",
                    "INSURANCE_CLAIM_NUMBER": "replace",
                    "INVOICE_NUMBER": "replace",
                    "DATE": "replace",
                    "ID_NUMBER": "replace",
                    "CREDIT_CARD_NUMBER": "redact",
                    "PHONE_NUMBER": "mask",
                    "URL": "mask",
                    "IP_ADDRESS": "mask"
                }
            
            anonymized = self.anonymizer.anonymize(
                text=text,
                operators=operators
            )
            
            results["anonymized_text"] = anonymized["text"]
            results["anonymization_stats"] = anonymized.get("statistics", {})
        
        return results
    
    def batch_process(
        self,
        texts: List[str],
        content_types: Optional[List[str]] = None,
        anonymize: bool = True,
        operators: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple texts in batch.
        
        Args:
            texts: List of texts to process
            content_types: Optional list of content types matching the texts
            anonymize: Whether to anonymize the texts
            operators: Optional custom anonymization operators
            
        Returns:
            List of processing results for each text
        """
        results = []
        
        for i, text in enumerate(texts):
            content_type = None
            if content_types and i < len(content_types):
                content_type = content_types[i]
                
            result = self.process(
                text=text,
                content_type=content_type,
                anonymize=anonymize,
                operators=operators
            )
            
            results.append(result)
        
        return results
    
    def process_files(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None,
        content_types: Optional[List[str]] = None,
        anonymize: bool = True,
        operators: Optional[Dict[str, str]] = None,
        save_results: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple files.
        
        Args:
            file_paths: Paths to files to process
            output_dir: Optional directory to save results
            content_types: Optional list of content types matching the files
            anonymize: Whether to anonymize the texts
            operators: Optional custom anonymization operators
            save_results: Whether to save results to files
            
        Returns:
            List of processing results for each file
        """
        import json
        
        results = []
        
        # Create output directory if needed
        if save_results and output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        for i, file_path in enumerate(file_paths):
            try:
                # Read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Get content type if provided
                content_type = None
                if content_types and i < len(content_types):
                    content_type = content_types[i]
                
                # Process the text
                result = self.process(
                    text=text,
                    content_type=content_type,
                    anonymize=anonymize,
                    operators=operators
                )
                
                # Add file metadata
                result["file_metadata"] = {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "file_size": os.path.getsize(file_path)
                }
                
                # Save results if requested
                if save_results and output_dir:
                    file_name = os.path.basename(file_path)
                    file_base = os.path.splitext(file_name)[0]
                    
                    # Save anonymized text
                    if anonymize:
                        with open(os.path.join(output_dir, f"{file_base}_anonymized.txt"), 'w', encoding='utf-8') as f:
                            f.write(result["anonymized_text"])
                    
                    # Save analysis results
                    analysis_result = {k: v for k, v in result.items() if k != "anonymized_text"}
                    with open(os.path.join(output_dir, f"{file_base}_analysis.json"), 'w', encoding='utf-8') as f:
                        json.dump(analysis_result, f, indent=2)
                
                results.append(result)
                
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                results.append({
                    "error": str(e),
                    "file_path": file_path
                })
        
        return results
    
    def _detect_content_type(self, text: str) -> str:
        """
        Detect the type of content from its text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Content type string
        """
        import re
        
        # Check each content type's patterns
        for content_type, patterns in self.content_type_patterns.items():
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                    matches += 1
            
            # If enough patterns match, return this content type
            if matches >= len(patterns) // 3:  # At least 1/3 of patterns match
                return content_type
        
        # Default to generic if no specific type is detected
        return "generic"
    
    def _process_email(self, text: str) -> Dict[str, Any]:
        """Process email text."""
        analysis = self.email_analyzer.analyze(text)
        
        # Extract PIIs using the enhanced analyzer
        entities = self.analyzer.analyze(text)
        
        # Add entities to results
        analysis["entities"] = [
            {
                "entity_type": entity.entity_type,
                "text": text[entity.start:entity.end],
                "start": entity.start,
                "end": entity.end,
                "score": entity.score
            }
            for entity in entities
        ]
        
        return analysis
    
    def _process_claim_note(self, text: str) -> Dict[str, Any]:
        """Process insurance claim note text."""
        analysis = analyze_claim_note(text)
        
        # Add PII segments
        pii_segments = extract_pii_rich_segments(text)
        analysis["pii_segments"] = pii_segments
        
        return analysis
    
    def _process_medical_report(self, text: str) -> Dict[str, Any]:
        """Process medical report text."""
        # For now, process as generic text with medical-specific focus
        segments = segment_long_text(text)
        
        # Extract PII segments
        pii_segments = extract_pii_rich_segments(text)
        
        # Basic analysis with focus on medical terms
        return {
            "segments": segments,
            "pii_segments": pii_segments,
            "content_type": "medical_report"
        }
    
    def _process_generic_text(self, text: str) -> Dict[str, Any]:
        """Process generic text."""
        # Segment the text
        segments = segment_long_text(text)
        
        # Get PII-rich segments
        pii_segments = extract_pii_rich_segments(text)
        
        return {
            "segments": segments,
            "pii_segments": pii_segments,
            "content_type": "generic"
        }