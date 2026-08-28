import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import App from '../App';

describe('Tier 2: Boundary and Corner Cases', () => {
  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
  });

  test('Offline submissions are saved in local SQLite with synced = 0', async () => {
    const { getByTestId, findByTestId } = render(<App />);

    // Log in online to load catalog
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

    // Enter selection flow
    fireEvent.press(getByTestId('obra-card-obra-789'));
    await findByTestId('obra-menu-screen');
    fireEvent.press(getByTestId('btn-avance'));
    await findByTestId('selection-flow-screen');

    // Submit advance offline
    fireEvent.changeText(getByTestId('progress-input'), '15');
    fireEvent.press(getByTestId('progress-continue-button'));

    await act(async () => {
      fireEvent.press(getByTestId('capture-photo-button'));
    });

    const commentInput = await findByTestId('comment-input');
    fireEvent.changeText(commentInput, 'Avance registrado offline');
    fireEvent.press(getByTestId('comment-continue-button'));
    
    await act(async () => {
      fireEvent.press(getByTestId('submit-advance-button'));
    });

    // Verify stored locally with synced = 0
    await waitFor(() => {
      expect(global.dbTables.avances.length).toBe(1);
      expect(global.dbTables.avances[0].synced).toBe(0);
      expect(global.dbTables.avances[0].fecha_subida_servidor).toBeNull();
    });
  });

  test('Empty state displays when no works are assigned', async () => {
    // Simulates zero works returned from Supabase
    global.setMockEmptyCatalog(true);

    const { getByTestId, findByTestId, queryByTestId } = render(<App />);

    // Log in
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });
    await findByTestId('home-screen');

    // Check empty state components
    expect(getByTestId('empty-obras-view')).toBeTruthy();
    expect(queryByTestId('start-flow-button')).toBeNull();

    // Restore catalog mock settings for subsequent tests
    global.setMockEmptyCatalog(false);
  });

  test('Input validation prevents submissions exceeding item limits', async () => {
    const { getByTestId, findByTestId, getByText } = render(<App />);

    // Log in
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });
    await findByTestId('home-screen');

    fireEvent.press(getByTestId('obra-card-obra-789'));
    await findByTestId('obra-menu-screen');
    fireEvent.press(getByTestId('btn-avance'));
    await findByTestId('selection-flow-screen');
    
    // Total quantity is 100, try to input 150
    fireEvent.changeText(getByTestId('progress-input'), '150');
    
    await act(async () => {
      fireEvent.press(getByTestId('progress-continue-button'));
    });

    // Check that Toast notification alerts user and SQLite remains empty
    await waitFor(() => {
      expect(getByText('Máximo: 100 m2')).toBeTruthy();
      expect(global.dbTables.avances.length).toBe(0);
    });
  });
});
