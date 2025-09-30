"""
Service to generate mock data for development and testing
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import numpy as np


class DataMockService:
    """Service to generate realistic mock data"""
    
    def __init__(self):
        self.cultivos = ["trigo", "soja", "maiz", "cebada", "girasol"]
        self.tipos_suelo = ["arenoso", "franco", "arcilloso"]
        self.variedades = {
            "trigo": ["Klein Dragón", "Baguette Premium", "SY 100"],
            "soja": ["DM 4670", "NA 5009", "Nidera A 4910"],
            "maiz": ["DK 7210", "ACA 417", "P1630"]
        }
    
    def get_mock_lotes_data(self, n_lotes: int = 10) -> List[Dict[str, Any]]:
        """Generate mock lotes data"""
        lotes = []
        for i in range(n_lotes):
            lotes.append({
                "id": f"lote-{str(i+1).zfill(3)}",
                "cliente_id": f"cliente-{str((i % 3) + 1).zfill(3)}",
                "nombre": f"Lote {i+1}",
                "latitud": round(-34.5 + random.uniform(-3, 3), 6),
                "longitud": round(-58.5 + random.uniform(-3, 3), 6),
                "superficie_ha": round(random.uniform(50, 300), 2),
                "tipo_suelo": random.choice(self.tipos_suelo),
                "caracteristicas": {
                    "drenaje": random.choice(["bueno", "moderado", "pobre"]),
                    "pendiente": random.choice(["plano", "suave", "moderado"])
                }
            })
        return lotes
    
    def get_mock_lote_by_id(self, lote_id: str) -> Dict[str, Any]:
        """Get a specific lote by ID"""
        # Generate deterministic data based on ID
        seed = sum(ord(c) for c in lote_id)
        random.seed(seed)
        
        lote = {
            "id": lote_id,
            "cliente_id": f"cliente-{str((seed % 3) + 1).zfill(3)}",
            "nombre": f"Lote {lote_id.split('-')[-1]}",
            "latitud": round(-34.5 + random.uniform(-3, 3), 6),
            "longitud": round(-58.5 + random.uniform(-3, 3), 6),
            "superficie_ha": round(random.uniform(50, 300), 2),
            "tipo_suelo": random.choice(self.tipos_suelo),
            "caracteristicas": {
                "drenaje": random.choice(["bueno", "moderado", "pobre"]),
                "pendiente": random.choice(["plano", "suave", "moderado"])
            }
        }
        
        random.seed()  # Reset seed
        return lote
    
    def get_mock_lotes_by_cliente(self, cliente_id: str) -> List[Dict[str, Any]]:
        """Get all lotes for a cliente"""
        all_lotes = self.get_mock_lotes_data(10)
        return [l for l in all_lotes if l["cliente_id"] == cliente_id]
    
    def get_mock_ordenes_trabajo(self, lote_id: str = None) -> List[Dict[str, Any]]:
        """Generate mock work orders"""
        ordenes = []
        n_ordenes = random.randint(5, 15)
        
        for i in range(n_ordenes):
            fecha = datetime.now() - timedelta(days=random.randint(1, 365))
            ordenes.append({
                "id": f"orden-{str(i+1).zfill(4)}",
                "lote_id": lote_id or f"lote-{str(random.randint(1, 10)).zfill(3)}",
                "tipo_labor": random.choice([
                    "siembra", "fertilizacion", "pulverizacion", 
                    "cosecha", "labranza"
                ]),
                "fecha": fecha.isoformat(),
                "cultivo": random.choice(self.cultivos),
                "insumos": {
                    "tipo": random.choice(["semilla", "fertilizante", "herbicida"]),
                    "cantidad": round(random.uniform(50, 200), 2)
                },
                "estado": "completado"
            })
        
        return sorted(ordenes, key=lambda x: x["fecha"], reverse=True)
    
    def get_mock_cosechas_historicas(self, lote_id: str = None) -> List[Dict[str, Any]]:
        """Generate mock historical harvest data"""
        cosechas = []
        
        for year in range(3):  # Últimos 3 años
            fecha = datetime.now() - timedelta(days=365 * (year + 1))
            cultivo = random.choice(self.cultivos)
            
            # Rendimiento base por cultivo
            rendimiento_base = {
                "trigo": 3500,
                "soja": 3000,
                "maiz": 8000,
                "cebada": 3200,
                "girasol": 2500
            }
            
            base = rendimiento_base.get(cultivo, 3000)
            rendimiento = base + random.uniform(-500, 1000)
            
            cosechas.append({
                "id": f"cosecha-{year+1}",
                "lote_id": lote_id or f"lote-{str(random.randint(1, 10)).zfill(3)}",
                "cultivo": cultivo,
                "fecha": fecha.isoformat(),
                "rendimiento": round(rendimiento, 2),
                "calidad": random.choice(["excelente", "buena", "regular"]),
                "humedad_pct": round(random.uniform(12, 16), 1),
                "cantidad_cosechada": round(rendimiento * random.uniform(80, 120), 2)
            })
        
        return sorted(cosechas, key=lambda x: x["fecha"], reverse=True)
    
    def get_mock_clima_data(
        self, 
        latitud: float, 
        longitud: float, 
        dias: int = 365
    ) -> List[Dict[str, Any]]:
        """Generate mock climate data"""
        clima_data = []
        
        # Base temperature según latitud
        temp_base = 20 - abs(latitud + 34) * 0.5
        
        for i in range(dias):
            fecha = datetime.now() - timedelta(days=dias - i)
            mes = fecha.month
            
            # Variación estacional
            factor_estacional = np.sin((mes - 1) / 12 * 2 * np.pi)
            temp_media = temp_base + factor_estacional * 8 + random.uniform(-3, 3)
            
            # Precipitación con tendencia estacional
            precip_base = 80 if mes in [10, 11, 12, 1, 2, 3] else 40
            precipitacion = max(0, random.gauss(precip_base / 30, 20))
            
            clima_data.append({
                "fecha": fecha.date().isoformat(),
                "temperatura_min": round(temp_media - 5, 1),
                "temperatura_max": round(temp_media + 5, 1),
                "temperatura_media": round(temp_media, 1),
                "precipitacion": round(precipitacion, 1),
                "humedad_relativa": round(random.uniform(50, 90), 1),
                "radiacion_solar": round(random.uniform(15, 25), 1),
                "velocidad_viento": round(random.uniform(5, 20), 1)
            })
        
        return clima_data
    
    def get_mock_suelo_data(self, lote_id: str) -> Dict[str, Any]:
        """Generate mock soil characteristics"""
        # Generate deterministic data based on ID
        seed = sum(ord(c) for c in lote_id)
        random.seed(seed)
        
        suelo = {
            "lote_id": lote_id,
            "profundidad_cm": 30,
            "ph": round(random.uniform(5.8, 7.2), 1),
            "materia_organica": round(random.uniform(2.0, 4.5), 1),
            "nitrogeno": round(random.uniform(15, 35), 1),
            "fosforo": round(random.uniform(10, 25), 1),
            "potasio": round(random.uniform(150, 280), 1),
            "textura": random.choice(self.tipos_suelo),
            "capacidad_campo": round(random.uniform(20, 35), 1),
            "conductividad_electrica": round(random.uniform(0.3, 1.2), 2),
            "fecha_analisis": (datetime.now() - timedelta(days=random.randint(30, 180))).isoformat()
        }
        
        random.seed()  # Reset seed
        return suelo