import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY; // service_role

const supabase = createClient(supabaseUrl, serviceRoleKey);

async function main() {
  const email = 'test@test.cl';
  const password = '123456';

  // 1) Crear usuario en Auth
  const { data, error } = await supabase.auth.admin.createUser({
    email,
    password,
    // OJO: si quieres que pueda loguear sin confirmar email:
    email_confirm: true,
    // Puedes guardar metadatos si tu app los usa:
    user_metadata: {
      nombre: 'Francisco Lavin',
    },
    app_metadata: {
      role: 'jefe_obra',
    },
  });

  if (error) {
    console.error('Error creando usuario:', error);
    process.exit(1);
  }

  console.log('Usuario creado:', data.user.id);
}

main();