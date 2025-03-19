import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import upgrade
from sqlalchemy import func

# Initialize Flask app
app = Flask(__name__)

# Get the database URL from Render environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)



# Define the GPSData model
class GPSData:
    def __init__(self, timestamp, wind_speed, lat, lon, water_temp, tracker_id):
        self.timestamp = timestamp
        self.wind_speed = wind_speed
        self.lat = lat
        self.lon = lon
        self.water_temp = water_temp
        self.tracker_id = tracker_id

    # The to_dict() method should be indented properly within the class
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'wind_speed': self.wind_speed,
            'lat': self.lat,
            'lon': self.lon,
            'water_temp': self.water_temp,
            'tracker_id': self.tracker_id
        }



# Create the database tables
with app.app_context():
    db.create_all()

# Homepage - Basic Welcome Message
@app.route("/")
def home():
    
    # Get the latest record for each tracker_id
    subquery = db.session.query(
        GPSData.tracker_id,
        func.max(GPSData.timestamp).label('latest_timestamp')
    ).group_by(GPSData.tracker_id).subquery()

    # Join to get the latest data for each tracker
    latest_data = GPSData.query.join(
        subquery,
        (GPSData.tracker_id == subquery.c.tracker_id) &
        (GPSData.timestamp == subquery.c.latest_timestamp)
    ).all()

    # Clean the data to avoid None/Undefined issues
    clean_gps_data = [clean_data(data) for data in latest_data]

    #get all data for table
    all_data = GPSData.query.order_by(GPSData.timestamp.desc()).all()
    
    return render_template("index.html", gps_data=clean_gps_data, tracker_data=all_data)

# API Endpoint to Update GPS Location
@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.get_json()
    
    # Validate incoming data
    if not data or "lat" not in data or "lon" not in data:
        return jsonify({"error": "Invalid data. Please provide 'lat' and 'lon'"}), 400

    # Get additional fields with defaults
    wind_speed = data.get("wind_speed", 0.0)
    water_temp = data.get("water_temp", 0.0)

    # Create a new GPSData record with additional data
    new_location = GPSData(
    lat=data["lat"],
    lon=data["lon"],
    wind_speed=data.get("wind_speed", 0.0),
    water_temp=data.get("water_temp", 0.0),
    tracker_id=data["tracker_id"]
    )
    db.session.add(new_location)
    db.session.commit()

    return jsonify({"message": "Location and data saved successfully!"}), 200
    
@app.route("/delete_locations_by_timestamp", methods=["DELETE"])
def delete_locations_by_timestamp():
    timestamp = request.args.get('timestamp')  # Get the timestamp parameter

    # Delete records with that timestamp
    gps_data = db.session.query(GPSData).filter(GPSData.timestamp == timestamp).all()

    if gps_data:
        for data in gps_data:
            db.session.delete(data)
        db.session.commit()
        return jsonify({"message": "Locations deleted successfully"})
    else:
        return jsonify({"message": "No matching locations found"}), 404

def clean_data(data):
    return {
        "id": data.id,
        "tracker_id": data.tracker_id,
        "lat": data.lat,
        "lon": data.lon,
        "wind_speed": data.wind_speed if data.wind_speed is not None else 0.0,
        "water_temp": data.water_temp if data.water_temp is not None else 0.0,
        "timestamp": data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }

@app.route("/api/live_data")
def live_data():
    # Get the latest record for each tracker
    subquery = db.session.query(
        GPSData.tracker_id,
        func.max(GPSData.timestamp).label('latest_timestamp')
    ).group_by(GPSData.tracker_id).subquery()

    # Get the latest location data for each tracker
    latest_data = GPSData.query.join(
        subquery,
        (GPSData.tracker_id == subquery.c.tracker_id) &
        (GPSData.timestamp == subquery.c.latest_timestamp)
    ).all()

    # Format data for JSON
    data = [{
        "tracker_id": record.tracker_id,
        "lat": record.lat,
        "lon": record.lon,
        "wind_speed": record.wind_speed,
        "water_temp": record.water_temp,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for record in latest_data]

    return jsonify(data)


# Page to View GPS Location History
@app.route("/history/<int:tracker_id>")
def history(tracker_id):
    tracker_data = GPSData.query.filter_by(tracker_id=str(tracker_id)).order_by(GPSData.timestamp.desc()).all()
    tracker_data_dicts = [data.to_dict() for data in tracker_data]
    
    if not tracker_data:
        return "No data found for this tracker.", 404

    return render_template("history.html", tracker_data=tracker_data, bouy_data=json.dumps(tracker_data_dicts))


# Run Flask app with dynamic port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

def run_migrations():
    try:
        upgrade()
        print("✅ Migrations applied successfully!")
    except Exception as e:
        print(f"⚠️ Error applying migrations: {e}")


