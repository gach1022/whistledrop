import os
import psycopg2

SERVER_DB_URL = os.environ.get('SERVER_DB_URL')
JOURNALIST_DB_URL = os.environ.get('JOURNALIST_DB_URL')

def migrate_serverdb():
    with psycopg2.connect(SERVER_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public_keys (
                    id SERIAL PRIMARY KEY,
                    public_key TEXT NOT NULL,
                    used BOOLEAN DEFAULT FALSE
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_encrypted BYTEA NOT NULL,
                    aes_key_encrypted BYTEA NOT NULL,
                    public_key_id INTEGER REFERENCES public_keys(id),
                    uploaded_at TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
    print("Server-DB Migration fertig.")

def migrate_journalistdb():
    with psycopg2.connect(JOURNALIST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS keypairs (
                    id SERIAL PRIMARY KEY,
                    public_key TEXT NOT NULL,
                    private_key TEXT NOT NULL
                );
            """)
        conn.commit()
    print("Journalist-DB Migration fertig.")

if __name__ == '__main__':
    migrate_serverdb()
    migrate_journalistdb()
    print("Migration abgeschlossen!")