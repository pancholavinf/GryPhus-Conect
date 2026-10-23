// Web stub for expo-sqlite
// On web mode, SQLite is stubbed out and data flows through memoryCache.js

function openDatabaseSync() {
  return {
    execSync: () => {},
    runSync: () => ({ insertId: Date.now(), rowsAffected: 1 }),
    getAllSync: () => [],
    getFirstSync: () => null,
  };
}

module.exports = { openDatabaseSync };
