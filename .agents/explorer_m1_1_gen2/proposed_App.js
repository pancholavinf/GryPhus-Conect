import React, { useState, useEffect, useCallback, useRef } from 'react';
import { StyleSheet, SafeAreaView, View, Text, TouchableOpacity } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useFonts } from 'expo-font';
import { Montserrat_700Bold, Montserrat_600SemiBold } from '@expo-google-fonts/montserrat';
import { Inter_400Regular, Inter_500Medium, Inter_700Bold } from '@expo-google-fonts/inter';
import * as SplashScreen from 'expo-splash-screen';
import Toast from 'react-native-toast-message';

import { initDatabase } from './src/database/db';
import { syncCatalog } from './src/database/sync';
import { COLORS } from './src/constants/theme';
import { supabase } from './src/services/supabase';

import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import SelectionFlowScreen from './src/screens/SelectionFlowScreen';

// Keep the splash screen visible while we fetch resources
SplashScreen.preventAutoHideAsync().catch((err) => {
  console.warn('SplashScreen.preventAutoHideAsync() failed', err);
});

const Stack = createNativeStackNavigator();

export default function App() {
  const [dbReady, setDbReady] = useState(false);
  const [dbError, setDbError] = useState(null);
  const [session, setSession] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [activeObra, setActiveObra] = useState(null);
  const [catalogSynced, setCatalogSynced] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  const isSyncingCatalogRef = useRef(false);

  // Load custom fonts asynchronously
  const [fontsLoaded, fontError] = useFonts({
    'Montserrat-Bold': Montserrat_700Bold,
    'Montserrat-SemiBold': Montserrat_600SemiBold,
    'Montserrat': Montserrat_600SemiBold,
    'Inter-Regular': Inter_400Regular,
    'Inter-Medium': Inter_500Medium,
    'Inter-Bold': Inter_700Bold,
    'Inter': Inter_400Regular,
  });

  const runSyncCatalog = async (jefeId) => {
    if (isSyncingCatalogRef.current) return;
    isSyncingCatalogRef.current = true;
    try {
      await syncCatalog(jefeId);
      setCatalogSynced(true);
    } catch (err) {
      console.error('Catalog sync failed:', err);
    } finally {
      isSyncingCatalogRef.current = false;
    }
  };

  // Initialize DB and fetch session on mount
  useEffect(() => {
    try {
      initDatabase();
      setDbReady(true);
    } catch (error) {
      console.error('Failed to initialize database:', error);
      setDbError(error.message || 'Database initialization error');
    }

    let isMounted = true;
    let subscription = null;

    const checkInitialSessionAndSubscribe = async () => {
      let initialSession = null;
      try {
        if (supabase.auth && typeof supabase.auth.getSession === 'function') {
          const { data } = await supabase.auth.getSession();
          initialSession = data?.session;
        }
      } catch (err) {
        console.warn('Failed to retrieve initial session:', err);
      }

      if (isMounted) {
        if (initialSession) {
          const profile = {
            id: initialSession.user?.id || 'jefe-123',
            email: initialSession.user?.email,
            nombre: initialSession.user?.email?.split('@')[0],
            rol: 'jefe_obra',
          };
          setSession(initialSession);
          setUserProfile(profile);
          await runSyncCatalog(profile.id);
        }
        setIsAuthChecking(false);
      }

      // Subscribe to auth state changes for subsequent events
      if (supabase.auth && typeof supabase.auth.onAuthStateChange === 'function') {
        const authListener = supabase.auth.onAuthStateChange(async (event, activeSession) => {
          if (!isMounted) return;

          // Prevent duplicate sync on initial connection since getSession handles it
          if (event === 'INITIAL_SESSION' && initialSession) {
            return;
          }

          if (activeSession) {
            const profile = {
              id: activeSession.user?.id || 'jefe-123',
              email: activeSession.user?.email,
              nombre: activeSession.user?.email?.split('@')[0],
              rol: 'jefe_obra',
            };
            setSession(activeSession);
            setUserProfile(profile);
            await runSyncCatalog(profile.id);
          } else {
            setSession(null);
            setUserProfile(null);
            setCatalogSynced(false);
          }
          setIsAuthChecking(false);
        });
        subscription = authListener?.data?.subscription;
      }
    };

    checkInitialSessionAndSubscribe();

    return () => {
      isMounted = false;
      if (subscription && typeof subscription.unsubscribe === 'function') {
        subscription.unsubscribe();
      }
    };
  }, []);

  const handleLoginSuccess = async ({ session: userSession, userProfile: profile }) => {
    setIsAuthChecking(true);
    try {
      await runSyncCatalog(profile.id);
    } catch (err) {
      console.error('Catalog sync failed on manual login:', err);
    } finally {
      setSession(userSession);
      setUserProfile(profile);
      setIsAuthChecking(false);
    }
  };

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
    } catch (err) {
      console.warn('Sign out error:', err);
    } finally {
      setSession(null);
      setUserProfile(null);
      setActiveObra(null);
      setCatalogSynced(false);
    }
  };

  // Hide splash screen once fonts are loaded, DB is ready, and initial auth check is finished
  const onLayoutRootView = useCallback(async () => {
    if ((fontsLoaded || fontError) && (dbReady || dbError) && !isAuthChecking) {
      try {
        await SplashScreen.hideAsync();
      } catch (err) {
        console.warn('SplashScreen.hideAsync() failed', err);
      }
    }
  }, [fontsLoaded, fontError, dbReady, dbError, isAuthChecking]);

  if ((!fontsLoaded && !fontError) || (!dbReady && !dbError) || isAuthChecking) {
    return null;
  }

  // If local database initialization failed, display error fallback screen
  if (dbError) {
    return (
      <SafeAreaView style={styles.errorContainer} onLayout={onLayoutRootView}>
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Error de Inicialización</Text>
          <Text style={styles.errorMessage}>
            No se pudo inicializar la base de datos local: {dbError}
          </Text>
          <Text style={styles.errorMessage}>
            Verifique el espacio de almacenamiento del dispositivo o reinicie la aplicación.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  const isUserAuthenticated = session && userProfile && catalogSynced;

  return (
    <SafeAreaView style={styles.container} onLayout={onLayoutRootView}>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {!isUserAuthenticated ? (
            <Stack.Screen name="Login">
              {props => <LoginScreen {...props} onLoginSuccess={handleLoginSuccess} />}
            </Stack.Screen>
          ) : (
            <>
              <Stack.Screen name="Home">
                {props => (
                  <HomeScreen
                    {...props}
                    userProfile={userProfile}
                    onSelectObra={(obra) => {
                      setActiveObra(obra);
                      props.navigation.navigate('SelectionFlow');
                    }}
                    onLogout={handleLogout}
                    onNavigateToFlow={() => props.navigation.navigate('SelectionFlow')}
                  />
                )}
              </Stack.Screen>
              <Stack.Screen name="SelectionFlow">
                {props => (
                  <SelectionFlowScreen
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
      <Toast />
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
    backgroundColor: '#FFF',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorBox: {
    padding: 20,
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#EF4444',
    borderRadius: 8,
    alignItems: 'center',
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#B91C1C',
    fontFamily: 'Montserrat-Bold',
    marginBottom: 10,
  },
  errorMessage: {
    fontSize: 14,
    color: '#7F1D1D',
    fontFamily: 'Inter-Regular',
    textAlign: 'center',
    marginTop: 5,
  },
});
