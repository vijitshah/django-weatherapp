import requests
import json
import logging
from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

logger = logging.getLogger(__name__)

def is_processed(resp, process_list):
    key = f"{resp['name']}_{resp['country']}"
    if key in process_list:
        return True
    return False

# All app's logic goes inside index function
def index(request):
    # if there are no errors the code inside try block will execute
    city_country_counter = []
    cities_weather_data = []
    try:
        # checking if the method is POST, meaning user has requested to search
        if request.method == 'POST':
            API_KEY = settings.API_KEY
            # getting the city name from the form input   
            request_city_name = request.POST.get('city')
            logger.debug(f"Requested city : {request_city_name}")
            
            # city options render
            geocode_url = f'https://api.openweathermap.org/geo/1.0/direct?q={request_city_name}&limit=5&appid={API_KEY}'
            cities = requests.get(geocode_url).json()
            if not len(cities) > 0:
                logger.warning("No geocoding results found.")
                raise
           
            for city in cities:
                if not is_processed(city, city_country_counter):
                    # the url for current weather, takes city_name and API_KEY   
                    url = f'https://api.openweathermap.org/data/2.5/weather?q={request_city_name},{city["country"]}&appid={API_KEY}&units=metric'
                    # converting the request response to json   
                    city_weather_response = requests.get(url).json()
                    # Skip the bad data
                    if 'cod' in city_weather_response and city_weather_response['cod'] == '404':
                        logger.debug("Bad data, skipping...")
                        continue

                    # getting the current time
                    current_time = datetime.now()
                    # formatting the time using directives, it will take this format Day, Month Date Year, Current Time 
                    formatted_time = current_time.strftime("%A, %B %d %Y, %H:%M:%S %p")
                    
                    # bundling the weather information in one dictionary
                    print(f"Processing {city['name']} - {city['state']} - {city['country']}, {city_weather_response['weather']}")
                    city_weather_update = {
                        'city': city['name'].title(),
                        'state': city['state'].title(),
                        'description': city_weather_response['weather'][0]['description'],
                        'icon': city_weather_response['weather'][0]['icon'],
                        'temperature': 'Temperature: ' + str(city_weather_response['main']['temp']) + ' °C',
                        'country_code': city_weather_response['sys']['country'],
                        'wind': 'Wind: ' + str(city_weather_response['wind']['speed']) + 'km/h',
                        'humidity': 'Humidity: ' + str(city_weather_response['main']['humidity']) + '%',
                        'time': formatted_time
                    }
                    # update the process counter
                    city_country_counter.append(city['name']+'_'+city['country'])

                    # append the resultset
                    cities_weather_data.append(city_weather_update)    
                else:
                    logger.debug(f"{city['name']}_{city['country']} already processed. Skipping this one...")
                    continue
        else:
            cities_weather_data = [{}]
        context = {'cities_weather_data': cities_weather_data}
        return render(request, 'weatherupdates/home.html', context)
        # if there is an error the 404 page will be rendered 
        # the except will catch all the errors 
    except:
        logger.error("Error occured.")
        return render(request, 'weatherupdates/404.html')