import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import App from '../App';
import { saveAdvance, getUnsyncedAdvances } from '../src/database/db';

describe('Tier 3: Resilience and Recovery', () => {
  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
  });

  test('Queued offline reports sync successfully when reconnection occurs', async () => {
    const { getByTestId, findByTestId } = render(<App />);

    // Log in online
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });
    await findByTestId('home-screen');

    // Go offline
    await act(async () => {
      global.setNetworkState(false);
    });

    // Record 2 offline reports
    for (let i = 1; i <= 2; i++) {
      fireEvent.press(getByTestId('obra-card-obra-789'));
      await findByTestId('obra-menu-screen');
      fireEvent.press(getByTestId('btn-avance'));
      await findByTestId('selection-flow-screen');
      fireEvent.changeText(getByTestId('progress-input'), i.toString());
      fireEvent.press(getByTestId('progress-continue-button'));
      
      await act(async () => {
        fireEvent.press(getByTestId('capture-photo-button'));
      });
      
      const commentInput = await findByTestId('comment-input');
      fireEvent.changeText(commentInput, `Offline index ${i}`);
      fireEvent.press(getByTestId('comment-continue-button'));
      
      await act(async () => {
        fireEvent.press(getByTestId('submit-advance-button'));
      });
      await findByTestId('obra-menu-screen');
      fireEvent.press(getByTestId('back-button'));
      await findByTestId('home-screen');
    }

    // Verify they are unsynced in SQLite
    expect(global.dbTables.avances.length).toBe(2);
    expect(global.dbTables.avances.filter(x => x.synced === 0).length).toBe(2);

    // Reconnect online
    await act(async () => {
      global.setNetworkState(true);
    });

    // Click Sync Button on Home Screen
    fireEvent.press(getByTestId('menu-button'));
    const syncButton1 = await findByTestId('sync-button');
    await act(async () => {
      fireEvent.press(syncButton1);
    });

    // Verify both items are now synced
    await waitFor(() => {
      expect(global.dbTables.avances.filter(x => x.synced === 1).length).toBe(2);
    });
  });

  test('Database retains unsynced items across app unmount/crash, and syncs on restart', async () => {
    // 1. Setup unsynced advances in the DB (simulating offline work before a crash)
    global.dbTables.avances.push({
      id: 'crash-advance-1',
      id_item: 'item-101',
      id_jefe: 'jefe-123',
      item_obra_id: 'item-101',
      jefe_obra_id: 'jefe-123',
      cantidad: 10,
      comentario: 'Antes del crash',
      foto_path: 'file://photo.jpg',
      foto_url: 'file://photo.jpg',
      synced: 0,
      fecha_creacion: new Date().toISOString(),
      fecha_captura_local: new Date().toISOString(),
      fecha_subida_servidor: null
    });

    // Verify DB has the unsynced record
    expect(getUnsyncedAdvances().length).toBe(1);

    // 2. Restart/Remount app
    const { getByTestId, findByTestId } = render(<App />);

    // Log in
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });
    await findByTestId('home-screen');

    // 3. Perform Sync
    fireEvent.press(getByTestId('menu-button'));
    const syncButton2 = await findByTestId('sync-button');
    await act(async () => {
      fireEvent.press(syncButton2);
    });

    // 4. Assert that the pre-crash record was synced
    await waitFor(() => {
      const unsynced = getUnsyncedAdvances();
      expect(unsynced.length).toBe(0);
      expect(global.dbTables.avances.find(x => x.id === 'crash-advance-1').synced).toBe(1);
    });
  });
});
