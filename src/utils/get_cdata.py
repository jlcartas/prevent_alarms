import xml.etree.ElementTree as ET
from typing import Dict, List, Union
import re

def extract_field_value(content: str, field_names: List[str], all_field_variants: List[List[str]]) -> str:
    """Helper to extract a field value from CDATA content."""
    for field_name in field_names:
        if field_name not in content:
            continue
            
        start_idx = content.find(field_name) + len(field_name)
        
        # Handle separators
        if content[start_idx:start_idx+3] == ' : ':
            start_idx += 3
        elif content[start_idx] == ':':
            start_idx += 1
        
        # Find value end
        end_idx = find_value_end(content, start_idx, all_field_variants)
        # Remove newlines and extra spaces
        value = content[start_idx:end_idx].strip()
        value = ' '.join(value.split())
        return value
    
    return "0"

def find_value_end(content: str, start_idx: int, all_field_variants: List[List[str]]) -> int:
    """Find the end position of the current field's value."""
    end_idx = len(content)
    for field_variants in all_field_variants:
        for field in field_variants:
            pos = content.find(field, start_idx)
            if -1 < pos < end_idx:
                end_idx = pos
    return end_idx

def extract_cdata(xml_input: Union[str, bytes], config: Dict) -> Dict[str, str]:
    """
    Extracts data from CDATA using a configuration dictionary.
    Now accepts the new format with "_id" and "datos" as a dictionary.
    """
    try:
        # Get the fields dictionary from the config
        fields_dict = config.get("datos", {})
        
        # Decode XML with error tolerance
        xml_str = decode_xml(xml_input)
        
        # Try parsing with recovery
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            # Try with XML with CDATA stripped if parsing fails
            xml_str = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', xml_str)
            root = ET.fromstring(xml_str)
        
        # Get CDATA content
        cdata_content = get_cdata_content(root)
        
        # Extract all fields
        result = extract_all_fields(cdata_content, fields_dict)
        
        # Return with the same structure but with extracted values
        return result
    
    except Exception as e:
        print(f"Error processing XML: {str(e)}")
        return {
            #"_id": config.get("_id", "datos_xml"),
            "datos": {k: "Error in XML" for k in config.get("datos", {}).keys()}
        }

def clean_xml(xml_str: str) -> str:
    """Clean malformed XML."""
    xml_str = re.sub(r'<\?xml.*?\?>', '<?xml version="1.0" encoding="utf-8"?>', xml_str)
    xml_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_str)
    
    # Comprimir CDATA a una sola línea
    xml_str = re.sub(
        r'<!\[CDATA\[(.*?)\]\]>',
        lambda m: f"<![CDATA[{ ' '.join(m.group(1).split()) }]]>",
        xml_str
    )
    
    return xml_str

def decode_xml(xml_input: Union[str, bytes]) -> str:
    """Handle XML decoding with fallbacks."""
    if isinstance(xml_input, str):
        xml_str = xml_input
    else:
        try:
            xml_str = xml_input.decode('utf-8')
        except UnicodeDecodeError:
            xml_str = xml_input.decode('latin-1')
    # Eliminar saltos de línea y espacios múltiples
    xml_str = ' '.join(xml_str.split())
    
    # Pero preservamos los saltos de línea entre etiquetas para legibilidad básica
    xml_str = xml_str.replace('> <', '>\n<')
    
    return clean_xml(xml_str)

def get_cdata_content(root: ET.Element) -> str:
    """Extract CDATA content from XML element."""
    extra_text = root.find('ExtraText')
    return extra_text.text if extra_text is not None else ""

def extract_all_fields(content: str, fields_dict: Dict[str, List[str]]) -> Dict[str, str]:
    """Extract all fields from CDATA content."""
    all_field_variants = list(fields_dict.values())
    return {
        output_name: extract_field_value(content, field_names, all_field_variants)
        for output_name, field_names in fields_dict.items()
    }