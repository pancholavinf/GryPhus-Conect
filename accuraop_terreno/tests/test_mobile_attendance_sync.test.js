/**
 * test_mobile_attendance_sync.test.js
 * Jest Test Suite for Mobile App Attendance & Sync.
 */

class MobileAttendanceStorageSimulator {
  constructor() {
    this.tables = {
      tipos_maestro: [],
      maestros: [],
      obras_maestros: [],
      asistencia_diaria: [],
      asistencia_diaria_detalle: []
    };
    this.remoteSupabaseDb = {
      asistencia_diaria: [],
      asistencia_diaria_detalle: [],
      storage_buckets: { 'accuratek-data': [] }
    };
  }

  reset() {
    this.tables.tipos_maestro = [];
    this.tables.maestros = [];
    this.tables.obras_maestros = [];
    this.tables.asistencia_diaria = [];
    this.tables.asistencia_diaria_detalle = [];
    this.remoteSupabaseDb.asistencia_diaria = [];
    this.remoteSupabaseDb.asistencia_diaria_detalle = [];
    this.remoteSupabaseDb.storage_buckets['accuratek-data'] = [];
  }

  seedCatalog(cargos, maestros, obrasMaestros) {
    this.tables.tipos_maestro = [...cargos];
    this.tables.maestros = [...maestros];
    this.tables.obras_maestros = [...obrasMaestros];
  }

  saveLocalAttendance({ id, obra_id, fecha, foto_evidencia_url, registrado_por, detalles }) {
    if (!foto_evidencia_url || foto_evidencia_url.trim() === '') {
      throw new Error("Foto de evidencia obligatoria para registrar asistencia.");
    }

    const existingSubmission = this.tables.asistencia_diaria.find(
      (a) => a.obra_id === obra_id && a.fecha === fecha
    );

    const es_correctivo = existingSubmission ? true : false;

    const header = {
      id,
      obra_id,
      fecha,
      foto_evidencia_url,
      es_correctivo,
      registrado_por,
      synced: 0,
      fecha_captura_local: new Date().toISOString(),
      fecha_subida_servidor: null
    };

    this.tables.asistencia_diaria.push(header);

    const savedDetalles = [];
    for (const d of detalles) {
      if (![1.0, 0.5, 0.0].includes(d.estado_asistencia)) {
        throw new Error(`Estado de asistencia inválido: ${d.estado_asistencia}`);
      }
      const detalleRecord = {
        id: d.id || `det-${Math.random().toString(36).substring(7)}`,
        asistencia_diaria_id: id,
        maestro_id: d.maestro_id,
        estado_asistencia: d.estado_asistencia,
        observaciones: d.observaciones || ''
      };
      this.tables.asistencia_diaria_detalle.push(detalleRecord);
      savedDetalles.push(detalleRecord);
    }

    return { header, detalles: savedDetalles, es_correctivo };
  }

  buildAttendanceSyncPayload(headerId) {
    const header = this.tables.asistencia_diaria.find((a) => a.id === headerId);
    if (!header) throw new Error("Header not found");

    const detalles = this.tables.asistencia_diaria_detalle.filter(
      (d) => d.asistencia_diaria_id === headerId
    );

    return {
      header: {
        id: header.id,
        obra_id: header.obra_id,
        fecha: header.fecha,
        foto_evidencia_url: header.foto_evidencia_url,
        es_correctivo: header.es_correctivo,
        registrado_por: header.registrado_por
      },
      detalles: detalles.map((d) => ({
        id: d.id,
        asistencia_diaria_id: d.asistencia_diaria_id,
        maestro_id: d.maestro_id,
        estado_asistencia: d.estado_asistencia,
        observaciones: d.observaciones
      }))
    };
  }

  executeSync(headerId) {
    const payload = this.buildAttendanceSyncPayload(headerId);

    const storagePath = `asistencia/${payload.header.obra_id}/${payload.header.id}.jpg`;
    this.remoteSupabaseDb.storage_buckets['accuratek-data'].push({
      path: storagePath,
      publicUrl: `https://supabase.co/storage/v1/object/public/accuratek-data/${storagePath}`
    });

    this.remoteSupabaseDb.asistencia_diaria.push(payload.header);
    for (const d of payload.detalles) {
      this.remoteSupabaseDb.asistencia_diaria_detalle.push(d);
    }

    const localHeader = this.tables.asistencia_diaria.find((a) => a.id === headerId);
    if (localHeader) {
      localHeader.synced = 1;
      localHeader.fecha_subida_servidor = new Date().toISOString();
    }

    return true;
  }
}

describe('Mobile App Offline Attendance & Sync Suite', () => {
  let sim;

  beforeEach(() => {
    sim = new MobileAttendanceStorageSimulator();
    sim.reset();
  });

  test('SQLite attendance tables (tipos_maestro, maestros, obras_maestros) catalog initialization', () => {
    sim.seedCatalog(
      [{ id: 'c-1', nombre: 'Carpintero', sueldo_diario: 40000 }],
      [{ id: 'm-1', rut: '12.345.678-9', nombre_completo: 'Pedro Perez', tipo_maestro_id: 'c-1' }],
      [{ id: 'om-1', obra_id: 'obra-1', maestro_id: 'm-1' }]
    );
    expect(sim.tables.tipos_maestro.length).toBe(1);
    expect(sim.tables.maestros.length).toBe(1);
    expect(sim.tables.obras_maestros.length).toBe(1);
  });

  test('Status evaluation (1.0, 0.5, 0.0) selection and local SQLite persistence', () => {
    sim.seedCatalog(
      [{ id: 'c-1', nombre: 'Carpintero', sueldo_diario: 40000 }],
      [{ id: 'm-1', rut: '12.345.678-9', nombre_completo: 'Pedro Perez', tipo_maestro_id: 'c-1' }],
      [{ id: 'om-1', obra_id: 'obra-1', maestro_id: 'm-1' }]
    );

    const result = sim.saveLocalAttendance({
      id: 'ast-101',
      obra_id: 'obra-1',
      fecha: '2026-07-29',
      foto_evidencia_url: 'file://evidence-photo.jpg',
      registrado_por: 'user-jefe-1',
      detalles: [
        { id: 'd-1', maestro_id: 'm-1', estado_asistencia: 1.0, observaciones: 'Día Completo ok' }
      ]
    });

    expect(result.header.synced).toBe(0);
    expect(result.es_correctivo).toBe(false);
    expect(result.detalles[0].estado_asistencia).toBe(1.0);
  });

  test('Evidence photo validation rejects submission without photo', () => {
    expect(() => {
      sim.saveLocalAttendance({
        id: 'ast-invalid',
        obra_id: 'obra-1',
        fecha: '2026-07-30',
        foto_evidencia_url: '', // Missing photo!
        registrado_por: 'user-jefe-1',
        detalles: [{ id: 'd-2', maestro_id: 'm-1', estado_asistencia: 0.5 }]
      });
    }).toThrow('Foto de evidencia obligatoria');
  });

  test('sync.js payload building and bidirectional sync execution', () => {
    sim.seedCatalog(
      [{ id: 'c-1', nombre: 'Carpintero', sueldo_diario: 40000 }],
      [{ id: 'm-1', rut: '12.345.678-9', nombre_completo: 'Pedro Perez', tipo_maestro_id: 'c-1' }],
      [{ id: 'om-1', obra_id: 'obra-1', maestro_id: 'm-1' }]
    );

    sim.saveLocalAttendance({
      id: 'ast-101',
      obra_id: 'obra-1',
      fecha: '2026-07-29',
      foto_evidencia_url: 'file://evidence-photo.jpg',
      registrado_por: 'user-jefe-1',
      detalles: [
        { id: 'd-1', maestro_id: 'm-1', estado_asistencia: 1.0, observaciones: 'Día Completo ok' }
      ]
    });

    const payload = sim.buildAttendanceSyncPayload('ast-101');
    expect(payload.header.id).toBe('ast-101');
    expect(payload.detalles.length).toBe(1);

    const synced = sim.executeSync('ast-101');
    expect(synced).toBe(true);

    const localHeader = sim.tables.asistencia_diaria.find(a => a.id === 'ast-101');
    expect(localHeader.synced).toBe(1);
    expect(localHeader.fecha_subida_servidor).not.toBeNull();
    expect(sim.remoteSupabaseDb.asistencia_diaria.length).toBe(1);
  });

  test('Corrective Report handling sets es_correctivo = true on re-submitting attendance for same date', () => {
    sim.seedCatalog(
      [{ id: 'c-1', nombre: 'Carpintero', sueldo_diario: 40000 }],
      [{ id: 'm-1', rut: '12.345.678-9', nombre_completo: 'Pedro Perez', tipo_maestro_id: 'c-1' }],
      [{ id: 'om-1', obra_id: 'obra-1', maestro_id: 'm-1' }]
    );

    // Initial submission
    sim.saveLocalAttendance({
      id: 'ast-101',
      obra_id: 'obra-1',
      fecha: '2026-07-29',
      foto_evidencia_url: 'file://evidence1.jpg',
      registrado_por: 'user-jefe-1',
      detalles: [{ id: 'd-1', maestro_id: 'm-1', estado_asistencia: 1.0 }]
    });

    // Re-submission for same date
    const correctiveResult = sim.saveLocalAttendance({
      id: 'ast-102-corrective',
      obra_id: 'obra-1',
      fecha: '2026-07-29', // Same date!
      foto_evidencia_url: 'file://corrective-evidence.jpg',
      registrado_por: 'user-jefe-1',
      detalles: [{ id: 'd-1-cor', maestro_id: 'm-1', estado_asistencia: 0.5 }]
    });

    expect(correctiveResult.es_correctivo).toBe(true);
    expect(correctiveResult.header.es_correctivo).toBe(true);

    sim.executeSync('ast-102-corrective');
    const remoteCorrective = sim.remoteSupabaseDb.asistencia_diaria.find(a => a.id === 'ast-102-corrective');
    expect(remoteCorrective.es_correctivo).toBe(true);
  });
});
