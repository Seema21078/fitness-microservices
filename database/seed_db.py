import psycopg2
import os
import csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Define the file paths for each table
DATA_FILES = {
    "users": "database/data/users.csv",
    "activity": "database/data/activity.csv",
    "mood": "database/data/mood.csv",
    "notifications": "database/data/notifications.csv",
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
    "users": "INSERT INTO activity_service.users (user_id, name, age, gender, weight) VALUES (%s, %s, %s, %s, %s)",
    "activity": "INSERT INTO activity_service.activity (user_id, date, steps, calories_burned, distance_km, active_minutes, workout_type) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    "mood": "INSERT INTO ml_mood_service.mood (user_id, date, mood) VALUES (%s, %s, %s)",
    "notifications": "INSERT INTO notification_service.notifications (user_id, timestamp, message) VALUES (%s, %s, %s)",
}

# Execute data insertion for each table
for table, file_path in DATA_FILES.items():
    insert_data_from_csv(table, file_path, INSERT_QUERIES[table])
