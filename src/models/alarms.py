'''
Created on 22 oct 2025

@author: jlcartas
'''
from pydantic import BaseModel, model_validator, Field, AliasChoices, IPvAnyAddress, field_validator
from pydantic import ConfigDict
from datetime import datetime
from typing import List

   
class AlarmsDetail(BaseModel):
    camera_name: str
    camera_channel: int
    count_lost: int
    date_lost: datetime
    is_lost: bool = False
    
    @field_validator("date_lost", mode="before")
    @classmethod
    def parse_date_lost(cls, v):        
        if isinstance(v, datetime):
        # Ya es datetime, no hace nada
            return v
    
        if isinstance(v, str):
            v = v.replace(",", " ")
            try:
                return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            
            try:
                return datetime.strptime(v, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                raise ValueError(f"Formato de fecha inválido: {v}")
        
        raise TypeError(f"Tipo inválido para fecha: {type(v)}")

    
    @model_validator(mode="after")
    def uppercase_strings(self):
        #Convierte todos los campos str en mayúsculas.
        for field, value in self.__dict__.items():
            if isinstance(value, str):
                setattr(self, field, value.upper())
        return self

class Alarms(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,  # también permite 'id' como nombre de campo
        extra="ignore",         # ignora claves desconocidas
        ser_json_typed= True
    )
    
    #acepta '_id' o 'id' al validar; exporta siempre como '_id'
    id:str | None = Field(
        default=None,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="_id"
        )
    
    device_name: str
    device_ip: IPvAnyAddress
    dvr: str
    date: datetime
    count_alarms: int
    is_incident: bool = False
    #lista de detalles de alarmas
    details: List[AlarmsDetail] = []
    
    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, datetime):
        # Ya es datetime, no hace nada
            return v
    
        if isinstance(v, str):
            v = v.replace(",", " ")
            try:
                return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            
            try:
                return datetime.strptime(v, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                raise ValueError(f"Formato de fecha inválido: {v}")
        
        raise TypeError(f"Tipo inválido para fecha: {type(v)}")
            
    #vallidador para pasar a mayúsculas
    @model_validator(mode="after")
    def normalize(self):
        # Convertir IP a str si es IPvAnyAddress
        if not isinstance(self.device_ip, str):
            self.device_ip = str(self.device_ip)
        
        
        # Convierte todos los campos str del modelo a mayúsculas.
        for field, value in self.__dict__.items():
            if isinstance(value, str):
                setattr(self, field, value.upper())

        
        if self.details:
            self.details = [
                d if isinstance(d, AlarmsDetail) else AlarmsDetail(**d)
                for d in self.details
                ]
                
        # Genera el id si no está presente
        if not self.id and self.device_ip and self.dvr:
            self.id = f"{self.device_ip}:{self.dvr}"
            
        return self

'''Si quieres imprimir el modelo
   usa print(a.model_dump())
'''