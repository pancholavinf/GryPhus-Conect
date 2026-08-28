from PyQt6.QtCore import QThread, pyqtSignal, QSettings
from supabase import Client
import pandas as pd
import uuid
import datetime
import os
from src.core.data_manager import DataManager

class LoginWorker(QThread):
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, email: str, password: str):
        super().__init__()
        self.supabase = supabase
        self.email = email
        self.password = password

    def run(self):
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": self.email,
                "password": self.password
            })
            if response and response.user:
                # Validación definitiva mediante BD
                rol = ""
                try:
                    res = self.supabase.table("perfiles_usuario").select("rol").eq("id", response.user.id).execute()
                    if res.data and len(res.data) > 0:
                        rol = res.data[0].get("rol", "")
                except Exception:
                    pass
                
                # Hint/Optimización en caso de fallo al consultar BD
                if not rol:
                    user_meta = response.user.user_metadata or {}
                    if "rol" in user_meta:
                        rol = user_meta.get("rol")
                
                if rol and str(rol).lower() == "jefe_obra":
                    self.supabase.auth.sign_out()
                    self.error.emit("Acceso denegado: Los Supervisores no pueden acceder a la aplicación de escritorio.")
                    return
                
                # Guardar sesión en QSettings para auto-login futuro
                try:
                    settings = QSettings("Accuratek", "TrabsGerencia")
                    if hasattr(response, "session") and response.session and response.session.refresh_token:
                        settings.setValue("auth/refresh_token", response.session.refresh_token)
                    settings.setValue("auth/saved_email", self.email)
                except Exception as e_set:
                    print(f"Advertencia al guardar sesión en QSettings: {e_set}")
                
                self.success.emit()
            else:
                self.error.emit("No se pudo autenticar el usuario.")
        except Exception as e:
            self.error.emit(f"Credenciales incorrectas o error de red: {str(e)}")


class SessionCheckWorker(QThread):
    valid = pyqtSignal()
    invalid = pyqtSignal()

    def __init__(self, supabase: Client):
        super().__init__()
        self.supabase = supabase

    def run(self):
        try:
            if not self.supabase:
                self.invalid.emit()
                return

            settings = QSettings("Accuratek", "TrabsGerencia")
            saved_refresh_token = settings.value("auth/refresh_token", "")

            session = None
            try:
                session = self.supabase.auth.get_session()
            except Exception:
                session = None

            # Si no hay sesión en memoria pero tenemos token guardado, refrescar la sesión
            if not session and saved_refresh_token:
                try:
                    refreshed = self.supabase.auth.refresh_session(saved_refresh_token)
                    if refreshed and hasattr(refreshed, "session") and refreshed.session:
                        session = refreshed.session
                        # Actualizar el nuevo refresh_token
                        settings.setValue("auth/refresh_token", session.refresh_token)
                except Exception as e_ref:
                    print(f"No se pudo refrescar la sesión guardada: {e_ref}")
                    settings.remove("auth/refresh_token")
                    self.invalid.emit()
                    return

            if session and session.user:
                user = session.user
                # Validación definitiva de rol mediante BD
                rol = ""
                try:
                    res = self.supabase.table("perfiles_usuario").select("rol").eq("id", user.id).execute()
                    if res.data and len(res.data) > 0:
                        rol = res.data[0].get("rol", "")
                except Exception:
                    pass
                
                # Hint/Optimización en caso de fallo
                if not rol:
                    user_meta = user.user_metadata or {}
                    if "rol" in user_meta:
                        rol = user_meta.get("rol")
                
                if rol and str(rol).lower() == "jefe_obra":
                    self.supabase.auth.sign_out()
                    settings.remove("auth/refresh_token")
                    self.invalid.emit()
                    return
                    
                self.valid.emit()
            else:
                if saved_refresh_token:
                    settings.remove("auth/refresh_token")
                self.invalid.emit()
        except Exception as e:
            print(f"Error en SessionCheckWorker: {e}")
            self.invalid.emit()


class LogoutWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, supabase: Client):
        super().__init__()
        self.supabase = supabase

    def run(self):
        try:
            settings = QSettings("Accuratek", "TrabsGerencia")
            settings.remove("auth/refresh_token")
            if self.supabase:
                self.supabase.auth.sign_out()
        except Exception:
            pass
        finally:
            self.finished.emit()


class FetchInitialBatchWorker(QThread):
    progress = pyqtSignal(int, str)
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = True):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            res = dm.fetch_initial_batch(
                progress_callback=lambda pct, msg: self.progress.emit(pct, msg),
                force_refresh=self.force_refresh
            )
            self.success.emit(res)
        except Exception as e:
            self.error.emit(f"Error en la carga inicial de datos: {str(e)}")


class FetchDashboardDataWorker(QThread):
    success = pyqtSignal(list, dict)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            obras, jefes_por_obra = dm.get_dashboard_data(force_refresh=self.force_refresh)
            self.success.emit(obras, jefes_por_obra)
        except Exception as e:
            self.error.emit(f"Error al obtener datos del dashboard: {str(e)}")


class FetchJefesWorker(QThread):
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            jefes = dm.get_jefes(force_refresh=self.force_refresh)
            self.success.emit(jefes)
        except Exception as e:
            self.error.emit(f"Error al cargar supervisores: {str(e)}")


class FetchObrasWorker(QThread):
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client):
        super().__init__()
        self.supabase = supabase

    def run(self):
        try:
            res = self.supabase.table("obras").select("id, nombre").execute()
            self.success.emit(res.data)
        except Exception as e:
            self.error.emit(f"Error al cargar obras: {str(e)}")


class CreateJefeWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, nombre: str, email: str, password: str,
                 rut_dni: str = "", telefono: str = "", foto_perfil_url: str = ""):
        super().__init__()
        self.supabase = supabase
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rut_dni = rut_dni
        self.telefono = telefono
        self.foto_perfil_url = foto_perfil_url

    def run(self):
        if not self.nombre or not self.email or not self.password:
            self.error.emit("Faltan datos obligatorios.")
            return
            
        try:
            auth_res = self.supabase.auth.sign_up({
                "email": self.email,
                "password": self.password,
                "options": {
                    "data": {
                        "nombre": self.nombre,
                        "full_name": self.nombre,
                        "rol": "Jefe_Obra",
                        "telefono": self.telefono,
                        "foto_perfil_url": self.foto_perfil_url
                    }
                }
            })
            
            if not auth_res.user:
                self.error.emit("No se pudo registrar el usuario.")
                return
                
            nuevo_id = auth_res.user.id
            jefe_data = {
                "id": nuevo_id,
                "nombre": self.nombre,
                "rol": "Jefe_Obra",
                "rut_dni": self.rut_dni or None,
                "telefono": self.telefono,
                "foto_perfil_url": self.foto_perfil_url
            }
            
            self.supabase.table("perfiles_usuario").upsert(jefe_data).execute()
            self.success.emit(f"Supervisor '{self.nombre}' creado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al crear Supervisor: {str(e)}")


class AssignJefeWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, obra_id: str, jefe_id: str):
        super().__init__()
        self.supabase = supabase
        self.obra_id = obra_id
        self.jefe_id = jefe_id

    def run(self):
        if not self.obra_id or not self.jefe_id:
            self.error.emit("Debe seleccionar un Jefe y una Obra válidos.")
            return
            
        asignacion = {
            "id": str(uuid.uuid4()),
            "obra_id": self.obra_id,
            "jefe_obra_id": self.jefe_id
        }
        try:
            self.supabase.table("obras_jefes_obra").insert(asignacion).execute()
            self.success.emit("Supervisor asignado a la obra exitosamente.")
        except Exception as e:
            self.error.emit(f"Error en la asignación: {str(e)}")


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

class ProcessIngestaWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, file_path: str, nombre_obra: str, jefe_obra_id: str, precios_materiales: dict, color_obra: str, mapeo_materiales_id: dict):
        super().__init__()
        self.supabase = supabase
        self.file_path = file_path
        self.nombre_obra = nombre_obra
        self.jefe_obra_id = jefe_obra_id
        self.precios_materiales = precios_materiales
        self.color_obra = color_obra
        self.mapeo_materiales_id = mapeo_materiales_id

    def run(self):
        if not self.file_path or not self.nombre_obra:
            self.error.emit("Faltan datos obligatorios (Archivo o Nombre de Obra).")
            return
        
        # 1. Crear Obra
        obra_id = str(uuid.uuid4())
        obra_data = {
            "id": obra_id,
            "nombre": self.nombre_obra,
            "estado": "Activa",
            "color": self.color_obra,
            "fecha_creacion": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        try:
            obra_res = self.supabase.table("obras").insert(obra_data).execute()
            if not obra_res.data:
                self.error.emit("No se pudo crear la obra en la base de datos.")
                return
        except Exception as e:
            self.error.emit(f"Error al crear la obra: {str(e)}")
            return

        # 2. Subir archivo a Storage
        try:
            file_name = os.path.basename(self.file_path)
            storage_path = f"obras/{obra_id}/{file_name}"
            with open(self.file_path, 'rb') as f:
                self.supabase.storage.from_("accuratek-data").upload(storage_path, f)
        except Exception as e:
            print(f"Advertencia: No se pudo subir el archivo: {e}")

        # 3. Parsear el Excel
        try:
            columnas_interes = [
                "UBICACIÓN", "PLANO", "DESCRIPCIÓN EN PLANO", "ESTRUCTURA", "DIMENSIONES",
                "PERFIL", "CANT.", "CANTIDAD ESTRUCTURAS", "LARGO\n[mm]", "CARAS EXPTAS.",
                "PERÍMETRO EXPUESTO\n[mm]", "RESIST. AL FUEGO", "MASIV. (M-1)",
                "ÁREA EXPUESTA\n[m2]", "MATERIAL", "CERTIFICACION", "MICRAS",
                "FORMULA", "TINETAS", "ESPESOR (mm)", "SACOS", "ANOTACIONES"
            ]
            df = pd.read_excel(self.file_path, sheet_name="CUBICACION", skiprows=7, usecols=columnas_interes)
            df.dropna(subset=['UBICACIÓN'], inplace=True)
        except Exception as e:
            try:
                self.supabase.table("obras").delete().eq("id", obra_id).execute()
            except:
                pass
            self.error.emit(f"Error al leer la hoja 'CUBICACION' del Excel: {str(e)}")
            return

        # 4. Insertar Ítems
        try:
            df = df.where(pd.notnull(df), None)
            
            items_to_insert = []
            for index, row in df.iterrows():
                row_dict = row.to_dict()
                
                material_val = safe_str(row_dict.get("MATERIAL"))
                precio_unit = self.precios_materiales.get(material_val, 0.0) if self.precios_materiales else 0.0
                mat_id = self.mapeo_materiales_id.get(material_val)
                
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
                    "material_id": mat_id,
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
                # Subir en chunks si es muy grande para no exceder límites
                chunk_size = 500
                for i in range(0, len(items_to_insert), chunk_size):
                    chunk = items_to_insert[i:i + chunk_size]
                    self.supabase.table("items_obra").insert(chunk).execute()
        except Exception as e:
            self.error.emit(f"Error al insertar ítems de la obra: {str(e)}")
            return

        # 5. Asignar Supervisor
        if self.jefe_obra_id:
            try:
                asignacion = {
                    "id": str(uuid.uuid4()),
                    "obra_id": obra_id,
                    "jefe_obra_id": self.jefe_obra_id
                }
                self.supabase.table("obras_jefes_obra").insert(asignacion).execute()
            except Exception as e:
                print(f"Advertencia: No se pudo asignar el supervisor: {e}")

        self.success.emit("Obra, ítems y asignación creados exitosamente.")


class FetchObraDetailsWorker(QThread):
    success = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, obra_id: str, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.obra_id = obra_id
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            items, avances = dm.get_obra_details(self.obra_id, force_refresh=self.force_refresh)
            self.success.emit(items, avances)
        except Exception as e:
            self.error.emit(f"Error al cargar detalles de la obra: {str(e)}")


class FetchReportesWorker(QThread):
    success = pyqtSignal(list, list, list, list, list)  # reportes, consumos, materiales, items, avances
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            reps, consumos, materiales, items, avances = dm.get_reportes(force_refresh=self.force_refresh)
            self.success.emit(reps, consumos, materiales, items, avances)
        except Exception as e:
            self.error.emit(f"Error al cargar reportes: {str(e)}")


class RespondReporteWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, reporte_id: str, mensaje_respuesta: str, marcar_solo_leido: bool = False):
        super().__init__()
        self.supabase = supabase
        self.reporte_id = reporte_id
        self.mensaje_respuesta = mensaje_respuesta
        self.marcar_solo_leido = marcar_solo_leido

    def run(self):
        try:
            if self.marcar_solo_leido:
                update_data = {
                    "estado_reb": "leido"
                }
            else:
                update_data = {
                    "estado_reb": "respondido",
                    "respuesta": True,
                    "mensaje_respuesta": self.mensaje_respuesta
                }

            self.supabase.table("reporte_obra").update(update_data).eq("id", self.reporte_id).execute()
            status_text = "leído" if self.marcar_solo_leido else "respondido"
            self.success.emit(f"Reporte marcado como {status_text} exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al responder al reporte: {str(e)}")


class FetchEDPHistorialWorker(QThread):
    finished = pyqtSignal(list, dict, list, list) # historial, edp_meta_preview, items_detail, candidato_avances_ids
    error = pyqtSignal(str)

    def __init__(self, edp_controller, obra_id, periodo_desde=None, periodo_hasta=None):
        super().__init__()
        self.controller = edp_controller
        self.obra_id = obra_id
        self.periodo_desde = periodo_desde
        self.periodo_hasta = periodo_hasta

    def run(self):
        try:
            historial = self.controller.get_historial_edps(self.obra_id)
            meta, items, candidatos = self.controller.fetch_edp_preview_data(self.obra_id, self.periodo_desde, self.periodo_hasta)
            self.finished.emit(historial, meta, items, candidatos)
        except Exception as e:
            self.error.emit(str(e))


class EmitEDPWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, edp_controller, obra_id, periodo_desde, periodo_hasta,
                 retencion_pct=0.05, anticipo_monto=0.0, user_id=None):
        super().__init__()
        self.controller = edp_controller
        self.obra_id = obra_id
        self.periodo_desde = periodo_desde
        self.periodo_hasta = periodo_hasta
        self.retencion_pct = retencion_pct
        self.anticipo_monto = anticipo_monto
        self.user_id = user_id

    def run(self):
        try:
            success, res = self.controller.emit_estado_pago(
                self.obra_id,
                self.periodo_desde,
                self.periodo_hasta,
                self.retencion_pct,
                self.anticipo_monto,
                user_id=self.user_id
            )
            if success:
                self.finished.emit(res)
            else:
                self.error.emit(str(res))
        except Exception as e:
            self.error.emit(str(e))


class FetchMaterialesWorker(QThread):
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            mats = dm.get_materiales(force_refresh=self.force_refresh)
            self.success.emit(mats)
        except Exception as e:
            self.error.emit(f"Error al cargar materiales: {str(e)}")


class SaveMaterialWorker(QThread):
    success = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, data: dict, is_new: bool = False):
        super().__init__()
        self.supabase = supabase
        self.data = data
        self.is_new = is_new

    def run(self):
        try:
            if self.is_new:
                if "id" not in self.data or not self.data["id"]:
                    self.data["id"] = str(uuid.uuid4())
                res = self.supabase.table("materiales").insert(self.data).execute()
                msg = f"Material '{self.data.get('nombre')}' creado con éxito."
            else:
                mat_id = self.data.get("id")
                res = self.supabase.table("materiales").update(self.data).eq("id", mat_id).execute()
                msg = f"Material '{self.data.get('nombre')}' actualizado con éxito."

            DataManager(self.supabase).invalidate_cache("materiales")
            saved_item = res.data[0] if res.data else self.data
            self.success.emit(saved_item, msg)
        except Exception as e:
            self.error.emit(f"Error al guardar material: {str(e)}")


class UploadMaterialFileWorker(QThread):
    success = pyqtSignal(str, str) # file_url, file_type
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, local_filepath: str, file_type: str):
        super().__init__()
        self.supabase = supabase
        self.local_filepath = local_filepath
        self.file_type = file_type  # 'foto', 'ficha', 'estudio'

    def run(self):
        try:
            if not self.local_filepath or not os.path.exists(self.local_filepath):
                self.error.emit("El archivo local seleccionado no existe o no se puede leer.")
                return

            file_name = os.path.basename(self.local_filepath)
            ext = os.path.splitext(file_name)[1].lower()
            unique_name = f"{self.file_type}_{uuid.uuid4().hex[:8]}{ext}"
            storage_path = f"materiales/{self.file_type}s/{unique_name}"

            # Content type detection
            content_type = "application/octet-stream"
            if ext == ".pdf": content_type = "application/pdf"
            elif ext in [".png"]: content_type = "image/png"
            elif ext in [".jpg", ".jpeg"]: content_type = "image/jpeg"
            elif ext in [".webp"]: content_type = "image/webp"

            with open(self.local_filepath, 'rb') as f:
                file_bytes = f.read()

            self.supabase.storage.from_("accuratek-data").upload(
                path=storage_path,
                file=file_bytes,
                file_options={"upsert": "true", "content-type": content_type}
            )

            # Obtener URL pública
            public_url = self.supabase.storage.from_("accuratek-data").get_public_url(storage_path)
            self.success.emit(public_url, self.file_type)
        except Exception as e:
            self.error.emit(f"Error al subir archivo a Supabase Storage: {str(e)}")



class DeleteMaterialWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, material_id: str):
        super().__init__()
        self.supabase = supabase
        self.material_id = material_id

    def run(self):
        try:
            self.supabase.table("materiales").delete().eq("id", self.material_id).execute()
            self.success.emit("Material eliminado correctamente.")
        except Exception as e:
            self.error.emit(f"Error al eliminar material: {str(e)}")


# =============================================================================
# WORKERS — CONTROL DE PERSONAL: TIPOS DE MAESTRO
# =============================================================================

class FetchTiposMaestroWorker(QThread):
    """Carga todos los tipos/cargos de maestro ordenados por nombre."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            tipos = dm.get_tipos_maestro(force_refresh=self.force_refresh)
            self.success.emit(tipos)
        except Exception as e:
            self.error.emit(f"Error al cargar tipos de maestro: {str(e)}")


class CreateTipoMaestroWorker(QThread):
    """Crea un nuevo tipo/cargo de maestro."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, nombre: str, sueldo_diario: float):
        super().__init__()
        self.supabase = supabase
        self.nombre = nombre
        self.sueldo_diario = sueldo_diario

    def run(self):
        if not self.nombre:
            self.error.emit("El nombre del cargo no puede estar vacío.")
            return
        if self.sueldo_diario < 0:
            self.error.emit("El sueldo diario no puede ser negativo.")
            return
        try:
            data = {
                "id": str(uuid.uuid4()),
                "nombre": self.nombre,
                "sueldo_diario": self.sueldo_diario,
            }
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("tipos_maestro").insert(data))
            dm.invalidate_cache()
            self.success.emit(f"Cargo '{self.nombre}' creado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al crear cargo: {str(e)}")


class UpdateTipoMaestroWorker(QThread):
    """Actualiza nombre y sueldo_diario de un tipo de maestro existente."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, tipo_id: str, nombre: str, sueldo_diario: float):
        super().__init__()
        self.supabase = supabase
        self.tipo_id = tipo_id
        self.nombre = nombre
        self.sueldo_diario = sueldo_diario

    def run(self):
        try:
            dm = DataManager(self.supabase)
            dm.execute_safe(
                self.supabase.table("tipos_maestro").update({
                    "nombre": self.nombre,
                    "sueldo_diario": self.sueldo_diario,
                }).eq("id", self.tipo_id)
            )
            dm.invalidate_cache()
            self.success.emit(f"Cargo '{self.nombre}' actualizado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al actualizar cargo: {str(e)}")


class DeleteTipoMaestroWorker(QThread):
    """Elimina un tipo de maestro por ID."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, tipo_id: str):
        super().__init__()
        self.supabase = supabase
        self.tipo_id = tipo_id

    def run(self):
        try:
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("tipos_maestro").delete().eq("id", self.tipo_id))
            dm.invalidate_cache()
            self.success.emit("Cargo eliminado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al eliminar cargo: {str(e)}")


# =============================================================================
# WORKERS — CONTROL DE PERSONAL: MAESTROS
# =============================================================================

class FetchMaestrosWorker(QThread):
    """Carga todos los maestros con su tipo/cargo anidado."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            maestros = dm.get_maestros(force_refresh=self.force_refresh)
            self.success.emit(maestros)
        except Exception as e:
            self.error.emit(f"Error al cargar maestros: {str(e)}")


class CreateMaestroWorker(QThread):
    """Crea un nuevo maestro."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, nombre: str, rut_dni: str, tipo_maestro_id: str,
                 telefono: str = "", foto_perfil_url: str = ""):
        super().__init__()
        self.supabase = supabase
        self.nombre = nombre
        self.rut_dni = rut_dni
        self.tipo_maestro_id = tipo_maestro_id
        self.telefono = telefono
        self.foto_perfil_url = foto_perfil_url

    def run(self):
        if not self.nombre or not self.tipo_maestro_id:
            self.error.emit("Nombre y Cargo son obligatorios.")
            return
        try:
            data = {
                "id": str(uuid.uuid4()),
                "nombre": self.nombre,
                "rut_dni": self.rut_dni or None,
                "tipo_maestro_id": self.tipo_maestro_id,
                "telefono": self.telefono or None,
                "foto_perfil_url": self.foto_perfil_url or None,
                "estado": "Activo",
                "fecha_creacion": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("maestros").insert(data))
            dm.invalidate_cache()
            self.success.emit(f"Maestro '{self.nombre}' creado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al crear maestro: {str(e)}")


class AssignMaestroObraWorker(QThread):
    """Asigna un maestro a una obra (upsert para evitar duplicados)."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, obra_id: str, maestro_id: str):
        super().__init__()
        self.supabase = supabase
        self.obra_id = obra_id
        self.maestro_id = maestro_id

    def run(self):
        if not self.obra_id or not self.maestro_id:
            self.error.emit("Seleccione un maestro y una obra válidos.")
            return
        try:
            data = {
                "obra_id": self.obra_id,
                "maestro_id": self.maestro_id,
                "fecha_asignacion": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("obras_maestros").upsert(data))
            dm.invalidate_cache()
            self.success.emit("Maestro asignado a la obra exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al asignar maestro: {str(e)}")


class FetchMaestrosByObraWorker(QThread):
    """Carga todos los maestros asignados a una obra específica."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, obra_id: str):
        super().__init__()
        self.supabase = supabase
        self.obra_id = obra_id

    def run(self):
        try:
            res = self.supabase.table("obras_maestros").select(
                "maestro_id, maestros(id, nombre, rut_dni, estado, tipos_maestro(nombre, sueldo_diario))"
            ).eq("obra_id", self.obra_id).execute()
            maestros = [row["maestros"] for row in (res.data or []) if row.get("maestros")]
            self.success.emit(maestros)
        except Exception as e:
            self.error.emit(f"Error al cargar maestros de la obra: {str(e)}")


# =============================================================================
# WORKERS — ASISTENCIA: DASHBOARD Y REPORTES
# =============================================================================

class FetchDashboardAsistenciaWorker(QThread):
    """Carga métricas de asistencia de HOY para el dashboard principal."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, force_refresh: bool = False):
        super().__init__()
        self.supabase = supabase
        self.force_refresh = force_refresh

    def run(self):
        try:
            dm = DataManager(self.supabase)
            asistencias = dm.get_dashboard_asistencia(force_refresh=self.force_refresh)
            self.success.emit(asistencias)
        except Exception as e:
            self.error.emit(f"Error al cargar asistencia del dashboard: {str(e)}")


class FetchAsistenciaReporteWorker(QThread):
    """Genera reporte de asistencia por obra en un rango de fechas.
    
    Emite success(list, dict) donde list = maestros con totales y dict = resumen global.
    """
    success = pyqtSignal(list, dict)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, obra_id: str, fecha_desde: str, fecha_hasta: str):
        super().__init__()
        self.supabase = supabase
        self.obra_id = obra_id
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta

    def run(self):
        try:
            res_cabs = self.supabase.table("asistencia_diaria").select("id").eq(
                "obra_id", self.obra_id
            ).gte("fecha", self.fecha_desde).lte("fecha", self.fecha_hasta).execute()
            cabeceras = res_cabs.data or []

            if not cabeceras:
                self.success.emit([], {"total_pago": 0, "total_jornales": 0})
                return

            cab_ids = [c["id"] for c in cabeceras]

            res_det = self.supabase.table("asistencia_diaria_detalle").select(
                "maestro_id, valor_jornada, maestros(nombre, tipos_maestro(nombre, sueldo_diario))"
            ).in_("asistencia_id", cab_ids).execute()
            detalles = res_det.data or []

            maestros_map = {}
            for det in detalles:
                mid = det.get("maestro_id")
                if not mid:
                    continue
                val = float(det.get("valor_jornada", 0))
                maestro_data = det.get("maestros") or {}
                tipo_data = maestro_data.get("tipos_maestro") or {}

                if mid not in maestros_map:
                    maestros_map[mid] = {
                        "maestro_id": mid,
                        "maestro_nombre": maestro_data.get("nombre", "Desconocido"),
                        "tipo_nombre": tipo_data.get("nombre", ""),
                        "sueldo_diario": float(tipo_data.get("sueldo_diario", 0)),
                        "dias_completos": 0,
                        "medios_dias": 0,
                        "jornales_totales": 0.0,
                        "pago_total": 0.0,
                    }

                maestros_map[mid]["jornales_totales"] += val
                maestros_map[mid]["pago_total"] += val * maestros_map[mid]["sueldo_diario"]
                if val == 1.0:
                    maestros_map[mid]["dias_completos"] += 1
                elif val == 0.5:
                    maestros_map[mid]["medios_dias"] += 1

            result = sorted(maestros_map.values(), key=lambda x: x["maestro_nombre"])
            total_pago = sum(m["pago_total"] for m in result)
            total_jornales = sum(m["jornales_totales"] for m in result)
            summary = {"total_pago": total_pago, "total_jornales": total_jornales}

            self.success.emit(result, summary)
        except Exception as e:
            self.error.emit(f"Error al generar reporte de asistencia: {str(e)}")


class UpdateAvanceStatusWorker(QThread):
    success = pyqtSignal(list, str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, avance_ids: list, nuevo_estado: str = "aprobado"):
        super().__init__()
        self.supabase = supabase
        self.avance_ids = avance_ids if isinstance(avance_ids, list) else [avance_ids]
        self.nuevo_estado = nuevo_estado

    def run(self):
        try:
            if not self.avance_ids:
                self.error.emit("No hay avances seleccionados para actualizar.")
                return

            chunk_size = 200
            for i in range(0, len(self.avance_ids), chunk_size):
                chunk = self.avance_ids[i:i + chunk_size]
                self.supabase.table("avances").update({"estado_revision": self.nuevo_estado}).in_("id", chunk).execute()

            self.success.emit(self.avance_ids, self.nuevo_estado)
        except Exception as e:
            self.error.emit(f"Error al actualizar el estado de los avances: {str(e)}")


class UpdateJefeWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, jefe_id: str, nombre: str,
                 rut_dni: str = "", telefono: str = "", foto_perfil_url: str = ""):
        super().__init__()
        self.supabase = supabase
        self.jefe_id = jefe_id
        self.nombre = nombre
        self.rut_dni = rut_dni
        self.telefono = telefono
        self.foto_perfil_url = foto_perfil_url

    def run(self):
        try:
            if not self.jefe_id or not self.nombre:
                self.error.emit("ID y Nombre son obligatorios.")
                return
            data = {
                "nombre": self.nombre,
                "rut_dni": self.rut_dni,
                "telefono": self.telefono,
                "foto_perfil_url": self.foto_perfil_url
            }
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("perfiles_usuario").update(data).eq("id", self.jefe_id))
            self.success.emit(f"Supervisor '{self.nombre}' actualizado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al actualizar Supervisor: {str(e)}")


class DeleteJefeWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, jefe_id: str):
        super().__init__()
        self.supabase = supabase
        self.jefe_id = jefe_id

    def run(self):
        try:
            if not self.jefe_id:
                self.error.emit("ID no válido para eliminar.")
                return
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("perfiles_usuario").delete().eq("id", self.jefe_id))
            self.success.emit("Supervisor eliminado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al eliminar Supervisor: {str(e)}")


class UpdateMaestroWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, maestro_id: str, nombre: str, rut_dni: str, tipo_maestro_id: str, telefono: str = "", estado: str = "activo", foto_url: str = ""):
        super().__init__()
        self.supabase = supabase
        self.maestro_id = maestro_id
        self.nombre = nombre
        self.rut_dni = rut_dni
        self.tipo_maestro_id = tipo_maestro_id
        self.telefono = telefono
        self.estado = estado
        self.foto_url = foto_url

    def run(self):
        try:
            if not self.maestro_id or not self.nombre or not self.tipo_maestro_id:
                self.error.emit("ID, Nombre y Cargo son obligatorios.")
                return
            data = {
                "nombre": self.nombre,
                "rut_dni": self.rut_dni,
                "tipo_maestro_id": self.tipo_maestro_id,
                "telefono": self.telefono,
                "estado": self.estado,
                "foto_perfil_url": self.foto_url
            }
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("maestros").update(data).eq("id", self.maestro_id))
            self.success.emit(f"Maestro '{self.nombre}' actualizado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al actualizar Maestro: {str(e)}")


class DeleteMaestroWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, maestro_id: str):
        super().__init__()
        self.supabase = supabase
        self.maestro_id = maestro_id

    def run(self):
        try:
            if not self.maestro_id:
                self.error.emit("ID no válido para eliminar.")
                return
            dm = DataManager(self.supabase)
            dm.execute_safe(self.supabase.table("maestros").delete().eq("id", self.maestro_id))
            self.success.emit("Maestro eliminado exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al eliminar Maestro: {str(e)}")


class UploadFotoPerfilWorker(QThread):
    """Sube una imagen local al bucket 'fotos-perfil' y emite la URL pública resultante."""
    success = pyqtSignal(str)   # URL pública de la imagen subida
    error = pyqtSignal(str)

    MIME_MAP = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    def __init__(self, supabase: Client, file_path: str, subfolder: str = "personal"):
        super().__init__()
        self.supabase = supabase
        self.file_path = file_path
        self.subfolder = subfolder

    def run(self):
        try:
            ext = os.path.splitext(self.file_path)[1].lower()
            if ext not in self.MIME_MAP:
                self.error.emit(f"Formato no soportado: {ext}. Use JPG, PNG o WebP.")
                return

            unique_name = f"{self.subfolder}/{uuid.uuid4()}{ext}"
            mime_type = self.MIME_MAP[ext]

            with open(self.file_path, "rb") as f:
                content = f.read()

            self.supabase.storage.from_("accuratek-data").upload(
                path=unique_name,
                file=content,
                file_options={"content-type": mime_type}
            )
            public_url = self.supabase.storage.from_("accuratek-data").get_public_url(unique_name)
            self.success.emit(public_url)
        except Exception as e:
            self.error.emit(f"Error al subir foto: {str(e)}")
