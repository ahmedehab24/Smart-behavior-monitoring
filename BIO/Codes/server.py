from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

fleet_data = {}

@app.route('/trigger', methods=['POST'])
def trigger():
    data = request.get_json()

    plate = data.get("plate")
    if not plate:
        return jsonify({"status": "error", "message": "No plate provided"}), 400

#register the vehicle if wasnt registered
    if plate not in fleet_data:
        fleet_data[plate] = {
            "model": data.get("model", "Unknown"),
            "history": [],
            "latest": {
                "cv_label": "No detection",
                "cv_image": "",
                "vd_label": "normal",
                "bio": {
                    "heart_rate": 0,
                    "temperature": 0,
                    "oxygen": 0,
                    "respiration_rate": 0,
                    "alcohol": 0.0,
                    "blood_pressure": {"systolic": 0, "diastolic": 0}
                }
            }
        }

    # update the new values from upcoming data
    if "cv_label" in data:
        fleet_data[plate]["latest"]["cv_label"] = data["cv_label"]
    if "cv_image" in data:
        fleet_data[plate]["latest"]["cv_image"] = data["cv_image"]
    if "vd_label" in data:
        fleet_data[plate]["latest"]["vd_label"] = data["vd_label"]
    if "bio" in data:
        fleet_data[plate]["latest"]["bio"] = data["bio"]

    #history
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cv_label": fleet_data[plate]["latest"]["cv_label"],
        "cv_image": fleet_data[plate]["latest"]["cv_image"],
        "vd_label": fleet_data[plate]["latest"]["vd_label"],
        "bio": fleet_data[plate]["latest"]["bio"]
    }
    fleet_data[plate]["history"].append(entry)
 
    return jsonify({"status": "success", "message": "Partial update received"}), 200

@app.route('/data/<plate>', methods=['GET'])
def get_latest_data(plate):
    if plate in fleet_data:
        return jsonify(fleet_data[plate]["latest"])
    else:
        return jsonify({"message": "No data available"}), 404

@app.route('/history/<plate>', methods=['GET'])
def get_history(plate):
    if plate in fleet_data:
        return jsonify(fleet_data[plate]["history"])
    else:
        return jsonify({"message": "No history available"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
