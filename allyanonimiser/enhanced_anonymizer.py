"""
Enhanced anonymizer for PII data anonymization.
"""
import re
import datetime

class EnhancedAnonymizer:
    """
    Enhanced anonymizer for PII data anonymization.
    This is a wrapper around Presidio Anonymizer with additional functionality.
    """
    def __init__(self, analyzer=None):
        self.analyzer = analyzer
    
    def anonymize(self, text, operators=None, language="en", age_bracket_size=5, keep_postcode=True):
        """
        Anonymize PII entities in text.
        
        Args:
            text: The text to anonymize
            operators: Dict of entity_type to anonymization operator
                       (e.g. "PERSON": "replace", "PHONE": "mask")
            language: The language of the text (default: en)
            age_bracket_size: Size of age brackets when using "age_bracket" operator (default: 5)
            keep_postcode: Whether to keep the postcode when anonymizing addresses (default: True)
            
        Returns:
            Dict with anonymized text and other metadata
        """
        # Validate input parameters
        if text is None:
            return {"text": "", "items": []}
            
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
            
        # Handle invalid age_bracket_size (use default if not valid)
        if not isinstance(age_bracket_size, int) or age_bracket_size <= 0:
            # Use default and don't raise error
            age_bracket_size = 5
            
        # Convert keep_postcode to boolean
        keep_postcode = bool(keep_postcode)
        
        # Check if analyzer is available
        if not self.analyzer:
            return {"text": text, "items": []}
            
        # Get the entities from the analyzer
        results = self.analyzer.analyze(text, language)
        
        # Default operators if none provided
        if not operators:
            operators = {}
            
        # Keep track of replacements
        replacements = []
        anonymized_text = text
        
        # Collect all entities first
        anonymization_entities = []
        
        # First pass: collect postcode entities if keep_postcode is True
        postcode_entities = []
        address_entities = []
        if keep_postcode:
            for result in results:
                if result.entity_type == "AU_POSTCODE":
                    postcode_entities.append((result.start, result.end, text[result.start:result.end]))
                elif result.entity_type == "AU_ADDRESS":
                    address_entities.append((result.start, result.end))
        
        # Process all entities
        for result in results:
            entity_type = result.entity_type
            start = result.start
            end = result.end
            
            # Get the original text
            original = text[start:end]
            
            # Skip postcode if it's within address and keep_postcode is True
            if keep_postcode and entity_type == "AU_POSTCODE":
                # Check if this postcode is part of an address
                is_part_of_address = any(addr_start <= start and end <= addr_end for addr_start, addr_end in address_entities)
                if is_part_of_address:
                    continue
            
            # Determine operator
            operator = operators.get(entity_type, "replace")
            
            # Apply anonymization based on operator
            if operator == "replace":
                replacement = f"<{entity_type}>"
            elif operator == "mask":
                replacement = "*" * len(original)
            elif operator == "redact":
                replacement = "[REDACTED]"
            elif operator == "hash":
                replacement = f"HASH-{hash(original) % 1000000:06d}"
            elif operator == "age_bracket" and entity_type == "DATE_OF_BIRTH":
                # Try to extract date and convert to age bracket
                age = self._extract_age_from_date(original)
                if age is not None:
                    # Calculate the age bracket
                    bracket_start = (age // age_bracket_size) * age_bracket_size
                    bracket_end = bracket_start + age_bracket_size - 1
                    replacement = f"{bracket_start}-{bracket_end}"
                else:
                    # If we can't extract age, use a clear replacement indicating the issue
                    replacement = f"<{entity_type}>"
            else:
                replacement = f"<{entity_type}>"
            
            # Special handling for address to keep postcode if required
            if keep_postcode and entity_type == "AU_ADDRESS":
                # Find postcodes within this address
                postcodes_in_address = [
                    (pc_start, pc_end, pc_text) for pc_start, pc_end, pc_text in postcode_entities 
                    if start <= pc_start and pc_end <= end
                ]
                
                # If we found postcodes in the address
                if postcodes_in_address:
                    # Sort postcodes by position (in reverse order)
                    postcodes_in_address.sort(key=lambda x: x[0], reverse=True)
                    
                    # Create modified replacement with postcode preserved
                    modified_replacement = replacement
                    address_offset = 0
                    
                    for pc_start, pc_end, pc_text in postcodes_in_address:
                        # Calculate relative position within the address
                        rel_start = pc_start - start
                        rel_end = pc_end - start
                        
                        # Insert postcode into the replacement
                        modified_replacement = (
                            modified_replacement[:rel_start] + 
                            f" {pc_text} " + 
                            modified_replacement[rel_end:]
                        )
                    
                    replacement = modified_replacement
            
            # Add to entities list
            anonymization_entities.append({
                "entity_type": entity_type,
                "start": start,
                "end": end,
                "original": original,
                "replacement": replacement
            })
        
        # Remove overlapping entities, keeping the most specific ones
        anonymization_entities = self._remove_overlapping_entities(anonymization_entities)
        
        # Sort entities by start position in reverse order to process from end to start
        anonymization_entities.sort(key=lambda x: x["start"], reverse=True)
        
        # Apply replacements from end to start to maintain correct offsets
        for entity in anonymization_entities:
            start = entity["start"]
            end = entity["end"]
            replacement = entity["replacement"]
            
            # Replace in the text
            anonymized_text = anonymized_text[:start] + replacement + anonymized_text[end:]
            
            # Add to replacements list
            replacements.append(entity)
        
        return {
            "text": anonymized_text,
            "items": replacements
        }
    
    def _remove_overlapping_entities(self, entities):
        """
        Remove overlapping entities, keeping the most specific/important ones.
        
        Args:
            entities: List of entity dictionaries with start, end, entity_type
            
        Returns:
            List of non-overlapping entities
        """
        if not entities:
            return entities
        
        # Sort by start position, then by length (longer first)
        sorted_entities = sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))
        
        # Priority order for entity types (higher priority wins in overlaps)
        priority_order = {
            # Specific identifiers have highest priority
            "AU_MEDICARE": 100,
            "AU_TFN": 100,
            "AU_ABN": 100,
            "AU_ACN": 100,
            "INSURANCE_POLICY_NUMBER": 95,
            "INSURANCE_CLAIM_NUMBER": 95,
            "EMAIL_ADDRESS": 90,
            "AU_PHONE": 85,
            "CREDIT_CARD": 85,
            "AU_DRIVERS_LICENSE": 80,
            "AU_PASSPORT": 80,
            "AU_CENTRELINK_CRN": 80,
            "PERSON": 70,
            "AU_ADDRESS": 60,
            "ADDRESS": 60,
            "LOCATION": 50,
            "DATE": 40,
            "AU_POSTCODE": 30,
            "NUMBER": 20,
            # Generic types have lowest priority
            "VEHICLE_REGISTRATION": 15,
            "FACILITY": 10,
            "PRODUCT": 10,
            "INCIDENT_DATE": 10
        }
        
        result = []
        for entity in sorted_entities:
            # Check if this entity overlaps with any already selected entity
            overlaps = False
            for selected in result:
                if (entity["start"] < selected["end"] and 
                    entity["end"] > selected["start"]):
                    # There's an overlap
                    entity_priority = priority_order.get(entity["entity_type"], 0)
                    selected_priority = priority_order.get(selected["entity_type"], 0)
                    
                    # If current entity has higher priority and is not contained within selected
                    if (entity_priority > selected_priority and 
                        not (entity["start"] >= selected["start"] and entity["end"] <= selected["end"])):
                        # Remove the lower priority entity and add this one
                        result.remove(selected)
                        result.append(entity)
                    # If priorities are equal, prefer the longer match
                    elif (entity_priority == selected_priority and 
                          (entity["end"] - entity["start"]) > (selected["end"] - selected["start"])):
                        result.remove(selected)
                        result.append(entity)
                    
                    overlaps = True
                    break
            
            if not overlaps:
                result.append(entity)
        
        return result
    
    def _extract_age_from_date(self, date_string):
        """
        Extract age from a date string.
        
        Args:
            date_string: The date string to parse
            
        Returns:
            Age in years or None if parsing fails
        """
        # Try different date formats
        date_formats = [
            r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})',  # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
            r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})',  # YYYY/MM/DD, YYYY-MM-DD, YYYY.MM.DD
            r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2})'   # DD/MM/YY, DD-MM-YY, DD.MM.YY
        ]
        
        for fmt in date_formats:
            match = re.search(fmt, date_string)
            if match:
                try:
                    if len(match.group(3)) == 4:  # YYYY format
                        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    elif match.group(1) == 4:  # YYYY/MM/DD format
                        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    else:  # YY format
                        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        # Convert 2-digit year to 4-digit
                        if year < 100:
                            # Assume 20xx for years less than 30, 19xx otherwise
                            year = 2000 + year if year < 30 else 1900 + year
                    
                    # Create date object
                    birth_date = datetime.date(year, month, day)
                    
                    # Calculate age
                    today = datetime.date.today()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    
                    return age
                except (ValueError, IndexError):
                    # Invalid date, try next format
                    continue
        
        # Try to find age directly in text (e.g., "Age: 42")
        age_match = re.search(r'Age:\s*(\d+)', date_string)
        if age_match:
            try:
                return int(age_match.group(1))
            except (ValueError, IndexError):
                pass
                
        return None