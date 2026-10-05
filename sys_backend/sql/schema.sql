create table if not exists sensors (
  id                bigint generated always as identity primary key,
  name              text        not null,
  install_height_cm double precision not null check (install_height_cm > 0),
  attention_cm      double precision not null,
  avoid_cm          double precision not null,
  blocked_cm        double precision not null,
  api_key_hash      text        not null unique,
  created_at        timestamptz not null default now(),
  check (0 < attention_cm and attention_cm < avoid_cm and avoid_cm < blocked_cm and blocked_cm < install_height_cm)
);

create table if not exists readings (
  id             bigint generated always as identity primary key,
  sensor_id      bigint      not null references sensors(id) on delete cascade,
  distance_cm    double precision not null,
  water_level_cm double precision not null,
  status         text        not null check (status in ('livre', 'atencao', 'evitar', 'bloqueada')),
  created_at     timestamptz not null default now()
);

create index if not exists readings_sensor_created_idx on readings (sensor_id, created_at desc);

alter table sensors enable row level security;
alter table readings enable row level security;
