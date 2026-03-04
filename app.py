from flask import Flask, jsonify, request, render_template
import urllib.request
import json
import urllib.parse
import os

app = Flask(__name__)


# this gets the lat and long for a city so we can pass it to the weather API
def get_coordinates(city):
    encoded_city = urllib.parse.quote(city)
    url = "https://geocoding-api.open-meteo.com/v1/search?name=" + encoded_city + "&count=1&language=en&format=json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            if "results" not in data or len(data["results"]) == 0:
                return None
            r = data["results"][0]
            return {
                "city": r["name"],
                "country": r.get("country", "Unknown"),
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "timezone": r.get("timezone", "UTC")
            }
    except:
        return None


# calls the open-meteo API and gets the weather data back
def get_weather(lat, lon, timezone="UTC"):
    url = "https://api.open-meteo.com/v1/forecast?latitude=" + str(lat) + "&longitude=" + str(lon)
    url += "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,wind_direction_10m,weather_code"
    url += "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset,wind_speed_10m_max"
    url += "&timezone=" + urllib.parse.quote(timezone) + "&forecast_days=7"
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except:
        return None


# converts the weather code number into a readable description
# got the codes from the open-meteo docs
def get_condition(code):
    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Icy fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Heavy drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight showers",
        81: "Moderate showers",
        82: "Heavy showers",
        95: "Thunderstorm",
        99: "Thunderstorm with hail"
    }
    return conditions.get(code, "Unknown")


# home page
@app.route('/', methods=['GET'])
def home():
    return jsonify({...})


# returns the current weather for a city
@app.route('/api/weather')
def current_weather():
    city = request.args.get('city')
    units = request.args.get('units', 'metric')

    if not city:
        return jsonify({"error": "Please provide a city. Example: /api/weather?city=London"}), 400

    location = get_coordinates(city)
    if not location:
        return jsonify({"error": "City not found. Please try another name."}), 404

    weather_data = get_weather(location["latitude"], location["longitude"], location["timezone"])
    if not weather_data:
        return jsonify({"error": "Could not get weather data. Please try again."}), 500

    current = weather_data["current"]
    temp = current["temperature_2m"]
    feels_like = current["apparent_temperature"]
    wind = current["wind_speed_10m"]

    # convert to fahrenheit if the user wants imperial
    if units == "imperial":
        temp = round((temp * 9/5) + 32, 1)
        feels_like = round((feels_like * 9/5) + 32, 1)
        wind = round(wind * 0.621371, 1)
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
            "temperature": str(temp) + temp_unit,
            "feels_like": str(feels_like) + temp_unit,
            "humidity": str(current["relative_humidity_2m"]) + "%",
            "precipitation": str(current["precipitation"]) + "mm",
            "wind_speed": str(wind) + wind_unit,
            "condition": get_condition(current["weather_code"])
        }
    })


# returns a 7 day forecast for a city
@app.route('/api/forecast')
def forecast():
    city = request.args.get('city')

    if not city:
        return jsonify({"error": "Please provide a city. Example: /api/forecast?city=Manchester"}), 400

    location = get_coordinates(city)
    if not location:
        return jsonify({"error": "City not found."}), 404

    weather_data = get_weather(location["latitude"], location["longitude"], location["timezone"])
    if not weather_data:
        return jsonify({"error": "Could not get forecast data."}), 500

    daily = weather_data["daily"]
    forecast_list = []

    for i in range(len(daily["time"])):
        forecast_list.append({
            "date": daily["time"][i],
            "max_temp": str(daily["temperature_2m_max"][i]) + "°C",
            "min_temp": str(daily["temperature_2m_min"][i]) + "°C",
            "precipitation": str(daily["precipitation_sum"][i]) + "mm",
            "sunrise": daily["sunrise"][i],
            "sunset": daily["sunset"][i]
        })

    return jsonify({
        "location": {
            "city": location["city"],
            "country": location["country"]
        },
        "forecast": forecast_list
    })


# compares weather across multiple cities
@app.route('/api/compare')
def compare():
    cities_param = request.args.get('cities')

    if not cities_param:
        return jsonify({"error": "Please provide cities. Example: /api/compare?cities=London,Paris,Manchester"}), 400

    # split the cities by comma
    cities = [c.strip() for c in cities_param.split(',')]

    if len(cities) < 2:
        return jsonify({"error": "Please provide at least 2 cities."}), 400

    if len(cities) > 5:
        return jsonify({"error": "Maximum 5 cities."}), 400

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
            "temperature": str(current["temperature_2m"]) + "°C",
            "humidity": str(current["relative_humidity_2m"]) + "%",
            "wind_speed": str(current["wind_speed_10m"]) + "km/h",
            "condition": get_condition(current["weather_code"])
        })

    return jsonify({
        "cities_compared": len(results),
        "comparison": results,
        "not_found": not_found
    })


# search for cities by name
@app.route('/api/search')
def search():
    query = request.args.get('city')

    if not query or len(query) < 2:
        return jsonify({"error": "Please enter at least 2 characters."}), 400

    encoded = urllib.parse.quote(query)
    url = "https://geocoding-api.open-meteo.com/v1/search?name=" + encoded + "&count=10&language=en&format=json"

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
    except:
        return jsonify({"error": "Search failed. Please try again."}), 500


port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)