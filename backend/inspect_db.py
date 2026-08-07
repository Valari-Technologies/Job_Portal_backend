import psycopg2

try:
    conn = psycopg2.connect(
        dbname='job_portal',
        user='postgres',
        password='vetrivinayagar',
        host='localhost',
        port='5432'
    )
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cur.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    for table in [t[0] for t in tables]:
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'")
        cols = cur.fetchall()
        print(f"Table {table} columns:", cols)
        
    cur.close()
    conn.close()
except Exception as e:
    print("Error:", e)
