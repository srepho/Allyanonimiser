"""
Long text processor for breaking down and analyzing text.
"""
import re

class LongTextProcessor:
    """
    Processes long texts by breaking them into segments and analyzing them.
    """
    def __init__(self, analyzer=None):
        self.analyzer = analyzer
    
    def process(self, text):
        """Process a long text by breaking it into segments."""
        segments = segment_long_text(text)
        return segments

def segment_long_text(text, max_segment_length=300, overlap=50):
    """
    Segment long text into smaller, manageable chunks.
    
    Args:
        text: The text to segment
        max_segment_length: Maximum length of each segment
        overlap: Number of characters to overlap between segments
        
    Returns:
        List of segments
    """
    if not text:
        return []
        
    # If text is shorter than max length, return as single segment
    if len(text) <= max_segment_length:
        return [{'text': text, 'start': 0, 'end': len(text)}]
    
    # Split text into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    segments = []
    current_segment = ""
    current_start = 0
    
    for para in paragraphs:
        # If adding this paragraph exceeds max length, add current segment to list
        if len(current_segment) + len(para) > max_segment_length and current_segment:
            segments.append({
                'text': current_segment.strip(),
                'start': current_start,
                'end': current_start + len(current_segment)
            })
            
            # Start new segment with overlap
            overlap_start = max(0, len(current_segment) - overlap)
            current_segment = current_segment[overlap_start:] + "\n\n" + para
            current_start = current_start + overlap_start
        else:
            # Add paragraph to current segment
            if current_segment:
                current_segment += "\n\n" + para
            else:
                current_segment = para
    
    # Add the last segment
    if current_segment:
        segments.append({
            'text': current_segment.strip(),
            'start': current_start,
            'end': current_start + len(current_segment)
        })
    
    return segments

def extract_pii_rich_segments(text, analyzer=None):
    """
    Extract segments from text that are likely to contain PII.
    
    Args:
        text: The text to analyze
        analyzer: Optional analyzer to use for PII detection
        
    Returns:
        List of segments with PII likelihood scores
    """
    # First segment the text
    segments = segment_long_text(text)
    
    # Add PII likelihood scores
    for segment in segments:
        segment_text = segment['text']
        
        # Simple heuristic for PII likelihood
        pii_likelihood = 0.0
        
        # Check for common PII patterns
        pii_patterns = {
            'PHONE': r'\b(?:\+?61|0)[2378]\s*\d{4}\s*\d{4}\b',
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'DATE': r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
            'ADDRESS': r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr)\b',
            'POSTCODE': r'\b\d{4}\b',
            'NAME': r'\b(?:Mr|Ms|Mrs|Dr|Professor|Prof)\.\s+[A-Z][a-z]+\b',
            'TFN': r'\b\d{3}\s*\d{3}\s*\d{3}\b',
            'MEDICARE': r'\b\d{4}\s*\d{5}\s*\d{1}\b'
        }
        
        pii_scores = {}
        
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, segment_text)
            if matches:
                score = min(1.0, len(matches) * 0.2)
                pii_scores[pii_type] = score
                pii_likelihood = max(pii_likelihood, score)
        
        # If no patterns matched but contains words like "customer" or "patient"
        if pii_likelihood == 0.0:
            pii_keywords = ['customer', 'patient', 'client', 'insured', 'member', 'policy', 'claim']
            for keyword in pii_keywords:
                if keyword in segment_text.lower():
                    pii_likelihood = 0.3
                    pii_scores['CONTEXT'] = 0.3
                    break
        
        segment['pii_likelihood'] = pii_likelihood
        segment['pii_scores'] = pii_scores
    
    # Sort segments by PII likelihood
    segments.sort(key=lambda x: x['pii_likelihood'], reverse=True)
    
    return segments

def analyze_claim_notes(text, analyzer=None):
    """
    Analyze insurance claim notes.
    
    Args:
        text: The claim note text
        analyzer: Optional analyzer to use
        
    Returns:
        Dict with structured information from the claim notes
    """
    # Extract segments with PII
    segments = extract_pii_rich_segments(text, analyzer)
    
    # Identify main sections
    section_patterns = {
        'claim': r'(?:Claim\s+Details|Incident\s+Details|Accident\s+Details)',
        'customer': r'(?:Customer\s+Details|Insured\s+Details|Policyholder\s+Details)',
        'vehicle': r'(?:Vehicle\s+Details|Car\s+Details|Vehicle\s+Information)',
        'assessment': r'(?:Assessment|Evaluation|Inspection)',
        'actions': r'(?:Actions|Next\s+Steps|Follow-up)'
    }
    
    section_segments = {}
    for segment in segments:
        segment_text = segment['text']
        
        for section_type, pattern in section_patterns.items():
            if re.search(pattern, segment_text, re.IGNORECASE):
                if section_type not in section_segments:
                    section_segments[section_type] = []
                section_segments[section_type].append(segment)
    
    # Extract key information
    result = {
        'pii_segments': segments,
        'section_segments': section_segments,
        'metadata': {}
    }
    
    # Extract claim number
    claim_match = re.search(r'Claim\s+(?:Number|#|Reference):\s+([A-Z0-9-]+)', text, re.IGNORECASE)
    if claim_match:
        result['metadata']['claim_number'] = claim_match.group(1)
    
    # Extract policy number
    policy_match = re.search(r'Policy\s+(?:Number|#):\s+([A-Z0-9-]+)', text, re.IGNORECASE)
    if policy_match:
        result['metadata']['policy_number'] = policy_match.group(1)
    
    # Extract customer name
    customer_match = re.search(r'(?:Customer|Insured|Policyholder):\s+([A-Za-z\s]+)', text, re.IGNORECASE)
    if customer_match:
        result['metadata']['customer_name'] = customer_match.group(1)
    
    # Extract incident date
    date_match = re.search(r'(?:occurred|happened|date)(?:\s+on)?\s+(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})', text, re.IGNORECASE)
    if date_match:
        result['metadata']['incident_date'] = date_match.group(1)
    
    # Extract incident description
    if 'claim' in section_segments and section_segments['claim']:
        incident_text = section_segments['claim'][0]['text']
        # Remove the header
        incident_text = re.sub(r'^.*?(?:Details|Information):\s*', '', incident_text, flags=re.IGNORECASE|re.DOTALL)
        result['incident_description'] = incident_text.strip()
    
    return result