// src/screens/SelectionFlowScreen.js
import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TouchableOpacity, 
  ScrollView, 
  SafeAreaView,
  TextInput,
  ActivityIndicator
} from 'react-native';
import { theme } from '../constants/theme';
import { useToast } from '../components/Toast';

const STEPS = {
  1: 'Ubicación/Plano',
  2: 'Item de Obra',
  3: 'Registro de Avance',
  4: 'Foto & Confirmación'
};

export default function SelectionFlowScreen({ navigation }) {
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form states
  const [selectedUbicacion, setSelectedUbicacion] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [avanceValue, setAvanceValue] = useState('');
  const [photoUri, setPhotoUri] = useState(null);
  const [comentario, setComentario] = useState('');

  // Mock choices (would read SQLite db in M2)
  const ubicaciones = ['Piso 1 - Sector A', 'Piso 1 - Sector B', 'Piso 2 - Helipuerto', 'Subterráneo - Sala de Bombas'];
  const items = [
    { id: '1', nombre: 'Viga V-101 (Mortero F-60) - 15 m²' },
    { id: '2', nombre: 'Pilar P-203 (Pintura F-90) - 8 m²' },
    { id: '3', nombre: 'Sello de Pasada S-01 (Hilti CP606) - 12 ud' }
  ];

  const handleNextStep = () => {
    if (currentStep === 1 && !selectedUbicacion) {
      showToast('Selecciona una ubicación para continuar', 'error');
      return;
    }
    if (currentStep === 2 && !selectedItem) {
      showToast('Selecciona un ítem de obra para continuar', 'error');
      return;
    }
    if (currentStep === 3 && !avanceValue) {
      showToast('Ingresa el avance registrado', 'error');
      return;
    }

    if (currentStep < 4) {
      setCurrentStep(prev => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBackStep = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    } else {
      navigation.goBack();
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    showToast('Guardando avance en base de datos local...', 'pending');

    try {
      // Simulate SQLite cache write & background sync trigger
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      showToast('Avance guardado localmente. Se sincronizará en segundo plano.', 'success');
      navigation.navigate('Home');
    } catch (err) {
      showToast('Error al guardar avance', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStepIndicator = () => {
    return (
      <View style={styles.indicatorContainer}>
        {Object.keys(STEPS).map((step) => {
          const stepNum = parseInt(step);
          const isActive = stepNum === currentStep;
          const isCompleted = stepNum < currentStep;

          return (
            <View key={step} style={styles.stepIndicatorWrapper}>
              <View 
                style={[
                  styles.dot, 
                  isActive && styles.activeDot, 
                  isCompleted && styles.completedDot
                ]}
              >
                <Text 
                  style={[
                    styles.dotText, 
                    (isActive || isCompleted) && styles.activeDotText
                  ]}
                >
                  {stepNum}
                </Text>
              </View>
              {stepNum < 4 && <View style={[styles.line, isCompleted && styles.completedLine]} />}
            </View>
          );
        })}
      </View>
    );
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <View style={styles.stepBody}>
            <Text style={styles.stepTitle}>Selecciona la Ubicación o Plano</Text>
            {ubicaciones.map((u) => (
              <TouchableOpacity
                key={u}
                style={[styles.selectOption, selectedUbicacion === u && styles.selectOptionSelected]}
                onPress={() => setSelectedUbicacion(u)}
              >
                <Text style={[styles.optionText, selectedUbicacion === u && styles.optionTextSelected]}>
                  {u}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 2:
        return (
          <View style={styles.stepBody}>
            <Text style={styles.stepTitle}>Selecciona el Ítem a Reportar</Text>
            <Text style={styles.stepSubtitle}>Ubicación: {selectedUbicacion}</Text>
            {items.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={[styles.selectOption, selectedItem?.id === item.id && styles.selectOptionSelected]}
                onPress={() => setSelectedItem(item)}
              >
                <Text style={[styles.optionText, selectedItem?.id === item.id && styles.optionTextSelected]}>
                  {item.nombre}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        );
      case 3:
        return (
          <View style={styles.stepBody}>
            <Text style={styles.stepTitle}>Registrar Cantidad Ejecutada</Text>
            <Text style={styles.stepSubtitle}>Ítem: {selectedItem?.nombre}</Text>
            
            <View style={styles.inputContainer}>
              <Text style={styles.label}>Cantidad Ejecutada (m² / ud)</Text>
              <TextInput
                style={styles.textInput}
                keyboardType="numeric"
                placeholder="Ej. 4.5"
                value={avanceValue}
                onChangeText={setAvanceValue}
              />
            </View>
          </View>
        );
      case 4:
        return (
          <View style={styles.stepBody}>
            <Text style={styles.stepTitle}>Registro Fotográfico & Envío</Text>
            <Text style={styles.stepSubtitle}>Resumen: {selectedItem?.nombre} - {avanceValue} m²</Text>
            
            {/* Camera Stub Box */}
            <View style={styles.cameraPlaceholderBox}>
              <Text style={styles.cameraPlaceholderText}>[ Foto Obligatoria del Avance ]</Text>
              <TouchableOpacity 
                style={styles.cameraMockButton}
                onPress={() => {
                  setPhotoUri('ph://mock-compressed-photo-uri.jpg');
                  showToast('Foto simulada capturada y comprimida exitosamente', 'success');
                }}
              >
                <Text style={styles.cameraMockButtonText}>Simular Captura (Cámara)</Text>
              </TouchableOpacity>
              {photoUri && <Text style={styles.photoAttachedText}>✓ Foto adjuntada y optimizada</Text>}
            </View>

            <View style={styles.inputContainer}>
              <Text style={styles.label}>Comentarios Adicionales (Opcional)</Text>
              <TextInput
                style={[styles.textInput, styles.textArea]}
                multiline
                numberOfLines={3}
                placeholder="Observaciones de terreno..."
                value={comentario}
                onChangeText={setComentario}
              />
            </View>
          </View>
        );
      default:
        return null;
    }
  };

  return (
    <SafeAreaView style={styles.safeContainer}>
      {renderStepIndicator()}
      <ScrollView contentContainerStyle={styles.container}>
        {renderStepContent()}
      </ScrollView>

      {/* Gloves-friendly navigation buttons */}
      <View style={styles.footer}>
        <TouchableOpacity 
          style={styles.navButtonSecondary} 
          onPress={handleBackStep}
          disabled={isSubmitting}
        >
          <Text style={styles.navButtonSecondaryText}>
            {currentStep === 1 ? 'Cancelar' : 'Atrás'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.navButtonPrimary, isSubmitting && styles.navButtonDisabled]} 
          onPress={handleNextStep}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.navButtonPrimaryText}>
              {currentStep === 4 ? 'GUARDAR' : 'Siguiente'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeContainer: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  indicatorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.layout.spacing.md,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.cardBorder,
  },
  stepIndicatorWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: '#CBD5E1', // slate-300
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2,
  },
  activeDot: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primary,
  },
  completedDot: {
    borderColor: theme.colors.accent,
    backgroundColor: theme.colors.accent,
  },
  dotText: {
    fontSize: 12,
    fontFamily: theme.typography.fonts.bodyBold,
    color: '#64748B',
  },
  activeDotText: {
    color: '#FFFFFF',
  },
  line: {
    width: 40,
    height: 3,
    backgroundColor: '#CBD5E1',
    marginHorizontal: -2,
    zIndex: 1,
  },
  completedLine: {
    backgroundColor: theme.colors.accent,
  },
  container: {
    padding: theme.layout.spacing.lg,
  },
  stepBody: {
    flex: 1,
  },
  stepTitle: {
    fontFamily: theme.typography.fonts.heading,
    fontSize: theme.typography.sizes.h2,
    color: theme.colors.primary,
    marginBottom: theme.layout.spacing.sm,
  },
  stepSubtitle: {
    fontFamily: theme.typography.fonts.bodySemiBold,
    fontSize: theme.typography.sizes.caption,
    color: theme.colors.textSecondary,
    marginBottom: theme.layout.spacing.md,
  },
  selectOption: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0', // slate-200
    borderRadius: theme.layout.borderRadius.md,
    padding: theme.layout.spacing.md,
    marginBottom: theme.layout.spacing.sm,
  },
  selectOptionSelected: {
    borderColor: theme.colors.accent,
    backgroundColor: '#F0F9FF', // Sky blue light
  },
  optionText: {
    fontFamily: theme.typography.fonts.body,
    fontSize: theme.typography.sizes.body,
    color: theme.colors.textPrimary,
  },
  optionTextSelected: {
    fontFamily: theme.typography.fonts.bodySemiBold,
    color: theme.colors.primary,
  },
  inputContainer: {
    marginTop: theme.layout.spacing.md,
  },
  label: {
    fontFamily: theme.typography.fonts.bodySemiBold,
    fontSize: theme.typography.sizes.body,
    color: theme.colors.textPrimary,
    marginBottom: theme.layout.spacing.xs,
  },
  textInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: theme.layout.borderRadius.md,
    padding: theme.layout.spacing.md,
    fontSize: theme.typography.sizes.body,
    color: theme.colors.textPrimary,
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  cameraPlaceholderBox: {
    height: 180,
    backgroundColor: '#F1F5F9', // slate-100
    borderWidth: 2,
    borderColor: '#CBD5E1', // slate-300
    borderStyle: 'dashed',
    borderRadius: theme.layout.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.layout.spacing.md,
    marginVertical: theme.layout.spacing.md,
  },
  cameraPlaceholderText: {
    fontFamily: theme.typography.fonts.bodySemiBold,
    color: theme.colors.textSecondary,
    marginBottom: theme.layout.spacing.md,
  },
  cameraMockButton: {
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.layout.spacing.md,
    paddingVertical: theme.layout.spacing.sm,
    borderRadius: theme.layout.borderRadius.md,
  },
  cameraMockButtonText: {
    color: '#FFFFFF',
    fontFamily: theme.typography.fonts.bodyBold,
    fontSize: 12,
  },
  photoAttachedText: {
    color: theme.colors.status.approved,
    fontFamily: theme.typography.fonts.bodySemiBold,
    fontSize: 12,
    marginTop: theme.layout.spacing.md,
  },
  footer: {
    flexDirection: 'row',
    padding: theme.layout.spacing.lg,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: theme.colors.cardBorder,
  },
  navButtonSecondary: {
    flex: 1,
    height: theme.layout.buttons.minHeight, // 48px
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: theme.layout.spacing.sm,
  },
  navButtonSecondaryText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fonts.bodyBold,
    fontSize: 15,
  },
  navButtonPrimary: {
    flex: 2,
    backgroundColor: theme.colors.secondary,
    borderRadius: theme.layout.borderRadius.full,
    height: theme.layout.buttons.minHeight, // 48px
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: theme.layout.spacing.sm,
  },
  navButtonDisabled: {
    backgroundColor: '#CBD5E1',
  },
  navButtonPrimaryText: {
    color: '#FFFFFF',
    fontFamily: theme.typography.fonts.heading,
    fontSize: 15,
    fontWeight: 'bold',
  },
});
