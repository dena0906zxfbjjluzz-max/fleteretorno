-- Esquema inicial app-fletes (Supabase → SQL Editor → Run)
-- InDrive camiones mayoristas

create table if not exists public.transportistas (
  id uuid default gen_random_uuid() primary key,
  dni text unique not null,
  nombre_completo text not null,
  celular text,
  licencia_conducir text unique not null,
  placa_camion text not null,
  estado_verificacion text default 'PENDIENTE',
  created_at timestamptz default now()
);

create table if not exists public.ofertas_fletes (
  id uuid default gen_random_uuid() primary key,
  origen text not null,
  destino text not null,
  descripcion_carga text not null,
  precio_ofrecido numeric not null,
  transportista_id uuid references public.transportistas(id),
  estado_viaje text default 'DISPONIBLE',
  created_at timestamptz default now()
);

create table if not exists public.lista_negra_seguridad (
  id uuid default gen_random_uuid() primary key,
  dni_bloqueado text unique,
  placa_bloqueada text unique,
  motivo text not null,
  fecha_bloqueo timestamptz default now()
);

alter table public.transportistas disable row level security;
alter table public.ofertas_fletes disable row level security;
alter table public.lista_negra_seguridad disable row level security;
