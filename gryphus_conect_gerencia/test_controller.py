import os, sys
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd
from src.core.controller import IngestaController

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
controller = IngestaController(supabase)

success, msg = controller.procesar_ingesta('test_obras.xlsx', 'Obra Test', '')
print("Success:", success)
print("Message:", msg)
