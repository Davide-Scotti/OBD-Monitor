import obd
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import time

# Creazione dell'app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Connessione al dispositivo OBD2
try:
    connection = obd.OBD()  # Usa la connessione predefinita al dispositivo OBD2
except Exception as e:
    print("Errore nella connessione OBD2:", e)
    connection = None  # Se la connessione fallisce, si imposta come None

def get_data():
    response = {}

    if connection and connection.is_connected():
        # Giri del motore
        rpm = connection.query(obd.commands.RPM)
        response["rpm"] = rpm.value.magnitude if rpm.is_valid() else "N/A"

        # Velocità
        speed = connection.query(obd.commands.SPEED)
        response["speed"] = speed.value.magnitude if speed.is_valid() else "N/A"

        # Temperatura motore
        temp = connection.query(obd.commands.COOLANT_TEMP)
        response["coolant_temp"] = temp.value.magnitude if temp.is_valid() else "N/A"

        # Carico motore
        engine_load = connection.query(obd.commands.ENGINE_LOAD)
        response["engine_load"] = engine_load.value.magnitude if engine_load.is_valid() else "N/A"

        # Forza G (calcolato)
        response["g_force"] = calculate_g_force(response["speed"], response["rpm"])

    return response

def calculate_g_force(speed, rpm):
    # Calcolo semplificato della forza G (questo è un esempio base, dovresti implementare una formula più accurata)
    if speed != "N/A" and rpm != "N/A":
        g_force = (speed / 100) * (rpm / 1000)  # Semplificato
        return round(g_force, 2)
    return "N/A"

@app.route("/data", methods=["GET"])
def send_data():
    data = get_data()
    return jsonify(data)

@app.route("/start_monitoring", methods=["GET"])
def start_monitoring():
    while True:
        data = get_data()
        socketio.emit('update_data', data)  # Invia i dati in tempo reale tramite WebSocket
        time.sleep(1)  # Attende 1 secondo prima di inviare i dati successivi
    return jsonify({"status": "monitoring started"})

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Invio dei dati iniziali al client quando si connette
    data = get_data()
    emit('update_data', data)

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000)
