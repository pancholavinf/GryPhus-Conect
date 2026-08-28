import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import App from '../App';

describe('Multi-Item Advance Publication with Single Photo', () => {
  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
  });

  test('User can add multiple items/quantities to a batch, take 1 photo, enter comment, and sync to DB', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);

    // 1. Login
    fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
    fireEvent.changeText(getByTestId('password-input'), '123456');
    await act(async () => {
      fireEvent.press(getByTestId('login-button'));
    });

    // 2. Wait for home screen
    const homeScreen = await findByTestId('home-screen');
    expect(homeScreen).toBeTruthy();

    // 3. Select Obra
    fireEvent.press(getByTestId('obra-card-obra-789'));
    await findByTestId('obra-menu-screen');

    // 4. Open Selection Flow
    fireEvent.press(getByTestId('btn-avance'));
    await findByTestId('selection-flow-screen');

    // 5. Input Quantity for Item 1
    fireEvent.changeText(getByTestId('progress-input'), '25');

    // 6. Press "+ Agregar otro ítem al lote"
    fireEvent.press(getByTestId('add-another-item-button'));

    // 7. Verify Batch Banner is now visible
    await waitFor(() => {
      expect(getByTestId('batch-banner')).toBeTruthy();
    });

    // 8. Add more quantity to the batch (simulating second item selection or addition)
    fireEvent.changeText(getByTestId('progress-input'), '15');

    // 9. Press "Continuar con Lote ? Foto"
    fireEvent.press(getByTestId('progress-continue-button'));

    // 10. Capture Single Photo for the batch
    await act(async () => {
      fireEvent.press(getByTestId('capture-photo-button'));
    });

    // 11. Enter Comment for the entire batch
    const commentInput = await findByTestId('comment-input');
    fireEvent.changeText(commentInput, 'Lote de estructuras protegidas hoy');
    fireEvent.press(getByTestId('comment-continue-button'));

    // 12. Verify Confirm step shows item in batch and photo
    await waitFor(() => {
      expect(getByTestId('confirm-photo')).toBeTruthy();
    });

    // 13. Submit the multi-item advance batch
    await act(async () => {
      fireEvent.press(getByTestId('submit-advance-button'));
    });

    // 14. Verify SQLite record is saved with the total quantity and photo
    await waitFor(() => {
      expect(global.dbTables.avances.length).toBeGreaterThanOrEqual(1);
      const saved = global.dbTables.avances[0];
      expect(saved.synced).toBe(1);
      expect(saved.cantidad).toBe(40); // 25 + 15 summed
      expect(saved.comentario).toBe('Lote de estructuras protegidas hoy');
      expect(saved.foto_url).toBeTruthy();
    });

    // 15. Verify redirection back to ObraMenuScreen
    await waitFor(() => {
      expect(queryByTestId('obra-menu-screen')).toBeTruthy();
    });
  });
});
