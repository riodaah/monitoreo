# Usa una imagen base oficial de Python
FROM python:3.8-slim

EXPOSE 8080

# Establecer directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY requirements.txt requirements.txt
COPY bookings.py bookings.py
COPY .env .env  

# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar la aplicación
CMD ["python", "bookings.py"]
