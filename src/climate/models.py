import os
import requests
from collections import UserList
from django.db import models
from django.core import serializers
from django.core.cache import caches
from dotenv import load_dotenv

load_dotenv()
CACHE = caches["default"]

# This functionality builds on an answer for the following SO question,
# but not the accepted answer; this one is farther down in the post:
#
# https://stackoverflow.com/questions/9091305/django-models-without-database


class ClimateModelManager(models.Manager):
    """
    A Django model manager that fetches and caches climate data from the OpenWeather API.

    This manager retrieves weather data based on the configured latitude and longitude
    and caches the response for a specified duration to minimize API requests.

    Attributes:
        * :api (str): The OpenWeather API key retrieved from environment variables.
        * :lat (str): The latitude coordinate for the weather query, retrieved from environment variables.
        * :lon (str): The longitude coordinate for the weather query, retrieved from environment variables.
        * :cache_key (str): The key used for caching the weather data.
        * :cache_sentinel (object): A unique object used to detect cache misses.
        * :cache_timeout (int): The duration (in seconds) for which the weather data is cached.
    """

    api = os.getenv("OPENWEATHER_API")
    lat = os.getenv("OPENWEATHER_LAT")
    lon = os.getenv("OPENWEATHER_LON")

    cache_key = "cached-transient-models"
    cache_sentinel = object()
    cache_timeout = 600

    def get_queryset(self):
        """
        Retrieve the weather data from cache or fetch it from the OpenWeather API if not cached.

        If the cache does not contain the weather data, this method queries the OpenWeather API
        using the configured latitude, longitude, and API key. The retrieved data is then cached
        for a specified timeout period.

        * :raises requests.exceptions.RequestException: If there is an issue with the API request.
        * :return: A queryset containing a single ClimateModel instance populated with weather data.
        * :rtype: ClimateModelQueryset
        """
        climate_model_data = CACHE.get(self.cache_key, self.cache_sentinel)
        if climate_model_data is self.cache_sentinel:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.api}"
            )
            response.raise_for_status()
            climate_model_data = response.json()
            CACHE.set(self.cache_key, climate_model_data, self.cache_timeout)
        return ClimateModelQueryset([ClimateModel(**climate_model_data)])


class ClimateModelQueryset(UserList):
    """
    A custom queryset class for ClimateModel that inherits from UserList.

    This class is intended to provide additional query capabilities specific
    to the ClimateModel data. Currently, it does not add any new functionality
    but serves as a placeholder for future enhancements.

    Attributes:
        * data (list): The list of ClimateModel instances.
    """

    pass


class ClimateModel(models.Model):
    """
    A Django model class representing weather data fetched from the OpenWeather API.

    This model is not managed by the Django's ORM (managed = False) and is used to
    structure and access weather data retrieved from the OpenWeather API. The data
    is stored in JSON fields corresponding to various weather attributes.

    Attributes:
        coord (JSONField): The Geographical coordinates of the location.
        weather (JSONField): Weather conditions at the location.
        base (JSONField): Internal parameter.
        main (JSONField): Main weather data (temperature, pressure, humidity, etc.).
        visibility (JSONField): Visibility information.
        wind (JSONField): Wind Conditions.
        rain (JSONField): Rain information.
        clouds (JSONField) Cloudiness information.
        dt (JSONField): data receiving time in unix format.
        sys (JSONField): System information.
        timezone (JSONField): Timezone information.
        name (JSONField): City name.
        cod (JSONField): Internal parameter.
    Methods:
        :as_dict: Returns the model data as a dictionary
    """

    class Meta:
        managed = False

    obj = ClimateModelManager.from_queryset(ClimateModelQueryset)()

    coord = models.JSONField()
    weather = models.JSONField()
    base = models.JSONField()
    main = models.JSONField()
    visibility = models.JSONField()
    wind = models.JSONField()
    rain = models.JSONField()
    clouds = models.JSONField()
    dt = models.JSONField()
    sys = models.JSONField()
    timezone = models.JSONField()
    name = models.JSONField()
    cod = models.JSONField()

    def as_dict(self):
        result = {}
        fields = self._meta.fields
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result
