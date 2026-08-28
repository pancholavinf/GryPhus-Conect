// src/constants/theme.js

export const COLORS = {
  // Brand Colors
  primary: '#1A529B',       // Azul Track (Headers, branding, navigation)
  secondary: '#EE741D',     // Naranja Obra (Main CTAs, buttons, primary action)
  accent: '#4BA2E3',        // Azul Acero (Secondary links, borders, graphics)
  
  // Background & Surfaces
  background: '#FAFAFA',    // Light background for mobile app
  surface: '#FFFFFF',       // Card & component containers
  cardBorder: '#F1F5F9',    // border-slate-100 for subtle dividers
  
  // Text Colors
  textPrimary: '#1E293B',   // slate-800 for main text
  textSecondary: '#64748B', // slate-500 (Support Gray) for labels, helpers
  textLight: '#FFFFFF',     // White text on dark backgrounds
  
  // Semantic Status Colors
  status: {
    pending: '#F59E0B',     // Yellow status
    approved: '#10B981',    // Green status
    error: '#EF4444',       // Red status (Error / Offline)
    offline: '#EF4444',     // Red status
  }
};

export const TYPOGRAPHY = {
  fonts: {
    heading: 'Montserrat_700Bold',
    headingMedium: 'Montserrat_500Medium',
    headingRegular: 'Montserrat_400Regular',
    body: 'Inter_400Regular',
    bodySemiBold: 'Inter_600SemiBold',
    bodyBold: 'Inter_700Bold',
  },
  sizes: {
    h1: 24,
    h2: 18,
    body: 14,
    caption: 12,
  },
  lineHeights: {
    h1: 32,
    h2: 22,
    body: 20,
    caption: 16,
  }
};

export const SHADOWS = {
  subtle: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  none: {
    shadowOpacity: 0,
    elevation: 0,
  }
};

export const LAYOUT = {
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    xxl: 32,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    full: 9999, // For rounded-full gloves-friendly buttons
  },
  buttons: {
    minHeight: 48, // Minimum 48px height for gloves-friendly use
  }
};

export const theme = {
  colors: COLORS,
  typography: TYPOGRAPHY,
  shadows: SHADOWS,
  layout: LAYOUT,
};

export default theme;
