import os
import sys
import math
import random
import datetime
import uuid

# Cargar la imagen del logo directamente desde el disco (evita librerías externas de imágenes como Pillow)
LOGO_PATH = os.path.join(os.path.dirname(__file__), "INFO PROYECTO", "LOGOS", "LOGO.png")
LOGO_BYTES = b""

if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_BYTES = f.read()
else:
    # Fallback minimal PNG bytes
    LOGO_BYTES = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4'
        b'\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x03\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82'
    )
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

# Asegurar codificación UTF-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- CONFIGURACIÓN DE ENTORNOS Y CREDENCIALES ---
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xkifhzhqgroemzudzxrf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_Lbkl0KuLm8h2ZaPQAUM7VQ_PVTjSw7W")

EMAIL_JEFE = "tor@lavin.cl"
PASSWORD_JEFE = "123456"
OBRA_ID = "a3c3b202-a183-48ea-b3eb-fb3cae8273aa"  # Obra Antofagasta

TARGET_TOTAL_ADVANCES = 100
PAUSE_INTERVAL = 25
GAUSS_MEAN = 10.0
GAUSS_STDDEV = 3.0

COMENTARIOS_EJEMPLO = [
    "Avanzando según programación del día.",
    "Montaje de estructura completado sin novedades.",
    "Aplicación de recubrimiento intumescente realizada.",
    "Verificación de dimensiones y alineación OK.",
    "Jornada sin inconvenientes técnicos.",
    "Avance registrado por la cuadrilla de la mañana.",
    "Revisión de superficie y sellado finalizado.",
    "Trabajo completado en el sector asignado.",
    "Instalación de perfiles finalizada con éxito.",
    "Inspección visual conforme al plano de detalle."
]

MENSAJES_REPORTE = [
    "Jornada terminada. Trabajos ejecutados conforme a la programación diaria.",
    "Reporte diario: Avances constantes en estructura y pintura intumescente.",
    "Jornada fluida. Se cumplió el objetivo de avance previsto para hoy.",
    "Reporte de avance diario completado. Cuadrillas operativas al 100%.",
    "Jornada finalizada sin incidentes de seguridad y con buen desempeño."
]

def generate_placeholder_image(avance_id, item_code, fecha_str):
    """Retorna los bytes de la imagen del logo (INFO PROYECTO/LOGOS/LOGO.png)."""
    return LOGO_BYTES

def get_workdays_backwards(start_date, num_days_needed):
    """Genera una lista de días laborables (lunes a viernes) hacia atrás."""
    workdays = []
    current = start_date
    while len(workdays) < num_days_needed:
        # 0: Lunes, ..., 4: Viernes, 5: Sábado, 6: Domingo
        if current.weekday() < 5:
            workdays.append(current)
        current -= datetime.timedelta(days=1)
    workdays.reverse()
    return workdays

def main():
    print("=" * 70)
    print("SIMULADOR DE AVANCES Y REPORTES DIARIOS - OBRA ANTOFAGASTA")
    print("=" * 70)
    
    # 1. Autenticación en Supabase
    print(f"[*] Autenticando como Jefe de Obra ({EMAIL_JEFE})...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        auth_resp = supabase.auth.sign_in_with_password({"email": EMAIL_JEFE, "password": PASSWORD_JEFE})
        jefe_obra_id = auth_resp.user.id
        print(f"[+] Autenticación exitosa. User ID: {jefe_obra_id}")
    except Exception as e:
        print(f"[-] Error de autenticación: {e}")
        sys.exit(1)

    # 2. Cargar ítems de la Obra Antofagasta
    print(f"[*] Cargando ítems de la Obra ({OBRA_ID})...")
    res_items = supabase.table("items_obra").select("*").eq("obra_id", OBRA_ID).execute()
    items = res_items.data or []
    
    if not items:
        print("[-] No se encontraron ítems para esta obra en la base de datos.")
        sys.exit(1)
        
    print(f"[+] {len(items)} ítems cargados correctamente.")

    # 3. Cargar materiales disponibles
    res_mat = supabase.table("materiales").select("*").execute()
    materiales = res_mat.data or []
    print(f"[+] {len(materiales)} materiales disponibles en catálogo.")

    # 4. Planificar la distribución de avances por días laborables
    print(f"\n[*] Calculando distribución gaussiana N(mean={GAUSS_MEAN}, std={GAUSS_STDDEV})...")
    random.seed(42)  # Semilla reproducible pero variada
    
    advances_per_day = []
    total_planned = 0
    while total_planned < TARGET_TOTAL_ADVANCES:
        val = int(round(random.gauss(GAUSS_MEAN, GAUSS_STDDEV)))
        val = max(1, val)  # Mínimo 1 avance por día activo
        if total_planned + val > TARGET_TOTAL_ADVANCES:
            val = TARGET_TOTAL_ADVANCES - total_planned
        advances_per_day.append(val)
        total_planned += val

    num_days = len(advances_per_day)
    print(f"[*] Se simularán {num_days} días laborables para alcanzar {TARGET_TOTAL_ADVANCES} avances.")
    
    # Obtener fechas de días hábiles terminando en el día laborable más reciente
    today = datetime.date.today()
    if today.weekday() >= 5:  # Si hoy es fin de semana, retroceder al viernes
        today -= datetime.timedelta(days=(today.weekday() - 4))
        
    workdays = get_workdays_backwards(today, num_days)
    
    # 5. Generar plan detallado de avances y reportes por día
    simulation_schedule = []
    for day_date, count in zip(workdays, advances_per_day):
        day_advances = []
        # Generar horas distribuidas ordenadamente entre 08:30 y 17:30
        times = []
        for _ in range(count):
            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            times.append(datetime.time(hour, minute, second))
        times.sort()
        
        for t in times:
            dt = datetime.datetime.combine(day_date, t)
            item = random.choice(items)
            
            # Cantidad razonable según la cantidad total del ítem
            item_cant = float(item.get("cantidad") or 10.0)
            cant_avance = round(random.uniform(0.5, max(1.0, min(5.0, item_cant / 2.0))), 2)
            
            day_advances.append({
                "id": str(uuid.uuid4()),
                "item": item,
                "cantidad": cant_avance,
                "comentario": random.choice(COMENTARIOS_EJEMPLO),
                "timestamp": dt.isoformat() + "Z"
            })
            
        simulation_schedule.append({
            "date": day_date,
            "advances": day_advances,
            "report_time": datetime.datetime.combine(day_date, datetime.time(18, 0, 0)).isoformat() + "Z"
        })

    # 6. Ejecutar la publicación con Barra de Progreso y Pausas Cada 25 Avances
    print("\n" + "=" * 70)
    print("INICIANDO SUBIDA DE AVANCES Y REPORTES")
    print("=" * 70 + "\n")
    
    published_count = 0
    
    with tqdm(total=TARGET_TOTAL_ADVANCES, desc="Subiendo avances", unit="avance", dynamic_ncols=True) as pbar:
        for day_info in simulation_schedule:
            day_date_str = day_info["date"].strftime("%Y-%m-%d")
            
            # --- Subir Avances del Día ---
            for adv in day_info["advances"]:
                adv_id = adv["id"]
                item = adv["item"]
                ts = adv["timestamp"]
                item_code = f"{item.get('ubicacion', '')} - {item.get('estructura', '')}"
                
                # A. Generar y subir imagen a Supabase Storage
                image_bytes = generate_placeholder_image(adv_id, item_code, ts[:16].replace('T', ' '))
                storage_path = f"avances/{jefe_obra_id}/{adv_id}.png"
                
                try:
                    supabase.storage.from_("accuratek-data").upload(
                        path=storage_path,
                        file=image_bytes,
                        file_options={"upsert": "true", "content-type": "image/png"}
                    )
                    public_url_resp = supabase.storage.from_("accuratek-data").get_public_url(storage_path)
                    foto_url = public_url_resp if isinstance(public_url_resp, str) else storage_path
                except Exception as st_err:
                    foto_url = f"https://placeholder.accuratek.cl/{adv_id}.jpg"
                
                # B. Insertar avance en la BD
                avance_record = {
                    "id": adv_id,
                    "item_obra_id": item["id"],
                    "jefe_obra_id": jefe_obra_id,
                    "foto_url": foto_url,
                    "comentario": adv["comentario"],
                    "cantidad": adv["cantidad"],
                    "fecha_captura_local": ts,
                    "fecha_subida_servidor": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "estado_revision": "pendiente"
                }
                
                res_ins = supabase.table("avances").insert(avance_record).execute()
                published_count += 1
                pbar.update(1)
                
                # C. Verificar Pausa interactiva cada 25 avances
                if published_count % PAUSE_INTERVAL == 0 or published_count == TARGET_TOTAL_ADVANCES:
                    pbar.write(f"\n[PAUSA DE REVISIÓN] Se han publicado {published_count}/{TARGET_TOTAL_ADVANCES} avances.")
                    pbar.write("--> Abre la App de Escritorio ('app_local') o consulta la BD para revisar los datos ingresados.")
                    
                    if published_count < TARGET_TOTAL_ADVANCES:
                        try:
                            input("\n[>] Presiona ENTER en esta consola para continuar con los siguientes avances...")
                        except EOFError:
                            pbar.write("[!] Ejecución en modo no interactivo. Continuando automáticamente...")
                        pbar.write("[>] Reanudando subida...\n")
            
            # --- Subir Reporte Diario de la Jornada ---
            reporte_id = str(uuid.uuid4())
            reporte_record = {
                "id": reporte_id,
                "obra_id": OBRA_ID,
                "jefe_obra_id": jefe_obra_id,
                "tipo_reporte": "actualizacion",
                "mensaje": f"[{day_date_str}] " + random.choice(MENSAJES_REPORTE),
                "archivos_adjuntos": [],
                "fecha_publicacion": day_info["report_time"],
                "estado_reb": "pendiente",
                "respuesta": False,
                "mensaje_respuesta": None
            }
            supabase.table("reporte_obra").insert(reporte_record).execute()
            
            # --- Subir Consumos de Materiales para el Reporte ---
            if materiales:
                num_consumos = random.randint(1, 3)
                mats_seleccionados = random.sample(materiales, min(num_consumos, len(materiales)))
                
                consumos_records = []
                for m in mats_seleccionados:
                    cant_mat = round(random.uniform(2.0, 15.0), 1)
                    consumos_records.append({
                        "id": str(uuid.uuid4()),
                        "reporte_obra_id": reporte_id,
                        "material_id": m.get("id"),
                        "material": m.get("nombre", "Material de Obra"),
                        "cantidad": cant_mat,
                        "unidad": m.get("unidad_medida", "unidades"),
                        "fecha": day_info["report_time"]
                    })
                
                if consumos_records:
                    supabase.table("reporte_obra_consumos").insert(consumos_records).execute()

    print("\n" + "=" * 70)
    print(f"SIMULACIÓN COMPLETADA EXITOSAMENTE: {published_count} avances publicados.")
    print(f"Total de días laborables simulados: {num_days} días con sus reportes diarios y consumos.")
    print("=" * 70)

if __name__ == "__main__":
    main()
