import React, { useEffect, useState, useCallback } from 'react';
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
} from 'react-native';
import { COLORS } from '../constants/theme';
import { downloadAndInstallApk } from '../services/updateService';

/**
 * Modal Bloqueante de Actualización Obligatoria.
 * Se muestra cuando existe una nueva versión en GitHub Releases.
 * Inicia la descarga del APK automáticamente y no permite cancelarse.
 */
export default function MandatoryUpdateModal({
  visible,
  updateInfo,
  onInstallationLaunched,
}) {
  const [downloadState, setDownloadState] = useState('idle'); // 'idle' | 'downloading' | 'ready' | 'error'
  const [progress, setProgress] = useState(0);
  const [downloadedMb, setDownloadedMb] = useState(0);
  const [totalMb, setTotalMb] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');

  const startAutoDownload = useCallback(async () => {
    if (!updateInfo?.downloadUrl) return;

    setDownloadState('downloading');
    setErrorMessage('');
    setProgress(0);

    const result = await downloadAndInstallApk(
      updateInfo.downloadUrl,
      ({ downloadedBytes, totalBytes, percent }) => {
        setProgress(percent);
        setDownloadedMb((downloadedBytes / (1024 * 1024)).toFixed(1));
        setTotalMb((totalBytes / (1024 * 1024)).toFixed(1));
      }
    );

    if (result.success) {
      setDownloadState('ready');
      if (typeof onInstallationLaunched === 'function') {
        onInstallationLaunched();
      }
    } else {
      setDownloadState('error');
      setErrorMessage(result.error || result.message || 'Error al descargar el instalador.');
    }
  }, [updateInfo, onInstallationLaunched]);

  // Iniciar descarga automáticamente apenas sea visible
  useEffect(() => {
    if (visible && updateInfo?.isUpdateAvailable && downloadState === 'idle') {
      startAutoDownload();
    }
  }, [visible, updateInfo, downloadState, startAutoDownload]);

  if (!visible || !updateInfo?.isUpdateAvailable) {
    return null;
  }

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
            source={require('../../assets/logo_trabs_circular_sf.png')}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.title}>Actualización Requerida</Text>
          <Text style={styles.subtitle}>
            Trabs Terreno <Text style={styles.versionBadge}>v{updateInfo.remoteVersion}</Text>
          </Text>
        </View>

        {/* Mensaje descriptivo */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Novedades de la versión:</Text>
          <ScrollView style={styles.notesContainer} showsVerticalScrollIndicator={false}>
            <Text style={styles.notesText}>{updateInfo.releaseNotes}</Text>
          </ScrollView>
        </View>

        {/* Zona de Estado y Progreso */}
        <View style={styles.progressSection}>
          {downloadState === 'downloading' && (
            <>
              <View style={styles.progressBarTrack}>
                <View style={[styles.progressBarFill, { width: `${progress}%` }]} />
              </View>
              <View style={styles.progressLabels}>
                <Text style={styles.progressPercent}>{Math.round(progress)}%</Text>
                <Text style={styles.progressBytes}>
                  {downloadedMb} MB / {totalMb} MB
                </Text>
              </View>
              <Text style={styles.statusText}>
                Descargando actualización en segundo plano...
              </Text>
            </>
          )}

          {downloadState === 'ready' && (
            <View style={styles.centerBox}>
              <Text style={styles.readyTitle}>¡Descarga Completa!</Text>
              <Text style={styles.readyText}>
                Se ha abierto el instalador de Android en tu pantalla. Si la ventana se cerró o necesitas reinstalar, presiona el botón a continuación:
              </Text>
              <TouchableOpacity
                style={styles.primaryButton}
                activeOpacity={0.8}
                onPress={startAutoDownload}
              >
                <Text style={styles.primaryButtonText}>Abrir Instalador de Android</Text>
              </TouchableOpacity>
            </View>
          )}

          {downloadState === 'error' && (
            <View style={styles.centerBox}>
              <Text style={styles.errorTitle}>Problema de Descarga</Text>
              <Text style={styles.errorDescription}>{errorMessage}</Text>
              <TouchableOpacity
                style={styles.retryButton}
                activeOpacity={0.8}
                onPress={startAutoDownload}
              >
                <Text style={styles.retryButtonText}>Reintentar Descarga</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Pie de pantalla / Aviso de seguridad */}
        <View style={styles.footer}>
          <Text style={styles.footerNotice}>
            🔒 Tus registros locales y datos de faena se conservarán intactos durante la actualización.
          </Text>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1E2124',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'android' ? 50 : 60,
    paddingBottom: 30,
    justifyContent: 'space-between',
  },
  header: {
    alignItems: 'center',
    marginTop: 20,
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
    color: '#A0AEC0',
    marginTop: 6,
  },
  versionBadge: {
    color: COLORS.primary || '#FF6B00',
    fontFamily: 'Montserrat-Bold',
  },
  card: {
    backgroundColor: '#2B2F33',
    borderRadius: 14,
    padding: 16,
    marginVertical: 20,
    maxHeight: 180,
    borderWidth: 1,
    borderColor: '#3D4247',
  },
  cardTitle: {
    fontSize: 13,
    fontFamily: 'Montserrat-SemiBold',
    color: '#E2E8F0',
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
    color: '#CBD5E0',
    lineHeight: 20,
  },
  progressSection: {
    minHeight: 140,
    justifyContent: 'center',
  },
  progressBarTrack: {
    height: 12,
    backgroundColor: '#373B40',
    borderRadius: 6,
    overflow: 'hidden',
    marginBottom: 10,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: COLORS.primary || '#FF6B00',
    borderRadius: 6,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressPercent: {
    fontSize: 16,
    fontFamily: 'Montserrat-Bold',
    color: '#FFFFFF',
  },
  progressBytes: {
    fontSize: 13,
    fontFamily: 'Inter-Regular',
    color: '#A0AEC0',
  },
  statusText: {
    fontSize: 13,
    fontFamily: 'Inter-Medium',
    color: '#E2E8F0',
    textAlign: 'center',
    marginTop: 14,
  },
  centerBox: {
    alignItems: 'center',
  },
  readyTitle: {
    fontSize: 18,
    fontFamily: 'Montserrat-Bold',
    color: '#48BB78',
    marginBottom: 8,
  },
  readyText: {
    fontSize: 13,
    fontFamily: 'Inter-Regular',
    color: '#E2E8F0',
    textAlign: 'center',
    lineHeight: 19,
    marginBottom: 18,
  },
  primaryButton: {
    backgroundColor: COLORS.primary || '#FF6B00',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    shadowColor: COLORS.primary || '#FF6B00',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  primaryButtonText: {
    fontSize: 15,
    fontFamily: 'Montserrat-Bold',
    color: '#FFFFFF',
  },
  errorTitle: {
    fontSize: 17,
    fontFamily: 'Montserrat-Bold',
    color: '#F56565',
    marginBottom: 6,
  },
  errorDescription: {
    fontSize: 13,
    fontFamily: 'Inter-Regular',
    color: '#E2E8F0',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#E53E3E',
    paddingVertical: 12,
    paddingHorizontal: 22,
    borderRadius: 10,
  },
  retryButtonText: {
    fontSize: 14,
    fontFamily: 'Montserrat-Bold',
    color: '#FFFFFF',
  },
  footer: {
    alignItems: 'center',
  },
  footerNotice: {
    fontSize: 11,
    fontFamily: 'Inter-Regular',
    color: '#718096',
    textAlign: 'center',
    lineHeight: 16,
  },
});
