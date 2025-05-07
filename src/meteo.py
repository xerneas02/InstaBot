import requests

# dictionnaire de correspondance code → description
WEATHER_DESC = {
    0:  "Ciel clair",
    1:  "Principalement clair",
    2:  "Partiellement nuageux",
    3:  "Couvert",
    45: "Brouillard",
    48: "Brouillard givrants",
    51: "Bruine légère",
    53: "Bruine modérée",
    55: "Bruine dense",
    61: "Pluie légère",
    63: "Pluie modérée",
    65: "Pluie forte",
    66: "Pluie verglaçante légère",
    67: "Pluie verglaçante forte",
    71: "Neige légère",
    73: "Neige modérée",
    75: "Neige forte",
    80: "Averses légères",
    81: "Averses modérées",
    82: "Averses violentes",
    95: "Orage",
    96: "Orage, grêle légère",
    99: "Orage, grêle forte",
}

def get_full_weather(lat, lon):
    """
    Interroge l'API open-meteo pour récupérer, à l'heure la plus proche :
      - temperature_2m (°C)
      - cloudcover (%)
      - weathercode
      - precipitation (mm)
      - snowfall (cm)
      - time (ISO string)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":  lat,
        "longitude": lon,
        "timezone":  "auto",
        "hourly":    "temperature_2m,cloudcover,weathercode,precipitation,snowfall"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # on prend le premier indice de chaque liste (heure la plus proche)
    tm    = data["hourly"]["time"][0]
    temp  = data["hourly"]["temperature_2m"][0]
    cc    = data["hourly"]["cloudcover"][0]
    code  = data["hourly"]["weathercode"][0]
    rain  = data["hourly"]["precipitation"][0]
    snow  = data["hourly"]["snowfall"][0]

    return temp, cc, code, rain, snow, tm

def get_temp_and_weather(lat, lon):
    """
    Renvoie (temperature, description_meteo) pour la position donnée.
    Si le code météo n'est pas connu, la description vaut 'Inconnu'.
    """
    temp, _, code, _, _, _ = get_full_weather(lat, lon)
    desc = WEATHER_DESC.get(code, "Inconnu")
    return temp, desc

if __name__ == "__main__":
    lat, lon = 48.85, 2.35
    temperature, meteo = get_temp_and_weather(lat, lon)
    print(f"T° à {lat},{lon} → {temperature}°C, météo : {meteo}")
