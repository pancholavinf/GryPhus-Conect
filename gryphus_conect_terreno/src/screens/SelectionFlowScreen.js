import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  Image, ScrollView, ActivityIndicator, StatusBar, Platform,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { getItemsForObra, saveAdvance } from '../database/db';
import { compressImage } from '../services/imageCompressor';
import { syncAdvances } from '../database/sync';
import { getCachedItemsForObra } from '../services/memoryCache';
import { COLORS } from '../constants/theme';
import Toast from 'react-native-toast-message';

// ── Step keys ─────────────────────────────────────────────────────
const STEP = {
  ESTRUCTURA : 'estructura',
  DIMENSION  : 'dimension',
  UBICACION  : 'ubicacion',
  LARGO      : 'largo',     // conditional — only when still ambiguous
  CANTIDAD   : 'cantidad',
  PHOTO      : 'photo',
  COMMENT    : 'comment',
  CONFIRM    : 'confirm',
};

const STEP_LABELS = {
  [STEP.ESTRUCTURA] : 'Estructura',
  [STEP.DIMENSION]  : 'Dimensión',
  [STEP.UBICACION]  : 'Ubicación',
  [STEP.LARGO]      : 'Largo',
  [STEP.CANTIDAD]   : 'Cantidad',
  [STEP.PHOTO]      : 'Foto',
  [STEP.COMMENT]    : 'Comentario',
  [STEP.CONFIRM]    : 'Confirmar',
};

// ── Helpers ───────────────────────────────────────────────────────
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

/** Unique sorted non-null values */
function unique(arr) {
  return [...new Set(arr.filter(v => v != null && v !== '' && v !== 'null' && v !== 'undefined'))]
    .sort((a, b) => String(a).localeCompare(String(b), undefined, { numeric: true }));
}

/** mm → "X.XX m" */
function mmToM(val) {
  const n = parseFloat(val);
  return isNaN(n) ? String(val) : `${(n / 1000).toFixed(2)} m`;
}

/** Filter items by a complete selection state object */
function filterBySelection(items, sel) {
  return items.filter(i =>
    (sel.estructura == null || i.estructura === sel.estructura) &&
    (sel.dimension  == null || i.dimension  === sel.dimension)  &&
    (sel.ubicacion  == null || i.ubicacion  === sel.ubicacion)  &&
    (sel.largo      == null || String(i.largo) === String(sel.largo))
  );
}

// ─────────────────────────────────────────────────────────────────
export default function SelectionFlowScreen({ userProfile, activeObra, onNavigateBack }) {
  const [items, setItems] = useState([]);

  // Current visible step and the list of steps the user actually saw
  const [currentStep, setCurrentStep] = useState(STEP.ESTRUCTURA);
  const [stepHistory, setStepHistory] = useState([]);

  // Selections
  const [selEstructura, setSelEstructura] = useState(null);
  const [selDimension,  setSelDimension]  = useState(null);
  const [selUbicacion,  setSelUbicacion]  = useState(null);
  const [selLargo,      setSelLargo]      = useState(null);
  const [selectedItem,  setSelectedItem]  = useState(null);

  // Mandatory input steps
  const [cantidad,    setCantidad]    = useState('');
  const [photoUri,    setPhotoUri]    = useState(null);
  const [comment,     setComment]     = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Multi-item batch state
  const [batchItems,  setBatchItems]  = useState([]);

  const submittingRef = useRef(false);
  const isWeb = Platform.OS === 'web';

  // ── Load items (SQLite on native, memory cache on web) ────────────
  useEffect(() => {
    if (!activeObra?.id) return;
    try {
      let list = getItemsForObra(activeObra.id);
      if (!list?.length) list = getCachedItemsForObra(activeObra.id);
      setItems(list || []);
    } catch {
      setItems(getCachedItemsForObra(activeObra.id) || []);
    }
  }, [activeObra?.id]);

  // ── Bootstrap: run advance logic when items first load ────────────
  useEffect(() => {
    if (items.length > 0) {
      advanceWith({ estructura: null, dimension: null, ubicacion: null, largo: null });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  // ── Core adaptive navigation ──────────────────────────────────────
  /**
   * advanceWith(sel) — given a complete selection snapshot, decides
   * which step to show next, auto-skipping steps with only 1 option.
   * Only stops (shows a step) when there is >1 option for the user to choose.
   */
  function advanceWith(sel) {
    // Apply new state values
    setSelEstructura(sel.estructura ?? null);
    setSelDimension (sel.dimension  ?? null);
    setSelUbicacion (sel.ubicacion  ?? null);
    setSelLargo     (sel.largo      ?? null);

    const filtered = filterBySelection(items, sel);

    // ✅ Item uniquely identified → jump to CANTIDAD
    if (filtered.length === 1) {
      setSelectedItem(filtered[0]);
      showStep(STEP.CANTIDAD);
      return;
    }

    // ❌ No match (shouldn't happen with valid data)
    if (filtered.length === 0) {
      Toast.show({ type: 'error', text1: 'Sin resultados', text2: 'Reinicie la selección', visibilityTime: 2500 });
      showStep(STEP.ESTRUCTURA);
      return;
    }

    // Determine next step based on what's still unresolved ─────────

    // 1. ESTRUCTURA
    if (sel.estructura == null) {
      const opts = unique(items.map(i => i.estructura));
      if (opts.length === 1) {
        advanceWith({ ...sel, estructura: opts[0] });   // auto-skip
      } else {
        showStep(STEP.ESTRUCTURA);
      }
      return;
    }

    // 2. DIMENSION
    if (sel.dimension == null) {
      const opts = unique(filtered.map(i => i.dimension));
      if (opts.length === 1) {
        advanceWith({ ...sel, dimension: opts[0] });    // auto-skip
      } else {
        showStep(STEP.DIMENSION);
      }
      return;
    }

    // 3. UBICACION
    if (sel.ubicacion == null) {
      const opts = unique(filtered.map(i => i.ubicacion));
      if (opts.length === 1) {
        advanceWith({ ...sel, ubicacion: opts[0] });    // auto-skip
      } else {
        showStep(STEP.UBICACION);
      }
      return;
    }

    // 4. LARGO (conditional disambiguator)
    if (sel.largo == null) {
      const opts = unique(filtered.map(i => String(i.largo)));
      if (opts.length === 1) {
        advanceWith({ ...sel, largo: opts[0] });        // auto-skip
      } else if (opts.length > 1) {
        showStep(STEP.LARGO);
      } else {
        // No largo data — pick first match and continue
        setSelectedItem(filtered[0]);
        showStep(STEP.CANTIDAD);
      }
      return;
    }

    // Fallback: still ambiguous — pick first and go to CANTIDAD
    setSelectedItem(filtered[0]);
    showStep(STEP.CANTIDAD);
  }

  /** Marks step as visible and updates history */
  function showStep(step) {
    setCurrentStep(step);
    setStepHistory(prev => prev.includes(step) ? prev : [...prev, step]);
  }

  // ── Helper to build batch item object ─────────────────────────────
  function buildBatchItem(item, qty, estructura, dimension, ubicacion, largo) {
    const label = [estructura, dimension, largo ? mmToM(largo) : null, ubicacion].filter(Boolean).join(' · ') || item?.descripcion || 'Ítem';
    return {
      item,
      cantidad: qty,
      label,
      estructura,
      dimension,
      ubicacion,
      largo,
    };
  }

  // ── Batch action handlers ─────────────────────────────────────────
  const handleAddToBatch = () => {
    if (!selectedItem) {
      Toast.show({ type: 'error', text1: 'Sin ítem seleccionado', visibilityTime: 2000 });
      return;
    }
    const qty = parseInt(cantidad, 10);
    if (isNaN(qty) || qty <= 0) {
      Toast.show({ type: 'error', text1: 'Ingrese una cantidad válida', visibilityTime: 2000 });
      return;
    }

    const existingIndex = batchItems.findIndex((b) => b.item.id === selectedItem.id);
    let updated = [];
    if (existingIndex >= 0) {
      updated = [...batchItems];
      updated[existingIndex] = {
        ...updated[existingIndex],
        cantidad: updated[existingIndex].cantidad + qty,
      };
      Toast.show({
        type: 'info',
        text1: '✓ Cantidad sumada',
        text2: `Total acumulado: ${updated[existingIndex].cantidad} ${selectedItem.unidad || 'un'}`,
        visibilityTime: 2500,
      });
    } else {
      const newItem = buildBatchItem(selectedItem, qty, selEstructura, selDimension, selUbicacion, selLargo);
      updated = [...batchItems, newItem];
      Toast.show({
        type: 'success',
        text1: '✓ Ítem agregado al lote',
        text2: `${updated.length} ítem(s) en total en este lote`,
        visibilityTime: 2000,
      });
    }

    setBatchItems(updated);
    setCantidad('');
    setSelectedItem(null);
    advanceWith({ estructura: null, dimension: null, ubicacion: null, largo: null });
  };

  const handleProceedToPhoto = () => {
    let updated = [...batchItems];
    if (selectedItem && cantidad) {
      const qty = parseInt(cantidad, 10);
      if (!isNaN(qty) && qty > 0) {
        const existingIndex = updated.findIndex((b) => b.item.id === selectedItem.id);
        if (existingIndex >= 0) {
          updated[existingIndex] = {
            ...updated[existingIndex],
            cantidad: updated[existingIndex].cantidad + qty,
          };
        } else {
          const newItem = buildBatchItem(selectedItem, qty, selEstructura, selDimension, selUbicacion, selLargo);
          updated.push(newItem);
        }
        setBatchItems(updated);
        setCantidad('');
        setSelectedItem(null);
      }
    }

    if (updated.length === 0) {
      Toast.show({ type: 'error', text1: 'Agregue al menos un ítem con cantidad válida', visibilityTime: 2000 });
      return;
    }

    showStep(STEP.PHOTO);
  };

  const handleRemoveBatchItem = (index) => {
    const updated = batchItems.filter((_, idx) => idx !== index);
    setBatchItems(updated);
    Toast.show({ type: 'info', text1: 'Ítem eliminado del lote', visibilityTime: 1500 });
    if (updated.length === 0) {
      advanceWith({ estructura: null, dimension: null, ubicacion: null, largo: null });
    }
  };

  // ── Derived option lists for rendering ────────────────────────────
  const estructuraOpts = useMemo(() =>
    unique(items.map(i => i.estructura)),
  [items]);

  const dimensionOpts = useMemo(() =>
    unique(filterBySelection(items, { estructura: selEstructura, dimension: null, ubicacion: null, largo: null }).map(i => i.dimension)),
  [items, selEstructura]);

  const ubicacionOpts = useMemo(() =>
    unique(filterBySelection(items, { estructura: selEstructura, dimension: selDimension, ubicacion: null, largo: null }).map(i => i.ubicacion)),
  [items, selEstructura, selDimension]);

  const largoOpts = useMemo(() =>
    unique(filterBySelection(items, { estructura: selEstructura, dimension: selDimension, ubicacion: selUbicacion, largo: null }).map(i => String(i.largo))),
  [items, selEstructura, selDimension, selUbicacion]);

  // ── Photo handlers ────────────────────────────────────────────────
  const handleOpenCamera = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Toast.show({ type: 'error', text1: 'Permiso denegado', text2: 'Se necesita acceso a la cámara', visibilityTime: 2500 });
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.85, allowsEditing: false });
    if (!result.canceled && result.assets?.[0]?.uri) {
      const compressed = await compressImage(result.assets[0].uri);
      setPhotoUri(compressed);
      showStep(STEP.COMMENT);
      Toast.show({ type: 'success', text1: '✓ Foto capturada', visibilityTime: 2000 });
    }
  };

  const handlePickFromGallery = async () => {
    if (!isWeb) {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Toast.show({ type: 'error', text1: 'Permiso denegado', text2: 'Se necesita acceso a la galería', visibilityTime: 2500 });
        return;
      }
    }
    const result = await ImagePicker.launchImageLibraryAsync({ quality: 0.85, allowsEditing: false });
    if (!result.canceled && result.assets?.[0]?.uri) {
      const compressed = await compressImage(result.assets[0].uri);
      setPhotoUri(compressed);
      showStep(STEP.COMMENT);
      Toast.show({ type: 'success', text1: '✓ Foto seleccionada', visibilityTime: 2000 });
    }
  };

  // ── Submit ────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (submittingRef.current) return;
    if (batchItems.length === 0) {
      Toast.show({ type: 'error', text1: 'Sin ítems en el lote', visibilityTime: 2000 });
      return;
    }
    if (!photoUri) {
      Toast.show({ type: 'error', text1: 'Foto obligatoria', visibilityTime: 2500 });
      return;
    }

    submittingRef.current = true;
    setIsSubmitting(true);
    Toast.show({
      type: 'info',
      text1: batchItems.length > 1 ? `Guardando ${batchItems.length} avances...` : 'Guardando avance...',
      visibilityTime: 60000,
    });

    try {
      const now = new Date().toISOString();
      const commentText = comment.trim() || null;

      for (const b of batchItems) {
        const advancePayload = {
          id                 : generateUUID(),
          item_obra_id       : b.item.id,
          jefe_obra_id       : userProfile?.id || 'fallback',
          foto_url           : photoUri,
          comentario         : commentText,
          cantidad           : b.cantidad,
          fecha_captura_local: now,
        };

        saveAdvance(advancePayload);
      }

      const syncOk = await syncAdvances((p) => {
        if (p.status === 'complete') {
          Toast.show({
            type : p.failed === 0 ? 'success' : 'info',
            text1: p.failed === 0
              ? (batchItems.length > 1 ? `¡${batchItems.length} avances enviados!` : '¡Avance enviado!')
              : 'Guardado offline',
            text2: p.message,
            visibilityTime: 3500,
          });
        }
      });

      if (!syncOk) {
        Toast.show({ type: 'info', text1: 'Guardado localmente', text2: 'Se sincronizará con conexión', visibilityTime: 3000 });
      }

      submittingRef.current = false;
      onNavigateBack();

    } catch (err) {
      Toast.show({ type: 'error', text1: 'Error', text2: err.message, visibilityTime: 3000 });
      setIsSubmitting(false);
      submittingRef.current = false;
    }
  };

  // ── Progress bar ──────────────────────────────────────────────────
  const stepIndex  = stepHistory.indexOf(currentStep);
  const totalSteps = stepHistory.length;

  // ── Confirm card label for item ───────────────────────────────────
  const itemLabel = selectedItem
    ? [selEstructura, selDimension, selLargo ? mmToM(selLargo) : null].filter(Boolean).join(' · ')
    : '';

  // ── Render ────────────────────────────────────────────────────────
  return (
    <View style={styles.container} testID="selection-flow-screen">
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />

      {/* ── Header ── */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onNavigateBack} style={styles.backBtn} testID="back-button">
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>{activeObra?.nombre || 'Registrar Avance'}</Text>
          <Text style={styles.headerStep}>
            Paso {stepIndex + 1} de {totalSteps || 1}: {STEP_LABELS[currentStep]}
          </Text>
        </View>
      </View>

      {/* ── Progress bar (dynamic — only shows steps user actually saw) ── */}
      <View style={styles.progressBar}>
        {stepHistory.map((step, idx) => (
          <View
            key={step}
            style={[styles.progressSegment, idx <= stepIndex && styles.progressSegmentActive]}
          />
        ))}
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── Persistent Batch Banner ── */}
        {batchItems.length > 0 && [STEP.ESTRUCTURA, STEP.DIMENSION, STEP.UBICACION, STEP.LARGO, STEP.CANTIDAD].includes(currentStep) && (
          <View style={styles.batchBanner} testID="batch-banner">
            <View style={styles.batchBannerLeft}>
              <Text style={styles.batchBannerIcon}>📦</Text>
              <View>
                <Text style={styles.batchBannerTitle}>
                  Lote actual: {batchItems.length} {batchItems.length === 1 ? 'ítem' : 'ítems'}
                </Text>
                <Text style={styles.batchBannerSub}>
                  {batchItems.reduce((acc, b) => acc + b.cantidad, 0)} un. acumuladas
                </Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.batchBannerBtn}
              onPress={handleProceedToPhoto}
              testID="batch-proceed-photo-button"
              activeOpacity={0.8}
            >
              <Text style={styles.batchBannerBtnText}>Ir a Foto ➔</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ════════ STEP: ESTRUCTURA ════════ */}
        {currentStep === STEP.ESTRUCTURA && (
          <View>
            <Text style={styles.stepTitle}>Estructura</Text>
            <Text style={styles.stepHint}>{estructuraOpts.length} opción(es) disponibles</Text>

            {estructuraOpts.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>No hay ítems para esta obra.</Text>
                <Text style={styles.emptyStateHint}>Deslice hacia abajo en la pantalla anterior para sincronizar el catálogo.</Text>
              </View>
            ) : (
              estructuraOpts.map(opt => (
                <TouchableOpacity
                  key={opt}
                  style={styles.selectorCard}
                  activeOpacity={0.7}
                  onPress={() => advanceWith({ estructura: opt, dimension: null, ubicacion: null, largo: null })}
                >
                  <Text style={styles.selectorIcon}>🏗️</Text>
                  <Text style={styles.selectorText}>{opt}</Text>
                  <Text style={styles.selectorArrow}>›</Text>
                </TouchableOpacity>
              ))
            )}
          </View>
        )}

        {/* ════════ STEP: DIMENSION ════════ */}
        {currentStep === STEP.DIMENSION && (
          <View>
            <TouchableOpacity
              style={styles.breadcrumb}
              onPress={() => advanceWith({ estructura: null, dimension: null, ubicacion: null, largo: null })}
            >
              <Text style={styles.breadcrumbText}>‹ {selEstructura}</Text>
            </TouchableOpacity>
            <Text style={styles.stepTitle}>Dimensión</Text>
            <Text style={styles.stepHint}>{dimensionOpts.length} opción(es)</Text>

            {dimensionOpts.map(opt => (
              <TouchableOpacity
                key={opt}
                style={styles.selectorCard}
                activeOpacity={0.7}
                onPress={() => advanceWith({ estructura: selEstructura, dimension: opt, ubicacion: null, largo: null })}
              >
                <Text style={styles.selectorIcon}>📐</Text>
                <Text style={styles.selectorText}>{opt}</Text>
                <Text style={styles.selectorArrow}>›</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* ════════ STEP: UBICACION ════════ */}
        {currentStep === STEP.UBICACION && (
          <View>
            <TouchableOpacity
              style={styles.breadcrumb}
              onPress={() => advanceWith({ estructura: selEstructura, dimension: null, ubicacion: null, largo: null })}
            >
              <Text style={styles.breadcrumbText}>‹ {selEstructura} · {selDimension}</Text>
            </TouchableOpacity>
            <Text style={styles.stepTitle}>Ubicación</Text>
            <Text style={styles.stepHint}>{ubicacionOpts.length} opción(es)</Text>

            {ubicacionOpts.map(opt => (
              <TouchableOpacity
                key={opt}
                style={styles.selectorCard}
                activeOpacity={0.7}
                onPress={() => advanceWith({ estructura: selEstructura, dimension: selDimension, ubicacion: opt, largo: null })}
              >
                <Text style={styles.selectorIcon}>📍</Text>
                <Text style={styles.selectorText}>{opt}</Text>
                <Text style={styles.selectorArrow}>›</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* ════════ STEP: LARGO (conditional) ════════ */}
        {currentStep === STEP.LARGO && (
          <View>
            <TouchableOpacity
              style={styles.breadcrumb}
              onPress={() => advanceWith({ estructura: selEstructura, dimension: selDimension, ubicacion: null, largo: null })}
            >
              <Text style={styles.breadcrumbText}>‹ {selUbicacion}</Text>
            </TouchableOpacity>
            <Text style={styles.stepTitle}>Largo del Perfil</Text>
            <Text style={styles.stepHint}>{largoOpts.length} opción(es)</Text>

            {largoOpts.map(opt => (
              <TouchableOpacity
                key={opt}
                style={styles.selectorCard}
                activeOpacity={0.7}
                onPress={() => {
                  const matched = filterBySelection(items, {
                    estructura: selEstructura, dimension: selDimension,
                    ubicacion: selUbicacion, largo: opt,
                  });
                  if (matched.length === 1) {
                    setSelLargo(opt);
                    setSelectedItem(matched[0]);
                    showStep(STEP.CANTIDAD);
                  } else {
                    advanceWith({ estructura: selEstructura, dimension: selDimension, ubicacion: selUbicacion, largo: opt });
                  }
                }}
              >
                <Text style={styles.selectorIcon}>📏</Text>
                <Text style={styles.selectorText}>{mmToM(opt)}</Text>
                <Text style={styles.selectorArrow}>›</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* ════════ STEP: CANTIDAD ════════ */}
        {currentStep === STEP.CANTIDAD && selectedItem && (
          <View>
            <Text style={styles.stepTitle}>Cantidad</Text>

            {/* Item recap card */}
            <View style={styles.recapCard}>
              <View style={styles.itemIdBadge}>
                <Text style={styles.itemIdText}>{selectedItem.id?.substring(0, 6).toUpperCase()}</Text>
              </View>
              <Text style={styles.recapLabel}>{itemLabel || selectedItem.descripcion || 'Ítem seleccionado'}</Text>
              {selUbicacion ? <Text style={styles.recapDesc}>📍 {selUbicacion}</Text> : null}
              <Text style={styles.recapTotal}>
                Presupuestado: {selectedItem.cantidad ?? '—'} {selectedItem.unidad || 'un'}
              </Text>
            </View>

            <Text style={styles.inputLabel}>
              Unidades ejecutadas ({selectedItem.unidad || 'un'})
            </Text>
            <TextInput
              placeholder="0"
              placeholderTextColor={COLORS.textLight}
              value={cantidad}
              onChangeText={text => setCantidad(text.replace(/[^0-9]/g, ''))}
              keyboardType="number-pad"
              style={styles.progressInput}
              testID="progress-input"
              autoFocus
            />

            <View style={styles.cantidadActions}>
              <TouchableOpacity
                style={[styles.ctaButton, !cantidad && styles.ctaButtonDisabled]}
                disabled={!cantidad}
                testID="progress-continue-button"
                onPress={handleProceedToPhoto}
              >
                <Text style={styles.ctaButtonText}>
                  {batchItems.length > 0 ? 'Continuar con Lote → Foto' : 'Continuar → Foto'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.secondaryButton, !cantidad && styles.secondaryButtonDisabled]}
                disabled={!cantidad}
                testID="add-another-item-button"
                onPress={handleAddToBatch}
                activeOpacity={0.8}
              >
                <Text style={styles.secondaryButtonText}>+ Agregar otro ítem al lote</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ════════ STEP: PHOTO ════════ */}
        {currentStep === STEP.PHOTO && (
          <View>
            <TouchableOpacity onPress={() => showStep(STEP.CANTIDAD)} style={styles.breadcrumb}>
              <Text style={styles.breadcrumbText}>‹ Volver a cantidad</Text>
            </TouchableOpacity>
            <Text style={styles.stepTitle}>Foto del Avance</Text>
            <View style={styles.mandatoryTag}>
              <Text style={styles.mandatoryText}>★ OBLIGATORIO PARA EL LOTE</Text>
            </View>
            <Text style={styles.stepHint}>
              {batchItems.length > 1
                ? `Esta fotografía será la evidencia común para los ${batchItems.length} ítems del lote.`
                : 'La foto documenta el avance y es requerida para registrar el progreso.'}
            </Text>

            {photoUri ? (
              <View style={styles.photoPreviewContainer}>
                <Image source={{ uri: photoUri }} style={styles.photoPreview} testID="photo-preview" />
                <TouchableOpacity style={styles.retakeBtn} onPress={() => setPhotoUri(null)}>
                  <Text style={styles.retakeBtnText}>↺ Cambiar foto</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctaButton} onPress={() => showStep(STEP.COMMENT)} testID="photo-continue-button">
                  <Text style={styles.ctaButtonText}>Continuar → Comentario</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.photoButtonsContainer}>
                {/* Gallery / File picker — web + native */}
                <TouchableOpacity
                  style={styles.photoPickerBtn}
                  onPress={handlePickFromGallery}
                  testID="capture-photo-button"
                  activeOpacity={0.7}
                >
                  <Text style={styles.photoPickerIcon}>{isWeb ? '📁' : '🖼️'}</Text>
                  <Text style={styles.photoPickerTitle}>{isWeb ? 'Seleccionar archivo' : 'Galería'}</Text>
                  <Text style={styles.photoPickerHint}>{isWeb ? 'Sube una foto desde tu equipo' : 'Elegir de la galería'}</Text>
                </TouchableOpacity>

                {/* Camera — native only */}
                {!isWeb && (
                  <TouchableOpacity
                    style={[styles.photoPickerBtn, styles.photoPickerBtnCamera]}
                    onPress={handleOpenCamera}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.photoPickerIcon}>📷</Text>
                    <Text style={styles.photoPickerTitle}>Cámara</Text>
                    <Text style={styles.photoPickerHint}>Capturar foto en vivo</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}
          </View>
        )}

        {/* ════════ STEP: COMMENT ════════ */}
        {currentStep === STEP.COMMENT && (
          <View>
            <TouchableOpacity onPress={() => showStep(STEP.PHOTO)} style={styles.breadcrumb}>
              <Text style={styles.breadcrumbText}>‹ Cambiar foto</Text>
            </TouchableOpacity>
            <Text style={styles.stepTitle}>Comentario</Text>
            <View style={styles.optionalTag}>
              <Text style={styles.optionalText}>Opcional para el lote</Text>
            </View>

            <TextInput
              placeholder="Observaciones generales, condiciones especiales, próximos pasos..."
              placeholderTextColor={COLORS.textLight}
              value={comment}
              onChangeText={setComment}
              style={styles.commentInput}
              multiline
              numberOfLines={4}
              testID="comment-input"
            />

            <TouchableOpacity
              style={styles.ctaButton}
              onPress={() => showStep(STEP.CONFIRM)}
              testID="comment-continue-button"
            >
              <Text style={styles.ctaButtonText}>Continuar → Revisar</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ════════ STEP: CONFIRM ════════ */}
        {currentStep === STEP.CONFIRM && batchItems.length > 0 && (
          <View>
            <Text style={styles.stepTitle}>Confirmar Avance</Text>
            <Text style={styles.stepHint}>
              {batchItems.length > 1
                ? `Revise los ${batchItems.length} ítems del lote y la evidencia antes de enviar`
                : 'Revise los datos antes de enviar'}
            </Text>

            {/* General Obra info */}
            <View style={styles.confirmHeaderCard}>
              <View style={styles.confirmHeaderRow}>
                <Text style={styles.confirmHeaderLabel}>Obra</Text>
                <Text style={styles.confirmHeaderValue}>{activeObra?.nombre}</Text>
              </View>
              <View style={styles.confirmHeaderRow}>
                <Text style={styles.confirmHeaderLabel}>Total ítems</Text>
                <Text style={[styles.confirmHeaderValue, { color: COLORS.cta, fontFamily: 'Montserrat-Bold' }]}>
                  {batchItems.length} {batchItems.length === 1 ? 'ítem' : 'ítems en este lote'}
                </Text>
              </View>
            </View>

            {/* Batch items list with delete button */}
            <Text style={styles.batchListTitle}>Ítems incluidos ({batchItems.length})</Text>
            <View style={styles.batchListContainer}>
              {batchItems.map((b, idx) => (
                <View key={`${b.item.id}-${idx}`} style={styles.batchItemCard} testID={`batch-item-card-${b.item.id}`}>
                  <View style={styles.batchItemCardLeft}>
                    <View style={styles.batchItemNum}>
                      <Text style={styles.batchItemNumText}>{idx + 1}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.batchItemName}>{b.estructura || 'Estructura'}</Text>
                      <Text style={styles.batchItemDetails}>
                        {[b.dimension, b.largo ? mmToM(b.largo) : null, b.ubicacion].filter(Boolean).join(' · ')}
                      </Text>
                      <Text style={styles.batchItemQty}>
                        Cantidad: <Text style={{ fontFamily: 'Montserrat-Bold', color: COLORS.text }}>{b.cantidad} {b.item.unidad || 'un'}</Text>
                      </Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    style={styles.batchItemDeleteBtn}
                    onPress={() => handleRemoveBatchItem(idx)}
                    testID={`remove-item-${b.item.id}`}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.batchItemDeleteIcon}>✕</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </View>

            {/* Photo preview */}
            <View style={styles.confirmSection}>
              <Text style={styles.confirmSectionTitle}>Evidencia Fotográfica (Común al lote)</Text>
              {photoUri && (
                <Image source={{ uri: photoUri }} style={styles.confirmPhoto} testID="confirm-photo" />
              )}
            </View>

            {/* Comment */}
            {comment ? (
              <View style={styles.confirmCommentCard}>
                <Text style={styles.confirmCommentLabel}>Nota / Comentario:</Text>
                <Text style={styles.confirmCommentValue}>{comment}</Text>
              </View>
            ) : null}

            <TouchableOpacity
              style={[styles.ctaButton, isSubmitting && styles.ctaButtonDisabled]}
              onPress={handleSubmit}
              disabled={isSubmitting}
              testID="submit-advance-button"
            >
              {isSubmitting ? (
                <ActivityIndicator color="#FFF" />
              ) : (
                <Text style={styles.ctaButtonText}>
                  ✓ Enviar {batchItems.length > 1 ? `${batchItems.length} Avances` : 'Avance'}
                </Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.editLink}
              onPress={() => advanceWith({ estructura: null, dimension: null, ubicacion: null, largo: null })}
              disabled={isSubmitting}
            >
              <Text style={styles.editLinkText}>+ Agregar más ítems o modificar selección</Text>
            </TouchableOpacity>
          </View>
        )}

      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  // Header
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 50,
    paddingBottom: 14,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  backText: {
    color: '#FFF',
    fontSize: 20,
    fontWeight: 'bold',
    lineHeight: 22,
  },
  headerCenter: { flex: 1 },
  headerTitle: {
    fontSize: 17,
    fontFamily: 'Montserrat-Bold',
    color: '#FFF',
  },
  headerStep: {
    fontSize: 12,
    fontFamily: 'Inter',
    color: 'rgba(255,255,255,0.7)',
    marginTop: 2,
  },

  // Progress bar
  progressBar: {
    flexDirection: 'row',
    height: 4,
    backgroundColor: COLORS.border,
  },
  progressSegment: {
    flex: 1,
    backgroundColor: 'rgba(26,82,155,0.15)',
    marginHorizontal: 1,
  },
  progressSegmentActive: {
    backgroundColor: COLORS.cta,
  },

  // Scroll
  scrollView: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 40 },

  // Step common
  stepTitle: {
    fontSize: 22,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.primary,
    marginBottom: 4,
    marginTop: 8,
  },
  stepHint: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginBottom: 18,
  },
  breadcrumb: { marginBottom: 12 },
  breadcrumbText: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.accent,
    fontWeight: '600',
  },

  // Selector cards
  selectorCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 16,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  selectorIcon: { fontSize: 20, marginRight: 12 },
  selectorText: {
    flex: 1,
    fontSize: 15,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.text,
  },
  selectorArrow: {
    fontSize: 22,
    color: COLORS.textLight,
    fontWeight: '300',
  },

  // Item id badge
  itemIdBadge: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  itemIdText: {
    color: '#FFF',
    fontSize: 11,
    fontFamily: 'Montserrat-Bold',
    letterSpacing: 0.5,
  },

  // Recap card (cantidad step)
  recapCard: {
    backgroundColor: '#EBE6DD',
    borderRadius: 12,
    padding: 14,
    marginBottom: 18,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  recapLabel: {
    fontSize: 15,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.text,
    marginBottom: 4,
  },
  recapDesc: {
    fontSize: 12,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginBottom: 4,
  },
  recapTotal: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.accent,
    fontWeight: '600',
  },
  inputLabel: {
    fontSize: 14,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.text,
    marginBottom: 8,
  },
  progressInput: {
    height: 72,
    borderWidth: 2,
    borderColor: COLORS.accent,
    borderRadius: 14,
    paddingHorizontal: 16,
    fontSize: 36,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.primary,
    backgroundColor: '#FFF',
    textAlign: 'center',
    marginBottom: 20,
  },

  // Tags
  mandatoryTag: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.error + '18',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 12,
  },
  mandatoryText: {
    color: COLORS.error,
    fontSize: 11,
    fontFamily: 'Montserrat-Bold',
    letterSpacing: 0.5,
  },
  optionalTag: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.textLight + '18',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 12,
  },
  optionalText: {
    color: COLORS.textLight,
    fontSize: 11,
    fontFamily: 'Montserrat-SemiBold',
    letterSpacing: 0.5,
  },

  // Photo buttons
  photoButtonsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginVertical: 12,
  },
  photoPickerBtn: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 14,
    borderWidth: 2,
    borderColor: COLORS.accent,
    paddingVertical: 28,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 3,
  },
  photoPickerBtnCamera: {
    borderColor: COLORS.primary,
    shadowColor: COLORS.primary,
  },
  photoPickerIcon: { fontSize: 36, marginBottom: 8 },
  photoPickerTitle: {
    fontSize: 14,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.primary,
    marginBottom: 4,
    textAlign: 'center',
  },
  photoPickerHint: {
    fontSize: 11,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    textAlign: 'center',
    paddingHorizontal: 8,
  },

  // Photo preview
  photoPreviewContainer: { marginVertical: 12 },
  photoPreview: {
    width: '100%',
    height: 220,
    borderRadius: 14,
    marginBottom: 12,
  },
  retakeBtn: {
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  retakeBtnText: {
    color: COLORS.accent,
    fontFamily: 'Inter',
    fontSize: 14,
    fontWeight: '600',
  },

  // Comment
  commentInput: {
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 14,
    fontSize: 14,
    fontFamily: 'Inter',
    color: COLORS.text,
    backgroundColor: '#FFF',
    minHeight: 110,
    textAlignVertical: 'top',
    marginBottom: 20,
  },

  // Confirm
  confirmCard: {
    backgroundColor: '#FFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 16,
    overflow: 'hidden',
  },
  confirmRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    gap: 12,
  },
  confirmLabel: {
    fontSize: 13,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.textLight,
    width: 80,
  },
  confirmValue: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.text,
    flex: 1,
    textAlign: 'right',
  },
  confirmPhoto: {
    width: '100%',
    height: 160,
    borderRadius: 12,
    marginBottom: 20,
  },

  // CTA Button
  ctaButton: {
    height: 52,
    backgroundColor: COLORS.cta,
    borderRadius: 26,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: COLORS.cta,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  ctaButtonDisabled: {
    opacity: 0.5,
    shadowOpacity: 0,
    elevation: 0,
  },
  ctaButtonText: {
    color: '#FFF',
    fontFamily: 'Montserrat-Bold',
    fontSize: 16,
    letterSpacing: 0.3,
  },
  editLink: {
    alignSelf: 'center',
    marginTop: 16,
    padding: 8,
  },
  editLinkText: {
    color: COLORS.textLight,
    fontFamily: 'Inter',
    fontSize: 13,
    textDecorationLine: 'underline',
  },

  // Batch Banner
  batchBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F5E6E0',
    borderWidth: 1,
    borderColor: '#B85A3A',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginBottom: 16,
    shadowColor: '#B85A3A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  batchBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  batchBannerIcon: {
    fontSize: 22,
  },
  batchBannerTitle: {
    fontSize: 13,
    fontFamily: 'Montserrat-Bold',
    color: '#7C3720',
  },
  batchBannerSub: {
    fontSize: 11,
    fontFamily: 'Inter',
    color: '#7C3720',
  },
  batchBannerBtn: {
    backgroundColor: COLORS.cta,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
  },
  batchBannerBtnText: {
    color: '#FFF',
    fontSize: 12,
    fontFamily: 'Montserrat-Bold',
  },

  // Cantidad actions
  cantidadActions: {
    gap: 12,
    marginTop: 4,
  },
  secondaryButton: {
    height: 50,
    backgroundColor: '#FFF',
    borderWidth: 2,
    borderColor: COLORS.cta,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  secondaryButtonDisabled: {
    opacity: 0.5,
    borderColor: COLORS.border,
  },
  secondaryButtonText: {
    color: COLORS.cta,
    fontFamily: 'Montserrat-Bold',
    fontSize: 15,
  },

  // Confirm Batch List
  confirmHeaderCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 16,
  },
  confirmHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  confirmHeaderLabel: {
    fontSize: 13,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.textLight,
  },
  confirmHeaderValue: {
    fontSize: 13,
    fontFamily: 'Inter-Medium',
    color: COLORS.text,
  },
  batchListTitle: {
    fontSize: 15,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
    marginBottom: 10,
  },
  batchListContainer: {
    gap: 10,
    marginBottom: 18,
  },
  batchItemCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  batchItemCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
    paddingRight: 8,
  },
  batchItemNum: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  batchItemNumText: {
    fontSize: 11,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.textLight,
  },
  batchItemName: {
    fontSize: 14,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
  },
  batchItemDetails: {
    fontSize: 12,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginTop: 1,
  },
  batchItemQty: {
    fontSize: 12,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginTop: 3,
  },
  batchItemDeleteBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FEE2E2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  batchItemDeleteIcon: {
    color: '#DC2626',
    fontSize: 14,
    fontWeight: 'bold',
  },
  confirmSection: {
    marginVertical: 12,
  },
  confirmSectionTitle: {
    fontSize: 13,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.textLight,
    marginBottom: 8,
  },
  confirmCommentCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 14,
    marginBottom: 18,
  },
  confirmCommentLabel: {
    fontSize: 12,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.textLight,
    marginBottom: 4,
  },
  confirmCommentValue: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.text,
    lineHeight: 18,
  },

  // Empty state
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 15,
    fontFamily: 'Montserrat-SemiBold',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  emptyStateHint: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 18,
  },
});
