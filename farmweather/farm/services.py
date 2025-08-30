import requests
from django.conf import settings

BASE_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
BASE_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"

def _params_by_location(location: str):
    # If user enters a numeric ID (like 990930), query by id
    if location.isdigit():
        return {"id": location, "appid": settings.OPENWEATHER_API_KEY, "units": "metric"}
    # Otherwise search by name (you can support "City,CountryCode" too)
    return {"q": location, "appid": settings.OPENWEATHER_API_KEY, "units": "metric"}

def fetch_current_weather(location: str) -> dict:
    r = requests.get(BASE_WEATHER, params=_params_by_location(location), timeout=15)
    r.raise_for_status()
    return r.json()

def fetch_forecast(location: str) -> dict:
    r = requests.get(BASE_FORECAST, params=_params_by_location(location), timeout=15)
    r.raise_for_status()
    return r.json()

def summarize_5day(forecast_json: dict):
    """
    OpenWeather 'forecast' returns 3-hour steps for ~5 days.
    We compute:
      - avg_temp: mean of all points
      - total_rain_mm: sum of rain volumes (3h buckets)
      - conditions: most frequent icon/description (rough)
    """
    items = forecast_json.get("list", [])
    if not items:
        return None

    temps = []
    rain_total = 0.0
    main_descs = []

    for it in items:
        # temperature
        main = it.get("main", {})
        if "temp" in main:
            temps.append(float(main["temp"]))

        # rain in mm for this 3h slot
        rain = it.get("rain", {})
        if "3h" in rain:
            rain_total += float(rain["3h"])

        # text condition
        w = it.get("weather", [])
        if w:
            main_descs.append(w[0].get("main", ""))

    avg_temp = sum(temps) / len(temps) if temps else None
    mode_condition = max(set(main_descs), key=main_descs.count) if main_descs else "N/A"

    return {
        "avg_temp": avg_temp,
        "total_rain_mm": round(rain_total, 1),
        "condition": mode_condition,
    }
