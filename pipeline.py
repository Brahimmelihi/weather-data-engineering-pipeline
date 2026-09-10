import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 1. Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "weather_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# List of cities to collect weather data for
CITIES = ["Casablanca", "Rabat", "Marrakech", "Agadir", "Tangier"]

# 2. EXTRACT PHASE: Fetch raw data from OpenWeatherMap API
def extract_weather_data(cities, api_key):
    print(" Getting weather data from OpenWeatherMap API...")
    raw_data = []
    for city in cities:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            raw_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch data for {city}: {response.status_code}")
    return raw_data

# 3. TRANSFORM PHASE: Clean and structure data using Pandas
def transform_weather_data(raw_data_list):
    print(" Transforming and cleaning data with Pandas...")
    transformed_records = []
    
    for item in raw_data_list:
        record = {
            "city": item.get("name"),
            "country": item.get("sys", {}).get("country"),
            "temperature_celsius": round(item.get("main", {}).get("temp", 0) - 273.15, 2), # Convert Kelvin to Celsius
            "feels_like_celsius": round(item.get("main", {}).get("feels_like", 0) - 273.15, 2),
            "humidity_percent": item.get("main", {}).get("humidity"),
            "pressure_hpa": item.get("main", {}).get("pressure"),
            "weather_description": item.get("weather", [{}])[0].get("description"),
            "wind_speed_m_s": item.get("wind", {}).get("speed"),
            "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        transformed_records.append(record)
        
    df = pd.DataFrame(transformed_records)
    return df

# 4. LOAD PHASE: Save transformed data into PostgreSQL Database
def load_to_postgresql(df):
    print(" Loading clean data into PostgreSQL Database...")
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)
    
    # Write DataFrame directly to PostgreSQL table 'weather_metrics'
    df.to_sql("weather_metrics", con=engine, if_exists="append", index=False)
    print(" Data successfully loaded to database!")

# MAIN ENTRY POINT
if __name__ == "__main__":
    if not API_KEY or API_KEY == "your_openopenweathermap_api_key_here":
        print(" Error: Please set your OpenWeatherMap API_KEY in .env file!")
    else:
        # Execute ETL Pipeline
        raw = extract_weather_data(CITIES, API_KEY)
        if raw:
            clean_df = transform_weather_data(raw)
            print("\nPreview of Processed Data:")
            print(clean_df.head())
            
            # Uncomment below to store in PostgreSQL when your database is active:
            # load_to_postgresql(clean_df)
