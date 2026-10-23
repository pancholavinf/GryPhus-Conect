import React from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  StatusBar,
} from "react-native";
import { COLORS } from "../constants/theme";

export default function ObraMenuScreen({
  userProfile,
  activeObra,
  onNavigateBack,
  onSelectAvance,
  onNavigateToAsistencia,
  onNavigateToReporte,
  onNavigateToControlObra,
}) {
  const cardColor = activeObra?.color || COLORS.primary;

  return (
    <View style={styles.container} testID="obra-menu-screen">
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
          <Text style={styles.backBtnLabel}>Menú Principal</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {activeObra?.nombre || "Detalle de Obra"}
          </Text>
          <Text style={styles.headerSubtitle}>Menú de Operaciones</Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* OPCIÓN 1: Reporte de Avance */}
        <View style={styles.cardSection}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Reporte de Avance</Text>
          </View>
          <Text style={styles.cardDesc}>
            Registrar el progreso físico de las estructuras en terreno paso a paso.
          </Text>
          <TouchableOpacity
            style={[styles.actionBtn, { backgroundColor: cardColor }]}
            onPress={onSelectAvance}
            testID="btn-avance"
            activeOpacity={0.85}
          >
            <Text style={styles.actionBtnText}>Registrar Avance</Text>
          </TouchableOpacity>
        </View>

        {/* OPCIÓN 2: Pasar Asistencia */}
        <View style={styles.cardSection}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Pasar Asistencia</Text>
          </View>
          <Text style={styles.cardDesc}>
            Pasar lista y registrar la asistencia diaria del personal asignado a esta obra.
          </Text>
          <TouchableOpacity
            style={[styles.actionBtn, styles.asistenciaBtn]}
            onPress={onNavigateToAsistencia}
            testID="btn-asistencia"
            activeOpacity={0.85}
          >
            <Text style={styles.actionBtnText}>Pasar Asistencia</Text>
          </TouchableOpacity>
        </View>

        {/* OPCIÓN 3: Reporte Diario */}
        <View style={styles.cardSection}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Reporte Diario</Text>
          </View>
          <Text style={styles.cardDesc}>
            Registrar los incidentes, bitácora diaria y el consumo de materiales de la jornada.
          </Text>
          <TouchableOpacity
            style={[styles.actionBtn, styles.reporteBtn]}
            onPress={onNavigateToReporte}
            testID="btn-reporte-diario"
            activeOpacity={0.85}
          >
            <Text style={styles.actionBtnText}>Generar Reporte Diario</Text>
          </TouchableOpacity>
        </View>

        {/* OPCIÓN 4: Control de Obra */}
        <View style={styles.cardSection}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Control de Obra</Text>
          </View>
          <Text style={styles.cardDesc}>
            Consultar la nómina de trabajadores asignados a esta obra, sus cargos y datos de contacto.
          </Text>
          <TouchableOpacity
            style={[styles.actionBtn, styles.controlBtn]}
            onPress={onNavigateToControlObra}
            testID="btn-control-obra"
            activeOpacity={0.85}
          >
            <Text style={styles.actionBtnText}>Ver Control de Obra</Text>
          </TouchableOpacity>
        </View>
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
  backBtnIcon: {
    color: "#FFF",
    fontSize: 22,
    fontWeight: "bold",
    marginRight: 4,
    marginTop: -2,
  },
  backBtnLabel: {
    color: "#FFF",
    fontSize: 13,
    fontFamily: "Montserrat-SemiBold",
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
    color: "rgba(255, 255, 255, 0.75)",
    marginTop: 2,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    gap: 16,
  },
  cardSection: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 18,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  cardTitle: {
    fontSize: 18,
    fontFamily: "Montserrat-Bold",
    color: COLORS.primary,
  },
  cardDesc: {
    fontSize: 13,
    fontFamily: "Inter",
    color: COLORS.textLight,
    marginBottom: 16,
    lineHeight: 19,
  },
  actionBtn: {
    height: 50,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  asistenciaBtn: {
    backgroundColor: COLORS.darkSurface,
  },
  reporteBtn: {
    backgroundColor: COLORS.accent,
  },
  controlBtn: {
    backgroundColor: COLORS.secondary,
  },
  actionBtnText: {
    color: "#FFF",
    fontFamily: "Montserrat-Bold",
    fontSize: 15,
    letterSpacing: 0.3,
  },
});
