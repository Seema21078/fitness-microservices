import psycopg2
import os
import csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL_SYNC")

# Define the file paths for each table
DATA_FILES = {
    "users": "data/users_updated1.csv",
    "activity": "data/activity.csv",
    "mood": "data/mood.csv",
}

def insert_data_from_csv(table_name, file_path, insert_query):
    """Reads CSV file and inserts data into the corresponding table."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            cur.executemany(insert_query, reader)

        conn.commit()
        cur.close()
        conn.close()
        print(f"Data inserted into {table_name} successfully!")
    
    except Exception as e:
        print(f"Error inserting data into {table_name}:", e)

# Insert queries for each table
INSERT_QUERIES = {
    "users": "INSERT INTO user_service.users (user_id, name, age, gender, weight, email, password_hash,role) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)",
    "activity": "INSERT INTO activity_service.activity_data (user_id, date, steps, calories_burned, distance_km, active_minutes, workout_type) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    "mood": "INSERT INTO mood_service.mood_data (user_id, date, heart_rate_avg, sleep_hours, mood, weather_conditions, location) VALUES (%s, %s, %s, %s, %s, %s, %s)",
}

# Execute data insertion for each table
for table, file_path in DATA_FILES.items():
    insert_data_from_csv(table, file_path, INSERT_QUERIES[table])
