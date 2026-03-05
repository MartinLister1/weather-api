# Weather App

A weather app with a front end and a REST API behind it. Search any 
city to get the current weather and a 7 day forecast. Built with 
Python and Flask, pulling live data from the Open-Meteo API.

## Built with
- Python
- Flask
- HTML, CSS, JavaScript
- Open-Meteo API (free, no key required)

## Live demo
https://weather-api-2lt1.onrender.com

Note: hosted on Render's free tier so may take ~50 seconds to wake 
up if it hasn't been used recently.

## API endpoints
- /api/weather?city=London
- /api/forecast?city=London
- /api/search?city=Man
- /api/compare?cities=London,Paris,Manchester

## Run locally
1. Clone the repo
2. Install dependencies: pip install flask
3. Run: python app.py
4. Open http://localhost:5000

## Author
Martin Lister