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

    entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Initialize if new plate
    if plate not in fleet_data:
        fleet_data[plate] = {
            "model": data.get("model", "Unknown"),
            "history": [],
            "latest": {
                "interior": {},
                "exterior": {},
                "bio": {},
                "vd_label": "normal",
                "speed": {"actual": 0.0, "target": 0.0},
            }
        }

    latest = fleet_data[plate]["latest"]
    source = data.get("source", "")

    # ---------- INTERIOR ----------
    if source == "interior":
        latest["interior"] = {
            "cv_label": data.get("cv_label", "No detection"),
            "cv_image": data.get("cv_image", "")
        }

    # ---------- EXTERIOR ----------
    elif source == "exterior":
        cv_label = data.get("cv_label", "")
        collision_warning = data.get("collision_warning", "")
        lane_alert = data.get("lane_alert", "")

        warnings = []
        if cv_label in ["COLLISION WARNING", "WRONG WAY DRIVING", "LANE DEPARTURE", "MULTIPLE HAZARDS"]:
            warnings.append(cv_label)
        if collision_warning == "true":
            warnings.append("COLLISION WARNING")
        if lane_alert:
            warnings.append("LANE DEPARTURE")

        latest["exterior"] = {
            "cv_label": cv_label,
            "exterior_image": data.get("exterior_image", ""),
            "collision_warning": collision_warning,
            "lane_alert": lane_alert,
            "warnings": list(set(warnings))  # Remove duplicates
        }

    # ---------- BIOSIGNALS ----------
    if "bio" in data:
        latest["bio"] = data["bio"]

    # ---------- VEHICLE DYNAMICS ----------
    if "vd_label" in data:
        latest["vd_label"] = data["vd_label"]

    # ---------- SPEED ----------
    if "actual_speed" in data or "target_speed" in data:
        latest["speed"] = {
            "actual": data.get("actual_speed", 0.0),
            "target": data.get("target_speed", 0.0)
        }

    # ---------- Save History ----------
    entry = {
        "timestamp": entry_time,
        "source": source,
        **data  # include all fields in the snapshot
    }
    fleet_data[plate]["history"].append(entry)

    return jsonify({"status": "success"}), 200

@app.route('/data/<plate>', methods=['GET'])
def get_latest_data(plate):
    if plate in fleet_data:
        return jsonify(fleet_data[plate]["latest"])
    return jsonify({"message": "No data available"}), 404

@app.route('/history/<plate>', methods=['GET'])
def get_history(plate):
    if plate in fleet_data:
        return jsonify(fleet_data[plate]["history"])
    return jsonify({"message": "No history available"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
