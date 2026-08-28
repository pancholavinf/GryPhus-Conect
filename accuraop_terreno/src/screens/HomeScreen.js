import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  StatusBar,
  Modal,
  ScrollView,
  RefreshControl,
  Image,
} from 'react-native';
import {
  getObrasForJefe,
  getUnsyncedAvances,
  getUnsyncedAsistencias,
  getUnsyncedReportes,
} from '../database/db';
import { syncCatalog, syncAvances, syncAsistencias, syncReportes } from '../database/sync';
import { COLORS } from '../constants/theme';
import Toast from 'react-native-toast-message';

export default function HomeScreen({ userProfile, onSelectObra, onLogout, onUpdateProfile }) {
  const [obras, setObras] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [unsyncedCount, setUnsyncedCount] = useState(0);
  const [showProfileModal, setShowProfileModal] = useState(false);

  const loadObrasAndStats = useCallback(() => {
    try {
      const list = getObrasForJefe(userProfile?.id);
      setObras(list || []);

      const pendingAv = getUnsyncedAvances().length;
      const pendingAs = getUnsyncedAsistencias().length;
      const pendingRep = getUnsyncedReportes().length;
      setUnsyncedCount(pendingAv + pendingAs + pendingRep);
    } catch (err) {
      console.warn('Error cargando obras locales:', err);
      setObras([]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [userProfile?.id]);

  useEffect(() => {
    loadObrasAndStats();
  }, [loadObrasAndStats]);

  const handleManualSync = async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    Toast.show({ type: 'info', text1: 'Sincronizando...', text2: 'Descargando catálogo y subiendo pendientes' });

    try {
      // 1. Download updated catalog
      await syncCatalog(userProfile.id);

      // 2. Upload pending offline data
      const avRes = await syncAvances();
      const asRes = await syncAsistencias();
      const repRes = await syncReportes();

      const totalSuccess = (avRes.success || 0) + (asRes.success || 0) + (repRes.success || 0);
      const totalFailed = (avRes.failed || 0) + (asRes.failed || 0) + (repRes.failed || 0);

      loadObrasAndStats();

      Toast.show({
        type: totalFailed === 0 ? 'success' : 'info',
        text1: '✓ Sincronización completa',
        text2: `Enviados: ${totalSuccess} | Fallidos: ${totalFailed}`,
      });
    } catch (err) {
      Toast.show({ type: 'error', text1: 'Error al sincronizar', text2: err.message });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    handleManualSync();
  };

  return (
    <View style={styles.container} testID="home-screen">
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.headerLeft}
          onPress={() => setShowProfileModal(true)}
          activeOpacity={0.8}
        >
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>
              {(userProfile.nombre || userProfile.email || 'U')[0].toUpperCase()}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.welcomeText}>Jefe de Obra</Text>
            <Text style={styles.userName} numberOfLines={1}>
              {userProfile.nombre || userProfile.email}
            </Text>
          </View>
        </TouchableOpacity>

        <View style={styles.headerActions}>
          <TouchableOpacity
            onPress={handleManualSync}
            style={styles.iconBtn}
            disabled={isSyncing}
            activeOpacity={0.7}
          >
            {isSyncing ? (
              <ActivityIndicator color="#FFF" size="small" />
            ) : (
              <Text style={styles.iconBtnText}>🔄</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            onPress={onLogout}
            style={styles.logoutBtn}
            testID="logout-button"
          >
            <Text style={styles.logoutText}>Salir</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Offline Pending Items Banner */}
      {unsyncedCount > 0 && (
        <TouchableOpacity
          style={styles.syncBanner}
          onPress={handleManualSync}
          activeOpacity={0.85}
        >
          <Text style={styles.syncBannerText}>
            ⚠️ {unsyncedCount} registro(s) pendiente(s) por sincronizar. Toca para enviar.
          </Text>
        </TouchableOpacity>
      )}

      {/* Section title */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Obras Asignadas</Text>
        <Text style={styles.sectionSub}>Seleccione una obra para operar</Text>
      </View>

      {/* Obras list */}
      {isLoading ? (
        <ActivityIndicator color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : obras.length === 0 ? (
        <ScrollView
          contentContainerStyle={styles.emptyContainer}
          refreshControl={
            <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} colors={[COLORS.primary]} />
          }
        >
          <Text style={styles.emptyIcon}>🏗️</Text>
          <Text style={styles.emptyTitle}>Sin obras asignadas</Text>
          <Text style={styles.emptyText}>
            No tiene obras asignadas en este momento. Deslice hacia abajo para actualizar.
          </Text>
        </ScrollView>
      ) : (
        <FlatList
          data={obras}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} colors={[COLORS.primary]} />
          }
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.obraCard}
              onPress={() => onSelectObra(item)}
              testID={`obra-card-${item.id}`}
              activeOpacity={0.85}
            >
              <View style={[styles.obraColorBar, { backgroundColor: item.color || COLORS.primary }]} />
              <View style={styles.obraCardContent}>
                <Text style={styles.obraName} numberOfLines={1}>{item.nombre}</Text>
                {item.direccion ? (
                  <Text style={styles.obraDir} numberOfLines={1}>📍 {item.direccion}</Text>
                ) : null}
                <View style={styles.badgeRow}>
                  <View style={[styles.statusBadge, item.estado === 'Activa' ? styles.badgeActive : styles.badgeInactive]}>
                    <Text style={styles.statusBadgeText}>{item.estado || 'Activa'}</Text>
                  </View>
                </View>
              </View>
              <Text style={styles.obraArrow}>›</Text>
            </TouchableOpacity>
          )}
        />
      )}

      {/* User Profile Modal */}
      <Modal
        visible={showProfileModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowProfileModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Perfil de Usuario</Text>
              <TouchableOpacity onPress={() => setShowProfileModal(false)}>
                <Text style={styles.closeBtn}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.profileAvatarSection}>
              <View style={styles.largeAvatarCircle}>
                <Text style={styles.largeAvatarText}>
                  {(userProfile.nombre || userProfile.email || 'U')[0].toUpperCase()}
                </Text>
              </View>
              <Text style={styles.profileName}>{userProfile.nombre || 'Jefe de Obra'}</Text>
              <Text style={styles.profileRole}>Rol: {userProfile.rol || 'jefe_obra'}</Text>
            </View>

            <View style={styles.profileInfoList}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Correo:</Text>
                <Text style={styles.infoValue}>{userProfile.email}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>ID Usuario:</Text>
                <Text style={styles.infoValueSmall} numberOfLines={1}>{userProfile.id}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Teléfono:</Text>
                <Text style={styles.infoValue}>{userProfile.telefono || 'No registrado'}</Text>
              </View>
            </View>

            <View style={{ alignItems: 'center', marginVertical: 12 }}>
              <Image
                source={require('../../assets/logo_trabs_nombre_sf.png')}
                style={{ width: 140, height: 60 }}
                resizeMode="contain"
              />
              <Text style={{ fontSize: 11, color: COLORS.textLight, fontFamily: 'Inter', marginTop: 2 }}>
                Trabs Terreno · v1.0
              </Text>
            </View>

            <TouchableOpacity
              style={styles.closeModalBtn}
              onPress={() => setShowProfileModal(false)}
            >
              <Text style={styles.closeModalBtnText}>Cerrar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingBottom: 16,
    paddingHorizontal: 20,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  avatarCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    color: '#FFF',
    fontSize: 18,
    fontFamily: 'Montserrat-Bold',
  },
  welcomeText: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 11,
    fontFamily: 'Inter',
  },
  userName: {
    color: '#FFF',
    fontSize: 15,
    fontFamily: 'Montserrat-Bold',
  },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconBtnText: {
    fontSize: 16,
  },
  logoutBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 20,
  },
  logoutText: {
    color: '#FFF',
    fontSize: 12,
    fontFamily: 'Inter-Medium',
  },
  syncBanner: {
    backgroundColor: '#FEF3C7',
    borderBottomWidth: 1,
    borderColor: '#F59E0B',
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  syncBannerText: {
    color: '#92400E',
    fontSize: 12,
    fontFamily: 'Inter-Medium',
    textAlign: 'center',
  },
  sectionHeader: {
    marginTop: 20,
    marginBottom: 12,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
  },
  sectionSub: {
    fontSize: 12,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginTop: 2,
  },
  list: {
    paddingHorizontal: 20,
    paddingBottom: 24,
    gap: 12,
  },
  obraCard: {
    backgroundColor: '#FFF',
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  obraColorBar: {
    width: 6,
    alignSelf: 'stretch',
    minHeight: 70,
  },
  obraCardContent: {
    flex: 1,
    padding: 16,
  },
  obraName: {
    fontSize: 16,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
  },
  obraDir: {
    fontSize: 12,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginTop: 4,
  },
  badgeRow: {
    flexDirection: 'row',
    marginTop: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  badgeActive: {
    backgroundColor: '#D1FAE5',
  },
  badgeInactive: {
    backgroundColor: '#F3F4F6',
  },
  statusBadgeText: {
    fontSize: 10,
    fontFamily: 'Montserrat-SemiBold',
    color: '#065F46',
  },
  obraArrow: {
    fontSize: 22,
    color: COLORS.textLight,
    marginRight: 16,
  },
  emptyContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.primary,
  },
  closeBtn: {
    fontSize: 18,
    color: COLORS.textLight,
    padding: 4,
  },
  profileAvatarSection: {
    alignItems: 'center',
    marginBottom: 20,
  },
  largeAvatarCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  largeAvatarText: {
    color: '#FFF',
    fontSize: 26,
    fontFamily: 'Montserrat-Bold',
  },
  profileName: {
    fontSize: 18,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
  },
  profileRole: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginTop: 2,
  },
  profileInfoList: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    padding: 16,
    gap: 12,
    marginBottom: 20,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoLabel: {
    fontSize: 13,
    fontFamily: 'Inter-Medium',
    color: COLORS.textLight,
  },
  infoValue: {
    fontSize: 13,
    fontFamily: 'Inter-Bold',
    color: COLORS.text,
  },
  infoValueSmall: {
    fontSize: 11,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    maxWidth: 200,
  },
  closeModalBtn: {
    height: 48,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeModalBtnText: {
    color: '#FFF',
    fontFamily: 'Montserrat-Bold',
    fontSize: 15,
  },
});
