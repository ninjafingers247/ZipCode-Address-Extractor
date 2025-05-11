import time
import requests
import json
import csv

# Step 1: Load ZIP codes from file
def get_zip_codes(state_file_path):
    with open(state_file_path, 'r') as f:
        data = json.load(f)   
    zip_codes = [entry["zip"] for entry in data]
    return zip_codes

# Step 2: Get lat/lon from ZIP code
def get_lat_lon(zip_codes):
    zip_codes_with_lat_lon = {}
    for zip_code in zip_codes:
        url = f"http://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            place = data['places'][0]
            latitude = float(place['latitude'])
            longitude = float(place['longitude'])
            zip_codes_with_lat_lon[zip_code] = (latitude, longitude)
        else:
            zip_codes_with_lat_lon[zip_code] = (None, None)
        time.sleep(1)
        print(f"Zip code: {zip_code}, Latitude: {zip_codes_with_lat_lon[zip_code][0]}, Longitude: {zip_codes_with_lat_lon[zip_code][1]}")
    print("Finished fetching lat/lon for all ZIP codes.")
    return zip_codes_with_lat_lon

# Step 3: Generate offset points
def generate_offsets(center_lat, center_lon, offset_lat=0.03, offset_lon=0.03):
    return [
        (center_lat, center_lon),
        (center_lat + offset_lat, center_lon + offset_lon),
        (center_lat - offset_lat, center_lon - offset_lon),
        (center_lat + offset_lat, center_lon - offset_lon),
        (center_lat - offset_lat, center_lon + offset_lon)
    ]

# Step 4: Reverse geocode lat/lon → address + state
def reverse_geocode(lat, lon):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key=YOUR_API_KEY"
    # Replace YOUR_API_KEY with your actual Google Maps API key
    # Make sure to handle the API key securely and not hard-code it in production code
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        if result['results']:
            address = result['results'][0]['formatted_address']
            state = None
            for comp in result['results'][0]['address_components']:
                if 'administrative_area_level_1' in comp['types']:
                    state = comp['long_name']
            return (address, state)
    return ("Failed to fetch", None)

# Step 5: Orchestrate the entire workflow
def run_pipeline():
    zip_codes = get_zip_codes(r"C:\Users\akshi\Downloads\florida-zip-codes.json")
    zip_coords = get_lat_lon(zip_codes)
    
    with open(r"C:\Users\akshi\Documents\fl_zip_anchor_addresses.csv", "w", newline='', encoding="utf-8") as csvfile:
        fieldnames = ["ZIP", "Lat", "Lon", "Address"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for zip_code, (lat, lon) in zip_coords.items():
            if lat is None or lon is None:
                continue
            points = generate_offsets(lat, lon)
            for p_lat, p_lon in points:
                addr, state = reverse_geocode(p_lat, p_lon)
                if state == "Florida":  # Ensures we don't cross state lines
                    writer.writerow({
                        "ZIP": zip_code,
                        "Lat": p_lat,
                        "Lon": p_lon,
                        "Address": addr
                    })
                time.sleep(1)
                print(f"ZIP: {zip_code}, Lat: {p_lat}, Lon: {p_lon}, Address: {addr}")
    print("Finished writing to CSV.")

run_pipeline()
