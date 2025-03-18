from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Store last known GPS location
gps_location = {"lat": 0, "lon": 0}

@app.route("/")
def home():
    return render_template("index.html", lat=gps_location["lat"], lon=gps_location["lon"])

@app.route("/update_location", methods=["POST"])
def update_location():
    global gps_location
    data = request.json
    gps_location["lat"] = data.get("lat", gps_location["lat"])
    gps_location["lon"] = data.get("lon", gps_location["lon"])
    return jsonify({"message": "Location updated", "gps": gps_location})

@app.route("/get_location")
def get_location():
    return jsonify(gps_location)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
