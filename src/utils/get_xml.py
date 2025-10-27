'''
Created on 17 jul 2025

@author: jlcartas
'''
import re

def extraer_xml(full_text: str) -> str | None:
    """
    Extracts XML-like text from a larger string.
    
    Args:
        full_text: String that may contain XML data
        
    Returns:
        - XML string if found between <?xml and </Alarm>
        - None if no XML candidate found
    """
    # Regex pattern to find content between <?xml and </Alarm> (case insensitive)
    xml_pattern = re.compile(r'(<\?xml[\s\S]*?</Alarm>)', re.IGNORECASE)
    match = xml_pattern.search(full_text)
    
    return match.group(0) if match else None