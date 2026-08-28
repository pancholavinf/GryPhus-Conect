import os
import json
from supabase import create_client

# Read .env manually
env_vars = {}
with open(r'C:\Users\fcola\Desktop\APPACCURATEK\.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env_vars[k.strip()] = v.strip()

url = env_vars.get('SUPABASE_URL')
key = env_vars.get('SUPABASE_KEY')

print(f"Connecting to Supabase: {url}")
supabase = create_client(url, key)

tables = [
    'obras', 'perfiles_usuario', 'obras_jefes_obra', 'items_obra',
    'avances', 'reporte_obra', 'reporte_obra_consumos', 'materiales',
    'tipos_maestro', 'maestros', 'obras_maestros', 'asistencia_diaria', 'asistencia_diaria_detalle'
]

results = {}

for table in tables:
    try:
        res = supabase.table(table).select('*').limit(3).execute()
        sample = res.data[0] if res.data else None
        columns = list(sample.keys()) if sample else []
        results[table] = {
            'exists': True,
            'row_count_sample': len(res.data),
            'columns': columns,
            'sample_row': sample
        }
    except Exception as e:
        results[table] = {
            'exists': False,
            'error': str(e)
        }

print(json.dumps(results, indent=2, default=str))
