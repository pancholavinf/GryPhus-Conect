# Analysis Report: Mobile App Offline Attendance Screen & UI Architecture (Milestone 4 - R2)

**Author:** Explorer 2 (UI & Photo Capture & Local Attendance Screen Logic)  
**Date:** 2026-07-29  
**Target App:** `app_trackeo_avances` (React Native / Expo Mobile App)

---

## 1. Executive Summary & Context

Milestone 4 (R2) introduces **Mobile App Offline Attendance & Sync** to allow site leaders (*jefes de obra*) to log daily workforce attendance (*asistencia de personal*) in real time, even without internet connectivity.

This document details:
1. Navigation updates in `App.js` and button integration in `ObraMenuScreen.js`.
2. Detailed UI, UX, and operational state logic for `AsistenciaScreen.js`.
3. Database integration layer (`asistencia_diaria` and `asistencia_diaria_detalle`) matching `test_mobile_attendance_sync.test.js`.
4. Mandatory photo evidence capture using `expo-camera` / `expo-image-picker` and image compression via `compressImage`.
5. Automatic corrective report detection (`es_correctivo = true` when attendance for current date & obra already exists).

---

## 2. Navigation Architecture & UI Design Patterns

### 2.1 Stack Navigator Integration in `App.js`
`App.js` uses `@react-navigation/native-stack` with `screenOptions={{ headerShown: false }}`.

Currently registered screens in `App.js`:
- `Login`
- `Home`
- `ObraMenu`
- `SelectionFlow`
- `ReporteDiarioFlow`

To register `AsistenciaScreen`, we add the `<Stack.Screen name="AsistenciaFlow">` screen inside the authenticated stack:

```jsx
// App.js update snippet
import AsistenciaScreen from './src/screens/AsistenciaScreen';

// Inside <Stack.Navigator>:
<Stack.Screen name="AsistenciaFlow">
  {(props) => (
    <AsistenciaScreen
      {...props}
      userProfile={userProfile}
      activeObra={activeObra}
      onNavigateBack={() => props.navigation.goBack()}
    />
  )}
</Stack.Screen>
```

### 2.2 UI Design System Compliance
All screens in `app_trackeo_avances` strictly follow the design system defined in `src/constants/theme.js`:

- **Primary Brand**: `COLORS.primary` (`#1A529B`) – Used for header bar, titles, and primary action buttons.
- **CTA / Secondary**: `COLORS.secondary` / `COLORS.cta` (`#EE741D`) – Used for primary action highlights.
- **Accent**: `COLORS.accent` (`#4BA2E3`) – Used for interactive card borders and sub-controls.
- **Evaluation Statuses**:
  - `1.0 (Día Completo)`: `COLORS.approved` (`#10B981` / Emerald Green)
  - `0.5 (Medio Día)`: `COLORS.pending` (`#F59E0B` / Amber Orange)
  - `0.0 (Ausente)`: `COLORS.error` (`#EF4444` / Crimson Red)
- **Typography**: `Montserrat-Bold`, `Montserrat-SemiBold`, `Inter-Regular`, `Inter-Medium`.
- **Feedback**: `react-native-toast-message` with custom toast renderer defined in `App.js`.

---

## 3. `ObraMenuScreen.js` Integration Strategy

### 3.1 Proposed Navigation Wiring
`ObraMenuScreen` currently accepts `({ userProfile, activeObra, onNavigateBack, onSelectAvance })`. We update props to include `onSelectAsistencia` (or handle navigation via `props.navigation.navigate('AsistenciaFlow')`).

In `App.js`:
```jsx
<Stack.Screen name="ObraMenu">
  {(props) => (
    <ObraMenuScreen
      {...props}
      userProfile={userProfile}
      activeObra={activeObra}
      onNavigateBack={() => props.navigation.goBack()}
      onSelectAvance={() => props.navigation.navigate('SelectionFlow')}
      onSelectAsistencia={() => props.navigation.navigate('AsistenciaFlow')}
    />
  )}
</Stack.Screen>
```

### 3.2 UI Code Snippet for `ObraMenuScreen.js`
In `ObraMenuScreen.js`, directly above or alongside the Avances section, we add an operational card for **Asistencia de Personal**:

```jsx
{/* SECCIÓN: Asistencia de Personal */}
<View style={styles.asistenciaSection}>
  <Text style={styles.sectionTitle}>Asistencia de Personal</Text>
  <Text style={styles.sectionDesc}>
    Control diario de asistencia de la cuadrilla y maestros asignados a la obra con foto evidencia.
  </Text>
  <TouchableOpacity
    style={[styles.asistenciaBtn, { backgroundColor: cardColor }]}
    onPress={onSelectAsistencia}
    testID="btn-asistencia"
    activeOpacity={0.85}
  >
    <View style={styles.btnIconContent}>
      <Text style={styles.asistenciaBtnText}>📋 Registrar Asistencia</Text>
    </View>
  </TouchableOpacity>
</View>
```

---

## 4. `AsistenciaScreen.js` UI & Operational Screen Logic

### 4.1 Functional Requirements & Flow
1. **Screen Load**:
   - Reads `activeObra.id` and current local date (`YYYY-MM-DD`).
   - Queries assigned maestros via `getMaestrosForObra(activeObra.id)`.
   - Checks if an attendance record already exists for today via `checkAttendanceExistsToday(activeObra.id, currentDate)`.
   - If existing record found: sets state `esCorrectivo = true` and displays notice header `"⚠️ REPORTE CORRECTIVO DE ASISTENCIA"`.

2. **Maestro List & Evaluation Status Selector**:
   - Displays each assigned maestro with:
     - Full Name (`nombre_completo`)
     - RUT (`rut`)
     - Role/Cargo (`tipo_maestro_nombre` e.g., Carpintero, Encofrador)
   - Evaluation Pills for status selection:
     - `[1.0] Día Completo` (Default)
     - `[0.5] Medio Día`
     - `[0.0] Ausente`
   - Optional observations text field (`observaciones`) for custom note per worker (e.g., "Retiro anticipado 14:00 hrs").

3. **Mandatory Photo Evidence Capture**:
   - Requires taking a live photo (via camera) or selecting from gallery.
   - Invokes `compressImage(uri)` before setting state.
   - Shows photo preview thumbnail with a delete button (`✕`).
   - If user attempts submission without a photo:
     - Displays error Toast: `"Foto de evidencia obligatoria"`, `"Debe capturar o adjuntar una foto de la cuadrilla antes de guardar."`
     - Prevents submission.

4. **Submission & Local Database Persistence**:
   - Generates unique ID `ast-${UUID}` for `asistencia_diaria`.
   - Generates detail records for each maestro in `asistencia_diaria_detalle`.
   - Calls `saveLocalAttendance(...)` in `db.js`.
   - Displays success Toast: `"Asistencia guardada"`, `"Se sincronizará en segundo plano."`.
   - Triggers `syncAsistencia()` and navigates back to `ObraMenu`.

---

## 5. Required Database Helper Functions (`src/database/db.js`)

To support `AsistenciaScreen.js`, the database layer must expose:

```js
/**
 * Returns all assigned maestros for an obra joined with their cargo/tipo_maestro.
 */
export function getMaestrosForObra(obraId) {
  try {
    const database = getDatabase();
    return database.getAllSync(
      `SELECT 
        m.id as maestro_id, 
        m.rut, 
        m.nombre_completo, 
        tm.nombre as tipo_maestro_nombre, 
        tm.sueldo_diario
       FROM maestros m
       JOIN obras_maestros om ON m.id = om.maestro_id
       LEFT JOIN tipos_maestro tm ON m.tipo_maestro_id = tm.id
       WHERE om.obra_id = ?`,
      [obraId]
    );
  } catch (_e) {
    return getCachedMaestrosForObra(obraId); // Memory cache fallback for web
  }
}

/**
 * Checks if attendance was already recorded for today in local DB.
 */
export function checkAttendanceExistsToday(obraId, fecha) {
  try {
    const database = getDatabase();
    const row = database.getFirstSync(
      `SELECT id FROM asistencia_diaria WHERE obra_id = ? AND fecha = ?`,
      [obraId, fecha]
    );
    return !!row;
  } catch (_e) {
    return getPendingAttendanceForObraAndDate(obraId, fecha);
  }
}

/**
 * Saves attendance header and detail records locally to SQLite & memory cache.
 */
export function saveLocalAttendance({ id, obra_id, fecha, foto_evidencia_url, es_correctivo, registrado_por, detalles }) {
  if (!foto_evidencia_url || foto_evidencia_url.trim() === '') {
    throw new Error('Foto de evidencia obligatoria para registrar asistencia.');
  }

  const header = {
    id,
    obra_id,
    fecha,
    foto_evidencia_url,
    es_correctivo: es_correctivo ? 1 : 0,
    registrado_por,
    synced: 0,
    fecha_captura_local: new Date().toISOString(),
    fecha_subida_servidor: null,
  };

  addPendingAsistencia(header, detalles);

  try {
    const database = getDatabase();
    database.runSync(
      `INSERT INTO asistencia_diaria
        (id, obra_id, fecha, foto_evidencia_url, es_correctivo, registrado_por, synced, fecha_captura_local)
       VALUES (?, ?, ?, ?, ?, ?, 0, ?)`,
      [id, obra_id, fecha, foto_evidencia_url, es_correctivo ? 1 : 0, registrado_por, header.fecha_captura_local]
    );

    for (const d of detalles) {
      database.runSync(
        `INSERT INTO asistencia_diaria_detalle
          (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones)
         VALUES (?, ?, ?, ?, ?)`,
        [d.id, id, d.maestro_id, d.estado_asistencia, d.observaciones || '']
      );
    }
  } catch (_e) {
    // Web memory fallback handles it
  }

  return { header, detalles };
}
```

---

## 6. Proposed Full Source Code: `src/screens/AsistenciaScreen.js`

Here is the exact proposed implementation for `src/screens/AsistenciaScreen.js`:

```javascript
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Platform,
  StatusBar,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import {
  getMaestrosForObra,
  checkAttendanceExistsToday,
  saveLocalAttendance,
} from "../database/db";
import { compressImage } from "../services/imageCompressor";
import { syncAsistencia } from "../database/sync";
import { COLORS } from "../constants/theme";
import Toast from "react-native-toast-message";

const CARPETA_LOGO = require("../../assets/sprites/carpeta_logo.png");
const CAMARA_LOGO = require("../../assets/sprites/camara_logo.png");
const LISTO_LOGO = require("../../assets/sprites/listo_logo.png");

function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function getTodayFormatted() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function AsistenciaScreen({
  userProfile,
  activeObra,
  onNavigateBack,
}) {
  const [maestros, setMaestros] = useState([]);
  const [evaluaciones, setEvaluaciones] = useState({}); // { [maestroId]: { estado: 1.0, observaciones: "" } }
  const [fotoEvidencia, setFotoEvidencia] = useState(null);
  const [isCorrectivo, setIsCorrectivo] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isWeb = Platform.OS === "web";
  const fechaHoy = getTodayFormatted();

  useEffect(() => {
    if (!activeObra?.id) return;
    try {
      // 1. Fetch assigned maestros
      const list = getMaestrosForObra(activeObra.id) || [];
      setMaestros(list);

      // Initialize default evaluation (1.0 Día Completo)
      const initEval = {};
      list.forEach((m) => {
        initEval[m.maestro_id] = { estado: 1.0, observaciones: "" };
      });
      setEvaluaciones(initEval);

      // 2. Check if attendance already exists for today
      const exists = checkAttendanceExistsToday(activeObra.id, fechaHoy);
      setIsCorrectivo(!!exists);
    } catch (err) {
      console.error("Error loading attendance initialization:", err);
    } finally {
      setIsLoading(false);
    }
  }, [activeObra?.id, fechaHoy]);

  // Handle Photo Capture (Camera)
  const handleOpenCamera = async () => {
    if (isWeb) return;
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Toast.show({
        type: "error",
        text1: "Permiso denegado",
        text2: "Se requiere acceso a la cámara para tomar evidencia.",
        visibilityTime: 2500,
      });
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.85 });
    if (!result.canceled && result.assets?.[0]?.uri) {
      const compressed = await compressImage(result.assets[0].uri);
      setFotoEvidencia(compressed);
      Toast.show({ type: "success", text1: "Foto de evidencia capturada", visibilityTime: 1500 });
    }
  };

  // Handle Pick from Gallery
  const handlePickFromGallery = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Toast.show({
        type: "error",
        text1: "Permiso denegado",
        text2: "Se requiere acceso a la galería.",
        visibilityTime: 2500,
      });
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
    });
    if (!result.canceled && result.assets?.[0]?.uri) {
      const compressed = await compressImage(result.assets[0].uri);
      setFotoEvidencia(compressed);
      Toast.show({ type: "success", text1: "Foto seleccionada", visibilityTime: 1500 });
    }
  };

  // Toggle evaluation status
  const handleSelectEstado = (maestroId, val) => {
    setEvaluaciones((prev) => ({
      ...prev,
      [maestroId]: {
        ...prev[maestroId],
        estado: val,
      },
    }));
  };

  // Update observations per maestro
  const handleUpdateObs = (maestroId, text) => {
    setEvaluaciones((prev) => ({
      ...prev,
      [maestroId]: {
        ...prev[maestroId],
        observaciones: text,
      },
    }));
  };

  // Submit Attendance Record
  const handleSubmit = async () => {
    // 1. Mandatory Photo Evidence Validation
    if (!fotoEvidencia) {
      Toast.show({
        type: "error",
        text1: "Foto de evidencia obligatoria",
        text2: "Debe tomar o adjuntar una foto de la cuadrilla antes de guardar.",
        visibilityTime: 3500,
      });
      return;
    }

    if (maestros.length === 0) {
      Toast.show({
        type: "error",
        text1: "Sin cuadrilla asignada",
        text2: "No hay maestros asignados a esta obra.",
        visibilityTime: 2500,
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const headerId = `ast-${generateUUID()}`;
      const registradoPor = userProfile?.id || "jefe-123";

      const detalles = maestros.map((m) => ({
        id: `det-${generateUUID()}`,
        maestro_id: m.maestro_id,
        estado_asistencia: evaluaciones[m.maestro_id]?.estado ?? 1.0,
        observaciones: evaluaciones[m.maestro_id]?.observaciones || "",
      }));

      // 2. Save locally in SQLite & memory cache
      saveLocalAttendance({
        id: headerId,
        obra_id: activeObra.id,
        fecha: fechaHoy,
        foto_evidencia_url: fotoEvidencia,
        es_correctivo: isCorrectivo,
        registrado_por: registradoPor,
        detalles,
      });

      Toast.show({
        type: "success",
        text1: isCorrectivo
          ? "Reporte Correctivo Guardado"
          : "Asistencia Guardada Exitosamente",
        text2: "Se sincronizará en segundo plano al estar online.",
        visibilityTime: 3000,
      });

      // 3. Trigger background sync attempt
      syncAsistencia?.().catch((e) => console.log("Background sync error:", e));

      // Navigate back after short delay
      setTimeout(() => {
        onNavigateBack?.();
      }, 1000);
    } catch (err) {
      Toast.show({
        type: "error",
        text1: "Error al guardar asistencia",
        text2: err.message,
        visibilityTime: 3000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cargando cuadrilla de la obra...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container} testID="asistencia-screen">
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onNavigateBack} style={styles.backBtn} testID="back-button">
          <Text style={styles.backText}>{"<"}</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {activeObra?.nombre || "Asistencia de Personal"}
          </Text>
          <Text style={styles.headerSubtitle}>Fecha: {fechaHoy}</Text>
        </View>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Banner Reporte Correctivo */}
        {isCorrectivo && (
          <View style={styles.correctiveBanner} testID="corrective-banner">
            <Text style={styles.correctiveBannerTitle}>⚠️ Reporte Correctivo de Asistencia</Text>
            <Text style={styles.correctiveBannerText}>
              Ya existe una toma de asistencia previa para el día de hoy ({fechaHoy}). Este registro marcará el envío como correctivo.
            </Text>
          </View>
        )}

        {/* Sección: Evidencia Fotográfica (Obligatoria) */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>
            1. Foto de Evidencia <Text style={styles.requiredTag}>(Obligatorio)</Text>
          </Text>
          <Text style={styles.sectionDesc}>
            Capture una fotografía actual de la cuadrilla o frente de trabajo para validar el registro.
          </Text>

          {fotoEvidencia ? (
            <View style={styles.previewContainer}>
              <Image source={{ uri: fotoEvidencia }} style={styles.photoPreview} />
              <TouchableOpacity style={styles.removePhotoBtn} onPress={() => setFotoEvidencia(null)}>
                <Text style={styles.removePhotoText}>✕ Cambiar Foto</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.photoButtonsContainer}>
              {!isWeb && (
                <TouchableOpacity
                  style={[styles.photoBtn, styles.photoBtnCamera]}
                  onPress={handleOpenCamera}
                  activeOpacity={0.7}
                  testID="btn-camera"
                >
                  <Image source={CAMARA_LOGO} style={styles.photoBtnIcon} />
                  <Text style={styles.photoBtnTextCamera}>Tomar Foto</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity
                style={styles.photoBtn}
                onPress={handlePickFromGallery}
                activeOpacity={0.7}
                testID="btn-gallery"
              >
                <Image source={CARPETA_LOGO} style={styles.photoBtnIcon} />
                <Text style={styles.photoBtnText}>Galería</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Sección: Evaluación de Asistencia de Cuadrilla */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>2. Control de Asistencia ({maestros.length} Personal)</Text>
          <Text style={styles.sectionDesc}>
            Seleccione el estado de jornada para cada maestro asignado a la obra:
          </Text>

          {maestros.length > 0 ? (
            maestros.map((m) => {
              const currentEval = evaluaciones[m.maestro_id]?.estado ?? 1.0;
              const currentObs = evaluaciones[m.maestro_id]?.observaciones ?? "";

              return (
                <View key={m.maestro_id} style={styles.maestroCard} testID={`maestro-card-${m.maestro_id}`}>
                  <View style={styles.maestroHeader}>
                    <View style={styles.maestroInfo}>
                      <Text style={styles.maestroName}>{m.nombre_completo}</Text>
                      <Text style={styles.maestroRole}>{m.tipo_maestro_nombre || "Maestro"} • RUT: {m.rut || "N/A"}</Text>
                    </View>
                  </View>

                  {/* Segmented Status Control */}
                  <View style={styles.statusSegmentContainer}>
                    <TouchableOpacity
                      style={[
                        styles.segmentBtn,
                        currentEval === 1.0 && styles.segmentBtnCompleto,
                      ]}
                      onPress={() => handleSelectEstado(m.maestro_id, 1.0)}
                      activeOpacity={0.8}
                    >
                      <Text
                        style={[
                          styles.segmentText,
                          currentEval === 1.0 && styles.segmentTextActive,
                        ]}
                      >
                        1.0 Día Compl.
                      </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[
                        styles.segmentBtn,
                        currentEval === 0.5 && styles.segmentBtnMedio,
                      ]}
                      onPress={() => handleSelectEstado(m.maestro_id, 0.5)}
                      activeOpacity={0.8}
                    >
                      <Text
                        style={[
                          styles.segmentText,
                          currentEval === 0.5 && styles.segmentTextActive,
                        ]}
                      >
                        0.5 Medio Día
                      </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[
                        styles.segmentBtn,
                        currentEval === 0.0 && styles.segmentBtnAusente,
                      ]}
                      onPress={() => handleSelectEstado(m.maestro_id, 0.0)}
                      activeOpacity={0.8}
                    >
                      <Text
                        style={[
                          styles.segmentText,
                          currentEval === 0.0 && styles.segmentTextActive,
                        ]}
                      >
                        0.0 Ausente
                      </Text>
                    </TouchableOpacity>
                  </View>

                  {/* Opcional: Observación por maestro */}
                  {currentEval !== 1.0 && (
                    <TextInput
                      placeholder="Observaciones (motivo de ausencia / medio día)..."
                      placeholderTextColor={COLORS.textLight}
                      value={currentObs}
                      onChangeText={(t) => handleUpdateObs(m.maestro_id, t)}
                      style={styles.obsInput}
                    />
                  )}
                </View>
              );
            })
          ) : (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyText}>No hay maestros asignados a esta obra.</Text>
            </View>
          )}
        </View>

        {/* Action Button */}
        <TouchableOpacity
          style={[styles.submitBtn, isSubmitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={isSubmitting}
          testID="submit-asistencia-button"
        >
          {isSubmitting ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.submitBtnText}>
              {isCorrectivo ? "Enviar Reporte Correctivo" : "Guardar Asistencia Diaria"}
            </Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: COLORS.background,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    fontFamily: "Inter-Medium",
    color: COLORS.textLight,
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
    color: "rgba(255,255,255,0.8)",
    marginTop: 2,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  correctiveBanner: {
    backgroundColor: "#FEF3C7",
    borderWidth: 1.5,
    borderColor: "#F59E0B",
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  correctiveBannerTitle: {
    fontSize: 14,
    fontFamily: "Montserrat-Bold",
    color: "#B45309",
    marginBottom: 4,
  },
  correctiveBannerText: {
    fontSize: 12,
    fontFamily: "Inter",
    color: "#78350F",
    lineHeight: 16,
  },
  sectionCard: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 5,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontFamily: "Montserrat-Bold",
    color: COLORS.primary,
    marginBottom: 4,
  },
  requiredTag: {
    color: COLORS.error,
    fontSize: 13,
  },
  sectionDesc: {
    fontSize: 12,
    fontFamily: "Inter",
    color: COLORS.textLight,
    marginBottom: 14,
  },
  photoButtonsContainer: {
    flexDirection: "row",
    gap: 12,
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
    backgroundColor: COLORS.primary,
  },
  photoBtnIcon: {
    width: 20,
    height: 20,
    resizeMode: "contain",
  },
  photoBtnText: {
    fontSize: 13,
    fontFamily: "Montserrat-Bold",
    color: COLORS.primary,
  },
  photoBtnTextCamera: {
    fontSize: 13,
    fontFamily: "Montserrat-Bold",
    color: "#FFF",
  },
  previewContainer: {
    alignItems: "center",
  },
  photoPreview: {
    width: "100%",
    height: 180,
    borderRadius: 10,
    marginBottom: 10,
  },
  removePhotoBtn: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    backgroundColor: COLORS.error,
    borderRadius: 8,
  },
  removePhotoText: {
    color: "#FFF",
    fontSize: 12,
    fontFamily: "Montserrat-Bold",
  },
  maestroCard: {
    backgroundColor: "#F9FAFB",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    padding: 12,
    marginBottom: 12,
  },
  maestroHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  maestroInfo: {
    flex: 1,
  },
  maestroName: {
    fontSize: 14,
    fontFamily: "Montserrat-Bold",
    color: COLORS.text,
  },
  maestroRole: {
    fontSize: 11,
    fontFamily: "Inter",
    color: COLORS.textLight,
    marginTop: 2,
  },
  statusSegmentContainer: {
    flexDirection: "row",
    backgroundColor: "#E5E7EB",
    borderRadius: 8,
    padding: 3,
    gap: 4,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: 6,
  },
  segmentBtnCompleto: {
    backgroundColor: COLORS.approved,
  },
  segmentBtnMedio: {
    backgroundColor: COLORS.pending,
  },
  segmentBtnAusente: {
    backgroundColor: COLORS.error,
  },
  segmentText: {
    fontSize: 11,
    fontFamily: "Montserrat-Bold",
    color: "#4B5563",
  },
  segmentTextActive: {
    color: "#FFF",
  },
  obsInput: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 12,
    fontFamily: "Inter",
    color: COLORS.text,
    backgroundColor: "#FFF",
  },
  emptyCard: {
    padding: 16,
    alignItems: "center",
  },
  emptyText: {
    fontSize: 13,
    fontFamily: "Inter",
    color: COLORS.textLight,
  },
  submitBtn: {
    backgroundColor: COLORS.cta,
    height: 52,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 5,
    elevation: 4,
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    color: "#FFF",
    fontSize: 15,
    fontFamily: "Montserrat-Bold",
    letterSpacing: 0.3,
  },
});
```

---

## 7. Verification Strategy & Invalidation Conditions

### Verification Method
1. **Catalog & Database Integrity**:
   - Verify `getMaestrosForObra(obraId)` correctly joins `maestros`, `obras_maestros`, and `tipos_maestro`.
   - Verify local SQLite insertion of `asistencia_diaria` and `asistencia_diaria_detalle` with `synced = 0`.
2. **Corrective Notice & Flag Validation**:
   - Verify `checkAttendanceExistsToday(obraId, fecha)` detects existing records and toggles `es_correctivo = true` on re-submission.
3. **Mandatory Photo Capture Validation**:
   - Confirm submitting without a photo triggers the error Toast and halts submission.
4. **Execution of Automated Test Suite**:
   - Run `npx jest tests/test_mobile_attendance_sync.test.js` or `npm run test:e2e` to verify payload structure and sync logic.

---

## 8. Summary of Component Deliverables & Handoff Summary

| Target File | Description / Modification |
|-------------|----------------------------|
| `App.js` | Register `<Stack.Screen name="AsistenciaFlow">` in main navigator stack. |
| `src/screens/ObraMenuScreen.js` | Add `onSelectAsistencia` prop and render "Asistencia de Personal" operational button card. |
| `src/screens/AsistenciaScreen.js` | Create component with maestro loading, 1.0/0.5/0.0 evaluation segment controls, mandatory photo capture, corrective detection, and SQLite local persistence. |
| `src/database/db.js` | Expose `getMaestrosForObra`, `checkAttendanceExistsToday`, and `saveLocalAttendance`. |

