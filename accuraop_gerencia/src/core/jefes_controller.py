import uuid
from supabase import Client

class JefesController:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def crear_jefe(self, nombre: str, email: str = None, password: str = None, rut_dni: str = "", telefono: str = "", foto_perfil_url: str = ""):
        """
        Crea un nuevo Supervisor en Auth y en perfiles_usuario.
        """
        if not nombre or not email or not password:
            return False, "Nombre, Correo y Contraseña son obligatorios."
            
        try:
            from supabase import create_client
            temp_client = create_client(str(self.supabase.supabase_url).rstrip("/"), str(self.supabase.supabase_key))
            auth_res = temp_client.auth.sign_up({
                "email": email.strip().lower(),
                "password": password.strip(),
                "options": {
                    "data": {
                        "nombre": nombre.strip(),
                        "full_name": nombre.strip(),
                        "rol": "jefe_obra",
                        "telefono": telefono.strip(),
                        "foto_perfil_url": foto_perfil_url.strip(),
                        "rut_dni": rut_dni.strip() or None
                    }
                }
            })
            if not auth_res or not auth_res.user:
                return False, "No se pudo registrar el usuario en el sistema de autenticación."

            nuevo_id = auth_res.user.id
            jefe_data = {
                "id": nuevo_id,
                "nombre": nombre.strip(),
                "email": email.strip().lower(),
                "rol": "jefe_obra",
                "rut_dni": rut_dni.strip() or None,
                "telefono": telefono.strip() or None,
                "foto_perfil_url": foto_perfil_url.strip() or None
            }
            self.supabase.table("perfiles_usuario").upsert(jefe_data).execute()
            return True, f"Supervisor '{nombre}' creado exitosamente."
        except Exception as e:
            return False, f"Error al crear Supervisor: {str(e)}"
            
    def obtener_jefes(self):
        """
        Obtiene la lista de Supervisores existentes (excluyendo administradores).
        """
        try:
            res = self.supabase.table("perfiles_usuario").select("*").order("nombre").execute()
            todos = res.data or []
            jefes = [
                p for p in todos 
                if str(p.get("rol", "")).strip().lower() not in ("administrador", "admin", "gerente")
            ]
            return True, jefes
        except Exception as e:
            return False, str(e)

    def obtener_obras(self):
        """
        Obtiene la lista de todas las obras registradas.
        """
        try:
            res = self.supabase.table("obras").select("id, nombre").execute()
            return True, res.data
        except Exception as e:
            return False, str(e)
            
    def asignar_jefe_obra(self, obra_id: str, jefe_id: str):
        """
        Relaciona un supervisor con una obra en la tabla obras_jefes_obra.
        """
        if not obra_id or not jefe_id:
            return False, "Debe seleccionar un Supervisor y una Obra válidos."
            
        asignacion = {
            "id": str(uuid.uuid4()),
            "obra_id": obra_id,
            "jefe_obra_id": jefe_id
        }
        try:
            self.supabase.table("obras_jefes_obra").insert(asignacion).execute()
            return True, "Supervisor asignado a la obra exitosamente."
        except Exception as e:
            return False, f"Error en la asignación: {str(e)}"
