import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { supabase } from '../services/supabase';
import { COLORS } from '../constants/theme';
import Toast from 'react-native-toast-message';

export default function LoginScreen({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      Toast.show({ type: 'error', text1: 'Campos requeridos', text2: 'Ingrese email y contraseña.' });
      return;
    }
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });

      if (error) {
        Toast.show({ type: 'error', text1: 'Error de acceso', text2: 'Credenciales inválidas. Verifique e intente de nuevo.' });
        return;
      }

      const user = data?.session?.user || data?.user || { id: 'user-123', email };
      const userId = user.id || 'user-123';

      // Fetch profile
      const { data: profiles } = await supabase
        .from('perfiles_usuario')
        .select('*')
        .eq('id', userId);

      const profileData = profiles?.[0] || null;

      const userProfile = profileData
        ? {
            id: profileData.id,
            email: profileData.email || user.email,
            nombre: profileData.nombre || user.user_metadata?.nombre || email.split('@')[0],
            foto_perfil_url: profileData.foto_perfil_url || '',
            telefono: profileData.telefono || '',
            rol: profileData.rol || 'jefe_obra',
          }
        : {
            id: userId,
            email: user.email || email,
            nombre: user.user_metadata?.nombre || email.split('@')[0],
            foto_perfil_url: '',
            telefono: '',
            rol: 'jefe_obra',
          };

      onLoginSuccess({ session: data?.session || { user }, userProfile });
    } catch (err) {
      Toast.show({ type: 'error', text1: 'Error inesperado', text2: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      testID="login-screen"
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logo / Brand */}
        <View style={styles.brandArea}>
          <Image
            source={require('../../assets/logo_trabs_nombre_sf.png')}
            style={styles.logoImage}
            resizeMode="contain"
          />
          <Text style={styles.appSubtitle}>Control de obras en faena</Text>
        </View>

        {/* Form */}
        <View style={styles.formCard}>
          <Text style={styles.formTitle}>Iniciar Sesión</Text>

          <Text style={styles.label}>Correo electrónico</Text>
          <TextInput
            placeholder="correo@empresa.cl"
            value={email}
            onChangeText={setEmail}
            style={styles.input}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            testID="email-input"
            placeholderTextColor={COLORS.textLight}
          />

          <Text style={styles.label}>Contraseña</Text>
          <TextInput
            placeholder="••••••••"
            value={password}
            onChangeText={setPassword}
            style={styles.input}
            secureTextEntry
            testID="password-input"
            placeholderTextColor={COLORS.textLight}
          />

          <TouchableOpacity
            onPress={handleLogin}
            style={[styles.button, loading && styles.buttonDisabled]}
            disabled={loading}
            testID="login-button"
            activeOpacity={0.85}
          >
            {loading ? (
              <ActivityIndicator color="#FFF" size="small" />
            ) : (
              <Text style={styles.buttonText}>Ingresar</Text>
            )}
          </TouchableOpacity>
        </View>

        <Text style={styles.footer}>© 2026 Trabs · v1.0</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scroll: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  brandArea: {
    alignItems: 'center',
    marginBottom: 24,
  },
  logoImage: {
    width: 200,
    height: 120,
    marginBottom: 8,
  },
  appSubtitle: {
    fontSize: 13,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginTop: 2,
  },
  formCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 3,
  },
  formTitle: {
    fontSize: 18,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
    marginBottom: 20,
  },
  label: {
    fontSize: 13,
    fontFamily: 'Inter-Medium',
    color: COLORS.text,
    marginBottom: 6,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    marginBottom: 16,
    fontFamily: 'Inter',
    fontSize: 15,
    color: COLORS.text,
    backgroundColor: '#FAFAFA',
  },
  button: {
    height: 50,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 4,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 4,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: '#FFF',
    fontFamily: 'Montserrat-Bold',
    fontSize: 16,
    letterSpacing: 0.3,
  },
  footer: {
    textAlign: 'center',
    fontFamily: 'Inter',
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 24,
  },
});
