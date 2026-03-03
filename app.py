from flask import Flask, jsonify, request
import urllib.request
import json
import urllib.parse

app = Flask(__name__)

# ── Helper: fetch coordinates for a city using Open-Meteo Geocoding API ──
def get_coordinates(city):
    encoded_city = urllib.parse.quote(city)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=en&format=json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            if "results" not in data or len(data["results"]) == 0:
                return None
            result = data["results"][0]
            return {
                "city": result["name"],
                "country": result.get("country", "Unknown"),
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "timezone": result.get("timezone", "UTC")
            }
    except Exception as e:
        return None


# ── Helper: fetch weather from Open-Meteo ──
def get_weather(latitude, longitude, timezone="UTC"):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"precipitation,wind_speed_10m,wind_direction_10m,weather_code"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        f"sunrise,sunset,wind_speed_10m_max"
        f"&timezone={urllib.parse.quote(timezone)}"
        f"&forecast_days=7"
    )
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        return None


# ── Helper: convert weather code to description ──
def weather_description(code):
    descriptions = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm with hail"
    }
    return descriptions.get(code, "Unknown")


# ════════════════════════════════════════════
# ROUTE 1: Home - API documentation
# ════════════════════════════════════════════
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "api": "Weather & Location API",
        "version": "1.0",
        "author": "Martin Lister",
        "description": "A REST API that fetches real-time weather and location data.",
        "endpoints": {
            "GET /": "API documentation (this page)",
            "GET /api/weather?city=London": "Get current weather for a city",
            "GET /api/forecast?city=Manchester": "Get 7-day forecast for a city",
            "GET /api/compare?cities=London,Manchester,Paris": "Compare weather across multiple cities",
            "GET /api/search?city=Man": "Search for matching city names",
        },
        "example_requests": [
            "/api/weather?city=London",
            "/api/forecast?city=Manchester",
            "/api/compare?cities=London,Paris,New York",
            "/api/search?city=Sto"
        ]
    })


# ════════════════════════════════════════════
# ROUTE 2: Current weather for a city
# ════════════════════════════════════════════
@app.route('/api/weather', methods=['GET'])
def current_weather():
    city = request.args.get('city')
    units = request.args.get('units', 'metric')  # metric or imperial

    if not city:
        return jsonify({"error": "Please provide a city. Example: /api/weather?city=London"}), 400

    # Get coordinates
    location = get_coordinates(city)
    if not location:
        return jsonify({"error": f"City '{city}' not found. Please try another name."}), 404

    # Get weather
    weather_data = get_weather(location["latitude"], location["longitude"], location["timezone"])
    if not weather_data:
        return jsonify({"error": "Could not fetch weather data. Please try again."}), 500

    current = weather_data["current"]
    temp = current["temperature_2m"]
    feels_like = current["apparent_temperature"]
    wind_speed = current["wind_speed_10m"]

    # Convert to imperial if requested
    if units == "imperial":
        temp = round((temp * 9/5) + 32, 1)
        feels_like = round((feels_like * 9/5) + 32, 1)
        wind_speed = round(wind_speed * 0.621371, 1)
        temp_unit = "°F"
        wind_unit = "mph"
    else:
        temp_unit = "°C"
        wind_unit = "km/h"

    return jsonify({
        "location": {
            "city": location["city"],
            "country": location["country"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "timezone": location["timezone"]
        },
        "current_weather": {
            "temperature": f"{temp}{temp_unit}",
            "feels_like": f"{feels_like}{temp_unit}",
            "humidity": f"{current['relative_humidity_2m']}%",
            "precipitation": f"{current['precipitation']}mm",
            "wind_speed": f"{wind_speed}{wind_unit}",
            "wind_direction": f"{current['wind_direction_10m']}°",
            "condition": weather_description(current["weather_code"])
        },
        "units": units
    })


# ════════════════════════════════════════════
# ROUTE 3: 7-day forecast
# ════════════════════════════════════════════
@app.route('/api/forecast', methods=['GET'])
def forecast():
    city = request.args.get('city')
    days = request.args.get('days', 7)

    if not city:
        return jsonify({"error": "Please provide a city. Example: /api/forecast?city=Manchester"}), 400

    try:
        days = int(days)
        if days < 1 or days > 7:
            days = 7
    except:
        days = 7

    location = get_coordinates(city)
    if not location:
        return jsonify({"error": f"City '{city}' not found."}), 404

    weather_data = get_weather(location["latitude"], location["longitude"], location["timezone"])
    if not weather_data:
        return jsonify({"error": "Could not fetch forecast data."}), 500

    daily = weather_data["daily"]
    forecast_list = []

    for i in range(min(days, len(daily["time"]))):
        forecast_list.append({
            "date": daily["time"][i],
            "max_temp": f"{daily['temperature_2m_max'][i]}°C",
            "min_temp": f"{daily['temperature_2m_min'][i]}°C",
            "precipitation": f"{daily['precipitation_sum'][i]}mm",
            "max_wind_speed": f"{daily['wind_speed_10m_max'][i]}km/h",
            "sunrise": daily["sunrise"][i],
            "sunset": daily["sunset"][i],
        })

    return jsonify({
        "location": {
            "city": location["city"],
            "country": location["country"],
        },
        "forecast_days": days,
        "forecast": forecast_list
    })


# ════════════════════════════════════════════
# ROUTE 4: Compare weather across multiple cities
# ════════════════════════════════════════════
@app.route('/api/compare', methods=['GET'])
def compare():
    cities_param = request.args.get('cities')

    if not cities_param:
        return jsonify({"error": "Please provide cities. Example: /api/compare?cities=London,Manchester,Paris"}), 400

    cities = [c.strip() for c in cities_param.split(',')]

    if len(cities) < 2:
        return jsonify({"error": "Please provide at least 2 cities to compare."}), 400

    if len(cities) > 5:
        return jsonify({"error": "Maximum 5 cities allowed for comparison."}), 400

    results = []
    not_found = []

    for city in cities:
        location = get_coordinates(city)
        if not location:
            not_found.append(city)
            continue

        weather_data = get_weather(location["latitude"], location["longitude"], location["timezone"])
        if not weather_data:
            not_found.append(city)
            continue

        current = weather_data["current"]
        results.append({
            "city": location["city"],
            "country": location["country"],
            "temperature": f"{current['temperature_2m']}°C",
            "feels_like": f"{current['apparent_temperature']}°C",
            "humidity": f"{current['relative_humidity_2m']}%",
            "wind_speed": f"{current['wind_speed_10m']}km/h",
            "condition": weather_description(current["weather_code"])
        })

    # Find hottest and coldest
    if results:
        temps = [float(r["temperature"].replace("°C", "")) for r in results]
        hottest = results[temps.index(max(temps))]["city"]
        coldest = results[temps.index(min(temps))]["city"]
    else:
        hottest = coldest = None

    response = {
        "cities_compared": len(results),
        "summary": {
            "hottest_city": hottest,
            "coldest_city": coldest
        },
        "comparison": results
    }

    if not_found:
        response["not_found"] = not_found

    return jsonify(response)


# ════════════════════════════════════════════
# ROUTE 5: Search for cities
# ════════════════════════════════════════════
@app.route('/api/search', methods=['GET'])
def search_cities():
    query = request.args.get('city')

    if not query or len(query) < 2:
        return jsonify({"error": "Please provide at least 2 characters. Example: /api/search?city=Man"}), 400

    encoded_query = urllib.parse.quote(query)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_query}&count=10&language=en&format=json"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

            if "results" not in data:
                return jsonify({"query": query, "results": [], "count": 0})

            cities = []
            for r in data["results"]:
                cities.append({
                    "city": r["name"],
                    "country": r.get("country", "Unknown"),
                    "region": r.get("admin1", ""),
                    "latitude": r["latitude"],
                    "longitude": r["longitude"]
                })

            return jsonify({
                "query": query,
                "count": len(cities),
                "results": cities
            })
    except Exception as e:
        return jsonify({"error": "Search failed. Please try again."}), 500


# ════════════════════════════════════════════
# Error handlers
# ════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Route not found",
        "message": "Visit / to see all available endpoints"
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed. This API only accepts GET requests."}), 405


if __name__ == '__main__':
    app.run(debug=True)