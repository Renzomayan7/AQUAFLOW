# --- main.py COMPLETO Y CORREGIDO ---
import joblib
import pandas as pd
import random
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

# --- 1. MODELOS DE DATOS ---
class DatosEntrada(BaseModel):
    sensor_id: str = "S-DEFAULT"
    Fuga_en: str
    Distrito: str
    Sector: int
    Gerencia: str
    Material: str
    Diametro_mm: float
    Presion_PSI: float
    Mes: int
    Dia_semana: int
    Hora_dia: int

class DatoSensor(BaseModel):
    presion: float
    flujo: float

# --- 2. INICIAR APP Y CARGAR MODELOS ---
app = FastAPI(title="API SEDAPAL V8", version="8.0")

try:
    print("Cargando modelos...")
    model = joblib.load('modelo_sedapal_xgb.pkl')
    label_encoder = joblib.load('etiquetas_encoder.pkl')
    model_columns = joblib.load('lista_de_columnas.pkl')
    print("Carga OK.")
except Exception as e:
    print(f"Error carga: {e}")
    model = None

# --- 3. MEMORIA TEMPORAL (LAS LISTAS) ---
# Historial para el gráfico (Monitoreo)
base_datos_grafico = [
    {"hora": "08:00", "presion": 50.0, "flujo": 100.5},
    {"hora": "08:15", "presion": 48.5, "flujo": 98.2},
]

# Historial de Predicciones (¡NUEVO!)
historial_predicciones = [] 

# --- 4. ENDPOINTS ---

# A. MONITOREO (GRÁFICOS)
@app.post("/sensor/enviar")
def recibir_dato_sensor(dato: DatoSensor):
    nueva = {
        "hora": datetime.now().strftime("%H:%M:%S"),
        "presion": dato.presion,
        "flujo": dato.flujo
    }
    base_datos_grafico.append(nueva)
    if len(base_datos_grafico) > 20: base_datos_grafico.pop(0)
    return {"mensaje": "Guardado", "dato": nueva}

@app.get("/monitoreo/historial")
def obtener_historial_grafico():
    return base_datos_grafico

# B. PREDICCION (CEREBRO)
@app.post("/predecir")
def predecir_fuga(datos: DatosEntrada):
    if not model: return {"error": "Modelo no cargado"}
    
    # Preparar datos
    d = datos.dict()
    sensor_id_input = d.pop('sensor_id')
    d['Diametro (mm)'] = d.pop('Diametro_mm')
    d['Presion (PSI)'] = d.pop('Presion_PSI')
    
    input_df = pd.DataFrame([d])
    input_transformed = pd.get_dummies(input_df)
    input_final = input_transformed.reindex(columns=model_columns, fill_value=0)
    
    # Predecir
    pred_num = model.predict(input_final)[0]
    pred_txt = label_encoder.inverse_transform([pred_num])[0]
    
    # Probabilidad
    probs = model.predict_proba(input_final)[0]
    prob_max = float(max(probs))
    
    # Simular Caudal
    caudal_est = 500.0
    if pred_txt == "Alta": caudal_est = 62000.0
    elif pred_txt == "Media": caudal_est = 4000.0

    # Construir respuesta
    respuesta = {
        "sensor_id": sensor_id_input,
        "probabilidad_fuga": round(prob_max, 2),
        "fuga": True if pred_txt != "Baja" else False,
        "presion_psi": datos.Presion_PSI,
        "caudal_lpd": caudal_est,
        "timestamp": datetime.now().isoformat()
    }
    
    # ¡GUARDAR EN EL HISTORIAL! (NUEVO)
    historial_predicciones.insert(0, respuesta) # Insertar al principio (más reciente primero)
    
    # Mantener solo las últimas 50 predicciones
    if len(historial_predicciones) > 50:
        historial_predicciones.pop()

    return respuesta

# C. OBTENER HISTORIAL DE PREDICCIONES (¡EL GET QUE PEDISTE!)
@app.get("/predicciones")
def ver_predicciones_guardadas():
    """Devuelve la lista de todas las alertas generadas"""
    return historial_predicciones

@app.get("/")
def root():
    return {"mensaje": "API V8 ACTIVA: ¡Con Historial de Alertas!"}