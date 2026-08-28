import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import App from '../App';

describe('Tier 4: Real-World Workload and Stress', () => {
  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
  });

  test('Simulates a full workday: downloads catalog, logs 5 reports offline, reconnects, logs 2 online, and syncs all', async () => {
    const { getByTestId, findByTestId } = render(<App />);

    // 1. Start App online and log in
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });
    await findByTestId('home-screen');

    // 2. Go offline
    await act(async () => {
      global.setNetworkState(false);
    });

    // 3. Log 5 reports offline
    for (let i = 1; i <= 5; i++) {
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
      fireEvent.changeText(commentInput, `Offline Workday Entry #${i}`);
      fireEvent.press(getByTestId('comment-continue-button'));
      await act(async () => {
        fireEvent.press(getByTestId('submit-advance-button'));
      });
      await findByTestId('obra-menu-screen');
      fireEvent.press(getByTestId('back-button'));
      await findByTestId('home-screen');
    }

    // Verify 5 offline entries stored locally
    expect(global.dbTables.avances.length).toBe(5);
    expect(global.dbTables.avances.filter(x => x.synced === 0).length).toBe(5);

    // 4. Reconnect to network
    await act(async () => {
      global.setNetworkState(true);
    });

    // 5. Log 2 reports online (which will trigger immediate sync)
    for (let i = 6; i <= 7; i++) {
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
      fireEvent.changeText(commentInput, `Online Workday Entry #${i}`);
      fireEvent.press(getByTestId('comment-continue-button'));
      await act(async () => {
        fireEvent.press(getByTestId('submit-advance-button'));
      });
      await findByTestId('obra-menu-screen');
      fireEvent.press(getByTestId('back-button'));
      await findByTestId('home-screen');
    }

    // 6. Run bulk synchronization (syncs the 5 offline ones, the online ones sync immediately)
    fireEvent.press(getByTestId('menu-button'));
    const syncBtn = await findByTestId('sync-button');
    await act(async () => {
      fireEvent.press(syncBtn);
    });

    // 7. Verify all 7 advances are synced
    await waitFor(() => {
      expect(global.dbTables.avances.length).toBe(7);
      expect(global.dbTables.avances.filter(x => x.synced === 1).length).toBe(7);
    });
  });

  test('Double submission prevention: rapid presses only insert a single record', async () => {
    const { getByTestId, findByTestId } = render(<App />);

    // Log in
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });
    await findByTestId('home-screen');

    // Enter Selection Flow Screen
    fireEvent.press(getByTestId('obra-card-obra-789'));
    await findByTestId('obra-menu-screen');
    fireEvent.press(getByTestId('btn-avance'));
    await findByTestId('selection-flow-screen');
    fireEvent.changeText(getByTestId('progress-input'), '10');
    fireEvent.press(getByTestId('progress-continue-button'));
    await act(async () => {
      fireEvent.press(getByTestId('capture-photo-button'));
    });
    const commentInput = await findByTestId('comment-input');
    fireEvent.changeText(commentInput, 'Evitar doble click');
    fireEvent.press(getByTestId('comment-continue-button'));

    // Click submit button 5 times rapidly
    await act(async () => {
      const submitBtn = getByTestId('submit-advance-button');
      fireEvent.press(submitBtn);
      fireEvent.press(submitBtn);
      fireEvent.press(submitBtn);
      fireEvent.press(submitBtn);
      fireEvent.press(submitBtn);
    });

    // Assert database has exactly 1 entry written
    await waitFor(() => {
      expect(global.dbTables.avances.length).toBe(1);
    });
  });
});
