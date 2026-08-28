// Metro module resolver — maps native-only modules to web stubs when running on web
// This allows `npx expo start --web` to work without crashing on SQLite / Camera imports

const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Add web-specific module aliases
config.resolver = config.resolver || {};
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web') {
    // Stub out native-only modules on web
    const nativeOnlyModules = {
      'expo-sqlite': require.resolve('./src/web-stubs/expo-sqlite-stub.js'),
      'expo-camera': require.resolve('./src/web-stubs/expo-camera-stub.js'),
      'expo-image-manipulator': require.resolve('./src/web-stubs/expo-image-manipulator-stub.js'),
    };

    for (const [native, stub] of Object.entries(nativeOnlyModules)) {
      if (moduleName === native || moduleName.startsWith(native + '/')) {
        return { filePath: stub, type: 'sourceFile' };
      }
    }
  }

  // Default resolution for everything else
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
