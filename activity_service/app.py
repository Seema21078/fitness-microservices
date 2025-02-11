from db import get_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    cursor.execute("SELECT NOW();")  # Example query
    print(cursor.fetchone())
    conn.close()
