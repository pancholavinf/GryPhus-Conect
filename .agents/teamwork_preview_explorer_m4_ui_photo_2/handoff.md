# Handoff Report: Explorer 2 (UI & Photo Capture & Local Attendance Screen Logic)

**Target Milestone:** Milestone 4 (R2: Mobile App Offline Attendance & Sync)  
**Working Directory:** `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_ui_photo_2`  
**Handoff Type:** Hard (Task Complete)

---

## 1. Observation

1. **Repository Structure**:
   - Mobile app directory: `app_trackeo_avances/` (React Native / Expo 54).
   - `App.js` configures `@react-navigation/native-stack` with `Stack.Navigator` (lines 223–277).
   - `package.json` includes `expo-camera` (`~17.0.10`), `expo-image-picker` (`~17.0.11`), `expo-sqlite` (`~16.0.10`), `expo-image-manipulator` (`~14.0.8`), `@react-navigation/native-stack` (`^6.11.0`).

2. **Existing Menu & UI Design**:
   - `src/screens/ObraMenuScreen.js` handles operational options for assigned obras, currently rendering `Avances de Obra` (`avanceBtn`, line 287) and `Reporte Diario de Terreno` (line 300).
   - `src/constants/theme.js` defines `COLORS.primary` (`#1A529B`), `COLORS.secondary` (`#EE741D`), `COLORS.approved` (`#10B981`), `COLORS.pending` (`#F59E0B`), `COLORS.error` (`#EF4444`).

3. **Attendance Local Storage & Sync Simulator Specifications**:
   - `tests/test_mobile_attendance_sync.test.js` specifies `MobileAttendanceStorageSimulator` testing:
     - Catalog tables: `tipos_maestro`, `maestros`, `obras_maestros`.
     - Evaluation statuses: `1.0` (Día Completo), `0.5` (Medio Día), `0.0` (Ausente).
     - Mandatory photo evidence validation: throws `"Foto de evidencia obligatoria"` when photo is missing.
     - Corrective report flag (`es_correctivo = true` when re-submitting attendance for the same date & obra).
     - Header schema: `asistencia_diaria` (`id`, `obra_id`, `fecha`, `foto_evidencia_url`, `es_correctivo`, `registrado_por`, `synced = 0`, `fecha_captura_local`, `fecha_subida_servidor`).
     - Detail schema: `asistencia_diaria_detalle` (`id`, `asistencia_diaria_id`, `maestro_id`, `estado_asistencia`, `observaciones`).

---

## 2. Logic Chain

1. **Observation 1 & 2** show that navigation in `App.js` routes from `HomeScreen` -> `ObraMenuScreen` -> operational flows.
   - *Inference*: Adding an operational button "Asistencia de Personal" in `ObraMenuScreen.js` and registering `<Stack.Screen name="AsistenciaFlow">` in `App.js` allows seamless navigation to `AsistenciaScreen.js`.

2. **Observation 2 & 3** indicate that site leaders require an offline screen (`AsistenciaScreen.js`) to query assigned maestros, select evaluation statuses (1.0, 0.5, 0.0), capture mandatory photo evidence, detect corrective reports, and persist locally to SQLite and memory cache.
   - *Inference*: `AsistenciaScreen.js` can be built using `expo-camera` / `expo-image-picker` with `compressImage()`, rendering segmented buttons per maestro for evaluation, checking existing date records to set `es_correctivo`, and calling `saveLocalAttendance(...)`.

3. **Observation 3** confirms that attendance headers require `synced = 0` initially and must enforce mandatory photo evidence before local saving.
   - *Inference*: The screen logic must validate `fotoEvidencia` before executing `saveLocalAttendance(...)`. If empty, a Toast error is displayed and submission is halted.

---

## 3. Caveats

- **Web Mode Limitations**: `expo-camera` is not available on web, so `AsistenciaScreen.js` gracefully degrades on web to gallery selection (`expo-image-picker`) and memory cache persistence (`addPendingAsistencia`).
- **Database Helper Dependencies**: Implementation requires `getMaestrosForObra`, `checkAttendanceExistsToday`, and `saveLocalAttendance` in `src/database/db.js` (detailed in `analysis.md`).

---

## 4. Conclusion

The complete UI specification, navigation wiring, state machine, photo capture integration, corrective notice logic, and exact source code for `AsistenciaScreen.js` and `ObraMenuScreen.js` have been formulated and documented in `analysis.md`. The design fulfills all requirements of Milestone 4 (R2) and matches `test_mobile_attendance_sync.test.js`.

---

## 5. Verification Method

To verify the implementation once applied by implementers:

1. **Static Analysis & File Inspection**:
   - Inspect `app_trackeo_avances/App.js` for `AsistenciaFlow` screen registration.
   - Inspect `app_trackeo_avances/src/screens/ObraMenuScreen.js` for `btn-asistencia` operational button.
   - Inspect `app_trackeo_avances/src/screens/AsistenciaScreen.js` for segment controls (1.0, 0.5, 0.0), camera launch, corrective banner, and `saveLocalAttendance` call.

2. **Automated Test Execution**:
   - Run Jest tests:
     ```cmd
     cd app_trackeo_avances
     npm test tests/test_mobile_attendance_sync.test.js
     ```

3. **Invalidation Conditions**:
   - Attempting to submit attendance without capturing/selecting a photo must be rejected with `"Foto de evidencia obligatoria"`.
   - Submitting attendance for an obra on a date that already has a record must set `es_correctivo = true` and show the corrective banner.
