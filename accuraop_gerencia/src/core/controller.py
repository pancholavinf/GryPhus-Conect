import os
import uuid
import pandas as pd
import datetime
from supabase import Client

def safe_float(val):
    if pd.isna(val) or val is None: return 0.0
    try:
        if isinstance(val, str):
            val = val.strip()
            if not val: return 0.0
        return float(val)
    except:
        return 0.0

def safe_int(val):
    if pd.isna(val) or val is None: return 0
    try:
        if isinstance(val, str):
            val = val.strip()
            if not val: return 0
        return int(float(val))
    except:
        return 0

def safe_str(val):
    if pd.isna(val) or val is None: return ""
    return str(val).strip()

class IngestaController:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def procesar_ingesta(self, file_path: str, nombre_obra: str, jefe_obra_id: str, precios_materiales: dict = None, color_obra: str = "#59789F"):
        """
        Orquesta el flujo: Crear Obra -> Subir Archivos -> Parsear Excel -> Insertar Items -> Asignar Jefe
        """
        if not file_path or not nombre_obra:
            return False, "Faltan datos obligatorios (Archivo o Nombre de Obra)."
        
        # 1. Crear Obra con estado "Activa"
        obra_id = str(uuid.uuid4())
        obra_data = {
            "id": obra_id,
            "nombre": nombre_obra,
            "estado": "Activa",
            "color": color_obra,
            "fecha_creacion": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        try:
            obra_res = self.supabase.table("obras").insert(obra_data).execute()
            if not obra_res.data:
                return False, "No se pudo crear la obra en la base de datos."
        except Exception as e:
            return False, f"Error al crear la obra: {str(e)}"

        # 2. Subir archivo a Storage
        try:
            file_name = os.path.basename(file_path)
            storage_path = f"obras/{obra_id}/{file_name}"
            # Subir al bucket unificado 'accuratek-data' en la subcarpeta obras/
            with open(file_path, 'rb') as f:
                self.supabase.storage.from_("accuratek-data").upload(storage_path, f)
        except Exception as e:
            # Continuamos aunque falle la subida
            print(f"Advertencia: No se pudo subir el archivo: {e}")

        # 3. Parsear el Excel ("CUBICACION", ignorar 8 filas)
        try:
            columnas_interes = [
                "UBICACIÓN", "PLANO", "DESCRIPCIÓN EN PLANO", "ESTRUCTURA", "DIMENSIONES",
                "PERFIL", "CANT.", "CANTIDAD ESTRUCTURAS", "LARGO\n[mm]", "CARAS EXPTAS.",
                "PERÍMETRO EXPUESTO\n[mm]", "RESIST. AL FUEGO", "MASIV. (M-1)",
                "ÁREA EXPUESTA\n[m2]", "MATERIAL", "CERTIFICACION", "MICRAS",
                "FORMULA", "TINETAS", "ESPESOR (mm)", "SACOS", "ANOTACIONES"
            ]
            # skiprows=7 ignora las filas 0-6, empieza a leer en la fila 8
            df = pd.read_excel(file_path, sheet_name="CUBICACION", skiprows=7, usecols=columnas_interes)
            df.dropna(subset=['UBICACIÓN'], inplace=True)
        except Exception as e:
            # Rollback simple de Obra si falla el excel
            self.supabase.table("obras").delete().eq("id", obra_id).execute()
            return False, f"Error al leer la hoja 'CUBICACION' del Excel: {str(e)}"

        # 4. Insertar Ítems
        try:
            df = df.where(pd.notnull(df), None) # Convertir NaN a None
            
            items_to_insert = []
            for index, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Mapeo de columnas: Ajustar según los nombres reales en el Excel
                material_val = safe_str(row_dict.get("MATERIAL"))
                precio_unit = precios_materiales.get(material_val, 0.0) if precios_materiales else 0.0
                
                item = {
                    "id": str(uuid.uuid4()),
                    "obra_id": obra_id,
                    "ubicacion": safe_str(row_dict.get("UBICACIÓN")),
                    "plano": safe_str(row_dict.get("PLANO")),
                    "descripcion_plano": safe_str(row_dict.get("DESCRIPCIÓN EN PLANO")),
                    "estructura": safe_str(row_dict.get("ESTRUCTURA")),
                    "dimension": safe_str(row_dict.get("DIMENSIONES")),
                    "perfil": safe_str(row_dict.get("PERFIL")),
                    "cantidad": safe_float(row_dict.get("CANT.")),
                    "cantidad_estructuras": safe_float(row_dict.get("CANTIDAD ESTRUCTURAS")),
                    "largo_mm": safe_float(row_dict.get("LARGO\n[mm]")),
                    "caras_expuestas": safe_int(row_dict.get("CARAS EXPTAS.")),
                    "perimetro_expuesto_mm": safe_float(row_dict.get("PERÍMETRO EXPUESTO\n[mm]")),
                    "resist_fuego": safe_str(row_dict.get("RESIST. AL FUEGO")),
                    "masividad_m1": safe_float(row_dict.get("MASIV. (M-1)")),
                    "area_expuesta_m2": safe_float(row_dict.get("ÁREA EXPUESTA\n[m2]")),
                    "material": material_val,
                    "certificacion": safe_str(row_dict.get("CERTIFICACION")),
                    "micras": safe_float(row_dict.get("MICRAS")),
                    "formula": safe_str(row_dict.get("FORMULA")),
                    "tinetas": safe_float(row_dict.get("TINETAS")),
                    "espesor_mm": safe_float(row_dict.get("ESPESOR (mm)")),
                    "sacos": safe_float(row_dict.get("SACOS")),
                    "anotaciones": safe_str(row_dict.get("ANOTACIONES")),
                    "precio_unitario_contrato": precio_unit
                }
                items_to_insert.append(item)

            if items_to_insert:
                self.supabase.table("items_obra").insert(items_to_insert).execute()
        except Exception as e:
            return False, f"Error al insertar ítems de la obra: {str(e)}"

        # 5. Asignar Supervisor
        if jefe_obra_id:
            try:
                asignacion = {
                    "id": str(uuid.uuid4()),
                    "obra_id": obra_id,
                    "jefe_obra_id": jefe_obra_id
                }
                self.supabase.table("obras_jefes_obra").insert(asignacion).execute()
            except Exception as e:
                print(f"Advertencia: No se pudo asignar el supervisor: {e}")

        return True, "Obra, ítems y asignación creados exitosamente."
