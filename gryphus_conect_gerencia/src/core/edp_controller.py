import os
import datetime
import uuid
from pathlib import Path
from src.utils.pdf_edp_generator import generate_edp_pdf


class EDPController:
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

    # ------------------------------------------------------------------
    # HELPERS INTERNOS
    # ------------------------------------------------------------------

    def _get_obra_item_ids(self, obra_id: str) -> list:
        """Retorna la lista de item_obra_id que pertenecen a una obra específica."""
        if not self.supabase:
            return []
        try:
            res = self.supabase.table('items_obra') \
                .select('id') \
                .eq('obra_id', obra_id) \
                .execute()
            return [row['id'] for row in (res.data or [])]
        except Exception as e:
            print(f"Error al obtener ítems de la obra {obra_id}: {e}")
            return []

    def _get_current_user_id(self) -> str | None:
        """Obtiene el ID del usuario autenticado desde la sesión activa de Supabase."""
        try:
            if not self.supabase:
                return None
            session = self.supabase.auth.get_session()
            if session and session.user:
                return session.user.id
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # CORRELATIVO DE FOLIO
    # ------------------------------------------------------------------

    def get_next_edp_number(self, obra_id: str) -> int:
        """
        Obtiene el siguiente folio/número correlativo de EDP para una obra.
        Consulta directamente la tabla para consistencia sin depender de RPC.
        """
        if not self.supabase:
            return 1
        try:
            res = self.supabase.table('estados_pago') \
                .select('numero_estado_pago') \
                .eq('obra_id', obra_id) \
                .order('numero_estado_pago', desc=True) \
                .limit(1) \
                .execute()
            if res.data and len(res.data) > 0:
                return int(res.data[0].get('numero_estado_pago', 0)) + 1
            return 1
        except Exception as e:
            print(f"Error al obtener número correlativo de EDP: {e}")
            return 1

    # ------------------------------------------------------------------
    # CÁLCULO DE VISTA PREVIA DEL EDP
    # ------------------------------------------------------------------

    def fetch_edp_preview_data(self, obra_id: str, periodo_desde=None, periodo_hasta=None):
        """
        Calcula la matriz completa de partidas y avances para la emisión o vista
        previa de un EDP. Todos los avances se filtran por obra_id para evitar
        mezclar datos de otras obras.

        Retorna (edp_meta, items_detail, candidato_avances_ids).
        """
        if not self.supabase:
            return {}, [], []

        # ── 1. Información de la obra ───────────────────────────────────────
        res_obra = self.supabase.table('obras').select('*').eq('id', obra_id).limit(1).execute()
        obra_info = res_obra.data[0] if res_obra.data else {}

        # ── 2. Ítems de la obra ─────────────────────────────────────────────
        res_items = self.supabase.table('items_obra').select('*').eq('obra_id', obra_id).execute()
        items_raw = res_items.data or []

        if not items_raw:
            # Devolver estructura vacía pero válida si la obra no tiene ítems
            edp_meta = {
                'obra_id': obra_id,
                'obra_nombre': obra_info.get('nombre', 'Sin Nombre'),
                'ubicacion': obra_info.get('ubicacion', 'Ubicación Obra'),
                'mandante': 'Gryphus Systems / Cliente',
                'orden_trabajo_num': f"OT-{obra_info.get('nombre', '01')[:6].upper()}",
                'numero_estado_pago': self.get_next_edp_number(obra_id),
                'fecha_emision': datetime.date.today().strftime("%d/%m/%Y"),
                'periodo_desde': str(periodo_desde) if periodo_desde else datetime.date.today().strftime("%Y-%m-01"),
                'periodo_hasta': str(periodo_hasta) if periodo_hasta else datetime.date.today().strftime("%Y-%m-%d"),
                'subtotal_pesos': 0.0,
                'cant_avances': 0
            }
            return edp_meta, [], []

        # Extraer lista de IDs de ítems de ESTA obra para todos los filtros
        item_ids_obra = [item['id'] for item in items_raw]

        # ── 3. Avances históricos YA pagados (EDPs anteriores) ─────────────
        # CORRECCIÓN: Filtrar por item_obra_id IN (ítems de ESTA obra) para
        # evitar mezclar avances pagados de otras obras en el cálculo histórico.
        q_anterior_map = {}
        try:
            # Procesar en chunks de 500 para evitar límites de URL
            chunk_size = 500
            for i in range(0, len(item_ids_obra), chunk_size):
                chunk_ids = item_ids_obra[i:i + chunk_size]
                res_ant = self.supabase.table('avances') \
                    .select('item_obra_id, cantidad') \
                    .in_('item_obra_id', chunk_ids) \
                    .not_.is_('estado_pago_id', 'null') \
                    .execute()
                for av in (res_ant.data or []):
                    item_id = av.get('item_obra_id')
                    q_val = float(av.get('cantidad') or 0)
                    q_anterior_map[item_id] = q_anterior_map.get(item_id, 0.0) + q_val
        except Exception as e:
            print(f"Advertencia: error al consultar avances anteriores: {e}")

        # ── 4. Avances APROBADOS pendientes de cobro (candidatos al EDP) ───
        # CORRECCIÓN: Filtrar también por item_obra_id IN (ítems de ESTA obra)
        q_presente_map = {}
        candidatos_ids = []
        avances_pendientes_raw = []

        try:
            for i in range(0, len(item_ids_obra), chunk_size):
                chunk_ids = item_ids_obra[i:i + chunk_size]
                query = self.supabase.table('avances') \
                    .select('id, item_obra_id, cantidad, fecha_captura_local') \
                    .in_('item_obra_id', chunk_ids) \
                    .eq('estado_revision', 'aprobado') \
                    .is_('estado_pago_id', 'null')

                # Filtrar por fecha si se especificó
                if periodo_desde:
                    query = query.gte('fecha_captura_local', str(periodo_desde)[:10])
                if periodo_hasta:
                    try:
                        hasta_date = datetime.date.fromisoformat(str(periodo_hasta)[:10])
                        next_day = (hasta_date + datetime.timedelta(days=1)).isoformat()
                        query = query.lt('fecha_captura_local', next_day)
                    except ValueError:
                        query = query.lte('fecha_captura_local', str(periodo_hasta) + "T23:59:59.999999Z")

                res_pend = query.execute()
                avances_pendientes_raw.extend(res_pend.data or [])
        except Exception as e:
            print(f"Advertencia: error al consultar avances pendientes: {e}")

        for av in avances_pendientes_raw:
            candidatos_ids.append(av['id'])
            item_id = av.get('item_obra_id')
            q_val = float(av.get('cantidad') or 0)
            q_presente_map[item_id] = q_presente_map.get(item_id, 0.0) + q_val

        # ── 5. Construir matriz de partidas ──────────────────────────────────
        items_detail = []
        subtotal_pesos = 0.0

        for item in items_raw:
            item_id = item.get('id')

            # Construir descripción limpia del ítem
            desc_parts = []
            if item.get('descripcion_plano'):
                desc_parts.append(item['descripcion_plano'])
            elif item.get('ubicacion'):
                desc_parts.append(item['ubicacion'])
            elif item.get('estructura'):
                desc_parts.append(item['estructura'])
            else:
                desc_parts.append("Partida de Obra")

            if item.get('perfil'):
                desc_parts.append(item['perfil'])
            if item.get('dimension'):
                desc_parts.append(item['dimension'])

            desc = " — ".join(desc_parts)

            # Cantidades de contrato (en m² de área expuesta, con fallback a cantidad)
            q_contrato = float(
                item.get('area_expuesta_m2') or
                item.get('cantidad') or
                0.0
            )
            pu = float(
                item.get('precio_unitario_contrato') or
                item.get('precio_unitario') or
                0.0
            )

            # Cantidades históricas y del presente EDP
            q_ant  = q_anterior_map.get(item_id, 0.0)
            q_pres = q_presente_map.get(item_id, 0.0)

            # Monto del presente EDP para este ítem
            p_total_pres = q_pres * pu
            subtotal_pesos += p_total_pres

            items_detail.append({
                'item_id': item_id,
                'descripcion': desc,
                'unidad': item.get('unidad') or 'm²',
                'cantidad_contrato': q_contrato,
                'precio_unitario': pu,
                'cantidad_anterior': q_ant,
                'cantidad_presente': q_pres,
                'monto_presente': p_total_pres
            })

        # ── 6. Siguiente correlativo de folio ────────────────────────────────
        next_num = self.get_next_edp_number(obra_id)

        edp_meta = {
            'obra_id': obra_id,
            'obra_nombre': obra_info.get('nombre', 'Sin Nombre'),
            'ubicacion': obra_info.get('ubicacion', 'Ubicación Obra'),
            'mandante': 'Gryphus Systems / Cliente',
            'orden_trabajo_num': f"OT-{obra_info.get('nombre', '01')[:6].upper()}",
            'numero_estado_pago': next_num,
            'fecha_emision': datetime.date.today().strftime("%d/%m/%Y"),
            'periodo_desde': str(periodo_desde) if periodo_desde else datetime.date.today().strftime("%Y-%m-01"),
            'periodo_hasta': str(periodo_hasta) if periodo_hasta else datetime.date.today().strftime("%Y-%m-%d"),
            'subtotal_pesos': subtotal_pesos,
            'cant_avances': len(candidatos_ids)
        }

        return edp_meta, items_detail, candidatos_ids

    # ------------------------------------------------------------------
    # EMISIÓN OFICIAL DEL ESTADO DE PAGO
    # ------------------------------------------------------------------

    def emit_estado_pago(
        self,
        obra_id: str,
        periodo_desde,
        periodo_hasta,
        retencion_pct: float = 0.05,
        anticipo_monto: float = 0.0,
        user_id: str = None
    ):
        """
        Emisión oficial de Estado de Pago:
        1. Consolida montos desde avances aprobados pendientes de cobro.
        2. Registra en DB `estados_pago`.
        3. Congela los avances asignando `estado_pago_id`.
        4. Genera el PDF institucional con ReportLab.
        5. Sube el PDF a Supabase Storage bucket `estados_pago`.

        Retorna (True, result_dict) en éxito o (False, error_str) en falla.
        """
        if not self.supabase:
            return False, "Cliente de Supabase no conectado."

        try:
            # ── 1. Obtener datos consolidados ────────────────────────────────
            edp_meta, items_detail, avances_ids = self.fetch_edp_preview_data(
                obra_id, periodo_desde, periodo_hasta
            )

            if len(avances_ids) == 0:
                return False, (
                    "No existen avances aprobados pendientes de cobro "
                    "para el período seleccionado."
                )

            # ── 2. Calcular montos financieros ───────────────────────────────
            subtotal_pesos  = edp_meta['subtotal_pesos']
            monto_retencion = subtotal_pesos * float(retencion_pct)
            monto_anticipo  = float(anticipo_monto)
            monto_neto      = max(0.0, subtotal_pesos - monto_retencion - monto_anticipo)
            monto_iva       = monto_neto * 0.19
            monto_total     = monto_neto + monto_iva

            # Enriquecer edp_meta con montos finales para el PDF
            edp_meta.update({
                'subtotal_pesos':  subtotal_pesos,
                'monto_retencion': monto_retencion,
                'monto_anticipo':  monto_anticipo,
                'monto_neto':      monto_neto,
                'monto_iva':       monto_iva,
                'monto_total':     monto_total,
            })

            # ── 3. Obtener user_id si no se proporcionó ──────────────────────
            if not user_id:
                user_id = self._get_current_user_id()

            # ── 4. Insertar registro en `estados_pago` ───────────────────────
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            db_payload = {
                'id':                  str(uuid.uuid4()),
                'obra_id':             obra_id,
                'numero_estado_pago':  edp_meta['numero_estado_pago'],
                'fecha_emision':       now_iso,
                'periodo_desde':       str(periodo_desde) if periodo_desde else None,
                'periodo_hasta':       str(periodo_hasta) if periodo_hasta else None,
                'subtotal_pesos':      round(subtotal_pesos, 2),
                'monto_retencion':     round(monto_retencion, 2),
                'monto_anticipo':      round(monto_anticipo, 2),
                'monto_neto':          round(monto_neto, 2),
                'monto_iva':           round(monto_iva, 2),
                'monto_total':         round(monto_total, 2),
                'orden_trabajo_num':   edp_meta.get('orden_trabajo_num'),
                'creado_por':          user_id,
            }

            res_ins = self.supabase.table('estados_pago').insert(db_payload).execute()
            if not res_ins.data:
                return False, "Error al crear el registro en la base de datos."

            edp_record = res_ins.data[0]
            edp_id     = edp_record['id']

            # ── 5. Congelar avances (inyectar estado_pago_id) ─────────────────
            # Procesar en chunks para no exceder límites de URL de Supabase
            chunk_size = 200
            for i in range(0, len(avances_ids), chunk_size):
                chunk = avances_ids[i:i + chunk_size]
                self.supabase.table('avances') \
                    .update({'estado_pago_id': edp_id}) \
                    .in_('id', chunk) \
                    .execute()

            try:
                from src.core.data_manager import DataManager
                DataManager(self.supabase).invalidate_obra_details(obra_id)
            except Exception:
                pass

            # ── 6. Generar archivo PDF local ────────────────────────────────
            docs_dir = Path(__file__).resolve().parents[2] / "documentos_edp"
            os.makedirs(docs_dir, exist_ok=True)

            pdf_filename = f"EDP_{edp_meta['numero_estado_pago']:03d}_{obra_id[:8]}.pdf"
            local_pdf_path = str(docs_dir / pdf_filename)

            # Buscar logo en assets o INFO PROYECTO
            logo_path = None
            posibles_logos = [
                Path(__file__).resolve().parents[2] / "assets" / "logo_gryphus_nombre_sf.png",
                Path(__file__).resolve().parents[2] / "assets" / "logo_gryphus_nombre_sf.png",
                Path(__file__).resolve().parents[2] / "assets" / "logo_gryphus_circular_sf.png",
                Path(__file__).resolve().parents[2] / "assets" / "LOGO.png",
                Path(__file__).resolve().parents[3] / "INFO PROYECTO" / "LOGOS" / "LOGO.png"
            ]
            for pl in posibles_logos:
                if pl.exists():
                    logo_path = str(pl)
                    break

            try:
                generate_edp_pdf(local_pdf_path, edp_meta, items_detail, logo_path=logo_path)
                pdf_generado = True
            except Exception as e_pdf:
                print(f"Advertencia: No se pudo generar el PDF ({e_pdf}).")
                pdf_generado = False
                local_pdf_path = None

            # ── 7. Subir PDF a Supabase Storage ─────────────────────────────
            storage_url = local_pdf_path or ""
            if pdf_generado and local_pdf_path:
                try:
                    storage_path = f"edp/{obra_id}/{pdf_filename}"
                    with open(local_pdf_path, 'rb') as f:
                        file_bytes = f.read()

                    self.supabase.storage.from_('accuratek-data').upload(
                        path=storage_path,
                        file=file_bytes,
                        file_options={"content-type": "application/pdf", "upsert": "true"}
                    )

                    # Obtener URL pública
                    pub_url = self.supabase.storage.from_('accuratek-data').get_public_url(storage_path)
                    if pub_url:
                        storage_url = pub_url

                    # Actualizar URL en la BD
                    self.supabase.table('estados_pago') \
                        .update({'archivo_pdf_url': storage_url}) \
                        .eq('id', edp_id) \
                        .execute()

                except Exception as e_st:
                    print(
                        f"Advertencia: No se pudo subir el PDF a Storage ({e_st}). "
                        f"Se conserva la ruta local."
                    )
                    # Guardar al menos la ruta local en la BD
                    if local_pdf_path:
                        try:
                            self.supabase.table('estados_pago') \
                                .update({'archivo_pdf_url': local_pdf_path}) \
                                .eq('id', edp_id) \
                                .execute()
                            storage_url = local_pdf_path
                        except Exception:
                            pass

            return True, {
                'edp_id':              edp_id,
                'numero_estado_pago':  edp_meta['numero_estado_pago'],
                'monto_total':         monto_total,
                'cant_avances':        len(avances_ids),
                'pdf_path':            local_pdf_path,
                'pdf_url':             storage_url,
                'pdf_generado':        pdf_generado,
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Ocurrió un error al procesar el Estado de Pago: {str(e)}"

    # ------------------------------------------------------------------
    # HISTORIAL DE EDPs
    # ------------------------------------------------------------------

    def get_historial_edps(self, obra_id: str) -> list:
        """Obtiene la lista de EDPs emitidos anteriormente para esta obra."""
        if not self.supabase:
            return []
        try:
            res = self.supabase.table('estados_pago') \
                .select('*') \
                .eq('obra_id', obra_id) \
                .order('numero_estado_pago', desc=True) \
                .execute()
            return res.data or []
        except Exception as e:
            print(f"Error al obtener historial de EDPs: {e}")
            return []

    def get_edp_avances(self, edp_id: str) -> list:
        """
        Retorna la lista de avances incluidos en un EDP específico.
        Útil para la vista detallada del historial.
        """
        if not self.supabase:
            return []
        try:
            res = self.supabase.table('avances') \
                .select('id, item_obra_id, cantidad, fecha_captura_local, jefe_obra_id') \
                .eq('estado_pago_id', edp_id) \
                .execute()
            return res.data or []
        except Exception as e:
            print(f"Error al obtener avances del EDP {edp_id}: {e}")
            return []
