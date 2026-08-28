// src/screens/LoginScreen.js
import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TextInput, 
  TouchableOpacity, 
  KeyboardAvoidingView, 
  Platform, 
  ScrollView,
  ActivityIndicator,
  Image
} from 'react-native';
import { theme } from '../constants/theme';
import { useToast } from '../components/Toast';

export default function LoginScreen({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();

  const handleLogin = async () => {
    // 1. Basic validation
    if (!email.trim() || !password.trim()) {
      showToast('Por favor, ingresa correo y contraseña', 'error');
      return;
    }

    // 2. Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      showToast('El formato del correo es inválido', 'error');
      return;
    }

    setIsLoading(true);
    showToast('Iniciando sesión...', 'pending', 1500);

    try {
      // 3. Supabase integration stub (To be fully implemented in M2)
      // For Milestone 1, we simulate a successful login with a short delay
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      // Simulating credentials check (mock)
      if (email.toLowerCase().includes('error')) {
        throw new Error('Credenciales inválidas');
      }

      showToast('¡Sesión iniciada con éxito!', 'success');
      onLoginSuccess();
    } catch (error) {
      showToast(error.message || 'Error al iniciar sesión', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.keyboardContainer}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.card}>
          {/* Logo Placeholder / Image */}
          <View style={styles.logoContainer}>
            <View style={styles.placeholderLogo}>
              <Text style={styles.logoText}>TRACK OBRA</Text>
            </View>
            <Text style={styles.subtitle}>Accuratek Terreno</Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <Text style={styles.label}>Correo Electrónico</Text>
            <TextInput
              style={styles.input}
              placeholder="correo@accuratek.cl"
              placeholderTextColor={theme.colors.textSecondary}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isLoading}
            />

            <Text style={styles.label}>Contraseña</Text>
            <TextInput
              style={styles.input}
              placeholder="••••••••"
              placeholderTextColor={theme.colors.textSecondary}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isLoading}
            />

            {/* Gloves-friendly Action Button */}
            <TouchableOpacity 
              style={[styles.button, isLoading && styles.buttonDisabled]}
              onPress={handleLogin}
              activeOpacity={0.8}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color={theme.colors.textLight} />
              ) : (
                <Text style={styles.buttonText}>INGRESAR</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardContainer: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: theme.layout.spacing.xl,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.layout.borderRadius.lg,
    padding: theme.layout.spacing.xl,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: theme.layout.spacing.xxl,
  },
  placeholderLogo: {
    width: 80,
    height: 80,
    borderRadius: theme.layout.borderRadius.md,
    backgroundColor: theme.colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.layout.spacing.md,
  },
  logoText: {
    color: '#FFFFFF',
    fontFamily: theme.typography.fonts.heading,
    fontSize: 16,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: theme.typography.sizes.h2,
    fontFamily: theme.typography.fonts.headingMedium,
    color: theme.colors.primary,
  },
  form: {
    width: '100%',
  },
  label: {
    fontSize: theme.typography.sizes.body,
    fontFamily: theme.typography.fonts.bodySemiBold,
    color: theme.colors.textPrimary,
    marginBottom: theme.layout.spacing.xs,
    marginTop: theme.layout.spacing.md,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E2E8F0', // slate-200
    borderRadius: theme.layout.borderRadius.md,
    paddingHorizontal: theme.layout.spacing.md,
    paddingVertical: theme.layout.spacing.sm,
    fontSize: theme.typography.sizes.body,
    fontFamily: theme.typography.fonts.body,
    color: theme.colors.textPrimary,
    backgroundColor: '#FFFFFF',
    height: 44,
  },
  button: {
    backgroundColor: theme.colors.secondary,
    borderRadius: theme.layout.borderRadius.full,
    height: theme.layout.buttons.minHeight, // 48px gloves-friendly
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: theme.layout.spacing.xxl,
    shadowColor: theme.colors.secondary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  buttonDisabled: {
    backgroundColor: '#CBD5E1', // slate-300
    shadowOpacity: 0,
    elevation: 0,
  },
  buttonText: {
    color: theme.colors.textLight,
    fontFamily: theme.typography.fonts.heading,
    fontSize: 15,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
});
