import threading
import time
import datetime
from typing import Dict, Any, Optional, Tuple, List
from supabase import Client

class DataManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, supabase_client: Optional[Client] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DataManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, supabase_client: Optional[Client] = None):
        if self._initialized:
            if supabase_client and not self.supabase:
                self.supabase = supabase_client
            return

        self.supabase: Optional[Client] = supabase_client
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutos en segundos
        self._exec_lock = threading.Lock()  # Asegura peticiones thread-safe a Supabase en Windows
        self._initialized = True

    def set_client(self, supabase_client: Client):
        self.supabase = supabase_client

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        entry = self._cache[key]
        return (time.time() - entry["timestamp"]) < self._cache_ttl

    def invalidate_cache(self, key: Optional[str] = None):
        """Invalida una clave específica o todo el caché si key es None."""
        with self._exec_lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    def _safe_execute(self, query_builder):
        """Ejecuta una consulta Supabase asegurando thread-safety y reintentos ante WSAEWOULDBLOCK en Windows."""
        with self._exec_lock:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return query_builder.execute()
                except Exception as e:
                    err_str = str(e).lower()
                    if attempt < max_retries - 1 and any(k in err_str for k in ["10035", "wsaewouldblock", "socket", "desbloqueo", "inmediata"]):
                        time.sleep(0.15)
                        continue
                    raise e

    def execute_safe(self, query_builder):
        """Alias público thread-safe para ejecutar consultas a Supabase."""
        return self._safe_execute(query_builder)

    def fetch_initial_batch(self, progress_callback=None, force_refresh: bool = True) -> dict:
        """
        Realiza el Pull Inicial completo de las tablas básicas en una sola operación optimizada.
        Carga: Obras, Supervisores, Materiales, Tipos de Maestro y Maestros.
        """
        if not self.supabase:
            return {}

        def update_progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        # 1. Obras y Supervisores asignados (20%)
        update_progress(10, "Cargando catálogo de obras...")
        obras, jefes_por_obra = self.get_dashboard_data(force_refresh=force_refresh)

        # 2. Supervisores / perfiles (40%)
        update_progress(35, "Cargando perfiles de Supervisores...")
        jefes = self.get_jefes(force_refresh=force_refresh)

        # 3. Materiales (60%)
        update_progress(55, "Cargando catálogo de materiales...")
        materiales = self.get_materiales(force_refresh=force_refresh)

        # 4. Tipos / Cargos de maestro (80%)
        update_progress(75, "Cargando cargos y tipos de personal...")
        tipos_maestro = self.get_tipos_maestro(force_refresh=force_refresh)

        # 5. Maestros (100%)
        update_progress(95, "Cargando nómina de maestros...")
        maestros = self.get_maestros(force_refresh=force_refresh)

        update_progress(100, "Carga inicial completada exitosamente.")

        return {
            "obras": obras,
            "jefes_por_obra": jefes_por_obra,
            "jefes": jefes,
            "materiales": materiales,
            "tipos_maestro": tipos_maestro,
            "maestros": maestros,
        }

    def get_reportes(self, force_refresh: bool = False) -> Tuple[List[dict], List[dict], List[dict], List[dict], List[dict]]:
        cache_key = "reportes_obra_data"
        if not force_refresh and self._is_cache_valid(cache_key):
            cached = self._cache[cache_key]["data"]
            return cached["reportes"], cached["consumos"], cached["materiales"], cached["items"], cached["avances"]

        if not self.supabase:
            return [], [], [], [], []

        # 1. Obtener reportes
        res_reportes = self._safe_execute(self.supabase.table("reporte_obra").select("*").order("fecha_publicacion", desc=True))
        reportes = res_reportes.data or []

        # 2. Obtener obras y supervisores para mapear nombres
        res_obras = self._safe_execute(self.supabase.table("obras").select("id, nombre"))
        obras_dict = {o.get("id"): o.get("nombre") for o in (res_obras.data or [])}

        res_jefes = self._safe_execute(self.supabase.table("perfiles_usuario").select("id, nombre"))
        jefes_dict = {j.get("id"): (j.get("nombre") or "Desconocido") for j in (res_jefes.data or [])}

        for rep in reportes:
            rep["obra_nombre"] = obras_dict.get(rep.get("obra_id")) or "Obra Desconocida"
            rep["jefe_nombre"] = jefes_dict.get(rep.get("jefe_obra_id")) or "Supervisor Desconocido"

        # 3. Consumos, Materiales, Items, Avances
        res_consumos = self._safe_execute(self.supabase.table("reporte_obra_consumos").select("*"))
        consumos = res_consumos.data or []

        res_materiales = self._safe_execute(self.supabase.table("materiales").select("*"))
        materiales = res_materiales.data or []

        res_items = self._safe_execute(self.supabase.table("items_obra").select("id, obra_id, material_id"))
        items = res_items.data or []

        res_avances = self._safe_execute(self.supabase.table("avances").select("id, item_obra_id, cantidad, fecha_captura_local"))
        avances = res_avances.data or []

        result = (reportes, consumos, materiales, items, avances)
        self._cache[cache_key] = {
            "timestamp": time.time(),
            "data": {
                "reportes": reportes,
                "consumos": consumos,
                "materiales": materiales,
                "items": items,
                "avances": avances
            }
        }
        return result

    # -------------------------------------------------------------------------
    # DASHBOARD & OBRAS
    # -------------------------------------------------------------------------
    def get_dashboard_data(self, force_refresh: bool = False) -> Tuple[List[dict], Dict[str, List[str]]]:
        cache_key = "dashboard_data"
        if not force_refresh and self._is_cache_valid(cache_key):
            cached = self._cache[cache_key]["data"]
            return cached["obras"], cached["jefes_por_obra"]

        if not self.supabase:
            return [], {}

        # Petición unificada en PostgREST: 1 sola consulta con JOIN relacional
        res = self._safe_execute(
            self.supabase.table("obras").select("*, obras_jefes_obra(jefe_obra_id, perfiles_usuario(id, nombre))")
        )
        obras_raw = res.data or []

        obras = []
        jefes_por_obra = {}

        for row in obras_raw:
            # Extraer jefes asignados
            asignaciones = row.pop("obras_jefes_obra", []) or []
            nombres_jefes = []
            for asig in asignaciones:
                perfil = asig.get("perfiles_usuario")
                if perfil and isinstance(perfil, dict) and perfil.get("nombre"):
                    nombres_jefes.append(perfil["nombre"])

            obra_id = row.get("id")
            if obra_id:
                jefes_por_obra[obra_id] = nombres_jefes

            obras.append(row)

        result = (obras, jefes_por_obra)
        self._cache[cache_key] = {
            "timestamp": time.time(),
            "data": {"obras": obras, "jefes_por_obra": jefes_por_obra}
        }
        return result

    def get_dashboard_asistencia(self, force_refresh: bool = False) -> List[dict]:
        cache_key = "dashboard_asistencia"
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]

        if not self.supabase:
            return []

        today = datetime.date.today().isoformat()
        
        # Petición unificada con joins
        res_cabs = self._safe_execute(
            self.supabase.table("asistencia_diaria").select("id, obra_id, obras(nombre)").eq("fecha", today)
        )
        cabeceras = res_cabs.data or []

        if not cabeceras:
            self._cache[cache_key] = {"timestamp": time.time(), "data": []}
            return []

        cab_ids = [c["id"] for c in cabeceras]
        res_det = self._safe_execute(
            self.supabase.table("asistencia_diaria_detalle").select(
                "asistencia_id, valor_jornada, maestros(tipos_maestro(sueldo_diario))"
            ).in_("asistencia_id", cab_ids)
        )
        detalles = res_det.data or []

        obras_map = {}
        for cab in cabeceras:
            oid = cab["obra_id"]
            obra_nombre = (cab.get("obras") or {}).get("nombre", "Obra Desconocida")
            if oid not in obras_map:
                obras_map[oid] = {
                    "obra_id": oid,
                    "obra_nombre": obra_nombre,
                    "presentes": 0,
                    "medios": 0,
                    "ausentes": 0,
                    "total": 0,
                    "costo_dia": 0.0,
                }

        cab_obra_map = {c["id"]: c["obra_id"] for c in cabeceras}

        for det in detalles:
            obra_id = cab_obra_map.get(det["asistencia_id"])
            if not obra_id or obra_id not in obras_map:
                continue
            val = float(det.get("valor_jornada", 0))
            maestro_data = det.get("maestros") or {}
            tipo_data = maestro_data.get("tipos_maestro") or {}
            sueldo = float(tipo_data.get("sueldo_diario", 0))

            obras_map[obra_id]["total"] += 1
            obras_map[obra_id]["costo_dia"] += val * sueldo
            if val == 1.0:
                obras_map[obra_id]["presentes"] += 1
            elif val == 0.5:
                obras_map[obra_id]["medios"] += 1
            else:
                obras_map[obra_id]["ausentes"] += 1

        result = list(obras_map.values())
        self._cache[cache_key] = {"timestamp": time.time(), "data": result}
        return result

    # -------------------------------------------------------------------------
    # JEFES & MAESTROS
    # -------------------------------------------------------------------------
    def get_jefes(self, force_refresh: bool = False) -> List[dict]:
        cache_key = "jefes_obra"
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]

        if not self.supabase:
            return []

        res = self._safe_execute(
            self.supabase.table("perfiles_usuario").select("*").order("nombre")
        )
        todos = res.data or []
        result = [
            p for p in todos 
            if str(p.get("rol", "")).strip().lower() not in ("administrador", "admin", "gerente")
        ]
        self._cache[cache_key] = {"timestamp": time.time(), "data": result}
        return result

    def get_tipos_maestro(self, force_refresh: bool = False) -> List[dict]:
        cache_key = "tipos_maestro"
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]

        if not self.supabase:
            return []

        res = self._safe_execute(
            self.supabase.table("tipos_maestro").select("*").order("nombre")
        )
        result = res.data or []
        self._cache[cache_key] = {"timestamp": time.time(), "data": result}
        return result

    def get_maestros(self, force_refresh: bool = False) -> List[dict]:
        cache_key = "maestros"
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]

        if not self.supabase:
            return []

        res = self._safe_execute(
            self.supabase.table("maestros").select("*, tipos_maestro(nombre, sueldo_diario)").order("nombre")
        )
        result = res.data or []
        self._cache[cache_key] = {"timestamp": time.time(), "data": result}
        return result

    # -------------------------------------------------------------------------
    # MATERIALES
    # -------------------------------------------------------------------------
    def get_materiales(self, force_refresh: bool = False) -> List[dict]:
        cache_key = "materiales"
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]

        if not self.supabase:
            return []

        res = self._safe_execute(
            self.supabase.table("materiales").select("*").order("nombre")
        )
        result = res.data or []
        self._cache[cache_key] = {"timestamp": time.time(), "data": result}
        return result

    # -------------------------------------------------------------------------
    # DETALLES DE OBRA & AVANCES
    # -------------------------------------------------------------------------
    def get_obra_details(self, obra_id: str, force_refresh: bool = False) -> Tuple[List[dict], List[dict]]:
        cache_key = f"obra_details_{obra_id}"
        if not force_refresh and self._is_cache_valid(cache_key):
            cached = self._cache[cache_key]["data"]
            return cached["items"], cached["avances"]

        if not self.supabase:
            return [], []

        # 1. Fetch items
        res_items = self._safe_execute(
            self.supabase.table("items_obra").select("*").eq("obra_id", obra_id)
        )
        items = res_items.data or []

        # 2. Fetch jefes para mapping
        res_jefes = self._safe_execute(
            self.supabase.table("perfiles_usuario").select("id, nombre")
        )
        jefes_dict = {j.get("id"): (j.get("nombre") or "Desconocido") for j in (res_jefes.data or [])}

        # 3. Fetch EDPs
        res_edps = self._safe_execute(
            self.supabase.table("estados_pago").select("id, numero_estado_pago, fecha_emision").eq("obra_id", obra_id)
        )
        edps_dict = {e.get("id"): e for e in (res_edps.data or [])}

        # 4. Fetch avances
        item_ids = [item.get("id") for item in items]
        avances = []

        if item_ids:
            items_dict = {item.get("id"): item for item in items}
            chunk_size = 300
            for i in range(0, len(item_ids), chunk_size):
                chunk_ids = item_ids[i:i + chunk_size]
                res_avances = self._safe_execute(
                    self.supabase.table("avances").select("*").in_("item_obra_id", chunk_ids)
                )

                if res_avances.data:
                    for av in res_avances.data:
                        j_id = av.get("jefe_obra_id")
                        av["jefe_nombre"] = jefes_dict.get(j_id) or "Desconocido"

                        item_id = av.get("item_obra_id")
                        item_info = items_dict.get(item_id, {})
                        av["item_ubicacion"] = item_info.get("ubicacion") or ""
                        av["item_plano"] = item_info.get("plano") or ""
                        av["item_estructura"] = item_info.get("estructura") or ""
                        av["item_descripcion_plano"] = item_info.get("descripcion_plano") or ""
                        av["item_material"] = item_info.get("material") or ""
                        av["item_precio_unitario"] = item_info.get("precio_unitario_contrato") or 0.0
                        av["item_cantidad_total"] = item_info.get("cantidad") or 0.0

                        edp_id = av.get("estado_pago_id")
                        if edp_id and edp_id in edps_dict:
                            edp_info = edps_dict[edp_id]
                            av["numero_estado_pago"] = edp_info.get("numero_estado_pago")
                            av["fecha_emision_edp"] = edp_info.get("fecha_emision")
                        else:
                            av["numero_estado_pago"] = None
                            av["fecha_emision_edp"] = None

                        avances.append(av)

        avances.sort(key=lambda x: x.get("fecha_captura_local", ""), reverse=True)

        result = (items, avances)
        self._cache[cache_key] = {
            "timestamp": time.time(),
            "data": {"items": items, "avances": avances}
        }
        return result
