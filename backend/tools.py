import httpx
from geopy.geocoders import Nominatim

def get_coordinates(city_name: str):
    """Converts a city name to Lat/Long using OpenStreetMap."""
    try:
        # User_agent is required by Nominatim policy
        geolocator = Nominatim(user_agent="allergy_agent_capstone")
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

def get_real_aqi(city_name: str):
    """Fetches REAL-TIME AQI, PM2.5, and Pollen proxy data."""
    lat, lon = get_coordinates(city_name)
    
    if not lat:
        return {"error": f"Could not find coordinates for {city_name}"}

    # OpenMeteo Air Quality API (Free, No Key required)
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["us_aqi", "pm2_5", "pm10", "ozone", "dust"],
        "hourly": ["alder_pollen", "grass_pollen", "mugwort_pollen"] # Pollen data
    }

    try:
        response = httpx.get(url, params=params)
        data = response.json()
        
        # Extracting the most relevant current data
        current = data.get("current", {})
        hourly = data.get("hourly", {})
        
        # Simple logic to get max pollen from the next hour
        grass_pollen = hourly.get("grass_pollen", [0])[0] if "grass_pollen" in hourly else 0
        
        return {
            "location": city_name,
            "aqi": current.get("us_aqi", 0),
            "pm2_5": current.get("pm2_5", 0),
            "dominant_pollutant": "PM2.5" if current.get("pm2_5", 0) > current.get("pm10", 0) else "PM10",
            "pollen_level": "High" if grass_pollen > 50 else "Low", # Simple threshold
            "raw_data": current # Sending raw data for Gemini to analyze
        }
    except Exception as e:
        return {"error": f"API Request failed: {e}"}

# Test it immediately
if __name__ == "__main__":
    print(get_real_aqi("New Delhi"))
    print(get_real_aqi("New York")) 
    # You should see DIFFERENT numbers now!