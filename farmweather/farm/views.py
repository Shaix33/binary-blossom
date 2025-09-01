from django.shortcuts import render
from django.contrib import messages
from .forms import LocationForm
from .services import fetch_current_weather, fetch_forecast, summarize_5day
from .crops import suggest_crops
import requests
import datetime

def group_daily_forecast(forecast):
    """Group forecast list (3-hourly data) into daily min/max + icon."""
    days = {}
    for entry in forecast.get("list", []):
        dt = datetime.datetime.fromtimestamp(entry["dt"])
        date = dt.date()

        temp = entry["main"]["temp"]
        weather = entry["weather"][0]

        if date not in days:
            days[date] = {
                "date": date,
                "min": temp,
                "max": temp,
                "icon": weather["icon"],
                "condition": weather["main"]
            }
        else:
            days[date]["min"] = min(days[date]["min"], temp)
            days[date]["max"] = max(days[date]["max"], temp)

    # return sorted list of days (skip today’s past slots)
    return list(days.values())

def home(request):
    form = LocationForm(request.POST or None)
    context = {"form": form, "weather": None, "summary": None, "crops": [], "daily": []}

    if request.method == "POST" and form.is_valid():
        loc = form.cleaned_data["location"].strip()
        try:
            current = fetch_current_weather(loc)
            forecast = fetch_forecast(loc)
            summary = summarize_5day(forecast)
            daily = group_daily_forecast(forecast)[:6]  # next 6 days

            crops = suggest_crops(
                avg_temp=summary["avg_temp"] if summary else None,
                total_rain_mm=summary["total_rain_mm"] if summary else None
            )

            context.update({
                "weather": current,
                "summary": summary,
                "crops": crops,
                "daily": daily,
                "location_label": f'{current.get("name", loc)}, {current.get("sys", {}).get("country","")}'.strip(", "),
            })
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                messages.error(request, "Location not found. Try another city or a city ID (e.g., 990930).")
            else:
                messages.error(request, f"Weather service error: {e.response.status_code}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {e}")

    return render(request, "farm/home.html", context)

from django.shortcuts import render

def check_box(request):
    return render(request, "farm/click.html")  # your checkbox page

def login_page(request):
    return render(request, "farm/login.html")  # login page




