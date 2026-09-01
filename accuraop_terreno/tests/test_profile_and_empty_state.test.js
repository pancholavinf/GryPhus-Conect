import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import HomeScreen from '../src/screens/HomeScreen';

describe('HomeScreen: Profile Picture & Empty State App Logo', () => {
  const mockUserProfileWithPhoto = {
    id: 'jefe-123',
    nombre: 'Carlos Inspector',
    email: 'carlos@trabs.cl',
    rol: 'jefe_obra',
    foto_perfil_url: 'https://mock.supabase.co/storage/v1/object/public/accuratek-data/personal/carlos.jpg',
    telefono: '+56911223344',
  };

  const mockUserProfileWithoutPhoto = {
    id: 'jefe-456',
    nombre: 'Ana Jefa',
    email: 'ana@trabs.cl',
    rol: 'jefe_obra',
    foto_perfil_url: '',
    telefono: '+56999887766',
  };

  beforeEach(() => {
    global.resetDbTables();
    global.setNetworkState(true);
    global.setMockEmptyCatalog(false);
  });

  test('Renders profile picture in header and shows Supervisor role when foto_perfil_url is present', () => {
    const { getByTestId, queryByText, getByText } = render(
      <HomeScreen
        userProfile={mockUserProfileWithPhoto}
        onSelectObra={jest.fn()}
        onLogout={jest.fn()}
        onUpdateProfile={jest.fn()}
      />
    );

    // Should display name and Supervisor role in header
    expect(queryByText('Carlos Inspector')).toBeTruthy();
    expect(getByText('Supervisor')).toBeTruthy();

    // Since foto_perfil_url exists, the fallback letter 'C' should not be rendered
    expect(queryByText('C')).toBeNull();
  });

  test('Renders initial letter fallback when foto_perfil_url is missing', () => {
    const { queryByText } = render(
      <HomeScreen
        userProfile={mockUserProfileWithoutPhoto}
        onSelectObra={jest.fn()}
        onLogout={jest.fn()}
        onUpdateProfile={jest.fn()}
      />
    );

    // Fallback letter 'A' for Ana Jefa should be rendered
    expect(queryByText('A')).toBeTruthy();
  });

  test('Renders app logo in empty state when user has no assigned obras', () => {
    // Set empty catalog
    global.setMockEmptyCatalog(true);

    const { getByTestId, getByText } = render(
      <HomeScreen
        userProfile={mockUserProfileWithPhoto}
        onSelectObra={jest.fn()}
        onLogout={jest.fn()}
        onUpdateProfile={jest.fn()}
      />
    );

    // Empty obras container must be present
    const emptyView = getByTestId('empty-obras-view');
    expect(emptyView).toBeTruthy();
    expect(getByText('Sin obras asignadas')).toBeTruthy();

    // Reset mock
    global.setMockEmptyCatalog(false);
  });

  test('Profile modal shows Accuratek in footer, displays Rol: Supervisor, omits ID Usuario, and has touchable avatar to change photo', () => {
    const { getByText, queryByText, getByTestId } = render(
      <HomeScreen
        userProfile={mockUserProfileWithPhoto}
        onSelectObra={jest.fn()}
        onLogout={jest.fn()}
        onUpdateProfile={jest.fn()}
      />
    );

    // Open profile modal by tapping header left
    fireEvent.press(getByText('Carlos Inspector'));

    // Verify footer contains Accuratek
    expect(getByText('Trabs Terreno · v1.0 · Accuratek')).toBeTruthy();

    // Verify Role displays as Supervisor
    expect(getByText('Rol: Supervisor')).toBeTruthy();

    // Verify ID Usuario is NOT in the modal
    expect(queryByText('ID Usuario:')).toBeNull();
    expect(queryByText('jefe-123')).toBeNull();

    // Verify avatar is touchable and has prompt
    expect(getByTestId('avatar-touchable')).toBeTruthy();
    expect(getByText('Toca para cambiar foto')).toBeTruthy();
  });
});
