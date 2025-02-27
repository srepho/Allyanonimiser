"""
Specialized analyzer for insurance-related emails.
Provides functionality for extracting structured information from email content.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import email
from email.parser import Parser
from email.policy import default

from ..utils.long_text_processor import LongTextProcessor
from ..enhanced_analyzer import EnhancedAnalyzer
from .. import create_au_insurance_analyzer

class InsuranceEmailAnalyzer:
    """
    Specialized analyzer for extracting structured information from insurance emails.
    Handles email headers, body, and attachments to extract relevant information.
    """
    
    def __init__(self, analyzer=None, nlp=None):
        """
        Initialize the insurance email analyzer.
        
        Args:
            analyzer: Optional EnhancedAnalyzer instance
            nlp: Optional spaCy language model
        """
        self.analyzer = analyzer or create_au_insurance_analyzer()
        self.text_processor = LongTextProcessor(nlp=nlp)
        
        # Patterns for extracting specific insurance information from emails
        self.patterns = {
            "claim_number": r'(?:claim|reference|ref).*?(?:number|#|\:)?\s*([A-Za-z]{0,3}[-]?[0-9]{4,10})',
            "policy_number": r'(?:policy|insurance).*?(?:number|#|\:)?\s*([A-Za-z0-9]{2,5}[-]?[A-Za-z0-9]{4,10})',
            "quote_number": r'(?:quote|quotation).*?(?:number|#|\:)?\s*([A-Za-z0-9]{2,5}[-]?[0-9]{4,8})',
            "case_number": r'(?:case|ticket|inquiry).*?(?:number|#|\:)?\s*([A-Za-z0-9]{2,5}[-]?[0-9]{4,8})',
            "customer_id": r'(?:customer|client|member).*?(?:id|number|#|\:)?\s*([A-Za-z0-9]{2,5}[-]?[0-9]{4,8})'
        }
        
        # Common salutation patterns for name extraction
        self.salutation_patterns = [
            r'Dear\s+(Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:Hello|Hi|Good\s+(?:morning|afternoon|evening)),?\s+(Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'Attention:?\s+(Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
    
    def analyze(self, email_text: str) -> Dict[str, Any]:
        """
        Analyze email content to extract structured information.
        
        Args:
            email_text: Raw email content (including headers)
            
        Returns:
            Dictionary with extracted information
        """
        # Parse the email
        parsed_email = self._parse_email(email_text)
        
        # Extract basic email metadata
        metadata = self._extract_metadata(parsed_email)
        
        # Extract specific insurance information from the body
        body_text = parsed_email.get('body', '')
        
        # Extract structured information
        extracted_info = self._extract_specific_information(body_text)
        
        # Extract customer name from salutation
        customer_name = self._extract_customer_name(body_text)
        if customer_name:
            metadata['customer_name'] = customer_name
        
        # Detect entities using EnhancedAnalyzer
        pii_entities = self._detect_pii_entities(body_text)
        
        # Identify key sections in the email body
        sections = self._identify_sections(body_text)
        
        # Analyze the body using LongTextProcessor to get PII-rich segments
        pii_segments = self.text_processor.extract_pii_rich_segments(body_text)
        
        # Combine all analyses
        result = {
            **metadata,
            **extracted_info,
            "pii_entities": pii_entities,
            "sections": sections,
            "pii_segments": pii_segments[:3],  # Top 3 PII-rich segments
            "body": body_text
        }
        
        return result
    
    def _parse_email(self, email_text: str) -> Dict[str, Any]:
        """
        Parse raw email content into structured parts.
        
        Args:
            email_text: Raw email content
            
        Returns:
            Dictionary with email parts
        """
        # Try to parse as email format first
        try:
            parser = Parser(policy=default)
            parsed = parser.parsestr(email_text)
            
            # Extract headers
            headers = {}
            for key in parsed.keys():
                headers[key.lower()] = parsed[key]
            
            # Extract body
            body = ""
            if parsed.is_multipart():
                for part in parsed.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode('utf-8', errors='replace')
            else:
                payload = parsed.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='replace')
            
            result = {
                "is_valid_email": True,
                "headers": headers,
                "subject": parsed.get('subject', ''),
                "from": parsed.get('from', ''),
                "to": parsed.get('to', ''),
                "date": parsed.get('date', ''),
                "body": body
            }
        except Exception:
            # If parsing fails, treat as plain text
            result = {
                "is_valid_email": False,
                "body": email_text
            }
        
        return result
    
    def _extract_metadata(self, parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic metadata from parsed email.
        
        Args:
            parsed_email: Parsed email dictionary
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            "is_valid_email": parsed_email.get("is_valid_email", False)
        }
        
        # Add headers if available
        if "headers" in parsed_email:
            metadata["subject"] = parsed_email.get("subject", "")
            metadata["from"] = parsed_email.get("from", "")
            metadata["to"] = parsed_email.get("to", "")
            metadata["date"] = parsed_email.get("date", "")
        
        return metadata
    
    def _extract_specific_information(self, text: str) -> Dict[str, Any]:
        """
        Extract specific insurance information using regex patterns.
        
        Args:
            text: Email body text
            
        Returns:
            Dictionary with extracted information
        """
        results = {}
        
        for info_type, pattern in self.patterns.items():
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                results[info_type] = matches.group(1).strip()
        
        return results
    
    def _extract_customer_name(self, text: str) -> Optional[str]:
        """
        Extract customer name from email salutation.
        
        Args:
            text: Email body text
            
        Returns:
            Customer name or None if not found
        """
        for pattern in self.salutation_patterns:
            matches = re.search(pattern, text)
            if matches:
                # If there's a title group, use the last group for the name
                if matches.group(1):
                    return matches.group(2).strip()
                # Otherwise use the first group
                return matches.group(1).strip()
        
        return None
    
    def _detect_pii_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect PII entities in the email body.
        
        Args:
            text: Email body text
            
        Returns:
            Dictionary of entity types to entity details
        """
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
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify key sections in the email body.
        
        Args:
            text: Email body text
            
        Returns:
            Dictionary of section types to section content
        """
        sections = {}
        
        # Common section headers in insurance emails
        section_patterns = {
            "greeting": r'^(?:Dear|Hello|Hi|Good\s+(?:morning|afternoon|evening)).*?(?=\n\n|\n)',
            "introduction": r'(?:I am writing|This is|We are|This email is).*?(?=\n\n|\n)',
            "claim_details": r'(?:Regarding|Concerning|About|In relation to).*?(?:claim|incident|accident|event).*?(?=\n\n|\n)',
            "policy_details": r'(?:Your|The)\s+policy.*?(?=\n\n|\n)',
            "action_required": r'(?:Please|Kindly|We need you to|We require).*?(?=\n\n|\n)',
            "contact_details": r'(?:If you have any questions|For more information|Should you require|If you need).*?(?:contact|call|email|reach).*?(?=\n\n|\n)',
            "closing": r'(?:Thank you|Thanks|Regards|Sincerely|Kind regards|Yours).*?$'
        }
        
        for section_type, pattern in section_patterns.items():
            matches = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if matches:
                sections[section_type] = matches.group(0).strip()
        
        return sections
    
    def analyze_thread(self, email_thread: str) -> List[Dict[str, Any]]:
        """
        Analyze an email thread with multiple messages.
        
        Args:
            email_thread: Email thread text
            
        Returns:
            List of dictionaries with analysis for each message
        """
        # Common patterns for email thread separators
        separator_patterns = [
            r'(?:^|\n)[-]+\s*Original Message\s*[-]+(?:\n|$)',
            r'(?:^|\n)[-]+\s*Forwarded Message\s*[-]+(?:\n|$)',
            r'(?:^|\n)On\s+.*?\s+wrote:(?:\n|$)',
            r'(?:^|\n)From:.*?(?:\n)Sent:.*?(?:\n)To:.*?(?:\n)Subject:.*?(?:\n)'
        ]
        
        # Combine patterns into one regex
        combined_pattern = '|'.join(f'({p})' for p in separator_patterns)
        
        # Split the thread into individual messages
        message_parts = re.split(combined_pattern, email_thread)
        
        # Filter out None and empty strings
        message_parts = [part for part in message_parts if part and part.strip()]
        
        # Analyze each message
        results = []
        for part in message_parts:
            # Check if this is just a separator
            is_separator = all(re.match(p, part) for p in separator_patterns)
            if not is_separator:
                # Analyze this message
                analysis = self.analyze(part)
                results.append(analysis)
        
        return results
    
    def anonymize_email(self, email_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Anonymize an email while preserving its structure.
        
        Args:
            email_text: Raw email content
            
        Returns:
            Tuple of (anonymized_email, anonymization_details)
        """
        from ..enhanced_anonymizer import EnhancedAnonymizer
        
        # Parse the email
        parsed_email = self._parse_email(email_text)
        
        # Create anonymizer
        anonymizer = EnhancedAnonymizer(analyzer=self.analyzer)
        
        # Define anonymization operators
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
            "INVOICE_NUMBER": "replace"
        }
        
        # Anonymize the body
        body_text = parsed_email.get('body', '')
        anonymized_body = anonymizer.anonymize(
            text=body_text,
            operators=operators
        )
        
        # If it's a valid email, reconstruct it
        if parsed_email.get("is_valid_email", False):
            # Anonymize subject
            subject = parsed_email.get("subject", "")
            anonymized_subject = anonymizer.anonymize(
                text=subject,
                operators=operators
            )
            
            # Anonymize email addresses
            from_email = parsed_email.get("from", "")
            to_email = parsed_email.get("to", "")
            
            anonymized_from = anonymizer.anonymize(
                text=from_email,
                operators={"EMAIL_ADDRESS": "mask"}
            )
            
            anonymized_to = anonymizer.anonymize(
                text=to_email,
                operators={"EMAIL_ADDRESS": "mask"}
            )
            
            # Reconstruct email headers
            headers = f"From: {anonymized_from['text']}\n"
            headers += f"To: {anonymized_to['text']}\n"
            headers += f"Subject: {anonymized_subject['text']}\n"
            headers += f"Date: {parsed_email.get('date', '')}\n\n"
            
            anonymized_email = headers + anonymized_body['text']
            
            details = {
                "headers_anonymized": True,
                "body_anonymized": True,
                "entities_found": anonymized_body['items']
            }
        else:
            # Just use the anonymized body
            anonymized_email = anonymized_body['text']
            
            details = {
                "headers_anonymized": False,
                "body_anonymized": True,
                "entities_found": anonymized_body['items']
            }
        
        return anonymized_email, details

# Helper function for directly analyzing emails
def analyze_insurance_email(email_text: str) -> Dict[str, Any]:
    """
    Analyze an insurance email using the InsuranceEmailAnalyzer.
    
    Args:
        email_text: Raw email content
        
    Returns:
        Dictionary with structured information
    """
    analyzer = InsuranceEmailAnalyzer()
    return analyzer.analyze(email_text)