import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  StatusBar,
  ActivityIndicator,
} from "react-native";
import { COLORS } from "../constants/theme";
import { getMaestrosForObra } from "../database/db";

export default function ControlObraScreen({ userProfile, activeObra, onNavigateBack }) {
  const [maestros, setMaestros] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!activeObra?.id) {
      setIsLoading(false);
      return;
    }

    try {
      const lista = getMaestrosForObra(activeObra.id);
      setMaestros(lista || []);
    } catch (error) {
      console.warn("Error al obtener maestros:", error);
      setMaestros([]);
    } finally {
      setIsLoading(false);
    }
  }, [activeObra?.id]);

  return (
    <View style={styles.container} testID="control-obra-screen">
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={onNavigateBack}
          style={styles.backBtn}
          testID="back-button"
          activeOpacity={0.7}
        >
          <Text style={styles.backBtnIcon}>‹</Text>
          <Text style={styles.backBtnLabel}>Menú de Obra</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {activeObra?.nombre || "Control de Obra"}
          </Text>
          <Text style={styles.headerSubtitle}>Nómina de Personal y Cargos</Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
      >
        <Text style={styles.sectionTitle}>Trabajadores Asignados</Text>
        <Text style={styles.sectionDesc}>
          Personal registrado y activo para las labores de esta obra.
        </Text>

        {isLoading ? (
          <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
        ) : maestros.length > 0 ? (
          <View style={styles.listContainer}>
            {maestros.map((maestro) => (
              <View key={maestro.id} style={styles.workerCard} testID={`worker-card-${maestro.id}`}>
                <View style={styles.workerHeader}>
                  <Text style={styles.workerName}>{maestro.nombre}</Text>
                  <View style={styles.roleBadge}>
                    <Text style={styles.roleBadgeText}>
                      {maestro.cargo || "Sin cargo asignado"}
                    </Text>
                  </View>
                </View>

                <View style={styles.divider} />

                <View style={styles.detailsRow}>
                  <View style={styles.detailItem}>
                    <Text style={styles.detailLabel}>RUT / DNI</Text>
                    <Text style={styles.detailValue}>{maestro.rut || "No especificado"}</Text>
                  </View>
                  <View style={styles.detailItem}>
                    <Text style={styles.detailLabel}>Teléfono de Contacto</Text>
                    <Text style={styles.detailValue}>{maestro.telefono || "No especificado"}</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No hay trabajadores asignados</Text>
            <Text style={styles.emptyText}>
              No se encontraron registros de personal en la base local para esta obra.
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 50,
    paddingBottom: 16,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
  },
  backBtn: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    marginRight: 12,
  },
  backBtnIcon: { color: "#FFF", fontSize: 22, fontWeight: "bold", marginRight: 4, marginTop: -2 },
  backBtnLabel: { color: "#FFF", fontSize: 13, fontFamily: "Montserrat-SemiBold" },
  headerCenter: { flex: 1 },
  headerTitle: { fontSize: 17, fontFamily: "Montserrat-Bold", color: "#FFF" },
  headerSubtitle: { fontSize: 12, fontFamily: "Inter", color: "rgba(255,255,255,0.75)", marginTop: 2 },
  scrollView: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 40 },
  sectionTitle: { fontSize: 18, fontFamily: "Montserrat-Bold", color: COLORS.primary, marginBottom: 4 },
  sectionDesc: { fontSize: 13, fontFamily: "Inter", color: COLORS.textLight, marginBottom: 16 },
  listContainer: { gap: 14 },
  workerCard: {
    backgroundColor: "#FFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  workerHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  workerName: { fontSize: 16, fontFamily: "Montserrat-Bold", color: COLORS.text, flex: 1, paddingRight: 8 },
  roleBadge: {
    backgroundColor: "#EFF6FF",
    borderWidth: 1,
    borderColor: COLORS.accent,
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 16,
  },
  roleBadgeText: { fontSize: 11, fontFamily: "Montserrat-SemiBold", color: COLORS.accent },
  divider: { height: 1, backgroundColor: COLORS.border, marginVertical: 12 },
  detailsRow: { flexDirection: "row", justifyContent: "space-between" },
  detailItem: { flex: 1 },
  detailLabel: { fontSize: 11, fontFamily: "Inter", color: COLORS.textLight, marginBottom: 2 },
  detailValue: { fontSize: 13, fontFamily: "Inter-Medium", color: COLORS.text },
  emptyCard: {
    backgroundColor: "#FFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 24,
    alignItems: "center",
    marginTop: 20,
  },
  emptyTitle: { fontSize: 15, fontFamily: "Montserrat-Bold", color: COLORS.text, marginBottom: 6 },
  emptyText: { fontSize: 13, fontFamily: "Inter", color: COLORS.textLight, textAlign: "center" },
});
