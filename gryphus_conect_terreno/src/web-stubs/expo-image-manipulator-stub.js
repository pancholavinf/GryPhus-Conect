// Web stub for expo-image-manipulator
// On web, just return the original URI unchanged

const SaveFormat = { JPEG: 'jpeg', PNG: 'png' };

async function manipulateAsync(uri, _actions, _options) {
  return { uri };
}

module.exports = { manipulateAsync, SaveFormat };
