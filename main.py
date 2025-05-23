from flask import Flask, request, jsonify
import hashlib
from app.rcv_scraper import obtener_rcv
import os

app = Flask(__name__)
SECRET_KEY = "tu_clave_secreta_segura"

def verify_hash(rut, clave, provided_hash):
    data_string = f"{rut}:{clave}:{SECRET_KEY}"
    expected_hash = hashlib.sha256(data_string.encode()).hexdigest()
    return expected_hash == provided_hash

@app.route("/api/rcv", methods=["POST"])
def api_obtener_rcv():
    body = request.json
    rut = body.get("rut")
    clave = body.get("clave")
    mes = body.get("mes")
    anho = body.get("anho")
    tipo = body.get("tipo", "compra")
    provided_hash = body.get("hash")

    if not verify_hash(rut, clave, provided_hash):
        return jsonify({"error": "Invalid authentication hash"}), 401

    try:
        data = obtener_rcv(rut, clave, mes, anho, tipo)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)