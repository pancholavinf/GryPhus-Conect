import '@testing-library/jest-native/extend-expect';

// Mock global fetch for local files in Node test environment
global.fetch = jest.fn().mockImplementation((url) => {
  return Promise.resolve({
    ok: true,
    status: 200,
    blob: () => Promise.resolve({
      size: 1024,
      type: 'image/jpeg'
    })
  });
});

// Stateful mockTables for SQLite Mock
const mockTables = {
  perfiles_usuario: [],
  obras: [],
  obras_jefes_obra: [],
  items_obra: [],
  materiales_obra: [],
  avances: []
};

// Global DB helpers for test verification
global.dbTables = mockTables;
global.resetDbTables = () => {
  mockTables.perfiles_usuario = [];
  mockTables.obras = [];
  mockTables.obras_jefes_obra = [];
  mockTables.items_obra = [];
  mockTables.materiales_obra = [];
  mockTables.avances = [];
};

// Mock expo-sqlite using mockTables
jest.mock('expo-sqlite', () => ({
  openDatabaseSync: () => ({
    execSync: (sql) => {
      // Setup tables Schema
    },
    runSync: (sql, params = []) => {
      if (sql.includes('INSERT OR REPLACE INTO perfiles_usuario')) {
        mockTables.perfiles_usuario = mockTables.perfiles_usuario.filter(x => x.id !== params[0]);
        mockTables.perfiles_usuario.push({ id: params[0], email: params[1], nombre: params[2], rol: params[3] });
        return { changes: 1 };
      }
      if (sql.includes('INSERT OR REPLACE INTO obras_jefes_obra')) {
        mockTables.obras_jefes_obra = mockTables.obras_jefes_obra.filter(x => !(x.id_obra === params[0] && x.id_jefe === params[1]));
        mockTables.obras_jefes_obra.push({ id_obra: params[0], id_jefe: params[1] });
        return { changes: 1 };
      }
      if (sql.includes('INSERT OR REPLACE INTO obras')) {
        mockTables.obras = mockTables.obras.filter(x => x.id !== params[0]);
        mockTables.obras.push({ id: params[0], nombre: params[1], direccion: params[2] });
        return { changes: 1 };
      }
      if (sql.includes('INSERT OR REPLACE INTO items_obra')) {
        mockTables.items_obra = mockTables.items_obra.filter(x => x.id !== params[0]);
        mockTables.items_obra.push({ id: params[0], id_obra: params[1], descripcion: params[2], cantidad_total: parseFloat(params[3]), unidad: params[4], material_id: params[11] });
        return { changes: 1 };
      }
      if (sql.includes('INSERT OR REPLACE INTO materiales')) {
        mockTables.materiales_obra = mockTables.materiales_obra.filter(x => x.id !== params[0]);
        mockTables.materiales_obra.push({ id: params[0], nombre: params[1], unidad_medida: params[2], rendimiento_teorico_m2: parseFloat(params[3]), descripcion: params[4] });
        return { changes: 1 };
      }
      if (sql.includes('INTO avances')) {
        mockTables.avances = mockTables.avances.filter(x => x.id !== params[0]);
        mockTables.avances.push({
          id: params[0],
          id_item: params[1],
          item_obra_id: params[1],
          id_jefe: params[2],
          jefe_obra_id: params[2],
          cantidad: parseFloat(params[3]),
          comentario: params[4],
          foto_path: params[5],
          foto_url: params[5],
          synced: 0,
          fecha_creacion: params[6],
          fecha_captura_local: params[6],
          fecha_subida_servidor: null
        });
        return { lastInsertRowId: mockTables.avances.length, changes: 1 };
      }
      if (sql.includes('UPDATE avances SET synced = 1')) {
        const item = mockTables.avances.find(x => x.id === params[1]);
        if (item) {
          item.synced = 1;
          item.fecha_subida_servidor = params[0];
        }
        return { changes: 1 };
      }
      return { changes: 0 };
    },
    getFirstSync: (sql, params = []) => undefined,
    getAllSync: (sql, params = []) => {
      if (sql.includes('SELECT * FROM avances WHERE synced = 0')) {
        return mockTables.avances.filter(x => x.synced === 0);
      }
      if (sql.includes('SELECT o.* FROM obras o JOIN obras_jefes_obra ojo')) {
        const jefeId = params[0];
        const assignedObraIds = mockTables.obras_jefes_obra
          .filter(x => x.id_jefe === jefeId)
          .map(x => x.id_obra);
        return mockTables.obras.filter(x => assignedObraIds.includes(x.id));
      }
      if (sql.includes('SELECT * FROM items_obra WHERE id_obra = ?')) {
        const obraId = params[0];
        return mockTables.items_obra.filter(x => x.id_obra === obraId || x.obra_id === obraId);
      }
      if (sql.includes('SELECT DISTINCT m.* FROM materiales m JOIN items_obra i ON i.material_id = m.id WHERE i.obra_id = ?')) {
        const obraId = params[0];
        const assignedMatIds = mockTables.items_obra
          .filter(x => x.id_obra === obraId || x.obra_id === obraId)
          .map(x => x.material_id)
          .filter(Boolean);
        return mockTables.materiales_obra.filter(x => assignedMatIds.includes(x.id));
      }
      return [];
    }
  })
}));

// Mock NetInfo for connection toggling using mockNetState and mockListeners
let mockNetState = { isConnected: true };
let mockListeners = [];

global.setNetworkState = (connected) => {
  mockNetState.isConnected = connected;
  mockListeners.forEach(l => l(mockNetState));
};

jest.mock('@react-native-community/netinfo', () => ({
  fetch: jest.fn().mockImplementation(() => Promise.resolve(mockNetState)),
  addEventListener: jest.fn((callback) => {
    mockListeners.push(callback);
    callback(mockNetState);
    return () => {
      mockListeners = mockListeners.filter(l => l !== callback);
    };
  }),
  useNetInfo: () => mockNetState
}));

// Mock expo-camera
jest.mock('expo-camera', () => {
  const React = require('react');
  const { View, Text } = require('react-native');
  return {
    CameraView: ({ children }) => <View testID="camera-view"><Text>Camera</Text>{children}</View>,
    useCameraPermissions: () => [{ granted: true }, () => Promise.resolve({ granted: true })]
  };
});

// Mock expo-image-manipulator
jest.mock('expo-image-manipulator', () => ({
  manipulateAsync: jest.fn().mockImplementation((uri, actions, saveOptions) => {
    const scaleFactor = saveOptions && saveOptions.compress ? saveOptions.compress : 1.0;
    return Promise.resolve({
      uri: 'file://mock-compressed-photo.jpg',
      width: 800,
      height: 600,
      sizeBytes: 5000000 * scaleFactor
    });
  }),
  SaveFormat: { JPEG: 'jpeg', PNG: 'png' }
}));

// Global toggle for empty catalog simulation
let mockEmptyCatalog = false;
global.setMockEmptyCatalog = (val) => {
  mockEmptyCatalog = val;
};

// Helper to provide tables mocked data
function getMockDataForTable(tableName) {
  if (mockEmptyCatalog && tableName !== 'perfiles_usuario') {
    return [];
  }
  if (tableName === 'perfiles_usuario') {
    return [{ id: 'jefe-123', email: 'test@test.cl', nombre: 'Juan Pérez', rol: 'jefe_obra' }];
  }
  if (tableName === 'obras') {
    return [{ id: 'obra-789', nombre: 'Edificio Central', estado: 'activa', fecha_creacion: '2026-01-01', color: '#1A529B' }];
  }
  if (tableName === 'obras_jefes_obra') {
    return [{
      id: 'relation-1',
      obra_id: 'obra-789',
      jefe_obra_id: 'jefe-123',
      // Compatibility keys
      id_obra: 'obra-789',
      id_jefe: 'jefe-123'
    }];
  }
  if (tableName === 'items_obra') {
    return [{
      id: 'item-101',
      obra_id: 'obra-789',
      ubicacion: 'Piso 1',
      plano: 'E-101',
      descripcion_plano: 'Plano E-101',
      estructura: 'Metálica',
      dimension: '100x50',
      perfil: 'IPE',
      cantidad: 100,
      unidad: 'm2',
      descripcion: 'F-60 Metálico',
      material_obra_id: 'mat-202',
      // Compatibility keys
      id_obra: 'obra-789',
      cantidad_total: 100
    }];
  }
  if (tableName === 'materiales_obra') {
    return [{
      id: 'mat-202',
      obra_id: 'obra-789',
      nombre: 'Pintura Intumescente F-60',
      unidad_medida: 'tinetas',
      rendimiento_teorico_m2: 0.35,
      descripcion: 'Pintura cortafuegos premium'
    }];
  }
  return [];
}

// Mock Supabase client using Native Promises with full chainable support
export const mockSupabase = {
  auth: {
    signInWithPassword: jest.fn().mockImplementation(({ email, password }) => {
      if (email === 'test@test.cl' && password === '123456') {
        return Promise.resolve({
          data: { user: { id: 'jefe-123' }, session: { access_token: 'mock-session-token' } },
          error: null
        });
      } else {
        return Promise.resolve({
          data: { user: null, session: null },
          error: { message: 'Invalid credentials' }
        });
      }
    }),
    signOut: jest.fn().mockResolvedValue({ error: null }),
    updateUser: jest.fn().mockResolvedValue({ data: { user: {} }, error: null })
  },
  from: jest.fn().mockImplementation((tableName) => {
    const data = getMockDataForTable(tableName);
    
    const chain = {
      data: [...data],
      error: null
    };

    chain.select = jest.fn().mockImplementation(() => {
      return chain;
    });

    chain.insert = jest.fn().mockImplementation((insertData) => {
      const insertChain = {
        select: jest.fn().mockImplementation(() => insertChain),
        then: (resolve) => resolve({ data: insertData, error: null })
      };
      return insertChain;
    });

    chain.update = jest.fn().mockImplementation((updateData) => {
      const updateChain = {
        eq: jest.fn().mockImplementation((column, value) => {
          // Update the matching rows in dbTables if available
          if (global.dbTables && global.dbTables.perfiles_usuario) {
            global.dbTables.perfiles_usuario = global.dbTables.perfiles_usuario.map(row =>
              row[column] === value ? { ...row, ...updateData } : row
            );
          }
          return Promise.resolve({ data: updateData, error: null });
        }),
        then: (resolve) => resolve({ data: updateData, error: null }),
      };
      return updateChain;
    });

    chain.upsert = jest.fn().mockImplementation((upsertData) => {
      const dataArray = Array.isArray(upsertData) ? upsertData : [upsertData];
      if (global.dbTables && global.dbTables.perfiles_usuario) {
        for (const item of dataArray) {
          const exists = global.dbTables.perfiles_usuario.some(row => row.id === item.id);
          if (exists) {
            global.dbTables.perfiles_usuario = global.dbTables.perfiles_usuario.map(row =>
              row.id === item.id ? { ...row, ...item } : row
            );
          } else {
            global.dbTables.perfiles_usuario.push(item);
          }
        }
      }
      const upsertChain = {
        then: (resolve) => resolve({ data: upsertData, error: null })
      };
      return upsertChain;
    });

    chain.eq = jest.fn().mockImplementation((column, value) => {
      chain.data = chain.data.filter(x => x[column] === value || (column === 'jefe_obra_id' && x.id_jefe === value) || (column === 'jefe_obra_id' && x.jefe_obra_id === value));
      return chain;
    });

    chain.in = jest.fn().mockImplementation((column, values) => {
      chain.data = chain.data.filter(x => values.includes(x[column]));
      return chain;
    });

    chain.single = jest.fn().mockImplementation(() => {
      const singleItem = chain.data[0] || null;
      return Promise.resolve({ data: singleItem, error: singleItem ? null : new Error('Not found') });
    });

    // Make the chain thenable so it can be awaited directly
    chain.then = (resolve) => {
      resolve({ data: chain.data, error: null });
    };

    return chain;
  }),
  storage: {
    from: jest.fn().mockReturnValue({
      upload: jest.fn().mockImplementation((path, file) => {
        return Promise.resolve({ data: { path: `fotos/${path}` }, error: null });
      }),
      getPublicUrl: jest.fn().mockImplementation((path) => {
        return { data: { publicUrl: `https://mock.supabase.co/storage/v1/object/public/${path}` } };
      })
    })
  }
};

jest.mock('@supabase/supabase-js', () => ({
  createClient: () => mockSupabase
}));

// Mock Async Storage
jest.mock('@react-native-async-storage/async-storage', () => 
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock expo-font
jest.mock('expo-font', () => ({
  useFonts: () => [true, null],
  loadAsync: () => Promise.resolve(),
}));

// Mock expo-splash-screen
jest.mock('expo-splash-screen', () => ({
  preventAutoHideAsync: jest.fn().mockResolvedValue(true),
  hideAsync: jest.fn().mockResolvedValue(true),
}));

// Mock expo-image-picker
jest.mock('expo-image-picker', () => ({
  requestMediaLibraryPermissionsAsync: jest.fn().mockResolvedValue({ status: 'granted' }),
  requestCameraPermissionsAsync: jest.fn().mockResolvedValue({ status: 'granted' }),
  launchImageLibraryAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: 'file://mock-photo.jpg' }]
  }),
  launchCameraAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: 'file://mock-photo.jpg' }]
  }),
  MediaTypeOptions: { Images: 'Images' }
}));

