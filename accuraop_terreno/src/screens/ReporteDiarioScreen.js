import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Image,
  ScrollView,
  ActivityIndicator,
  Platform,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { getMaterialesForObra, saveReporteObra, saveReporteConsumo } from "../database/db";
import { getCachedMaterialesForObra } from "../services/memoryCache";
import { compressImage } from "../services/imageCompressor";
import { syncReportes } from "../database/sync";
import { COLORS } from "../constants/theme";
import Toast from "react-native-toast-message";

const CARPETA_LOGO = require("../../assets/sprites/carpeta_logo.png");
const CAMARA_LOGO = require("../../assets/sprites/camara_logo.png");

function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export default function ReporteDiarioScreen({ userProfile, activeObra, onNavigateBack }) {
  // Form Reporte Obra
  const [tipoReporte, setTipoReporte] = useState("actualizacion");
  const [mensaje, setMensaje] = useState("");
  const [photos, setPhotos] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Catálogo de materiales y cantidades guiadas
  const [materialesObra, setMaterialesObra] = useState([]);
  const [consumoCantidades, setConsumoCantidades] = useState({}); // { [materialId]: cantidad_string }

  // Materiales personalizados de emergencia
  const [customMaterial, setCustomMaterial] = useState("");
  const [customCantidad, setCustomCantidad] = useState("");
  const [customUnidad, setCustomUnidad] = useState("un");
  const [customConsumos, setCustomConsumos] = useState([]);
  const [showCustomForm, setShowCustomForm] = useState(false);

  const isWeb = Platform.OS === "web";

  // Cargar catálogo de materiales de la obra
  useEffect(() => {
    if (!activeObra?.id) return;
    try {
      let list = getMaterialesForObra(activeObra.id);
      if (!list?.length) list = getCachedMaterialesForObra(activeObra.id);
      setMaterialesObra(list || []);
      
      const initCants = {};
      (list || []).forEach((m) => {
        initCants[m.id] = "";
      });
      setConsumoCantidades(initCants);
    } catch {
      const list = getCachedMaterialesForObra(activeObra.id) || [];
      setMaterialesObra(list);
      const initCants = {};
      list.forEach((m) => {
        initCants[m.id] = "";
      });
      setConsumoCantidades(initCants);
    }
  }, [activeObra?.id]);

  // Manejar fotos
  const handleOpenCamera = async () => {
    if (isWeb) return;
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Toast.show({ type: "error", text1: "Permiso de cámara denegado", visibilityTime: 2000 });
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.85 });
    if (!result.canceled && result.assets?.[0]?.uri) {
      const compressed = await compressImage(result.assets[0].uri);
      setPhotos((prev) => [...prev, compressed]);
      Toast.show({ type: "success", text1: "Foto capturada", visibilityTime: 1500 });
    }
  };

  const handlePickFromGallery = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Toast.show({ type: "error", text1: "Permiso de galería denegado", visibilityTime: 2000 });
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
    });
    if (!result.canceled && result.assets?.[0]?.uri) {
      const compressed = await compressImage(result.assets[0].uri);
      setPhotos((prev) => [...prev, compressed]);
      Toast.show({ type: "success", text1: "Foto agregada", visibilityTime: 1500 });
    }
  };

  const handleRemovePhoto = (index) => {
    setPhotos((prev) => prev.filter((_, idx) => idx !== index));
  };

  // Manejo de cantidades de materiales de la lista guiada
  const handleUpdateCantidad = (matId, text) => {
    const numericText = text.replace(/[^0-9.]/g, "");
    setConsumoCantidades((prev) => ({
      ...prev,
      [matId]: numericText,
    }));
  };

  const handleIncrement = (matId) => {
    const currentVal = parseFloat(consumoCantidades[matId] || 0);
    setConsumoCantidades((prev) => ({
      ...prev,
      [matId]: (currentVal + 1).toString(),
    }));
  };

  const handleDecrement = (matId) => {
    const currentVal = parseFloat(consumoCantidades[matId] || 0);
    if (currentVal <= 0) return;
    setConsumoCantidades((prev) => ({
      ...prev,
      [matId]: Math.max(0, currentVal - 1).toString(),
    }));
  };

  // Manejo de materiales personalizados de emergencia
  const handleAddCustomConsumo = () => {
    const name = customMaterial.trim();
    const qty = parseFloat(customCantidad);

    if (!name) {
      Toast.show({ type: "error", text1: "Ingrese el nombre del material", visibilityTime: 2000 });
      return;
    }
    if (isNaN(qty) || qty <= 0) {
      Toast.show({ type: "error", text1: "Ingrese una cantidad válida", visibilityTime: 2000 });
      return;
    }

    const nuevo = {
      id_temp: generateUUID(),
      material: name,
      cantidad: qty,
      unidad: customUnidad.trim() || "un",
    };

    setCustomConsumos((prev) => [...prev, nuevo]);
    setCustomMaterial("");
    setCustomCantidad("");
    setCustomUnidad("un");
    setShowCustomForm(false);
    Toast.show({ type: "success", text1: "Material personalizado agregado", visibilityTime: 1500 });
  };

  const handleRemoveCustomConsumo = (id_temp) => {
    setCustomConsumos((prev) => prev.filter((c) => c.id_temp !== id_temp));
  };

  // Enviar Reporte y Consumos
  const handleSubmit = async () => {
    if (!mensaje.trim()) {
      Toast.show({ type: "error", text1: "El mensaje del reporte es obligatorio", visibilityTime: 2500 });
      return;
    }

    setIsSubmitting(true);
    try {
      const reporteId = generateUUID();
      const jefeId = userProfile?.id || "jefe-123";
      const fechaPublicacion = new Date().toISOString();

      // 1. Guardar reporte localmente
      saveReporteObra({
        id: reporteId,
        obra_id: activeObra.id,
        jefe_obra_id: jefeId,
        tipo_reporte: tipoReporte,
        mensaje: mensaje.trim(),
        archivos_adjuntos: photos,
        fecha_publicacion: fechaPublicacion,
      });

      // 2. Guardar consumos de la lista guiada
      for (const mat of materialesObra) {
        const qty = parseFloat(consumoCantidades[mat.id]);
        if (qty > 0) {
          saveReporteConsumo({
            id: generateUUID(),
            reporte_obra_id: reporteId,
            material_obra_id: mat.id,
            material: mat.nombre,
            cantidad: qty,
            unidad: mat.unidad_medida,
            fecha: fechaPublicacion,
          });
        }
      }

      // 3. Guardar consumos personalizados de emergencia
      for (const con of customConsumos) {
        saveReporteConsumo({
          id: generateUUID(),
          reporte_obra_id: reporteId,
          material_obra_id: null,
          material: con.material,
          cantidad: con.cantidad,
          unidad: con.unidad,
          fecha: fechaPublicacion,
        });
      }

      Toast.show({
        type: "success",
        text1: "Reporte guardado",
        text2: "Se sincronizará en segundo plano",
        visibilityTime: 3000,
      });

      // Disparar sincronización
      syncReportes().catch((err) => console.log("Background sync error:", err));

      onNavigateBack();
    } catch (error) {
      Toast.show({ type: "error", text1: "Error al guardar el reporte", text2: error.message, visibilityTime: 3000 });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onNavigateBack} style={styles.backBtn} testID="back-button">
          <Text style={styles.backText}>{"<"}</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>{activeObra?.nombre || "Reporte Diario"}</Text>
          <Text style={styles.headerSubtitle}>Reporte y Consumos de Materiales</Text>
        </View>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Sección: Tipo de Reporte */}
        <Text style={styles.sectionTitle}>1. Tipo de Reporte</Text>
        <View style={styles.tipoContainer}>
          {[
            { id: "actualizacion", label: "📝 Diario", desc: "Reporte regular del día" },
            { id: "incidente", label: "⚠️ Incidente", desc: "Problema o retraso" },
            { id: "accidente", label: "🚨 Accidente", desc: "Incidente de seguridad" },
            { id: "otro", label: "⚙️ Otro", desc: "Notas adicionales" },
          ].map((t) => (
            <TouchableOpacity
              key={t.id}
              style={[styles.tipoCard, tipoReporte === t.id && styles.tipoCardActive]}
              onPress={() => setTipoReporte(t.id)}
              activeOpacity={0.7}
            >
              <Text style={styles.tipoLabel}>{t.label}</Text>
              <Text style={styles.tipoDesc}>{t.desc}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Sección: Mensaje de Reporte */}
        <Text style={styles.sectionTitle}>2. Avance Diario y Novedades</Text>
        <TextInput
          placeholder="Escriba cómo fue el día de trabajo, avances logrados, dificultades encontradas..."
          placeholderTextColor={COLORS.textLight}
          value={mensaje}
          onChangeText={setMensaje}
          style={styles.mensajeInput}
          multiline
          numberOfLines={5}
          testID="report-message-input"
        />

        {/* Sección: Fotos Adjuntas */}
        <Text style={styles.sectionTitle}>3. Fotos / Evidencia (Opcional)</Text>
        {photos.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.photosScroll}>
            {photos.map((uri, idx) => (
              <View key={uri} style={styles.photoContainer}>
                <Image source={{ uri }} style={styles.photoThumb} />
                <TouchableOpacity style={styles.removePhotoBtn} onPress={() => handleRemovePhoto(idx)}>
                  <Text style={styles.removePhotoText}>✕</Text>
                </TouchableOpacity>
              </View>
            ))}
          </ScrollView>
        )}

        <View style={styles.photoButtonsContainer}>
          <TouchableOpacity style={styles.photoBtn} onPress={handlePickFromGallery} activeOpacity={0.7}>
            <Image source={CARPETA_LOGO} style={styles.photoBtnIcon} />
            <Text style={styles.photoBtnText}>Galería</Text>
          </TouchableOpacity>
          {!isWeb && (
            <TouchableOpacity style={[styles.photoBtn, styles.photoBtnCamera]} onPress={handleOpenCamera} activeOpacity={0.7}>
              <Image source={CAMARA_LOGO} style={styles.photoBtnIcon} />
              <Text style={styles.photoBtnText}>Cámara</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Sección: Consumo de Materiales Guiado */}
        <View style={styles.divider} />
        <Text style={styles.sectionTitle}>4. Consumo de Materiales del Día</Text>
        <Text style={styles.hintText}>Indique las cantidades consumidas para los materiales de la obra:</Text>

        {materialesObra.length > 0 ? (
          <View style={styles.materialesListContainer}>
            {materialesObra.map((mat) => (
              <View key={mat.id} style={styles.materialRow}>
                <View style={styles.materialInfo}>
                  <Text style={styles.materialName}>{mat.nombre}</Text>
                  <Text style={styles.materialUnit}>Unidad: {mat.unidad_medida}</Text>
                </View>
                <View style={styles.counterContainer}>
                  <TouchableOpacity style={styles.counterBtn} onPress={() => handleDecrement(mat.id)}>
                    <Text style={styles.counterBtnText}>-</Text>
                  </TouchableOpacity>
                  <TextInput
                    style={styles.counterInput}
                    value={consumoCantidades[mat.id] || ""}
                    onChangeText={(text) => handleUpdateCantidad(mat.id, text)}
                    placeholder="0"
                    keyboardType="numeric"
                  />
                  <TouchableOpacity style={styles.counterBtn} onPress={() => handleIncrement(mat.id)}>
                    <Text style={styles.counterBtnText}>+</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.emptyConsumosCard}>
            <Text style={styles.emptyConsumosText}>No hay materiales preconfigurados en esta obra.</Text>
          </View>
        )}

        {/* Consumos Personalizados (Escape de Emergencia) */}
        {customConsumos.length > 0 && (
          <View style={styles.customConsumosListContainer}>
            <Text style={styles.customConsumosTitle}>Materiales personalizados reportados:</Text>
            {customConsumos.map((c) => (
              <View key={c.id_temp} style={styles.consumoRowItem}>
                <View style={styles.consumoDetails}>
                  <Text style={styles.consumoMatName}>{c.material}</Text>
                  <Text style={styles.consumoQty}>{c.cantidad} {c.unidad}</Text>
                </View>
                <TouchableOpacity style={styles.removeConsumoBtn} onPress={() => handleRemoveCustomConsumo(c.id_temp)}>
                  <Text style={styles.removeConsumoBtnText}>Quitar</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {!showCustomForm ? (
          <TouchableOpacity
            style={styles.toggleCustomBtn}
            onPress={() => setShowCustomForm(true)}
          >
            <Text style={styles.toggleCustomBtnText}>➕ Reportar otro material (no listado)</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.customFormCard}>
            <Text style={styles.customFormTitle}>Reportar Material Adicional</Text>
            <TextInput
              placeholder="Nombre del material..."
              placeholderTextColor={COLORS.textLight}
              value={customMaterial}
              onChangeText={setCustomMaterial}
              style={styles.customMaterialInput}
            />
            <View style={styles.qtyRow}>
              <View style={{ flex: 1 }}>
                <TextInput
                  placeholder="Cantidad"
                  placeholderTextColor={COLORS.textLight}
                  value={customCantidad}
                  onChangeText={(t) => setCustomCantidad(t.replace(/[^0-9.]/g, ""))}
                  keyboardType="numeric"
                  style={styles.customQtyInput}
                />
              </View>
              <View style={{ width: 100 }}>
                <TextInput
                  placeholder="Unidad (sacos, etc.)"
                  placeholderTextColor={COLORS.textLight}
                  value={customUnidad}
                  onChangeText={setCustomUnidad}
                  style={styles.customQtyInput}
                />
              </View>
            </View>
            <View style={styles.customFormActions}>
              <TouchableOpacity
                style={[styles.customFormBtn, styles.cancelBtn]}
                onPress={() => setShowCustomForm(false)}
              >
                <Text style={styles.cancelBtnText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.customFormBtn}
                onPress={handleAddCustomConsumo}
              >
                <Text style={styles.addCustomBtnText}>Agregar</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Botón de Enviar Reporte */}
        <TouchableOpacity
          style={[styles.submitBtn, isSubmitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={isSubmitting}
          testID="submit-report-button"
        >
          {isSubmitting ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.submitBtnText}>Enviar Reporte Diario</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 50,
    paddingBottom: 14,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(255,255,255,0.2)",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  backText: {
    color: "#FFF",
    fontSize: 20,
    fontWeight: "bold",
  },
  headerCenter: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 17,
    fontFamily: "Montserrat-Bold",
    color: "#FFF",
  },
  headerSubtitle: {
    fontSize: 12,
    fontFamily: "Inter",
    color: "rgba(255,255,255,0.7)",
    marginTop: 2,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  sectionTitle: {
    fontSize: 16,
    fontFamily: "Montserrat-Bold",
    color: COLORS.primary,
    marginTop: 16,
    marginBottom: 10,
  },
  tipoContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 16,
  },
  tipoCard: {
    flex: 1,
    minWidth: "45%",
    backgroundColor: "#FFF",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 2,
  },
  tipoCardActive: {
    borderColor: COLORS.accent,
    backgroundColor: "#EFF6FF",
    borderWidth: 2,
  },
  tipoLabel: {
    fontSize: 14,
    fontFamily: "Montserrat-Bold",
    color: COLORS.text,
    marginBottom: 4,
  },
  tipoDesc: {
    fontSize: 11,
    fontFamily: "Inter",
    color: COLORS.textLight,
  },
  mensajeInput: {
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 14,
    fontSize: 14,
    fontFamily: "Inter",
    color: COLORS.text,
    backgroundColor: "#FFF",
    minHeight: 120,
    textAlignVertical: "top",
    marginBottom: 20,
  },
  photosScroll: {
    flexDirection: "row",
    marginBottom: 12,
  },
  photoContainer: {
    position: "relative",
    marginRight: 10,
  },
  photoThumb: {
    width: 80,
    height: 80,
    borderRadius: 8,
  },
  removePhotoBtn: {
    position: "absolute",
    top: -5,
    right: -5,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: COLORS.error,
    justifyContent: "center",
    alignItems: "center",
  },
  removePhotoText: {
    color: "#FFF",
    fontSize: 12,
    fontWeight: "bold",
  },
  photoButtonsContainer: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 20,
  },
  photoBtn: {
    flex: 1,
    backgroundColor: "#FFF",
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: COLORS.accent,
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: 8,
  },
  photoBtnCamera: {
    borderColor: COLORS.primary,
  },
  photoBtnIcon: {
    width: 18,
    height: 18,
    resizeMode: "contain",
  },
  photoBtnText: {
    fontSize: 13,
    fontFamily: "Montserrat-Bold",
    color: COLORS.primary,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: 16,
  },
  hintText: {
    fontSize: 12,
    fontFamily: "Inter",
    color: COLORS.textLight,
    marginBottom: 12,
    marginTop: -4,
  },
  materialesListContainer: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 12,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.02,
    shadowRadius: 3,
    elevation: 1,
  },
  materialRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  materialInfo: {
    flex: 1,
    paddingRight: 10,
  },
  materialName: {
    fontSize: 14,
    fontFamily: "Montserrat-SemiBold",
    color: COLORS.text,
  },
  materialUnit: {
    fontSize: 11,
    fontFamily: "Inter",
    color: COLORS.textLight,
    marginTop: 2,
  },
  counterContainer: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    overflow: "hidden",
    backgroundColor: "#F9FAFB",
  },
  counterBtn: {
    width: 34,
    height: 34,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#FFF",
  },
  counterBtnText: {
    fontSize: 16,
    fontFamily: "Montserrat-Bold",
    color: COLORS.primary,
  },
  counterInput: {
    width: 50,
    height: 34,
    textAlign: "center",
    fontSize: 13,
    fontFamily: "Inter-Medium",
    color: COLORS.text,
    backgroundColor: "#F9FAFB",
    padding: 0,
  },
  emptyConsumosCard: {
    backgroundColor: "#F9FAFB",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 16,
    alignItems: "center",
    marginBottom: 20,
  },
  emptyConsumosText: {
    fontSize: 12,
    fontFamily: "Inter",
    color: COLORS.textLight,
  },
  toggleCustomBtn: {
    paddingVertical: 12,
    alignItems: "center",
    marginBottom: 20,
  },
  toggleCustomBtnText: {
    color: COLORS.accent,
    fontFamily: "Montserrat-Bold",
    fontSize: 13,
  },
  customFormCard: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 16,
    marginBottom: 20,
  },
  customFormTitle: {
    fontSize: 13,
    fontFamily: "Montserrat-Bold",
    color: COLORS.text,
    marginBottom: 12,
  },
  customMaterialInput: {
    height: 44,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 13,
    fontFamily: "Inter",
    color: COLORS.text,
    marginBottom: 12,
  },
  qtyRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 16,
  },
  customQtyInput: {
    height: 44,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 13,
    fontFamily: "Inter",
    color: COLORS.text,
    textAlign: "center",
  },
  customFormActions: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 12,
  },
  customFormBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    backgroundColor: COLORS.accent,
  },
  cancelBtn: {
    backgroundColor: "#FFF",
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  cancelBtnText: {
    color: COLORS.textLight,
    fontFamily: "Inter-Medium",
    fontSize: 12,
  },
  addCustomBtnText: {
    color: "#FFF",
    fontFamily: "Montserrat-Bold",
    fontSize: 12,
  },
  customConsumosListContainer: {
    backgroundColor: "#F8FAFC",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 12,
    marginBottom: 12,
  },
  customConsumosTitle: {
    fontSize: 12,
    fontFamily: "Montserrat-Bold",
    color: COLORS.primary,
    marginBottom: 8,
  },
  consumoRowItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#FFF",
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  consumoDetails: {
    flex: 1,
  },
  consumoMatName: {
    fontSize: 13,
    fontFamily: "Montserrat-SemiBold",
    color: COLORS.text,
  },
  consumoQty: {
    fontSize: 12,
    fontFamily: "Inter",
    color: COLORS.accent,
    fontWeight: "600",
    marginTop: 2,
  },
  removeConsumoBtn: {
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  removeConsumoBtnText: {
    color: COLORS.error,
    fontFamily: "Inter",
    fontSize: 12,
    fontWeight: "600",
  },
  submitBtn: {
    height: 52,
    backgroundColor: COLORS.cta,
    borderRadius: 26,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: COLORS.cta,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
    marginTop: 10,
  },
  submitBtnDisabled: {
    opacity: 0.5,
  },
  submitBtnText: {
    color: "#FFF",
    fontFamily: "Montserrat-Bold",
    fontSize: 16,
    letterSpacing: 0.3,
  },
});
