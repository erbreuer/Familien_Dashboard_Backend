"""Weather service - handles geocoding and weather API calls (Open-Meteo, no API key needed)"""
import requests
from app import db
from app.models import FamilyWeatherConfig, UserFamilyRole


GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search'
WEATHER_URL = 'https://api.open-meteo.com/v1/forecast'

WEATHER_CODES = {
    0: 'Klarer Himmel',
    1: 'Überwiegend klar', 2: 'Teilweise bewölkt', 3: 'Bewölkt',
    45: 'Nebel', 48: 'Raureif-Nebel',
    51: 'Leichter Nieselregen', 53: 'Mäßiger Nieselregen', 55: 'Starker Nieselregen',
    61: 'Leichter Regen', 63: 'Mäßiger Regen', 65: 'Starker Regen',
    71: 'Leichter Schneefall', 73: 'Mäßiger Schneefall', 75: 'Starker Schneefall',
    77: 'Schneekörner',
    80: 'Leichte Regenschauer', 81: 'Mäßige Regenschauer', 82: 'Starke Regenschauer',
    85: 'Leichte Schneeschauer', 86: 'Starke Schneeschauer',
    95: 'Gewitter', 96: 'Gewitter mit leichtem Hagel', 99: 'Gewitter mit starkem Hagel',
}


class WeatherService:
    """Handles weather config storage and API calls"""

    @staticmethod
    def geocode_city(city_name: str) -> dict:
        """Resolve a city name to lat/lon via Open-Meteo Geocoding API.

        Returns dict with keys: city_name, latitude, longitude
        Raises ValueError if city not found.
        """
        resp = requests.get(
            GEOCODING_URL,
            params={'name': city_name, 'count': 1, 'language': 'de', 'format': 'json'},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get('results')
        if not results:
            raise ValueError(f'Stadt "{city_name}" nicht gefunden')
        result = results[0]
        return {
            'city_name': result.get('name', city_name),
            'latitude': result['latitude'],
            'longitude': result['longitude'],
        }

    @staticmethod
    def get_or_create_config(family_id: int) -> FamilyWeatherConfig:
        """Return existing config or create default one for the family."""
        config = FamilyWeatherConfig.query.filter_by(family_id=family_id).first()
        if not config:
            config = FamilyWeatherConfig(family_id=family_id)
            db.session.add(config)
            db.session.commit()
        return config

    @staticmethod
    def update_location(family_id: int, city_name: str) -> FamilyWeatherConfig:
        """Geocode city_name and persist the new location for the family."""
        geo = WeatherService.geocode_city(city_name)
        config = WeatherService.get_or_create_config(family_id)
        config.city_name = geo['city_name']
        config.latitude = geo['latitude']
        config.longitude = geo['longitude']
        try:
            db.session.commit()
            return config
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def fetch_weather(family_id: int) -> dict:
        """Fetch current weather + 7-day daily forecast for the family's configured location."""
        config = WeatherService.get_or_create_config(family_id)

        resp = requests.get(
            WEATHER_URL,
            params={
                'latitude': config.latitude,
                'longitude': config.longitude,
                'current': [
                    'temperature_2m',
                    'relative_humidity_2m',
                    'apparent_temperature',
                    'weather_code',
                    'wind_speed_10m',
                ],
                'daily': [
                    'weather_code',
                    'temperature_2m_max',
                    'temperature_2m_min',
                ],
                'timezone': 'auto',
                'forecast_days': 7,
            },
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()

        current = data.get('current', {})
        daily = data.get('daily', {})

        # Build forecast list
        forecast = []
        dates = daily.get('time', [])
        for i, date in enumerate(dates):
            code = daily.get('weather_code', [])[i] if daily.get('weather_code') else None
            forecast.append({
                'date': date,
                'weather_code': code,
                'weather_description': WEATHER_CODES.get(code, 'Unbekannt'),
                'temperature_max': daily.get('temperature_2m_max', [])[i] if daily.get('temperature_2m_max') else None,
                'temperature_min': daily.get('temperature_2m_min', [])[i] if daily.get('temperature_2m_min') else None,
            })

        current_code = current.get('weather_code')
        return {
            'location': config.to_dict(),
            'current': {
                'temperature': current.get('temperature_2m'),
                'apparent_temperature': current.get('apparent_temperature'),
                'humidity': current.get('relative_humidity_2m'),
                'wind_speed': current.get('wind_speed_10m'),
                'weather_code': current_code,
                'weather_description': WEATHER_CODES.get(current_code, 'Unbekannt'),
            },
            'forecast': forecast,
        }

    @staticmethod
    def is_family_admin(user_id: int, family_id: int) -> bool:
        """Return True if the user has the Familyadmin role in the given family."""
        membership = UserFamilyRole.query.filter_by(
            user_id=user_id, family_id=family_id
        ).first()
        if not membership:
            return False
        return membership.role.name == 'Familyadmin'
