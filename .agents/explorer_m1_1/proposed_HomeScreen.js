// src/screens/HomeScreen.js
import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TouchableOpacity, 
  ScrollView, 
  SafeAreaView 
} from 'react-native';
import { theme } from '../constants/theme';
import { useToast } from '../components/Toast';

export default function HomeScreen({ navigation, onLogout }) {
  const { showToast } = useToast();
  
  // Mock data representing local database state (to be populated in M2)
  const [activeObra, setActiveObra] = useState({
    nombre: 'Construcción Estructura A - Planta Codelco',
    ubicacionesCount: 5,
    itemsCount: 42
  });

  const [pendingSyncCount, setPendingSyncCount] = useState(3);
  
  const handleSyncPress = () => {
    showToast('Iniciando sincronización manual...', 'pending', 1000);
    setTimeout(() => {
      setPendingSyncCount(0);
      showToast('Sincronización finalizada. Base de datos al día.', 'success');
    }, 1500);
  };

  return (
    <SafeAreaView style={styles.safeContainer}>
      <ScrollView contentContainerStyle={styles.container}>
        {/* Connection & Sync Status Widget */}
        <View style={styles.statusBarRow}>
          <View style={styles.statusIndicatorContainer}>
            <View style={[styles.statusDot, { backgroundColor: theme.colors.status.approved }]} />
            <Text style={styles.statusText}>En Línea</Text>
          </View>
          
          {pendingSyncCount > 0 ? (
            <TouchableOpacity onPress={handleSyncPress} style={styles.syncWarningBadge}>
              <Text style={styles.syncWarningText}>
                {pendingSyncCount} avance{pendingSyncCount > 1 ? 's' : ''} pendiente{pendingSyncCount > 1 ? 's' : ''}
              </Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.syncSuccessBadge}>
              <Text style={styles.syncSuccessText}>Sincronizado</Text>
            </View>
          )}
        </View>

        {/* Active Obra Card */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Obra Activa</Text>
          <Text style={styles.obraTitle}>{activeObra.nombre}</Text>
          
          <View style={styles.separator} />
          
          <View style={styles.statsRow}>
            <View style={styles.statCol}>
              <Text style={styles.statVal}>{activeObra.ubicacionesCount}</Text>
              <Text style={styles.statLabel}>Ubicaciones</Text>
            </View>
            <View style={styles.statCol}>
              <Text style={styles.statVal}>{activeObra.itemsCount}</Text>
              <Text style={styles.statLabel}>Ítems de Obra</Text>
            </View>
          </View>
        </View>

        {/* Major Action Button (rounded-full, min-height 48px, background orange) */}
        <TouchableOpacity 
          style={styles.ctaButton}
          activeOpacity={0.85}
          onPress={() => navigation.navigate('SelectionFlow')}
        >
          <Text style={styles.ctaButtonText}>REGISTRAR NUEVO AVANCE</Text>
        </TouchableOpacity>

        {/* Recent Advances Preview Header */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Últimos Registros (Hoy)</Text>
        </View>

        {/* Mock list of recent advances (would read SQLite in M2) */}
        <View style={styles.card}>
          <View style={styles.advanceItem}>
            <View style={styles.advanceHeader}>
              <Text style={styles.advanceId}>#042 - Ubicación A</Text>
              <View style={[styles.statusBadge, { backgroundColor: '#FEF3C7' }]}>
                <Text style={[styles.statusBadgeText, { color: theme.colors.status.pending }]}>
                  Pendiente
                </Text>
              </View>
            </View>
            <Text style={styles.advanceDetails}>Mortero Estructural • F-60 • 4.5 m²</Text>
            <Text style={styles.advanceTime}>Capturado hoy a las 11:20 (Offline)</Text>
          </View>

          <View style={styles.separator} />

          <View style={styles.advanceItem}>
            <View style={styles.advanceHeader}>
              <Text style={styles.advanceId}>#041 - Ubicación B</Text>
              <View style={[styles.statusBadge, { backgroundColor: '#D1FAE5' }]}>
                <Text style={[styles.statusBadgeText, { color: theme.colors.status.approved }]}>
                  Sincronizado
                </Text>
              </View>
            </View>
            <Text style={styles.advanceDetails}>Sello de Pasada • Hilti CF-128 • 2 ud</Text>
            <Text style={styles.advanceTime}>Sincronizado hoy a las 09:14</Text>
          </View>
        </View>

        {/* Logout button (Secondary design) */}
        <TouchableOpacity 
          style={styles.logoutButton}
          onPress={onLogout}
        >
          <Text style={styles.logoutButtonText}>Cerrar Sesión</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeContainer: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  container: {
    padding: theme.layout.spacing.lg,
  },
  statusBarRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.layout.spacing.md,
  },
  statusIndicatorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontFamily: theme.typography.fonts.bodySemiBold,
    fontSize: theme.typography.sizes.caption,
    color: theme.colors.textSecondary,
  },
  syncWarningBadge: {
    backgroundColor: '#FEF3C7', // Amber light
    paddingHorizontal: theme.layout.spacing.sm,
    paddingVertical: 4,
    borderRadius: theme.layout.borderRadius.sm,
  },
  syncWarningText: {
    color: theme.colors.status.pending,
    fontFamily: theme.typography.fonts.bodyBold,
    fontSize: 11,
  },
  syncSuccessBadge: {
    backgroundColor: '#D1FAE5', // Green light
    paddingHorizontal: theme.layout.spacing.sm,
    paddingVertical: 4,
    borderRadius: theme.layout.borderRadius.sm,
  },
  syncSuccessText: {
    color: theme.colors.status.approved,
    fontFamily: theme.typography.fonts.bodyBold,
    fontSize: 11,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.layout.borderRadius.md,
    padding: theme.layout.spacing.lg,
    marginBottom: theme.layout.spacing.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  cardLabel: {
    fontFamily: theme.typography.fonts.bodySemiBold,
    fontSize: theme.typography.sizes.caption,
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  obraTitle: {
    fontFamily: theme.typography.fonts.heading,
    fontSize: theme.typography.sizes.h2,
    color: theme.colors.primary,
    lineHeight: theme.typography.lineHeights.h2,
  },
  separator: {
    height: 1,
    backgroundColor: '#F1F5F9', // border-slate-100
    marginVertical: theme.layout.spacing.md,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statCol: {
    alignItems: 'center',
  },
  statVal: {
    fontFamily: theme.typography.fonts.heading,
    fontSize: 22,
    color: theme.colors.primary,
  },
  statLabel: {
    fontFamily: theme.typography.fonts.body,
    fontSize: theme.typography.sizes.caption,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  ctaButton: {
    backgroundColor: theme.colors.secondary,
    borderRadius: theme.layout.borderRadius.full,
    height: theme.layout.buttons.minHeight, // 48px
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.layout.spacing.xl,
    shadowColor: theme.colors.secondary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  ctaButtonText: {
    color: theme.colors.textLight,
    fontFamily: theme.typography.fonts.heading,
    fontSize: 15,
    fontWeight: 'bold',
  },
  sectionHeader: {
    marginBottom: theme.layout.spacing.sm,
  },
  sectionTitle: {
    fontFamily: theme.typography.fonts.heading,
    fontSize: 15,
    color: theme.colors.textPrimary,
  },
  advanceItem: {
    paddingVertical: theme.layout.spacing.xs,
  },
  advanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  advanceId: {
    fontFamily: theme.typography.fonts.bodyBold,
    fontSize: theme.typography.sizes.body,
    color: theme.colors.primary,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusBadgeText: {
    fontFamily: theme.typography.fonts.bodyBold,
    fontSize: 10,
  },
  advanceDetails: {
    fontFamily: theme.typography.fonts.body,
    fontSize: theme.typography.sizes.body,
    color: theme.colors.textPrimary,
  },
  advanceTime: {
    fontFamily: theme.typography.fonts.body,
    fontSize: theme.typography.sizes.caption,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  logoutButton: {
    paddingVertical: theme.layout.spacing.md,
    alignItems: 'center',
    marginTop: theme.layout.spacing.lg,
  },
  logoutButtonText: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fonts.bodySemiBold,
    fontSize: theme.typography.sizes.body,
  },
});
