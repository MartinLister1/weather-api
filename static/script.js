function getWeather() {
  var city = document.getElementById('city-input').value.trim();

  if (city == '') {
    alert('Please enter a city!');
    return;
  }

  // hide old results
  document.getElementById('weather-results').classList.add('hidden');
  document.getElementById('error').classList.add('hidden');

  // call the weather API
  fetch('/api/weather?city=' + city)
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {

      if (data.error) {
        document.getElementById('error-message').textContent = data.error;
        document.getElementById('error').classList.remove('hidden');
        return;
      }

      // put the data into the page
      document.getElementById('city-name').textContent = data.location.city;
      document.getElementById('country-name').textContent = data.location.country;
      document.getElementById('temperature').textContent = data.current_weather.temperature;
      document.getElementById('condition').textContent = data.current_weather.condition;
      document.getElementById('feels-like').textContent = data.current_weather.feels_like;
      document.getElementById('humidity').textContent = data.current_weather.humidity;
      document.getElementById('wind').textContent = data.current_weather.wind_speed;
      document.getElementById('precipitation').textContent = data.current_weather.precipitation;

      document.getElementById('weather-results').classList.remove('hidden');

      // get the forecast as well
      getForecast(city);
    })
    .catch(function(err) {
      document.getElementById('error-message').textContent = 'Something went wrong, please try again.';
      document.getElementById('error').classList.remove('hidden');
    });
}

function getForecast(city) {
  fetch('/api/forecast?city=' + city)
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {

      if (data.error) return;

      var forecastEl = document.getElementById('forecast');
      forecastEl.innerHTML = '';

      for (var i = 0; i < data.forecast.length; i++) {
        var day = data.forecast[i];

        // get the short day name e.g. Mon Tue Wed
        var date = new Date(day.date);
        var dayName = date.toLocaleDateString('en-GB', { weekday: 'short' });

        var card = document.createElement('article');
        card.className = 'forecast-day';

        card.innerHTML =
          '<small>' + dayName + '</small>' +
          '<span class="max">' + day.max_temp + '</span>' +
          '<span class="min">' + day.min_temp + '</span>';

        forecastEl.appendChild(card);
      }
    });
}

// press enter to search
document.getElementById('city-input').addEventListener('keypress', function(e) {
  if (e.key == 'Enter') {
    getWeather();
  }
});