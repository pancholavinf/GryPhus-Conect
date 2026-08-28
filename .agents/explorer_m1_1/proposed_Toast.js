// src/components/Toast.js
import React, { createContext, useContext, useState, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, Animated, TouchableOpacity } from 'react-native';
import { theme } from '../constants/theme';

const ToastContext = createContext(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const ToastProvider = ({ children }) => {
  const [toast, setToast] = useState({ message: '', type: 'info', visible: false });
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const timeoutRef = useRef(null);

  const hideToast = useCallback(() => {
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start(() => {
      setToast(prev => ({ ...prev, visible: false }));
    });
  }, [fadeAnim]);

  const showToast = useCallback((message, type = 'info', duration = 3000) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    setToast({ message, type, visible: true });

    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 350,
      useNativeDriver: true,
    }).start();

    timeoutRef.current = setTimeout(() => {
      hideToast();
    }, duration);
  }, [fadeAnim, hideToast]);

  const getBackgroundColor = () => {
    switch (toast.type) {
      case 'success':
        return theme.colors.status.approved;
      case 'error':
        return theme.colors.status.error;
      case 'pending':
        return theme.colors.status.pending;
      case 'info':
      default:
        return theme.colors.primary;
    }
  };

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      {toast.visible && (
        <Animated.View 
          style={[
            styles.toastContainer, 
            { 
              opacity: fadeAnim,
              backgroundColor: getBackgroundColor(),
              transform: [
                {
                  translateY: fadeAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [-30, 0], // slide down animation
                  }),
                },
              ],
            }
          ]}
        >
          <TouchableOpacity onPress={hideToast} activeOpacity={0.9} style={styles.content}>
            <Text style={styles.toastText}>{toast.message}</Text>
          </TouchableOpacity>
        </Animated.View>
      )}
    </ToastContext.Provider>
  );
};

const styles = StyleSheet.create({
  toastContainer: {
    position: 'absolute',
    top: 50, // Display at the top, below common status bar heights
    left: 20,
    right: 20,
    borderRadius: theme.layout.borderRadius.md,
    padding: theme.layout.spacing.md,
    zIndex: 9999,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 6,
  },
  content: {
    width: '100%',
    justifyContent: 'center',
  },
  toastText: {
    color: '#FFFFFF',
    fontFamily: theme.typography.fonts.bodySemiBold,
    fontSize: theme.typography.sizes.body,
    textAlign: 'center',
  },
});
