// App.js
import React, { useState, useEffect, useCallback } from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import * as SplashScreen from 'expo-splash-screen';

// Fonts
import { 
  useFonts,
  Montserrat_400Regular,
  Montserrat_500Medium,
  Montserrat_700Bold 
} from '@expo-google-fonts/montserrat';
import { 
  Inter_400Regular,
  Inter_600SemiBold,
  Inter_700Bold 
} from '@expo-google-fonts/inter';

// Theme & Components
import { theme } from './src/constants/theme';
import { ToastProvider } from './src/components/Toast';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import SelectionFlowScreen from './src/screens/SelectionFlowScreen';

// Prevent splash screen from auto-hiding until fonts are loaded
SplashScreen.preventAutoHideAsync().catch(() => {
  /* ignore error */
});

const Stack = createNativeStackNavigator();

export default function App() {
  const [fontsLoaded, fontError] = useFonts({
    Montserrat_400Regular,
    Montserrat_500Medium,
    Montserrat_700Bold,
    Inter_400Regular,
    Inter_600SemiBold,
    Inter_700Bold,
  });

  // Authentication state (to be integrated with Supabase/SQLite in M2)
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    // Check initial session (mock session check, to be updated in M2)
    const checkSession = async () => {
      try {
        // Mock latency for DB initialization
        await new Promise(resolve => setTimeout(resolve, 800));
        setIsAuthenticated(false); // Default to false to force login
      } catch (error) {
        console.error('Session initialization error:', error);
      } finally {
        setIsInitializing(false);
      }
    };
    checkSession();
  }, []);

  const onLayoutRootView = useCallback(async () => {
    if (fontsLoaded || fontError) {
      // Hide the splash screen once fonts are ready
      await SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) {
    return null; // Return null while fonts are loading and splash is visible
  }

  if (isInitializing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container} onLayout={onLayoutRootView}>
      <StatusBar style="auto" />
      <ToastProvider>
        <NavigationContainer>
          <Stack.Navigator
            screenOptions={{
              headerStyle: {
                backgroundColor: theme.colors.primary,
              },
              headerTintColor: theme.colors.textLight,
              headerTitleStyle: {
                fontFamily: theme.typography.fonts.heading,
                fontSize: theme.typography.sizes.h2,
              },
              contentStyle: {
                backgroundColor: theme.colors.background,
              },
            }}
          >
            {!isAuthenticated ? (
              <Stack.Screen 
                name="Login" 
                options={{ headerShown: false }}
              >
                {props => (
                  <LoginScreen 
                    {...props} 
                    onLoginSuccess={() => setIsAuthenticated(true)} 
                  />
                )}
              </Stack.Screen>
            ) : (
              <>
                <Stack.Screen 
                  name="Home" 
                  options={{ 
                    title: 'Track Obra - Avances',
                    headerBackVisible: false,
                  }}
                >
                  {props => (
                    <HomeScreen 
                      {...props} 
                      onLogout={() => setIsAuthenticated(false)} 
                    />
                  )}
                </Stack.Screen>
                <Stack.Screen 
                  name="SelectionFlow" 
                  component={SelectionFlowScreen}
                  options={{ 
                    title: 'Registrar Avance',
                  }}
                />
              </>
            )}
          </Stack.Navigator>
        </NavigationContainer>
      </ToastProvider>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FAFAFA',
  },
});
