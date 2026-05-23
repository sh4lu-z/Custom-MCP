import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-Weather-Tool")


def get_weather_desc(code):
    codes = {
        0:"Clear sky ☀️",1:"Mainly clear 🌤️",2:"Partly cloudy ⛅",3:"Overcast ☁️",
        45:"Fog 🌫️",48:"Rime fog 🌫️",51:"Light drizzle 🌧️",53:"Moderate drizzle 🌧️",
        55:"Dense drizzle 🌧️",61:"Slight rain ☔",63:"Moderate rain ☔",65:"Heavy rain ⛈️",
        71:"Slight snow ❄️",73:"Moderate snow ❄️",75:"Heavy snow ❄️",77:"Snow grains ❄️",
        80:"Rain showers 🌦️",81:"Moderate showers 🌦️",82:"Violent showers ⛈️",
        95:"Thunderstorm ⚡",96:"Thunderstorm+hail ⛈️",99:"Heavy thunderstorm ⛈️"
    }
    return codes.get(code, "Variable 🌤️")


def _get_coords(city: str):
    """City name → (lat, lon, display_name)"""
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "format": "json"}, timeout=5
    ).json()
    r   = geo["results"][0]
    return r["latitude"], r["longitude"], f"{r['name']}, {r.get('country','')}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Current Weather (20 server fallback)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_weather(location: str) -> str:
    """
    Current weather (20-server fallback system).
    Use for: 'weather', 'temperature', 'කාලගුණය'.
    """
    city = location.strip()
    key  = "060a6bcfa19809c2cd4d97a212b19273"

    def s1():
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                         params={"q": city, "appid": key, "units": "metric"}, timeout=4).json()
        return (f"🌤️ CURRENT WEATHER — {r['name']}, {r['sys']['country']}\n{'─'*35}\n"
                f"  🌡️  Temp      : {r['main']['temp']}°C (feels {r['main']['feels_like']}°C)\n"
                f"  ☁️  Sky       : {r['weather'][0]['description'].title()}\n"
                f"  💧 Humidity  : {r['main']['humidity']}%\n"
                f"  💨 Wind      : {r['wind']['speed']} m/s\n"
                f"  👁️  Visibility: {r.get('visibility',0)//1000} km\n")

    def s2():
        lat, lon, name = _get_coords(city)
        w = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": lat, "longitude": lon,
                                 "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m,apparent_temperature"},
                         timeout=4).json()
        c = w['current']
        return (f"🌤️ CURRENT WEATHER — {name}\n{'─'*35}\n"
                f"  🌡️  Temp      : {c['temperature_2m']}°C (feels {c['apparent_temperature']}°C)\n"
                f"  ☁️  Condition : {get_weather_desc(c['weather_code'])}\n"
                f"  💧 Humidity  : {c['relative_humidity_2m']}%\n"
                f"  💨 Wind      : {c['wind_speed_10m']} km/h\n")

    def s3():
        return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "3"}, timeout=5).text.strip()

    def s4():
        r = requests.get(f"https://goweather.herokuapp.com/weather/{city}", timeout=5).json()
        return f"🌤️ WEATHER — {city}\n  🌡️ {r['temperature']} | 💨 {r['wind']} | ☁️ {r['description']}"

    def s5():
        lat, lon, name = _get_coords(city)
        w = requests.get("http://www.7timer.info/bin/api.pl",
                         params={"lon": lon, "lat": lat, "product": "civil", "output": "json"}, timeout=4).json()
        return f"🌤️ 7Timer — {name}\n  🌡️ {w['dataseries'][0]['temp2m']}°C | ☁️ {w['dataseries'][0]['weather']}"

    def s6():  return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "4"}, timeout=5).text.strip()
    def s7():  return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "%l:+%c+%t"}, timeout=5).text.strip()
    def s8():  return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "%C+%t+%w"}, timeout=5).text.strip()
    def s9():  return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "%l+%t+%h"}, timeout=5).text.strip()
    def s10(): return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "v2"}, timeout=5).text[:200]
    def s11(): return "🌡️ Temp: " + requests.get(f"https://wttr.in/{city}", params={"format": "%t"}, timeout=5).text.strip()
    def s12(): return "💨 Wind: " + requests.get(f"https://wttr.in/{city}", params={"format": "%w"}, timeout=5).text.strip()
    def s13(): return "☁️ Sky: " + requests.get(f"https://wttr.in/{city}", params={"format": "%C"}, timeout=5).text.strip()
    def s14(): return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "1"}, timeout=5).text.strip()
    def s15(): return "🌤️ " + requests.get(f"https://wttr.in/{city}", params={"format": "2"}, timeout=5).text.strip()

    def s16():
        lat, lon, name = _get_coords(city)
        w = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": lat, "longitude": lon,
                                 "current": "relative_humidity_2m,apparent_temperature"}, timeout=4).json()
        return f"🌤️ {name} — Feels: {w['current']['apparent_temperature']}°C | Humidity: {w['current']['relative_humidity_2m']}%"

    def s17():
        lat, lon, name = _get_coords(city)
        w = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": lat, "longitude": lon,
                                 "current": "surface_pressure,precipitation"}, timeout=4).json()
        return f"🌤️ {name} — Pressure: {w['current']['surface_pressure']} hPa | Rain: {w['current']['precipitation']} mm"

    def s18():
        lat, lon, name = _get_coords(city)
        w = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": lat, "longitude": lon,
                                 "daily": "temperature_2m_max,temperature_2m_min", "timezone": "auto"}, timeout=4).json()
        return f"🌤️ {name} — Max: {w['daily']['temperature_2m_max'][0]}°C | Min: {w['daily']['temperature_2m_min'][0]}°C"

    def s19():
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                         params={"q": city, "appid": key, "units": "imperial"}, timeout=4).json()
        return f"🌤️ {r['name']} — {r['main']['temp']}°F"

    def s20():
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                         params={"q": city, "appid": key, "lang": "si", "units": "metric"}, timeout=4).json()
        return f"🌤️ {r['name']} — {r['main']['temp']}°C | {r['weather'][0]['description']}"

    for provider in [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20]:
        try:
            reply = provider()
            if reply and len(reply) > 10:
                return reply
        except Exception:
            continue

    return f"❌ '{city}' සඳහා weather servers ඔක්කොම fail විය."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: 7-Day Forecast
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_weather_forecast(location: str, days: int = 7) -> str:
    """
    7-day weather forecast ලබාගනී.
    Use for: 'weather forecast', 'next week weather', 'week forecast', 'ඉදිරි දින කාලගුණය'.
    """
    try:
        days = max(1, min(7, days))
        lat, lon, name = _get_coords(location)
        w = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "daily"   : "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,wind_speed_10m_max",
                "timezone": "auto"
            }, timeout=5
        ).json()
        d = w['daily']
        output = f"📅 {days}-DAY FORECAST — {name}\n{'═'*40}\n"
        for i in range(days):
            output += (
                f"  📆 {d['time'][i]}\n"
                f"     🔺 Max : {d['temperature_2m_max'][i]}°C  |  🔻 Min: {d['temperature_2m_min'][i]}°C\n"
                f"     ☁️  {get_weather_desc(d['weather_code'][i])}\n"
                f"     🌧️  Rain : {d['precipitation_sum'][i]} mm  |  💨 Wind: {d['wind_speed_10m_max'][i]} km/h\n"
                f"{'─'*40}\n"
            )
        return output
    except Exception as e:
        return f"❌ Forecast error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Air Quality
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_air_quality(location: str) -> str:
    """
    Air quality index ලබාගනී.
    Use for: 'air quality', 'pollution', 'AQI', 'air index'.
    """
    try:
        lat, lon, name = _get_coords(location)
        w = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": lat, "longitude": lon,
                "current" : "european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone"
            }, timeout=5
        ).json()
        c = w['current']

        def aqi_level(aqi):
            if aqi <= 50:   return "🟢 Good"
            if aqi <= 100:  return "🟡 Moderate"
            if aqi <= 150:  return "🟠 Unhealthy (Sensitive)"
            if aqi <= 200:  return "🔴 Unhealthy"
            if aqi <= 300:  return "🟣 Very Unhealthy"
            return "⚫ Hazardous"

        eu_aqi = c.get('european_aqi', 0)
        us_aqi = c.get('us_aqi', 0)
        return (
            f"🌬️ AIR QUALITY — {name}\n{'═'*35}\n"
            f"  🇪🇺 EU AQI  : {eu_aqi} — {aqi_level(eu_aqi)}\n"
            f"  🇺🇸 US AQI  : {us_aqi} — {aqi_level(us_aqi)}\n"
            f"  💨 PM2.5   : {c.get('pm2_5', 'N/A')} μg/m³\n"
            f"  🌫️  PM10    : {c.get('pm10', 'N/A')} μg/m³\n"
            f"  🟤 CO      : {c.get('carbon_monoxide', 'N/A')} μg/m³\n"
            f"  🔵 NO₂     : {c.get('nitrogen_dioxide', 'N/A')} μg/m³\n"
            f"  ⚗️  Ozone   : {c.get('ozone', 'N/A')} μg/m³\n"
        )
    except Exception as e:
        return f"❌ Air quality error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 4: UV Index
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_uv_index(location: str) -> str:
    """
    UV index ලබාගනී.
    Use for: 'UV index', 'sun exposure', 'sunburn risk', 'UV level'.
    """
    try:
        lat, lon, name = _get_coords(location)
        w = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={"latitude": lat, "longitude": lon, "current": "uv_index,uv_index_clear_sky"},
            timeout=5
        ).json()
        uv = w['current'].get('uv_index', 0)
        uc = w['current'].get('uv_index_clear_sky', 0)

        def uv_risk(u):
            if u < 3:  return "🟢 Low"
            if u < 6:  return "🟡 Moderate"
            if u < 8:  return "🟠 High"
            if u < 11: return "🔴 Very High"
            return "🟣 Extreme"

        def uv_advice(u):
            if u < 3:  return "No protection needed."
            if u < 6:  return "Wear sunscreen SPF 15+."
            if u < 8:  return "Sunscreen SPF 30+, hat required."
            if u < 11: return "SPF 50+, avoid midday sun."
            return "Stay indoors, max protection!"

        return (
            f"☀️ UV INDEX — {name}\n{'═'*35}\n"
            f"  🔆 UV Index       : {uv:.1f} — {uv_risk(uv)}\n"
            f"  ☁️  Clear Sky UV   : {uc:.1f}\n"
            f"  💡 Advice         : {uv_advice(uv)}\n"
        )
    except Exception as e:
        return f"❌ UV Index error: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')