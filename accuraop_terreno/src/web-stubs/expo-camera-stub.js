// Web stub for expo-camera
const React = require('react');
const { View, Text, Image } = require('react-native');

const CAMARA_LOGO = require('../../assets/sprites/camara_logo.png');

function CameraView({ children, style }) {
  return React.createElement(View, {
    style: [{ backgroundColor: '#222', justifyContent: 'center', alignItems: 'center' }, style]
  },
    React.createElement(Image, { source: CAMARA_LOGO, style: { width: 36, height: 36, marginBottom: 8, resizeMode: 'contain' } }),
    React.createElement(Text, { style: { color: '#fff', fontSize: 14 } }, 'Cámara no disponible en web'),
    children
  );
}

function useCameraPermissions() {
  return [{ granted: true }, async () => ({ granted: true })];
}

module.exports = { CameraView, useCameraPermissions };
