"""
Main interface for the Allyanonimiser package.

This module provides a unified interface for PII detection and anonymization
of mixed content types (emails, claim notes, reports, etc.) regardless of source.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Callable

from .enhanced_analyzer import EnhancedAnalyzer
from .enhanced_anonymizer import EnhancedAnonymizer
from presidio_anonymizer.entities import OperatorConfig

class Allyanonimiser:
    """
    Unified interface for PII detection and anonymization.
    
    This class provides a single entry point for processing any type of text,
    automatically detecting content type and applying appropriate processing.
    """
    
    def __init__(
        self,
        analyzer: Optional[EnhancedAnalyzer] = None,
        anonymizer: Optional[EnhancedAnonymizer] = None,
        language: str = "en",
        default_operators: Optional[Dict[str, Union[str, OperatorConfig]]] = None,
        custom_operators: Optional[Dict[str, Callable]] = None,
        log_results: bool = False
    ):
        """
        Initialize the Allyanonimiser.
        
        Args:
            analyzer: EnhancedAnalyzer instance to use
            anonymizer: EnhancedAnonymizer instance to use
            language: Default language code
            default_operators: Default operators for anonymization
            custom_operators: Custom operator functions
            log_results: Whether to log processing results
        """
        self.analyzer = analyzer or EnhancedAnalyzer()
        self.anonymizer = anonymizer or EnhancedAnonymizer(analyzer=self.analyzer, 
                                                          custom_operators=custom_operators)
        self.language = language
        self.default_operators = default_operators or {
            "PERSON": "replace",
            "PHONE_NUMBER": "mask",
            "EMAIL_ADDRESS": "mask",
            "CREDIT_CARD": "mask",
            "US_SSN": "mask",
            "AU_TFN": "mask",
            "AU_MEDICARE": "mask",
            "LOCATION": "replace",
            "AU_ABN": "mask",
            "IBAN_CODE": "mask",
            "AU_DRIVERS_LICENSE": "mask",
            "DATE_TIME": "replace",
            "AU_ADDRESS": "replace",
            "URL": "replace",
            "IP_ADDRESS": "mask",
            "VEHICLE_REGISTRATION": "mask",
            "VEHICLE_VIN": "mask",
            "INSURANCE_POLICY_NUMBER": "mask",
            "INSURANCE_CLAIM_NUMBER": "mask"
        }
        self.log_results = log_results
    
    def process(
        self,
        text: str,
        operators: Optional[Dict[str, Union[str, OperatorConfig]]] = None,
        language: Optional[str] = None,
        anonymize: bool = True
    ) -> Dict[str, Any]:
        """
        Process text to detect and anonymize PII.
        
        This unified method automatically detects the content type and applies
        the appropriate processing, returning a standardized result structure.
        
        Args:
            text: Text to process
            operators: Operators for anonymization (uses default_operators if None)
            language: Language of the text
            anonymize: Whether to anonymize the text
            
        Returns:
            Dictionary containing:
            - content_type: Detected type of content
            - analysis: Analysis results
            - anonymized: Anonymized text if anonymize=True
            - structured_data: Extracted structured information
            - segments: Content divided into logical segments
        """
        if not text:
            return {
                "content_type": "generic",
                "analysis": {"entities": []},
                "anonymized": "",
                "structured_data": {},
                "segments": []
            }
            
        # Use default operators if not specified
        used_operators = operators or self.default_operators
        
        # Use specified language or default
        lang = language or self.language
        
        # Process the text to detect content type and extract structured data
        analysis_result = self.analyzer.process_text(text, language=lang)
        
        # Return result without anonymization if requested
        if not anonymize:
            return {
                "content_type": analysis_result["content_type"],
                "analysis": {"entities": analysis_result["entities"]},
                "structured_data": analysis_result["structured_data"],
                "segments": analysis_result["segments"]
            }
            
        # Apply anonymization
        anonymized_result = self.anonymizer.process_and_anonymize(
            text=text,
            operators=used_operators,
            language=lang
        )
        
        # Log results if enabled
        if self.log_results:
            entity_count = len(analysis_result["entities"])
            logging.info(f"Processed {len(text)} chars of {analysis_result['content_type']} content, "
                        f"found {entity_count} PII entities")
        
        # Return combined result
        return {
            "content_type": analysis_result["content_type"],
            "analysis": {"entities": analysis_result["entities"]},
            "anonymized": anonymized_result["anonymized_text"],
            "structured_data": analysis_result["structured_data"],
            "segments": anonymized_result["anonymized_segments"]
        }
    
    def batch_process(
        self,
        texts: List[str],
        operators: Optional[Dict[str, Union[str, OperatorConfig]]] = None,
        language: Optional[str] = None,
        anonymize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple texts in batch.
        
        Args:
            texts: List of texts to process
            operators: Operators for anonymization
            language: Language of the texts
            anonymize: Whether to anonymize the texts
            
        Returns:
            List of processing results
        """
        return [
            self.process(
                text=text,
                operators=operators,
                language=language,
                anonymize=anonymize
            )
            for text in texts
        ]
    
    def process_files(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None,
        operators: Optional[Dict[str, Union[str, OperatorConfig]]] = None,
        language: Optional[str] = None,
        file_encoding: str = "utf-8",
        save_results: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple text files.
        
        Args:
            file_paths: Paths to text files
            output_dir: Directory to save anonymized files
            operators: Operators for anonymization
            language: Language of the files
            file_encoding: Encoding of the files
            save_results: Whether to save anonymized files
            
        Returns:
            List of processing results with file paths
        """
        results = []
        
        for file_path in file_paths:
            try:
                # Read file
                with open(file_path, "r", encoding=file_encoding) as f:
                    text = f.read()
                
                # Process text
                result = self.process(
                    text=text,
                    operators=operators,
                    language=language
                )
                
                # Add file path to result
                result["file_path"] = file_path
                
                # Save anonymized file if requested
                if save_results and output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(
                        output_dir,
                        f"anonymized_{os.path.basename(file_path)}"
                    )
                    
                    with open(output_path, "w", encoding=file_encoding) as f:
                        f.write(result["anonymized"])
                    
                    result["anonymized_path"] = output_path
                
                results.append(result)
                
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "error": str(e)
                })
        
        return results