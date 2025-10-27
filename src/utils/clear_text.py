'''
Created on 14 oct 2025

@author: jlcartas
'''
from bs4 import BeautifulSoup

def get_clean_body(msg):
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            return part.get_payload(decode=True).decode("utf-8", errors="ignore")
        elif part.get_content_type() == "text/html":
            html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text(separator="\n").strip()
    return ""