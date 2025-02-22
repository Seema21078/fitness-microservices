import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL_SYNC")

def execute_sql_file():
    """Reads and executes init.sql to set up the database schema."""
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Read and execute init.sql
        with open("database/init.sql", "r") as file:
            sql_script = file.read()
            cursor.execute(sql_script)

        # Commit changes and close connection
        conn.commit()
        cursor.close()
        conn.close()
        print("Database setup completed successfully!")

    except Exception as e:
        print(f"Error executing init.sql: {e}")

# Run the function
if __name__ == "__main__":
    execute_sql_file()
