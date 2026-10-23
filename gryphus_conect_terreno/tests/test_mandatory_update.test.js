import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import { compareSemver, checkForUpdate } from '../src/services/updateService';
import MandatoryUpdateModal from '../src/components/MandatoryUpdateModal';

// Mock FileSystem and IntentLauncher
jest.mock('expo-file-system', () => ({
  cacheDirectory: 'file:///data/cache/',
  getInfoAsync: jest.fn().mockResolvedValue({ exists: false }),
  deleteAsync: jest.fn().mockResolvedValue(true),
  getContentUriAsync: jest.fn().mockResolvedValue('content://trabs.provider/apk'),
  createDownloadResumable: jest.fn().mockReturnValue({
    downloadAsync: jest.fn().mockResolvedValue({ uri: 'file:///data/cache/GryPhusConectTerreno_Update.apk' }),
  }),
}));

jest.mock('expo-intent-launcher', () => ({
  startActivityAsync: jest.fn().mockResolvedValue(true),
}));

describe('Auto-Update System Tests', () => {
  describe('compareSemver', () => {
    test('identifica versiones superiores correctamente', () => {
      expect(compareSemver('1.0.1', '1.0.0')).toBe(1);
      expect(compareSemver('1.1.0', '1.0.9')).toBe(1);
      expect(compareSemver('2.0.0', '1.9.9')).toBe(1);
      expect(compareSemver('mobile-v1.0.5', '1.0.4')).toBe(1);
    });

    test('identifica versiones inferiores o iguales correctamente', () => {
      expect(compareSemver('1.0.0', '1.0.1')).toBe(-1);
      expect(compareSemver('1.0.0', '1.0.0')).toBe(0);
      expect(compareSemver('v1.0.0', '1.0.0')).toBe(0);
    });
  });

  describe('checkForUpdate with GitHub Releases API', () => {
    beforeEach(() => {
      global.fetch = jest.fn();
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    test('filtra releases móviles y descarta releases de escritorio', async () => {
      const mockReleases = [
        {
          tag_name: 'desktop-v1.0.6',
          body: 'Novedades escritorio',
          assets: [
            { name: 'GryPhusConectGerencia_Setup_v1.0.6.exe', browser_download_url: 'https://gh.com/exe' }
          ]
        },
        {
          tag_name: 'mobile-v2.0.0',
          body: 'Novedades mobile',
          published_at: '2026-09-01T20:00:00Z',
          assets: [
            { name: 'GryPhusConectTerreno_v2.0.0.apk', browser_download_url: 'https://gh.com/apk', size: 25000000 }
          ]
        }
      ];

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockReleases,
      });

      const result = await checkForUpdate();
      expect(result.isUpdateAvailable).toBe(true);
      expect(result.remoteVersion).toBe('2.0.0');
      expect(result.downloadUrl).toBe('https://gh.com/apk');
      expect(result.sizeBytes).toBe(25000000);
    });

    test('no detecta update si la versión móvil es igual o menor a la actual', async () => {
      const mockReleases = [
        {
          tag_name: 'mobile-v1.0.0',
          body: 'Version inicial',
          assets: [
            { name: 'GryPhusConectTerreno_v1.0.0.apk', browser_download_url: 'https://gh.com/apk' }
          ]
        }
      ];

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockReleases,
      });

      const result = await checkForUpdate();
      expect(result.isUpdateAvailable).toBe(false);
    });
  });

  describe('MandatoryUpdateModal Component', () => {
    test('se renderiza correctamente y muestra la versión remota', () => {
      const updateInfo = {
        isUpdateAvailable: true,
        remoteVersion: '1.5.0',
        releaseNotes: 'Correcciones críticas de terreno.',
        downloadUrl: 'https://gh.com/apk',
      };

      const { getByText } = render(
        <MandatoryUpdateModal visible={true} updateInfo={updateInfo} />
      );

      expect(getByText('Actualización Requerida')).toBeTruthy();
      expect(getByText('Correcciones críticas de terreno.')).toBeTruthy();
    });

    test('no se renderiza si visible es false', () => {
      const updateInfo = {
        isUpdateAvailable: false,
      };

      const { queryByText } = render(
        <MandatoryUpdateModal visible={false} updateInfo={updateInfo} />
      );

      expect(queryByText('Actualización Requerida')).toBeNull();
    });
  });

  describe('openPlayStore integration', () => {
    test('abre la URL de market si está soportada', async () => {
      const { openPlayStore } = require('../src/services/updateService');
      const { Linking } = require('react-native');
      jest.spyOn(Linking, 'canOpenURL').mockResolvedValueOnce(true);
      jest.spyOn(Linking, 'openURL').mockResolvedValueOnce(true);

      const res = await openPlayStore();
      expect(res.success).toBe(true);
      expect(res.via).toBe('market');
      expect(Linking.openURL).toHaveBeenCalledWith(expect.stringContaining('market://details?id='));
    });

    test('usa fallback web si market no está soportado', async () => {
      const { openPlayStore } = require('../src/services/updateService');
      const { Linking } = require('react-native');
      jest.spyOn(Linking, 'canOpenURL').mockResolvedValueOnce(false);
      jest.spyOn(Linking, 'openURL').mockResolvedValueOnce(true);

      const res = await openPlayStore();
      expect(res.success).toBe(true);
      expect(res.via).toBe('web');
      expect(Linking.openURL).toHaveBeenCalledWith(expect.stringContaining('https://play.google.com/store/apps/details?id='));
    });
  });
});
