'''
Created on 27 oct 2025

@author: javier
'''
from models.alarms import Alarms
import re

def set_doc_to_alarm(datos_extraidos):
    # Regex para cada cámara (termina en (D<number>))
    pattern = r".+?\(D\d+\)"
    matches = re.findall(pattern, datos_extraidos['fuente_alarma'], re.IGNORECASE)
    
    
    
    if not matches or len(matches) == 1:     
        alarm = Alarms(
            device_name = datos_extraidos['nombre_dispositivo'],
            device_ip = datos_extraidos['ip_dispositivo'],
            dvr = datos_extraidos['no_dispositivo'],
            date = datos_extraidos['tiempo_alarma'],
            count_alarms = 1,
            is_incident = False,
            details = [
                {
                    "camera_name": datos_extraidos['fuente_alarma'],
                    "camera_channel": datos_extraidos['canal'],
                    "count_lost": 1,
                    "date_lost": datos_extraidos['tiempo_alarma'],
                    "is_lost": False                
                    }
                ]
            )
        return alarm
    else:
        details = [
            {   "camera_name": cam.strip(),
                "camera_channel": datos_extraidos['canal'],
                "count_lost": 1,
                "date_lost": datos_extraidos['tiempo_alarma'],
                "is_lost": False
             }for cam in matches
            ]
        alarm = Alarms(
            device_name = datos_extraidos['nombre_dispositivo'],
            device_ip = datos_extraidos['ip_dispositivo'],
            dvr = datos_extraidos['no_dispositivo'],
            date = datos_extraidos['tiempo_alarma'],
            count_alarms = 1,
            is_incident = False,
            details = details
            )
        return alarm
        
        