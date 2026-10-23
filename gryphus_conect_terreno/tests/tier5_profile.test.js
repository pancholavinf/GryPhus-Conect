import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import App from '../App';

// Helper: login and reach home screen
async function loginAndGoHome(getByTestId, findByTestId) {
  fireEvent.changeText(getByTestId('email-input'), 'test@test.cl');
  fireEvent.changeText(getByTestId('password-input'), '123456');
  await act(async () => {
    fireEvent.press(getByTestId('login-button'));
  });
  return findByTestId('home-screen');
}

describe('Tier 5: Bottom Navigation & User Profile', () => {
  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
  });

  // ──────────────────────────────────────────────
  // T5-1: Bottom navigation bar renders
  // ──────────────────────────────────────────────
  test('Bottom navigation bar is visible after login', async () => {
    const { getByTestId, findByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    expect(getByTestId('bottom-navigation')).toBeTruthy();
    expect(getByTestId('tab-obras')).toBeTruthy();
    expect(getByTestId('tab-perfil')).toBeTruthy();
  });

  // ──────────────────────────────────────────────
  // T5-2: Obras tab is active by default
  // ──────────────────────────────────────────────
  test('Obras tab shows the obra list by default', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    // Default content should be obra list (obra-card or empty-obras-view)
    const hasObraCard = queryByTestId('obra-card-obra-789');
    const hasEmptyView = queryByTestId('empty-obras-view');
    expect(hasObraCard || hasEmptyView).toBeTruthy();

    // Profile view should NOT be visible
    expect(queryByTestId('profile-view')).toBeNull();
  });

  // ──────────────────────────────────────────────
  // T5-3: Switching to Perfil tab shows profile details
  // ──────────────────────────────────────────────
  test('Switching to Perfil tab shows the profile view in read-only mode by default', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    // Tap on Profile tab
    fireEvent.press(getByTestId('tab-perfil'));

    // Profile view should be visible
    const profileView = await findByTestId('profile-view');
    expect(profileView).toBeTruthy();

    // Obra list should no longer be visible
    expect(queryByTestId('obra-card-obra-789')).toBeNull();
    expect(queryByTestId('empty-obras-view')).toBeNull();

    // Displays name and phone labels/values instead of editable inputs by default
    expect(getByTestId('profile-name-display')).toBeTruthy();
    expect(getByTestId('profile-phone-display')).toBeTruthy();
    expect(getByTestId('edit-profile-button')).toBeTruthy();

    // Inputs should not be visible yet
    expect(queryByTestId('profile-name-input')).toBeNull();
  });

  // ──────────────────────────────────────────────
  // T5-4: Clicking edit shows the form inputs
  // ──────────────────────────────────────────────
  test('Clicking edit profile button switches to edit mode with inputs', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    fireEvent.press(getByTestId('tab-perfil'));
    await findByTestId('profile-view');

    // Press edit button
    fireEvent.press(getByTestId('edit-profile-button'));

    // Form inputs and camera/gallery buttons should now be visible
    expect(getByTestId('profile-name-input')).toBeTruthy();
    expect(getByTestId('profile-phone-input')).toBeTruthy();
    expect(getByTestId('avatar-camera-button')).toBeTruthy();
    expect(getByTestId('avatar-gallery-button')).toBeTruthy();
    expect(getByTestId('save-profile-button')).toBeTruthy();
    expect(getByTestId('cancel-profile-button')).toBeTruthy();

    // Muted/Display fields should be gone
    expect(queryByTestId('profile-name-display')).toBeNull();
  });

  // ──────────────────────────────────────────────
  // T5-5: Profile form edits, uploads photo and saves successfully
  // ──────────────────────────────────────────────
  test('User can edit name and phone, upload profile photo and save successfully returning to read mode', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    fireEvent.press(getByTestId('tab-perfil'));
    await findByTestId('profile-view');

    // Go to edit mode
    fireEvent.press(getByTestId('edit-profile-button'));

    // Edit name field
    fireEvent.changeText(getByTestId('profile-name-input'), 'Pedro Sánchez');
    // Edit phone field
    fireEvent.changeText(getByTestId('profile-phone-input'), '+56912345678');

    // Interact with Gallery selection (simulated via mock)
    await act(async () => {
      fireEvent.press(getByTestId('avatar-gallery-button'));
    });

    // Save profile
    await act(async () => {
      fireEvent.press(getByTestId('save-profile-button'));
    });

    // Verify the mock Supabase updated the record in dbTables
    await waitFor(() => {
      const updatedProfile = global.dbTables.perfiles_usuario.find(p => p.id === 'jefe-123');
      expect(updatedProfile).toBeDefined();
      expect(updatedProfile.nombre).toBe('Pedro Sánchez');
      expect(updatedProfile.telefono).toBe('+56912345678');
      expect(updatedProfile.foto_perfil_url).toContain('https://mock.supabase.co/storage/v1/object/public/');
    });

    // Should return to read mode and show updated values
    expect(getByTestId('profile-name-display')).toBeTruthy();
    expect(getByTestId('profile-name-display').props.children).toBe('Pedro Sánchez');
    expect(queryByTestId('profile-name-input')).toBeNull();
  });

  // ──────────────────────────────────────────────
  // T5-6: Profile form prevents save with empty name
  // ──────────────────────────────────────────────
  test('Saving with empty name does not call Supabase update', async () => {
    const { getByTestId, findByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    fireEvent.press(getByTestId('tab-perfil'));
    await findByTestId('profile-view');

    // Go to edit mode
    fireEvent.press(getByTestId('edit-profile-button'));

    // Clear the name field
    fireEvent.changeText(getByTestId('profile-name-input'), '');

    const dbSnapshot = [...global.dbTables.perfiles_usuario];

    await act(async () => {
      fireEvent.press(getByTestId('save-profile-button'));
    });

    // DB should remain unchanged
    await waitFor(() => {
      expect(global.dbTables.perfiles_usuario).toEqual(dbSnapshot);
    });
  });

  // ──────────────────────────────────────────────
  // T5-7: Switching back to Obras tab from Perfil
  // ──────────────────────────────────────────────
  test('Can switch back from Perfil to Obras tab', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    // Go to profile
    fireEvent.press(getByTestId('tab-perfil'));
    await findByTestId('profile-view');

    // Go back to obras
    fireEvent.press(getByTestId('tab-obras'));

    // Obra list or empty view should be visible again
    await waitFor(() => {
      const hasObraCard = queryByTestId('obra-card-obra-789');
      const hasEmptyView = queryByTestId('empty-obras-view');
      expect(hasObraCard || hasEmptyView).toBeTruthy();
    });

    // Profile view should be gone
    expect(queryByTestId('profile-view')).toBeNull();
  });

  // ──────────────────────────────────────────────
  // T5-8: Hamburger menu still works on Perfil tab
  // ──────────────────────────────────────────────
  test('Hamburger menu is accessible from Perfil tab', async () => {
    const { getByTestId, findByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    fireEvent.press(getByTestId('tab-perfil'));
    await findByTestId('profile-view');

    // Open hamburger menu
    fireEvent.press(getByTestId('menu-button'));
    const dropdownMenu = await findByTestId('dropdown-menu');
    expect(dropdownMenu).toBeTruthy();

    // Close via overlay
    fireEvent.press(getByTestId('menu-overlay'));
    await waitFor(() => {
      expect(getByTestId('profile-view')).toBeTruthy();
    });
  });

  // ──────────────────────────────────────────────
  // T5-9: Cancel editing profile discards changes
  // ──────────────────────────────────────────────
  test('Clicking cancel button discards changes and returns to read-only mode', async () => {
    const { getByTestId, findByTestId, queryByTestId } = render(<App />);
    await loginAndGoHome(getByTestId, findByTestId);

    fireEvent.press(getByTestId('tab-perfil'));
    await findByTestId('profile-view');

    // Default name
    const initialName = getByTestId('profile-name-display').props.children;

    // Go to edit mode
    fireEvent.press(getByTestId('edit-profile-button'));

    // Edit fields
    fireEvent.changeText(getByTestId('profile-name-input'), 'Pedro Sánchez');
    fireEvent.changeText(getByTestId('profile-phone-input'), '+56912345678');

    // Cancel edit
    fireEvent.press(getByTestId('cancel-profile-button'));

    // Verification
    expect(getByTestId('profile-name-display')).toBeTruthy();
    expect(getByTestId('profile-name-display').props.children).toBe(initialName);
    expect(queryByTestId('profile-name-input')).toBeNull();
  });
});
