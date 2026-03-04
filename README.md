# Weather & Location API
Built by Martin Lister | Python & Flask

A REST API that fetches real-time weather data for any city in the world.

## How to run
1. Install Flask: pip install flask
2. Run: python app.py
3. Visit: http://localhost:5000

## Endpoints

### Current Weather
http://localhost:5000/api/weather?city=London
http://localhost:5000/api/weather?city=Stockport

### 7 Day Forecast
http://localhost:5000/api/forecast?city=Manchester
http://localhost:5000/api/forecast?city=London

### Compare Cities
http://localhost:5000/api/compare?cities=London,Paris,Manchester
http://localhost:5000/api/compare?cities=New York,Tokyo,Sydney

### Search for a City
http://localhost:5000/api/search?city=Man
http://localhost:5000/api/search?city=Sto

## Technologies Used
- Python
- Flask
- Open-Meteo API (free real-time weather data)
- Git & GitHub