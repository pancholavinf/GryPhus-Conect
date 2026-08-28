import uuid
from supabase import Client

class JefesController:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def crear_jefe(self, nombre: str):
        """
        Crea un nuevo Supervisor en la tabla perfiles_usuario.
        """
        if not nombre:
            return False, "El nombre no puede estar vacío."
            
        nuevo_id = str(uuid.uuid4())
        jefe_data = {
            "id": nuevo_id,
            "nombre": nombre,
            "rol": "Jefe_Obra"
        }
        
        try:
            res = self.supabase.table("perfiles_usuario").insert(jefe_data).execute()
            return True, f"Supervisor '{nombre}' creado exitosamente."
        except Exception as e:
            return False, f"Error al crear Supervisor: {str(e)}"
            
    def obtener_jefes(self):
        """
        Obtiene la lista de Supervisores existentes.
        """
        try:
            res = self.supabase.table("perfiles_usuario").select("*").ilike("rol", "jefe_obra").execute()
            return True, res.data
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
