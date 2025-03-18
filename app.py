import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import upgrade

# Initialize Flask app
app = Flask(__name__)

# Get the database URL from Render environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)


def run_migrations():
    try:
        upgrade()
        print("✅ Migrations applied successfully!")
    except Exception as e:
        print(f"⚠️ Error applying migrations: {e}")

# Define the GPSData model
class GPSData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Float, nullable=True)
    water_temp = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# Create the database tables
with app.app_context():
    db.create_all()

# Homepage - Basic Welcome Message
@app.route("/")
def home():
    return render_template("index.html")

# API Endpoint to Update GPS Location
@app.route("/update_location", methods=["POST"])
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
        wind_speed=wind_speed,
        water_temp=water_temp,
    )
    db.session.add(new_location)
    db.session.commit()

    return jsonify({"message": "Location and data saved successfully!"}), 200

# Page to View GPS Location History
@app.route("/history")
def history():
    # Get all past GPS locations (most recent first)
    locations = GPSData.query.order_by(GPSData.timestamp.desc()).all()
    return render_template("history.html", locations=locations)

# Run Flask app with dynamic port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
