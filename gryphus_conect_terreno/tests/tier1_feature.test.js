import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import App from '../App';

describe('Tier 1: Feature Coverage (Happy Path)', () => {
  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
  });

  test('User can log in, select project/item, capture photo, save local DB, and sync to Supabase', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);

    // 1. Verify Login Screen displays
    expect(getByTestId('login-screen')).toBeTruthy();

    // 2. Fill login inputs
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');

    // 3. Press Login Button
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });

    // 4. Verify home screen is displayed
    const homeScreen = await findByTestId('home-screen');
    expect(homeScreen).toBeTruthy();

    // 5. Verify local DB tables are populated via catalog sync
    await waitFor(() => {
      expect(global.dbTables.obras.length).toBeGreaterThan(0);
      expect(global.dbTables.items_obra.length).toBeGreaterThan(0);
    });

    // 6. Select the Obra Card
    fireEvent.press(getByTestId('obra-card-obra-789'));

    // Verify Obra Menu Screen displays
    const menuScreen = await findByTestId('obra-menu-screen');
    expect(menuScreen).toBeTruthy();

    // Select the Avance Button
    fireEvent.press(getByTestId('btn-avance'));

    // 7. Verify Selection Flow Screen displays
    const flowScreen = await findByTestId('selection-flow-screen');
    expect(flowScreen).toBeTruthy();

    // 9. Input Quantity in Progress Step
    fireEvent.changeText(getByTestId('progress-input'), '45');
    
    // 10. Press Continue to Photo
    fireEvent.press(getByTestId('progress-continue-button'));

    // 11. Click Capture Photo
    await act(async () => {
      fireEvent.press(getByTestId('capture-photo-button'));
    });

    // 14. Input Comment
    const commentInput = await findByTestId('comment-input');
    fireEvent.changeText(commentInput, 'Avance completado hoy');

    // 15. Press Continue to Confirm
    fireEvent.press(getByTestId('comment-continue-button'));

    // 16. Submit the Advance
    await act(async () => {
      fireEvent.press(getByTestId('submit-advance-button'));
    });

    // 14. Verify SQLite record is updated to synced=1
    await waitFor(() => {
      expect(global.dbTables.avances.length).toBe(1);
      expect(global.dbTables.avances[0].synced).toBe(1);
      expect(global.dbTables.avances[0].fecha_subida_servidor).not.toBeNull();
    });

    // 15. Verify redirection back to ObraMenuScreen
    await waitFor(() => {
      expect(queryByTestId('obra-menu-screen')).toBeTruthy();
    });
  });
});
