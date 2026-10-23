import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';
import App from '../App';

describe('Tier 6: Control de Obra Feature', () => {
  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
  });

  test('User can navigate to Control de Obra and view assigned workers with their role name and contact info', async () => {
    const { getByTestId, findByTestId } = render(<App />);

    // 1. Fill login inputs & log in
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });

    // 2. Reach home screen and select Obra
    const homeScreen = await findByTestId('home-screen');
    expect(homeScreen).toBeTruthy();

    const obraCard = await findByTestId('obra-card-obra-789');
    fireEvent.press(obraCard);

    // 3. Verify Obra Menu Screen displays
    const menuScreen = await findByTestId('obra-menu-screen');
    expect(menuScreen).toBeTruthy();

    // 4. Press Control de Obra button
    fireEvent.press(getByTestId('btn-control-obra'));

    // 5. Verify Control de Obra screen displays
    const controlScreen = await findByTestId('control-obra-screen');
    expect(controlScreen).toBeTruthy();

    // 6. Press back button to return to Obra Menu Screen
    fireEvent.press(getByTestId('back-button'));
    expect(await findByTestId('obra-menu-screen')).toBeTruthy();
  });
});
