# --- Dockerfile ---

# 1. La imagen base: Usamos una imagen oficial de Python 3.10
# (Debe coincidir con el Python que usaste en tu entorno 'sedapal_env')
FROM python:3.10-slim

# 2. Establecer el directorio de trabajo DENTRO de la "caja"
WORKDIR /app

# 3. Copiar la "lista de compras" y los "cerebros" primero
# Copiamos los archivos de requerimientos y los .pkl a la "caja"
COPY requirements.txt .
COPY *.pkl .

# 4. Instalar las librerías
# Le decimos a la "caja" que instale todo lo de la lista de compras
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto del código
# Ahora copiamos el 'main.py' (el puente)
COPY main.py .

# 6. Exponer el puerto
# Le decimos a AWS que nuestra API (Uvicorn) se ejecutará en el puerto 8000
EXPOSE 8000

# 7. El comando final para ejecutar la API
# Este es el comando que AWS App Runner ejecutará cuando inicie tu "caja"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]