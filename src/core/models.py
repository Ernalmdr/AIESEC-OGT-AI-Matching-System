from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class OGTProject:
    """
    EXPA (GIS) API'den gelen proje verilerini temsil eden model.
    """
    op_id: str
    title: str
    organisation: str
    country: str
    city: str
    status: str
    salary: str
    duration: str
    link: str
    # AI Analizi için en kritik alanlar:
    description: str = ""        # Genel iş tanımı
    role_info: str = ""          # Rol detayları
    backgrounds: List[str] = field(default_factory=list) # İstenen eğitim geçmişi
    skills: List[str] = field(default_factory=list)      # İstenen yetenekler
    selection_process: str = ""  # Seçim süreci detayları

@dataclass
class ExchangeParticipant:
    """
    Podio'dan gelen aday (EP) verilerini temsil eden model.
    """
    ep_id: str
    full_name: str
    email: str
    background: str              # Örn: Business Administration
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    cv_text: str = ""
    phone: str = ""