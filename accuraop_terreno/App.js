import React, { useState, useEffect, useCallback, useRef } from 'react';
import { StyleSheet, SafeAreaView, Text, View, Image } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useFonts } from 'expo-font';
import { Montserrat_700Bold, Montserrat_600SemiBold } from '@expo-google-fonts/montserrat';
import { Inter_400Regular, Inter_500Medium, Inter_700Bold } from '@expo-google-fonts/inter';
import * as SplashScreen from 'expo-splash-screen';
import Toast from 'react-native-toast-message';

import { initDatabase } from './src/database/db';
import { syncCatalog, startBackgroundSync } from './src/database/sync';
import { COLORS } from './src/constants/theme';
import { supabase } from './src/services/supabase';

import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import SelectionFlowScreen from './src/screens/SelectionFlowScreen';
import ReporteDiarioScreen from './src/screens/ReporteDiarioScreen';
import ObraMenuScreen from './src/screens/ObraMenuScreen';
import AsistenciaScreen from './src/screens/AsistenciaScreen';
import ControlObraScreen from './src/screens/ControlObraScreen';

SplashScreen.preventAutoHideAsync().catch((err) => {
  console.warn('SplashScreen.preventAutoHideAsync() failed', err);
});

const Stack = createNativeStackNavigator();

export default function App() {
  const [dbReady, setDbReady] = useState(false);
  const [dbError, setDbError] = useState(null);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  const [session, setSession] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [activeObra, setActiveObra] = useState(null);
  const [catalogSynced, setCatalogSynced] = useState(false);

  const isSyncingRef = useRef(false);
  const bgSyncUnsubRef = useRef(null);

  const [fontsLoaded, fontError] = useFonts({
    'Montserrat-Bold': Montserrat_700Bold,
    'Montserrat-SemiBold': Montserrat_600SemiBold,
    'Montserrat': Montserrat_600SemiBold,
    'Inter-Regular': Inter_400Regular,
    'Inter-Medium': Inter_500Medium,
    'Inter-Bold': Inter_700Bold,
    'Inter': Inter_400Regular,
  });

  const lockedSyncCatalog = useCallback(async (userId) => {
    if (isSyncingRef.current) return;
    isSyncingRef.current = true;
    try {
      await syncCatalog(userId);
    } finally {
      isSyncingRef.current = false;
    }
  }, []);

  /** Start background sync listener and store the unsubscribe ref */
  const startBgSync = useCallback(() => {
    if (bgSyncUnsubRef.current) return; // already started
    bgSyncUnsubRef.current = startBackgroundSync((result) => {
      if (result?.status === 'complete' && result.success > 0) {
        Toast.show({
          type: result.failed === 0 ? 'success' : 'error',
          text1: result.failed === 0 ? 'Sincronización automática' : 'Sincronización parcial',
          text2: result.message,
          visibilityTime: 3000,
        });
      }
    });
  }, []);

  const stopBgSync = useCallback(() => {
    if (bgSyncUnsubRef.current) {
      bgSyncUnsubRef.current();
      bgSyncUnsubRef.current = null;
    }
  }, []);

  useEffect(() => {
    // Init local DB
    try {
      initDatabase();
      setDbReady(true);
    } catch (error) {
      console.error('Failed to initialize database:', error);
      setDbError(error);
    }

    if (supabase.auth && typeof supabase.auth.getSession === 'function') {
      supabase.auth.getSession().then(async ({ data: { session: activeSession } }) => {
        if (activeSession) {
          const profile = {
            id: activeSession.user?.id || 'jefe-123',
            email: activeSession.user?.email,
            nombre: activeSession.user?.user_metadata?.nombre || activeSession.user?.email?.split('@')[0],
            foto_perfil_url: activeSession.user?.user_metadata?.foto_perfil_url || '',
            telefono: activeSession.user?.user_metadata?.telefono || '',
            rol: 'jefe_obra',
          };
          setSession(activeSession);
          setUserProfile(profile);
          try {
            await lockedSyncCatalog(profile.id);
          } catch (err) {
            console.error('Initial catalog sync failed:', err);
          } finally {
            setCatalogSynced(true);
          }
        }
      }).catch((err) => {
        console.error('getSession error:', err);
        setSession(null);
      }).finally(() => {
        setIsAuthChecking(false);
      });
    } else {
      setIsAuthChecking(false);
    }

    let subscription = null;
    if (supabase.auth && typeof supabase.auth.onAuthStateChange === 'function') {
      const authListener = supabase.auth.onAuthStateChange(async (_event, activeSession) => {
        if (activeSession) {
          const profile = {
            id: activeSession.user?.id || 'jefe-123',
            email: activeSession.user?.email,
            nombre: activeSession.user?.user_metadata?.nombre || activeSession.user?.email?.split('@')[0],
            foto_perfil_url: activeSession.user?.user_metadata?.foto_perfil_url || '',
            telefono: activeSession.user?.user_metadata?.telefono || '',
            rol: 'jefe_obra',
          };
          setSession(activeSession);
          setUserProfile(profile);
          try {
            await lockedSyncCatalog(profile.id);
          } catch (err) {
            console.error('Catalog sync failed on auth change:', err);
          } finally {
            setCatalogSynced(true);
          }
        } else {
          setSession(null);
          setUserProfile(null);
          setCatalogSynced(false);
          stopBgSync();
        }
      });
      subscription = authListener?.data?.subscription;
    }

    return () => {
      subscription?.unsubscribe?.();
      stopBgSync();
    };
  }, [lockedSyncCatalog, startBgSync, stopBgSync]);

  // Start background sync listener when user authenticates
  useEffect(() => {
    if (session && userProfile && catalogSynced) {
      startBgSync();
    }
  }, [session, userProfile, catalogSynced, startBgSync]);

  const handleLoginSuccess = async ({ session: userSession, userProfile: profile }) => {
    try {
      await lockedSyncCatalog(profile.id);
    } catch (err) {
      console.error('Catalog sync failed:', err);
    } finally {
      setSession(userSession);
      setUserProfile(profile);
      setCatalogSynced(true);
    }
  };

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
    } catch (err) {
      console.warn('Sign out error:', err);
    } finally {
      stopBgSync();
      setSession(null);
      setUserProfile(null);
      setActiveObra(null);
      setCatalogSynced(false);
    }
  };

  const onLayoutRootView = useCallback(async () => {
    if (dbError || ((fontsLoaded || fontError) && dbReady && !isAuthChecking)) {
      try {
        await SplashScreen.hideAsync();
      } catch (err) {
        console.warn('SplashScreen.hideAsync() failed', err);
      }
    }
  }, [fontsLoaded, fontError, dbReady, isAuthChecking, dbError]);

  if (dbError) {
    return (
      <SafeAreaView style={styles.errorContainer} onLayout={onLayoutRootView}>
        <Text style={styles.errorTitle}>Error de Base de Datos</Text>
        <Text style={styles.errorMessage}>
          No se pudo inicializar la base de datos local. Por favor reinicie la aplicación.
        </Text>
      </SafeAreaView>
    );
  }

  if ((!fontsLoaded && !fontError) || !dbReady || isAuthChecking) {
    return null;
  }

  const isUserAuthenticated = session && userProfile && catalogSynced;

  return (
    <SafeAreaView style={styles.container} onLayout={onLayoutRootView}>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {!isUserAuthenticated ? (
            <Stack.Screen name="Login">
              {(props) => <LoginScreen {...props} onLoginSuccess={handleLoginSuccess} />}
            </Stack.Screen>
          ) : (
            <>
              <Stack.Screen name="Home">
                {(props) => (
                  <HomeScreen
                    {...props}
                    userProfile={userProfile}
                    onUpdateProfile={(updated) => setUserProfile(updated)}
                    onSelectObra={(obra) => {
                      setActiveObra(obra);
                      props.navigation.navigate('ObraMenu');
                    }}
                    onLogout={handleLogout}
                  />
                )}
              </Stack.Screen>
              <Stack.Screen name="ObraMenu">
                {(props) => (
                  <ObraMenuScreen
                    {...props}
                    userProfile={userProfile}
                    activeObra={activeObra}
                    onNavigateBack={() => props.navigation.goBack()}
                    onSelectAvance={() => props.navigation.navigate('SelectionFlow')}
                    onNavigateToAsistencia={() => props.navigation.navigate('Asistencia')}
                    onNavigateToReporte={() => props.navigation.navigate('ReporteDiarioFlow')}
                    onNavigateToControlObra={() => props.navigation.navigate('ControlObra')}
                  />
                )}
              </Stack.Screen>
              <Stack.Screen name="SelectionFlow">
                {(props) => (
                  <SelectionFlowScreen
                    {...props}
                    userProfile={userProfile}
                    activeObra={activeObra}
                    onNavigateBack={() => props.navigation.goBack()}
                  />
                )}
              </Stack.Screen>
              <Stack.Screen name="ReporteDiarioFlow">
                {(props) => (
                  <ReporteDiarioScreen
                    {...props}
                    userProfile={userProfile}
                    activeObra={activeObra}
                    onNavigateBack={() => props.navigation.goBack()}
                  />
                )}
              </Stack.Screen>
              <Stack.Screen name="Asistencia">
                {(props) => (
                  <AsistenciaScreen
                    {...props}
                    userProfile={userProfile}
                    activeObra={activeObra}
                    onNavigateBack={() => props.navigation.goBack()}
                  />
                )}
              </Stack.Screen>
              <Stack.Screen name="ControlObra">
                {(props) => (
                  <ControlObraScreen
                    {...props}
                    userProfile={userProfile}
                    activeObra={activeObra}
                    onNavigateBack={() => props.navigation.goBack()}
                  />
                )}
              </Stack.Screen>
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
      <Toast config={toastConfig} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    padding: 20,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.error,
    marginBottom: 10,
    fontFamily: 'Montserrat-Bold',
  },
  errorMessage: {
    fontSize: 16,
    color: COLORS.text,
    textAlign: 'center',
    fontFamily: 'Inter',
  },
  customToast: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderLeftWidth: 6,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginHorizontal: 20,
    width: '90%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 6,
  },
  toastIcon: {
    width: 24,
    height: 24,
    marginRight: 12,
  },
  toastTextContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  toastText1: {
    fontSize: 14,
    fontFamily: 'Montserrat-Bold',
    color: COLORS.text,
  },
  toastText2: {
    fontSize: 12,
    fontFamily: 'Inter',
    color: COLORS.textLight,
    marginTop: 2,
  },
});

const toastConfig = {
  success: ({ text1, text2 }) => (
    <View style={[styles.customToast, { borderLeftColor: COLORS.approved }]}>
      <Image source={require('./assets/sprites/listo_logo.png')} style={styles.toastIcon} />
      <View style={styles.toastTextContainer}>
        {text1 ? <Text style={styles.toastText1}>{text1}</Text> : null}
        {text2 ? <Text style={styles.toastText2}>{text2}</Text> : null}
      </View>
    </View>
  ),
  error: ({ text1, text2 }) => (
    <View style={[styles.customToast, { borderLeftColor: COLORS.error }]}>
      <Image source={require('./assets/sprites/error_logo.png')} style={styles.toastIcon} />
      <View style={styles.toastTextContainer}>
        {text1 ? <Text style={styles.toastText1}>{text1}</Text> : null}
        {text2 ? <Text style={styles.toastText2}>{text2}</Text> : null}
      </View>
    </View>
  ),
  info: ({ text1, text2 }) => (
    <View style={[styles.customToast, { borderLeftColor: COLORS.primary }]}>
      <View style={styles.toastTextContainer}>
        {text1 ? <Text style={styles.toastText1}>{text1}</Text> : null}
        {text2 ? <Text style={styles.toastText2}>{text2}</Text> : null}
      </View>
    </View>
  ),
};
