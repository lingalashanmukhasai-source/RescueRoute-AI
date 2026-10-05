from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import sqlite3
import os
import math
import requests
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "rescue-route-ai-hackathon-secret"
)

DB = "rescuoroute.db"

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
OSRM = "https://router.project-osrm.org/route/v1/driving"
OVERPASS = "https://overpass-api.de/api/interpreter"
USGS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
GDACS = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/latest"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            disaster TEXT,
            risk INTEGER,
            level TEXT,
            start_lat REAL,
            start_lng REAL,
            destination TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- HELPERS ----------------

def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(round(value))))


def haversine(lat1, lon1, lat2, lon2):
    radius = 6371

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


# ---------------- WEATHER ----------------

def get_weather(lat, lon):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m,"
                "wind_gusts_10m,"
                "visibility"
            ),
            "forecast_days": 1
        }

        response = requests.get(
            OPEN_METEO,
            params=params,
            timeout=8
        )

        response.raise_for_status()

        current = response.json().get("current", {})

        return {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "rain": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "wind": current.get("wind_speed_10m"),
            "gust": current.get("wind_gusts_10m"),
            "visibility": current.get("visibility"),
            "source": "Open-Meteo"
        }

    except Exception as error:
        return {
            "error": str(error)
        }


# ---------------- EARTHQUAKES ----------------

def get_earthquakes(lat, lon, radius_km=500):

    try:
        data = requests.get(
            USGS,
            timeout=8
        ).json()

        events = []

        for feature in data.get("features", []):

            coordinates = feature.get(
                "geometry",
                {}
            ).get("coordinates", [])

            if len(coordinates) < 2:
                continue

            event_lon = coordinates[0]
            event_lat = coordinates[1]

            distance = haversine(
                lat,
                lon,
                event_lat,
                event_lon
            )

            if distance <= radius_km:

                properties = feature.get(
                    "properties",
                    {}
                )

                events.append({
                    "magnitude": properties.get("mag"),
                    "place": properties.get("place"),
                    "time": properties.get("time"),
                    "distance": round(distance, 1),
                    "lat": event_lat,
                    "lon": event_lon
                })

        events.sort(
            key=lambda item: (
                -(item["magnitude"] or 0),
                item["distance"]
            )
        )

        return events[:15]

    except Exception:
        return []


# ---------------- GLOBAL DISASTER EVENTS ----------------

def get_disaster_events():

    try:

        response = requests.get(
            GDACS,
            timeout=8
        )

        data = response.json()

        if isinstance(data, dict):
            return data.get("features", [])[:20]

        return []

    except Exception:
        return []


# ---------------- EMERGENCY FACILITIES ----------------

def get_facilities(lat, lon):

    query = f"""
    [out:json][timeout:12];

    (
        nwr(
            around:7000,
            {lat},
            {lon}
        )["amenity"~"hospital|clinic|police|fire_station"];

        nwr(
            around:7000,
            {lat},
            {lon}
        )["amenity"="shelter"];

        nwr(
            around:7000,
            {lat},
            {lon}
        )["emergency"="ambulance_station"];
    );

    out center tags;
    """

    try:

        response = requests.post(
            OVERPASS,
            data=query,
            timeout=15
        )

        data = response.json()

        facilities = []

        for element in data.get("elements", []):

            tags = element.get("tags", {})

            latitude = element.get(
                "lat",
                element.get("center", {}).get("lat")
            )

            longitude = element.get(
                "lon",
                element.get("center", {}).get("lon")
            )

            if latitude is None or longitude is None:
                continue

            facility_type = (
                tags.get("amenity")
                or tags.get("emergency")
                or "facility"
            )

            facilities.append({
                "name": tags.get(
                    "name",
                    "Emergency Facility"
                ),
                "type": facility_type,
                "lat": latitude,
                "lon": longitude
            })

        return facilities[:80]

    except Exception:
        return []


# ---------------- ROUTING ----------------

def get_route(
    start_lat,
    start_lon,
    destination_lat,
    destination_lon
):

    try:

        url = (
            f"{OSRM}/"
            f"{start_lon},{start_lat};"
            f"{destination_lon},{destination_lat}"
        )

        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }

        response = requests.get(
            url,
            params=params,
            timeout=12
        )

        data = response.json()

        if data.get("code") != "Ok":
            return None

        route = data["routes"][0]

        return {
            "distance_km": round(
                route["distance"] / 1000,
                2
            ),
            "duration_min": round(
                route["duration"] / 60
            ),
            "geometry": route["geometry"]
        }

    except Exception:
        return None


# ---------------- AI RISK ENGINE ----------------

def calculate_risk(
    disaster,
    weather,
    earthquakes,
    distance_km
):

    base_risk = {
        "Flood": 55,
        "Cyclone": 48,
        "Earthquake": 35,
        "Wildfire": 45,
        "Landslide": 50,
        "Extreme Weather": 40
    }.get(disaster, 40)

    score = base_risk

    factors = []

    rainfall = float(
        weather.get("rain") or 0
    )

    wind = float(
        weather.get("wind") or 0
    )

    gust = float(
        weather.get("gust") or 0
    )

    visibility = float(
        weather.get("visibility") or 10000
    )

    if rainfall >= 10:
        score += 18
        factors.append(
            "Heavy precipitation detected"
        )

    elif rainfall >= 3:
        score += 8
        factors.append(
            "Rainfall detected"
        )

    if wind >= 40 or gust >= 60:
        score += 15
        factors.append(
            "Strong wind conditions"
        )

    if visibility < 2000:
        score += 12
        factors.append(
            "Low visibility"
        )

    if earthquakes:

        strongest = max(
            float(event.get("magnitude") or 0)
            for event in earthquakes
        )

        if strongest >= 5:
            score += 15
            factors.append(
                "Nearby significant seismic activity"
            )

        elif strongest >= 3.5:
            score += 7
            factors.append(
                "Nearby seismic activity"
            )

    if distance_km > 20:
        score += 5
        factors.append(
            "Longer travel distance"
        )

    score = clamp(score)

    if score < 35:
        level = "LOW"

    elif score < 60:
        level = "MODERATE"

    elif score < 80:
        level = "HIGH"

    else:
        level = "CRITICAL"

    return score, level, factors


# ---------------- FRONTEND ----------------

@app.route("/")
def home():

    return render_template(
        "index.html",
        user=session.get("name")
    )


# ---------------- REGISTER ----------------

@app.route(
    "/api/register",
    methods=["POST"]
)
def register():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if (
        not name
        or not email
        or len(password) < 6
    ):

        return jsonify({
            "ok": False,
            "error":
                "Enter a name, valid email and password of at least 6 characters."
        }), 400

    try:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                generate_password_hash(password)
            )
        )

        conn.commit()

        user_id = conn.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        ).fetchone()["id"]

        conn.close()

        session["user_id"] = user_id
        session["name"] = name

        return jsonify({
            "ok": True,
            "name": name
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "ok": False,
            "error":
                "An account with this email already exists."
        }), 409


# ---------------- LOGIN ----------------

@app.route(
    "/api/login",
    methods=["POST"]
)
def login():

    data = request.get_json() or {}

    email = data.get(
        "email",
        ""
    ).lower()

    password = data.get(
        "password",
        ""
    )

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    ).fetchone()

    conn.close()

    if (
        not user
        or not check_password_hash(
            user["password"],
            password
        )
    ):

        return jsonify({
            "ok": False,
            "error":
                "Incorrect email or password."
        }), 401

    session["user_id"] = user["id"]
    session["name"] = user["name"]

    return jsonify({
        "ok": True,
        "name": user["name"]
    })


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ---------------- CURRENT USER ----------------

@app.route("/api/me")
def current_user():

    return jsonify({
        "logged_in":
            bool(session.get("user_id")),
        "name":
            session.get("name")
    })


# ---------------- AI ANALYSIS ----------------

@app.route(
    "/api/analyze",
    methods=["POST"]
)
def analyze():

    data = request.get_json() or {}

    start_lat = float(
        data.get("lat", 16.5062)
    )

    start_lon = float(
        data.get("lng", 80.6480)
    )

    destination_lat = float(
        data.get("dest_lat", 16.49)
    )

    destination_lon = float(
        data.get("dest_lng", 80.63)
    )

    disaster = data.get(
        "disaster",
        "Flood"
    )

    weather_data = get_weather(
        start_lat,
        start_lon
    )

    earthquakes = get_earthquakes(
        start_lat,
        start_lon
    )

    route = get_route(
        start_lat,
        start_lon,
        destination_lat,
        destination_lon
    )

    if route:
        distance = route["distance_km"]
    else:
        distance = haversine(
            start_lat,
            start_lon,
            destination_lat,
            destination_lon
        )

    risk, level, factors = calculate_risk(
        disaster,
        weather_data,
        earthquakes,
        distance
    )

    recommendations = {

        "Flood":
            "Prefer elevated roads and avoid low-lying or waterlogged areas.",

        "Cyclone":
            "Avoid exposed coastal roads and move toward designated shelters.",

        "Earthquake":
            "Avoid damaged structures and prefer major accessible roads.",

        "Wildfire":
            "Avoid smoke or fire zones and follow official evacuation directions.",

        "Landslide":
            "Avoid steep slopes and roads near unstable terrain.",

        "Extreme Weather":
            "Prefer major roads and remain close to emergency services."
    }

    if session.get("user_id"):

        conn = get_db()

        conn.execute(
            """
            INSERT INTO analyses
            (
                user_id,
                disaster,
                risk,
                level,
                start_lat,
                start_lng,
                destination
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                disaster,
                risk,
                level,
                start_lat,
                start_lon,
                data.get(
                    "destination",
                    "Selected destination"
                )
            )
        )

        conn.commit()
        conn.close()

    return jsonify({

        "ok": True,

        "risk": risk,

        "level": level,

        "safety_score":
            100 - risk,

        "disaster": disaster,

        "factors": factors,

        "weather": weather_data,

        "earthquakes":
            earthquakes[:5],

        "route": route,

        "recommendation":
            recommendations.get(
                disaster,
                "Follow local emergency guidance."
            )
    })


# ---------------- FACILITIES ----------------

@app.route("/api/facilities")
def facilities():

    lat = float(
        request.args.get(
            "lat",
            16.5062
        )
    )

    lon = float(
        request.args.get(
            "lng",
            80.6480
        )
    )

    return jsonify({
        "facilities":
            get_facilities(lat, lon)
    })


# ---------------- DISASTER ALERTS ----------------

@app.route("/api/alerts")
def alerts():

    return jsonify({
        "events":
            get_disaster_events()
    })


# ---------------- HISTORY ----------------

@app.route("/api/history")
def history():

    if not session.get("user_id"):
        return jsonify({
            "items": []
        })

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM analyses
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return jsonify({
        "items": [
            dict(row)
            for row in rows
        ]
    })


# ---------------- START SERVER ----------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )