import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  ActivityIndicator,
  Platform,
  TextInput,
  Alert,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { COLORS, FONTS } from "../constants/theme";
import Toast from "react-native-toast-message";
import {
  getMaestrosForObra,
  saveAsistenciaDiaria,
  saveAsistenciaDetalle,
  getAsistenciaByObraFecha,
} from "../database/db";
import { syncAsistencias } from "../database/sync";

function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

const ESTADO_OPTIONS = [
  { label: "✓ Día Completo", value: "presente", jornada: 1.0, color: "#10B981" },
  { label: "½ Medio Día",    value: "medio_dia", jornada: 0.5, color: "#F59E0B" },
  { label: "✗ Ausente",     value: "ausente",   jornada: 0.0, color: "#EF4444" },
];

/**
 * AsistenciaScreen — Pantalla para pasar la asistencia diaria de maestros.
 * Props:
 *   userProfile   — perfil del jefe de obra logueado
 *   activeObra    — objeto de la obra activa
 *   onNavigateBack — callback para volver al menú de la obra
 */
export default function AsistenciaScreen({ userProfile, activeObra, onNavigateBack }) {
  const isWeb = Platform.OS === "web";

  const [maestros, setMaestros] = useState([]);
  const [asistencias, setAsistencias] = useState({}); // { [maestroId]: { estado, jornada } }
  const [foto, setFoto] = useState(null);
  const [observaciones, setObservaciones] = useState("");
  const [esCorrectivo, setEsCorrectivo] = useState(false);
  const [yaExisteAsistencia, setYaExisteAsistencia] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Fecha de hoy en formato YYYY-MM-DD
  const hoy = new Date().toISOString().split("T")[0];

  // ── Carga inicial ──
  useEffect(() => {
    if (!activeObra?.id) {
      setIsLoading(false);
      return;
    }

    // Verificar si ya se pasó asistencia hoy
    const existente = getAsistenciaByObraFecha(activeObra.id, hoy);
    if (existente) {
      setYaExisteAsistencia(true);
      setEsCorrectivo(true);
    }

    // Cargar maestros asignados a la obra
    const lista = getMaestrosForObra(activeObra.id);
    setMaestros(lista);

    // Inicializar todos en "presente" por defecto
    const init = {};
    for (const m of lista) {
      init[m.id] = { estado: "presente", jornada: 1.0 };
    }
    setAsistencias(init);
    setIsLoading(false);
  }, [activeObra?.id]);

  // ── Seleccionar estado de asistencia de un maestro ──
  const handleEstadoChange = useCallback((maestroId, opcion) => {
    setAsistencias((prev) => ({
      ...prev,
      [maestroId]: { estado: opcion.value, jornada: opcion.jornada },
    }));
  }, []);

  // ── Tomar foto ──
  const handleTomarFoto = async () => {
    if (isWeb) {
      Toast.show({ type: "info", text1: "Cámara no disponible en web" });
      return;
    }
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Toast.show({ type: "error", text1: "Se necesita permiso de cámara" });
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
      allowsEditing: false,
    });
    if (!result.canceled && result.assets?.[0]) {
      setFoto(result.assets[0].uri);
    }
  };

  // ── Seleccionar foto de galería ──
  const handleGaleria = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Toast.show({ type: "error", text1: "Se necesita permiso de galería" });
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
      allowsEditing: false,
    });
    if (!result.canceled && result.assets?.[0]) {
      setFoto(result.assets[0].uri);
    }
  };

  // ── Enviar asistencia ──
  const handleSubmit = async () => {
    // Validaciones
    if (maestros.length === 0) {
      Toast.show({ type: "error", text1: "No hay maestros asignados a esta obra" });
      return;
    }
    if (!foto) {
      Toast.show({ type: "error", text1: "Foto requerida", text2: "Tome una foto como evidencia de la asistencia" });
      return;
    }
    if (esCorrectivo && !observaciones.trim()) {
      Toast.show({ type: "error", text1: "Observación requerida", text2: "El reporte correctivo requiere una justificación" });
      return;
    }

    setIsSubmitting(true);
    try {
      const asistenciaId = generateUUID();

      // Guardar cabecera
      saveAsistenciaDiaria({
        id: asistenciaId,
        obra_id: activeObra.id,
        jefe_obra_id: userProfile.id,
        fecha: hoy,
        foto_url: foto,
        es_correctivo: esCorrectivo,
        observaciones: observaciones.trim() || null,
      });

      // Guardar detalle por maestro
      for (const m of maestros) {
        const estadoMaestro = asistencias[m.id] || { estado: "presente", jornada: 1.0 };
        saveAsistenciaDetalle({
          id: generateUUID(),
          asistencia_id: asistenciaId,
          maestro_id: m.id,
          estado: estadoMaestro.estado,
          valor_jornada: estadoMaestro.jornada,
          observacion: null,
        });
      }

      Toast.show({
        type: "success",
        text1: esCorrectivo ? "✓ Correctivo guardado" : "✓ Asistencia guardada",
        text2: "Sincronizando en segundo plano...",
      });

      // Sync en background sin bloquear
      syncAsistencias().catch((e) => console.warn("[AsistenciaScreen] Error sync:", e?.message));

      onNavigateBack();
    } catch (err) {
      console.error("[handleSubmit] Error:", err);
      Toast.show({ type: "error", text1: "Error al guardar", text2: err?.message || "Intente de nuevo" });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cargando personal...</Text>
      </View>
    );
  }

  const obraColor = activeObra?.color || COLORS.primary;
  const presentes = Object.values(asistencias).filter((a) => a.estado === "presente").length;
  const medios = Object.values(asistencias).filter((a) => a.estado === "medio_dia").length;
  const ausentes = Object.values(asistencias).filter((a) => a.estado === "ausente").length;

  return (
    <View style={styles.container}>
      {/* ── Header ── */}
      <View style={[styles.header, { backgroundColor: obraColor }]}>
        <TouchableOpacity onPress={onNavigateBack} style={styles.backBtn} activeOpacity={0.8}>
          <Text style={styles.backText}>← Volver</Text>
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {esCorrectivo ? "📋 Reporte Correctivo" : "📋 Asistencia Diaria"}
          </Text>
          <Text style={styles.headerSub}>{activeObra?.nombre || "Obra"}</Text>
          <Text style={styles.headerDate}>{hoy}</Text>
        </View>
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* ── Banner de correctivo ── */}
        {yaExisteAsistencia && (
          <View style={styles.correctivoBanner}>
            <Text style={styles.correctivoText}>
              ⚠️ Ya se registró asistencia hoy. Este envío se procesará como{" "}
              <Text style={{ fontFamily: FONTS.bodyBold }}>Reporte Correctivo</Text>.
            </Text>
          </View>
        )}

        {/* ── Observaciones (sólo correctivo) ── */}
        {esCorrectivo && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Motivo del Correctivo *</Text>
            <TextInput
              style={styles.textArea}
              multiline
              numberOfLines={3}
              placeholder="Describa por qué se corrige la asistencia..."
              placeholderTextColor={COLORS.textLight}
              value={observaciones}
              onChangeText={setObservaciones}
            />
          </View>
        )}

        {/* ── Lista de maestros ── */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Lista de Personal ({maestros.length})</Text>
          {/* Resumen rápido */}
          <View style={styles.summaryRow}>
            <View style={[styles.badge, { backgroundColor: "#D1FAE5" }]}>
              <Text style={[styles.badgeText, { color: "#065F46" }]}>✓ {presentes}</Text>
            </View>
            <View style={[styles.badge, { backgroundColor: "#FEF3C7" }]}>
              <Text style={[styles.badgeText, { color: "#92400E" }]}>½ {medios}</Text>
            </View>
            <View style={[styles.badge, { backgroundColor: "#FEE2E2" }]}>
              <Text style={[styles.badgeText, { color: "#991B1B" }]}>✗ {ausentes}</Text>
            </View>
          </View>

          {maestros.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>
                No hay maestros asignados a esta obra.{"\n"}
                Asígnelos desde la App de Escritorio en "Control de Personal".
              </Text>
            </View>
          ) : (
            maestros.map((m) => {
              const estadoActual = asistencias[m.id] || { estado: "presente", jornada: 1.0 };
              return (
                <View key={m.id} style={styles.maestroCard}>
                  <View style={styles.maestroInfo}>
                    <Text style={styles.maestroNombre}>{m.nombre}</Text>
                    <Text style={styles.maestroCargo}>{m.tipo_nombre || "Sin cargo"}</Text>
                  </View>
                  <View style={styles.estadoBtns}>
                    {ESTADO_OPTIONS.map((op) => {
                      const isSelected = estadoActual.estado === op.value;
                      return (
                        <TouchableOpacity
                          key={op.value}
                          style={[
                            styles.estadoBtn,
                            isSelected && { backgroundColor: op.color, borderColor: op.color },
                          ]}
                          onPress={() => handleEstadoChange(m.id, op)}
                          activeOpacity={0.8}
                        >
                          <Text style={[styles.estadoBtnText, isSelected && { color: "#FFFFFF" }]}>
                            {op.label}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>
              );
            })
          )}
        </View>

        {/* ── Sección de foto ── */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Foto de Evidencia *</Text>
          <Text style={styles.sectionDesc}>
            Tome una foto que evidencie la asistencia en terreno (ej. grupo de trabajo, firma).
          </Text>
          <View style={styles.fotoBtns}>
            {!isWeb && (
              <TouchableOpacity style={[styles.fotoBtn, { backgroundColor: COLORS.primary }]} onPress={handleTomarFoto} activeOpacity={0.85}>
                <Text style={styles.fotoBtnText}>📷 Cámara</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity style={[styles.fotoBtn, { backgroundColor: "#475569" }]} onPress={handleGaleria} activeOpacity={0.85}>
              <Text style={styles.fotoBtnText}>🖼 Galería</Text>
            </TouchableOpacity>
          </View>
          {foto ? (
            <View style={styles.fotoPreviewContainer}>
              <Image source={{ uri: foto }} style={styles.fotoPreview} resizeMode="cover" />
              <TouchableOpacity style={styles.removeFotoBtn} onPress={() => setFoto(null)}>
                <Text style={styles.removeFotoText}>✕</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.fotoPlaceholder}>
              <Text style={styles.fotoPlaceholderText}>Sin foto</Text>
            </View>
          )}
        </View>

        {/* ── Botón de envío ── */}
        <TouchableOpacity
          style={[
            styles.submitBtn,
            { backgroundColor: esCorrectivo ? "#F59E0B" : COLORS.primary },
            (!foto || isSubmitting) && styles.submitBtnDisabled,
          ]}
          onPress={handleSubmit}
          disabled={!foto || isSubmitting}
          activeOpacity={0.85}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.submitBtnText}>
              {esCorrectivo ? "📤 Enviar Correctivo" : "📤 Pasar Asistencia"}
            </Text>
          )}
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ESTILOS
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: COLORS.background,
    gap: 12,
  },
  loadingText: {
    fontFamily: FONTS.body,
    color: COLORS.textLight,
    fontSize: 15,
  },
  header: {
    paddingTop: Platform.OS === "ios" ? 54 : 36,
    paddingBottom: 16,
    paddingHorizontal: 20,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  backBtn: {
    marginTop: 4,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: "rgba(255,255,255,0.2)",
  },
  backText: {
    color: "#FFFFFF",
    fontFamily: FONTS.bodyBold,
    fontSize: 13,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    color: "#FFFFFF",
    fontFamily: FONTS.headingBold,
    fontSize: 18,
  },
  headerSub: {
    color: "rgba(255,255,255,0.85)",
    fontFamily: FONTS.body,
    fontSize: 13,
    marginTop: 2,
  },
  headerDate: {
    color: "rgba(255,255,255,0.7)",
    fontFamily: FONTS.body,
    fontSize: 11,
    marginTop: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    gap: 16,
  },
  correctivoBanner: {
    backgroundColor: "#FEF3C7",
    borderWidth: 1,
    borderColor: "#F59E0B",
    borderRadius: 10,
    padding: 12,
  },
  correctivoText: {
    fontFamily: FONTS.body,
    color: "#92400E",
    fontSize: 13,
    lineHeight: 18,
  },
  section: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    gap: 10,
  },
  sectionTitle: {
    fontFamily: FONTS.headingBold,
    fontSize: 15,
    color: COLORS.text,
  },
  sectionDesc: {
    fontFamily: FONTS.body,
    fontSize: 13,
    color: COLORS.textLight,
    lineHeight: 18,
  },
  textArea: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 12,
    fontFamily: FONTS.body,
    fontSize: 14,
    color: COLORS.text,
    minHeight: 80,
    textAlignVertical: "top",
    backgroundColor: "#F8FAFC",
  },
  summaryRow: {
    flexDirection: "row",
    gap: 8,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  badgeText: {
    fontFamily: FONTS.bodyBold,
    fontSize: 13,
  },
  emptyState: {
    alignItems: "center",
    padding: 20,
  },
  emptyText: {
    fontFamily: FONTS.body,
    color: COLORS.textLight,
    fontSize: 13,
    textAlign: "center",
    lineHeight: 20,
  },
  maestroCard: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    padding: 12,
    gap: 8,
    backgroundColor: "#FAFAFA",
  },
  maestroInfo: {
    gap: 2,
  },
  maestroNombre: {
    fontFamily: FONTS.bodyBold,
    fontSize: 14,
    color: COLORS.text,
  },
  maestroCargo: {
    fontFamily: FONTS.body,
    fontSize: 12,
    color: COLORS.textLight,
  },
  estadoBtns: {
    flexDirection: "row",
    gap: 6,
    flexWrap: "wrap",
  },
  estadoBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: "#CBD5E1",
    backgroundColor: "#FFFFFF",
  },
  estadoBtnText: {
    fontFamily: FONTS.body,
    fontSize: 12,
    color: COLORS.text,
  },
  fotoBtns: {
    flexDirection: "row",
    gap: 10,
  },
  fotoBtn: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 10,
    alignItems: "center",
  },
  fotoBtnText: {
    fontFamily: FONTS.bodyBold,
    color: "#FFFFFF",
    fontSize: 14,
  },
  fotoPreviewContainer: {
    position: "relative",
    alignSelf: "flex-start",
  },
  fotoPreview: {
    width: 200,
    height: 140,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  removeFotoBtn: {
    position: "absolute",
    top: -8,
    right: -8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#EF4444",
    justifyContent: "center",
    alignItems: "center",
  },
  removeFotoText: {
    color: "#FFFFFF",
    fontFamily: FONTS.bodyBold,
    fontSize: 14,
  },
  fotoPlaceholder: {
    width: 200,
    height: 140,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderStyle: "dashed",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#F8FAFC",
  },
  fotoPlaceholderText: {
    fontFamily: FONTS.body,
    color: COLORS.textLight,
    fontSize: 13,
  },
  submitBtn: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 4,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 3,
  },
  submitBtnDisabled: {
    opacity: 0.5,
  },
  submitBtnText: {
    fontFamily: FONTS.headingBold,
    color: "#FFFFFF",
    fontSize: 16,
  },
});
