import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';
import * as IntentLauncher from 'expo-intent-launcher';
import appConfig from '../../app.json';

const GITHUB_OWNER = 'pancholavinf';
const GITHUB_REPO = 'trabs-gerencia';
export const GITHUB_RELEASES_URL = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/releases`;

export const CURRENT_VERSION = appConfig?.expo?.version || '1.0.0';

/**
 * Compara dos versiones semánticas (ej: "1.0.1" vs "1.0.0")
 * Retorna:
 *  1 si v1 > v2
 * -1 si v1 < v2
 *  0 si v1 == v2
 */
export function compareSemver(v1, v2) {
  const parse = (v) =>
    (v || '0.0.0')
      .replace(/^[^\d]*/, '') // eliminar 'v', 'mobile-v', etc.
      .split('.')
      .map((num) => parseInt(num, 10) || 0);

  const parts1 = parse(v1);
  const parts2 = parse(v2);
  const len = Math.max(parts1.length, parts2.length);

  for (let i = 0; i < len; i++) {
    const num1 = parts1[i] || 0;
    const num2 = parts2[i] || 0;
    if (num1 > num2) return 1;
    if (num1 < num2) return -1;
  }
  return 0;
}

/**
 * Consulta GitHub Releases y busca la versión móvil más reciente con APK
 */
export async function checkForUpdate() {
  try {
    const response = await fetch(GITHUB_RELEASES_URL, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'TrabsTerreno-MobileApp',
      },
    });

    if (!response.ok) {
      console.warn(`[UpdateService] Error HTTP ${response.status} consultando releases`);
      return { isUpdateAvailable: false, error: `HTTP ${response.status}` };
    }

    const releases = await response.json();
    if (!Array.isArray(releases)) {
      return { isUpdateAvailable: false, error: 'Respuesta inválida de GitHub' };
    }

    // Buscar el release móvil más reciente
    let targetRelease = null;
    let targetAsset = null;

    for (const rel of releases) {
      const tag = (rel.tag_name || '').toLowerCase();
      // Filtrar por tags que comiencen con mobile- o contengan APK
      const isMobileTag = tag.startsWith('mobile-');
      const apkAsset = (rel.assets || []).find((a) =>
        (a.name || '').toLowerCase().endsWith('.apk')
      );

      if (isMobileTag && apkAsset) {
        targetRelease = rel;
        targetAsset = apkAsset;
        break;
      } else if (!targetRelease && apkAsset && !tag.startsWith('desktop-')) {
        // Fallback si no tiene prefijo mobile- pero tiene APK y no es desktop
        targetRelease = rel;
        targetAsset = apkAsset;
        break;
      }
    }

    if (!targetRelease || !targetAsset) {
      return {
        isUpdateAvailable: false,
        currentVersion: CURRENT_VERSION,
        remoteVersion: CURRENT_VERSION,
      };
    }

    const remoteTag = targetRelease.tag_name || '';
    const remoteVersion = remoteTag.replace(/^[^\d]*/, '').trim();
    const downloadUrl = targetAsset.browser_download_url;
    const sizeBytes = targetAsset.size || 0;
    const releaseNotes = targetRelease.body || 'Mejoras operativas y optimización de rendimiento.';
    const releaseDate = targetRelease.published_at
      ? targetRelease.published_at.substring(0, 10)
      : '';

    const isUpdateAvailable = compareSemver(remoteVersion, CURRENT_VERSION) > 0;

    return {
      isUpdateAvailable,
      currentVersion: CURRENT_VERSION,
      remoteVersion,
      downloadUrl,
      sizeBytes,
      releaseNotes,
      releaseDate,
    };
  } catch (error) {
    console.warn('[UpdateService] Excepción al comprobar actualizaciones:', error);
    return { isUpdateAvailable: false, error: error.message };
  }
}

/**
 * Descarga el APK con seguimiento de progreso e invoca el instalador nativo de Android
 */
export async function downloadAndInstallApk(downloadUrl, onProgress) {
  if (Platform.OS !== 'android') {
    return {
      success: false,
      message: 'La instalación automática de APK solo es soportada en Android.',
    };
  }

  const localApkPath = `${FileSystem.cacheDirectory}TrabsTerreno_Update.apk`;

  try {
    // 1. Eliminar descarga previa si existía
    const fileInfo = await FileSystem.getInfoAsync(localApkPath);
    if (fileInfo.exists) {
      await FileSystem.deleteAsync(localApkPath, { idempotent: true });
    }

    // 2. Descargar con seguimiento de progreso
    const downloadResumable = FileSystem.createDownloadResumable(
      downloadUrl,
      localApkPath,
      {},
      (downloadProgress) => {
        const total = downloadProgress.totalBytesExpectedToWrite;
        const current = downloadProgress.totalBytesWritten;
        const percent = total > 0 ? (current / total) * 100 : 0;
        if (typeof onProgress === 'function') {
          onProgress({
            downloadedBytes: current,
            totalBytes: total,
            percent: Math.min(100, Math.max(0, percent)),
          });
        }
      }
    );

    const result = await downloadResumable.downloadAsync();
    if (!result || !result.uri) {
      throw new Error('La descarga del instalador falló.');
    }

    // 3. Obtener Content URI compatible con Android FileProvider
    const contentUri = await FileSystem.getContentUriAsync(result.uri);

    // 4. Lanzar el Intent de instalación de paquete de Android
    await IntentLauncher.startActivityAsync('android.intent.action.VIEW', {
      data: contentUri,
      flags: 1, // FLAG_GRANT_READ_URI_PERMISSION
      type: 'application/vnd.android.package-archive',
    });

    return { success: true, localUri: result.uri, contentUri };
  } catch (error) {
    console.error('[UpdateService] Error durante la descarga/instalación:', error);
    return { success: false, error: error.message };
  }
}
