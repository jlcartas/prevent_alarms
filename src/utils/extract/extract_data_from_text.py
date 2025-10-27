'''
Created on 4 ago 2025

@author: jlcartas
'''
import re

from utils.extract.parse_alarm import parse_alarm
from utils.logger import LoggerSingleton
from database import get_alarm_patterns


logger = LoggerSingleton.get_logger("services.utils.extract_data_from_text")

def clean_text(text: str) -> str:
    """Elimina saltos de línea múltiples y espacios innecesarios"""
    return text.split()

def extract_data(text: str):
    """
    Searches the text for target phrases and returns the number of the first match found.
    Returns 0 if no matches are found.
    Args:
        text (str): Text to search through
        
    """
    
    patterns = get_alarm_patterns.get_patterns({"_id": {"$ne": "data_xml"}})
    text = re.sub(r'\s+', ' ', text.strip())  # Normalizar 
    
    extracted_data = parse_alarm(text.upper(), patterns)
    
    if extracted_data["nombre_dispositivo"] == "Not available":
        logger.warning("No se encontró el nombre del dispositivo en el texto.")
        raise ValueError("No se encontró el nombre del dispositivo en el texto.")
    return extracted_data
  
    