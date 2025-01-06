from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
from datetime import datetime
import re
from dateutil import parser

# Configuración de Twilio
account_sid = 'ACdc5ee1f123c4adfe557157b8d25e275a'  # Obtén esto de la consola de Twilio
auth_token = 'bcd894e9a2a463912e108cd91de640e9'    # Obtén esto de la consola de Twilio
client = Client(account_sid, auth_token)

# Crear la aplicación Flask
app = Flask(__name__)

# Horarios de actividades en el Coliseo (en formato 24h)
horarios_ocupados = {
    "Baloncesto INICIAL FEMENINO": [("Lunes", "17:00", "17:30"), ("Miércoles", "16:00", "17:15"), ("Viernes", "16:00", "16:45")],
    "Baloncesto INICIAL MASCULINO": [("Lunes", "17:30", "18:00"), ("Miércoles", "17:15", "18:30"), ("Viernes", "16:45", "17:30")],
    "Baloncesto AVANZADO FEMENINO": [("Lunes", "18:00", "19:30"), ("Martes", "18:30", "19:30"), ("Jueves", "18:30", "19:30")],
    "Baloncesto AVANZADO MASCULINO": [("Lunes", "19:30", "21:00"), ("Martes", "19:30", "21:00"), ("Jueves", "19:30", "21:00")],
    "Kendo": [("Lunes", "07:00", "09:00"), ("Miércoles", "07:00", "09:00"), ("Viernes", "07:00", "09:00")],
    "Pilates": [("Lunes", "13:00", "14:00"), ("Martes", "15:30", "16:30"), ("Miércoles", "11:00", "12:00")],
    "Taekwondo INICIAL": [("Martes", "12:00", "12:50"), ("Jueves", "13:00", "13:50")],
    "Danza aérea": [("Lunes", "11:00", "13:00"), ("Miércoles", "11:00", "13:00")],
    "Voleibol INICIAL FEMENINO": [("Martes", "16:30", "17:30"), ("Sábado", "08:00", "09:00")],
    "Voleibol INICIAL MASCULINO": [("Martes", "17:30", "18:30"), ("Sábado", "09:00", "10:00")],
    "Voleibol AVANZADO FEMENINO": [("Miércoles", "18:30", "19:30"), ("Viernes", "17:30", "19:30"), ("Sábado", "12:00", "13:00")],
    "Voleibol AVANZADO MASCULINO": [("Miércoles", "19:30", "21:00"), ("Viernes", "19:30", "21:00"), ("Sábado", "13:00", "14:00")],
}

# Función para verificar si el Coliseo está disponible
def verificar_disponibilidad(hora_consulta=None):
    # Si no se proporciona hora, verificamos si hay actividades actualmente
    if hora_consulta is None:
        now = datetime.now()
        current_time = now.strftime("%H:%M")  # Obtener hora actual en formato 24h
        hora_consulta = current_time  # Usamos la hora actual para la consulta

    # Convierte el horario de consulta a formato datetime
    hora_consulta = datetime.strptime(hora_consulta, "%H:%M")
    
    # Revisar los horarios ocupados
    for actividad, horarios in horarios_ocupados.items():
        for dia, hora_inicio, hora_fin in horarios:
            # Convertir horas de inicio y fin a formato datetime
            hora_inicio = datetime.strptime(hora_inicio, "%H:%M")
            hora_fin = datetime.strptime(hora_fin, "%H:%M")
            
            # Verificar si la hora de consulta se encuentra dentro del rango de horas ocupadas
            if hora_inicio <= hora_consulta < hora_fin:
                return f"El Coliseo está ocupado por '{actividad}' el {dia} de {hora_inicio.strftime('%H:%M')} a {hora_fin.strftime('%H:%M')}. No está disponible."
    
    return "El Coliseo está disponible en este horario."

# Ruta para manejar los mensajes entrantes de WhatsApp
@app.route("/webhook", methods=['POST'])
def webhook():
    # Obtener el mensaje recibido
    incoming_msg = request.form.get('Body', '').lower()
    from_number = request.form.get('From')

    # Eliminar signos de pregunta
    incoming_msg = incoming_msg.replace("?", "")

    # Crear la respuesta
    response = MessagingResponse()

    # Normalización de variaciones de las frases
    if re.search(r"(cancha|disponibilidad|disponible).*", incoming_msg):
        # Convertir formatos como "3 de la tarde" a "15:00 PM"
        incoming_msg = incoming_msg.replace(" de la tarde", " PM")
        incoming_msg = incoming_msg.replace(" del día", " AM")
        
        # Manejar frases como "a las 3 de la tarde" y convertirlas a un formato estándar
        if re.search(r"a las \d{1,2} de la tarde", incoming_msg):
            incoming_msg = incoming_msg.replace(" de la tarde", " PM")
        elif re.search(r"a las \d{1,2} del día", incoming_msg):
            incoming_msg = incoming_msg.replace(" del día", " AM")

        # Si hay una hora en el mensaje
        if re.search(r"\d{1,2}(:\d{2})?(\s*(am|pm))?", incoming_msg):  
            try:
                # Parsear la hora con dateutil.parser para aceptar múltiples formatos
                hora_usuario = parser.parse(incoming_msg.split()[-1]).strftime("%H:%M")
                disponibilidad = verificar_disponibilidad(hora_usuario)
                response.message(disponibilidad)
            except ValueError:
                response.message("No pude entender la hora que ingresaste. Por favor, usa un formato válido.")
        else:  # Si solo pregunta por la disponibilidad
            disponibilidad = verificar_disponibilidad()
            response.message(disponibilidad)
    else:
        response.message("Lo siento, solo puedo decirte si la cancha está disponible. Pregunta por la disponibilidad.")

    return str(response)

if __name__ == "__main__":
    app.run(debug=True)
