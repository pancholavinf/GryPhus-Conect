import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  Modal,
  Image,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Platform,
  Linking,
} from 'react-native';
import { COLORS } from '../constants/theme';
import { openPlayStore, PLAY_STORE_WEB_URL } from '../services/updateService';

/**
 * Modal Bloqueante de Actualización Obligatoria para Google Play Store.
 * Se muestra cuando existe una nueva versión oficial de la aplicación.
 * Redirige al supervisor directamente a la ficha de Google Play Store
 * garantizando cumplimiento 100% con las políticas de distribución de Google.
 */
export default function MandatoryUpdateModal({
  visible,
  updateInfo,
  onInstallationLaunched,
}) {
  const [isOpening, setIsOpening] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!visible || !updateInfo?.isUpdateAvailable) {
    return null;
  }

  const handleUpdatePress = async () => {
    setIsOpening(true);
    setErrorMessage('');
    try {
      const result = await openPlayStore();
      if (result?.success) {
        if (typeof onInstallationLaunched === 'function') {
          onInstallationLaunched();
        }
      } else {
        setErrorMessage(
          'No se pudo abrir la Play Store automáticamente. Puedes usar el enlace directo al navegador.'
        );
      }
    } catch (err) {
      setErrorMessage('Error al conectar con Google Play. Inténtalo de nuevo.');
    } finally {
      setIsOpening(false);
    }
  };

  const handleOpenWebFallback = () => {
    const webUrl = updateInfo?.playStoreWebUrl || PLAY_STORE_WEB_URL;
    Linking.openURL(webUrl).catch(() => {
      setErrorMessage('No se pudo abrir el navegador web.');
    });
  };

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent={false}
      statusBarTranslucent
      onRequestClose={() => {
        // Impedir que el botón atrás de Android cierre el modal
      }}
    >
      <View style={styles.container}>
        {/* Cabecera / Identidad */}
        <View style={styles.header}>
          <Image
            source={require('../../assets/logo_gryphus_circular_sf.png')}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.title}>Actualización Requerida</Text>
          <Text style={styles.subtitle}>
            Nueva versión <Text style={styles.versionBadge}>v{updateInfo.remoteVersion}</Text> disponible
          </Text>
        </View>

        {/* Mensaje descriptivo y novedades */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Novedades de la versión:</Text>
          <ScrollView style={styles.notesContainer} showsVerticalScrollIndicator={false}>
            <Text style={styles.notesText}>
              {updateInfo.releaseNotes || 'Mejoras de rendimiento y correcciones en faena.'}
            </Text>
          </ScrollView>
        </View>

        {/* Zona de Acción Google Play */}
        <View style={styles.actionSection}>
          <View style={styles.badgeStore}>
            <Text style={styles.badgeStoreText}>DISPONIBLE EN GOOGLE PLAY</Text>
          </View>

          <Text style={styles.actionPrompt}>
            Para continuar capturando avances y sincronizando con faena, actualiza la app a través de la tienda oficial:
          </Text>

          {errorMessage !== '' && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          <TouchableOpacity
            style={styles.primaryButton}
            activeOpacity={0.85}
            onPress={handleUpdatePress}
            disabled={isOpening}
          >
            {isOpening ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.primaryButtonText}>Actualizar en Google Play ➔</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.fallbackButton}
            activeOpacity={0.7}
            onPress={handleOpenWebFallback}
          >
            <Text style={styles.fallbackText}>Abrir enlace en el navegador web</Text>
          </TouchableOpacity>
        </View>

        {/* Pie de pantalla / Aviso de seguridad */}
        <View style={styles.footer}>
          <Text style={styles.footerNotice}>
            🔒 Tus registros locales y avances pendientes se conservarán intactos durante la actualización.
          </Text>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#262B29',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'android' ? 50 : 60,
    paddingBottom: 30,
    justifyContent: 'space-between',
  },
  header: {
    alignItems: 'center',
    marginTop: 15,
  },
  logo: {
    width: 80,
    height: 80,
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontFamily: 'Montserrat-Bold',
    color: '#FFFFFF',
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: 15,
    fontFamily: 'Inter-Medium',
    color: '#D8D5CD',
    marginTop: 6,
  },
  versionBadge: {
    color: COLORS.primary || '#3D523C',
    fontFamily: 'Montserrat-Bold',
  },
  card: {
    backgroundColor: '#2E3331',
    borderRadius: 14,
    padding: 18,
    marginVertical: 16,
    maxHeight: 180,
    borderWidth: 1,
    borderColor: '#4A524E',
  },
  cardTitle: {
    fontSize: 13,
    fontFamily: 'Montserrat-SemiBold',
    color: '#F2EFE9',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  notesContainer: {
    maxHeight: 120,
  },
  notesText: {
    fontSize: 13,
    fontFamily: 'Inter-Regular',
    color: '#F2EFE9',
    lineHeight: 20,
  },
  actionSection: {
    alignItems: 'center',
    width: '100%',
    paddingVertical: 10,
  },
  badgeStore: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: '#10B981',
    borderWidth: 1,
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 20,
    marginBottom: 12,
  },
  badgeStoreText: {
    color: '#10B981',
    fontSize: 11,
    fontFamily: 'Montserrat-Bold',
    letterSpacing: 0.6,
  },
  actionPrompt: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: '#D8D5CD',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 19,
    paddingHorizontal: 10,
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: '#EF4444',
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginBottom: 14,
    width: '100%',
  },
  errorText: {
    color: '#FCA5A5',
    fontSize: 12,
    fontFamily: 'Inter',
    textAlign: 'center',
  },
  primaryButton: {
    backgroundColor: COLORS.primary || '#3D523C',
    paddingVertical: 15,
    paddingHorizontal: 24,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    shadowColor: COLORS.primary || '#3D523C',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
    marginBottom: 14,
  },
  primaryButtonText: {
    fontSize: 15,
    fontFamily: 'Montserrat-Bold',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  fallbackButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  fallbackText: {
    fontSize: 12,
    fontFamily: 'Inter-Medium',
    color: '#718096',
    textDecorationLine: 'underline',
  },
  footer: {
    alignItems: 'center',
    marginTop: 10,
  },
  footerNotice: {
    fontSize: 11,
    fontFamily: 'Inter',
    color: '#718096',
    textAlign: 'center',
    lineHeight: 16,
  },
});
