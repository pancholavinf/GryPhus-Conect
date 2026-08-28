import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

dotenv_path = "C:/Users/fcola/Desktop/APPACCURATEK/.env"
load_dotenv(dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def dump_queries(client_name, client):
    print(f"\n===== Queries using {client_name} =====")
    for table in ["perfiles_usuario", "obras", "obras_jefes_obra", "items_obra", "avances", "estados_pago"]:
        try:
            res = client.table(table).select("*").execute()
            print(f"Table {table}: {len(res.data)} rows")
            if res.data:
                print(f"  First row: {json.dumps(res.data[0], indent=2, default=str)}")
        except Exception as e:
            print(f"Table {table} failed: {e}")

# 1. Query as anon
dump_queries("Anon Client", supabase)

# 2. Query as test@test.cl
print("\nLogging in as test@test.cl...")
try:
    login_res = supabase.auth.sign_in_with_password({
        "email": "test@test.cl",
        "password": "123456"
    })
    print(f"Logged in. User ID: {login_res.user.id}")
    dump_queries("test@test.cl Client", supabase)
    supabase.auth.sign_out()
except Exception as e:
    print(f"Login failed: {e}")

