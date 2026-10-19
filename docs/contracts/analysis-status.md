# GET /analysis/status — Situação atual das vias

Retorna a situação atual de cada via cadastrada e qual via é recomendada. É o endpoint principal do
painel.

| | |
|---|---|
| Método | `GET` |
| Rota | `/analysis/status` |
| Autenticação | Nenhuma |
| Sucesso | `200 OK` |

## Funcionamento

1. Busca todas as vias cadastradas e a **última leitura** de cada uma.
2. Se a via não tem leitura, ou a última leitura tem mais de **120 s** (`STALE_AFTER_SECONDS`), a via
   fica com `status: "sem_sinal"` e `water_level_cm: null`.
3. Nas demais, `status` e `water_level_cm` vêm da última leitura (nível já suavizado pela média móvel).
4. Ordena a lista `sensors`:
   - primeiro as vias **com sinal**, do **menor para o maior** nível de água;
   - depois as vias `sem_sinal`, por ordem de `sensor_id`.
5. `recommended_sensor_id` é a primeira via com sinal que **não** está `bloqueada`. Se todas estiverem
   bloqueadas ou sem sinal, vale `null`.

O resultado muda a cada nova leitura. Para manter o painel atualizado, faça polling (ex.: a cada
5–10 s).

## Request

Sem parâmetros, sem body.

```http
GET /analysis/status
```

## Response `200`

```json
{
  "generated_at": "2026-10-19T22:44:09.963685Z",
  "recommended_sensor_id": 1,
  "sensors": [
    {
      "sensor_id": 1,
      "name": "Rua A",
      "water_level_cm": 5.8,
      "status": "evitar",
      "last_reading_at": "2026-10-19T22:44:09.908153Z"
    },
    {
      "sensor_id": 2,
      "name": "Rua B",
      "water_level_cm": null,
      "status": "sem_sinal",
      "last_reading_at": "2026-10-19T22:34:09.948661Z"
    },
    {
      "sensor_id": 3,
      "name": "Rua C",
      "water_level_cm": null,
      "status": "sem_sinal",
      "last_reading_at": null
    }
  ]
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `generated_at` | `string` (datetime UTC) | Momento em que a análise foi gerada |
| `recommended_sensor_id` | `integer \| null` | Via recomendada. `null` se nenhuma via com sinal estiver transitável |
| `sensors` | `array` | Uma entrada por via cadastrada, na ordem descrita acima. Vazio se não houver vias |
| `sensors[].sensor_id` | `integer` | ID da via |
| `sensors[].name` | `string` | Nome da via |
| `sensors[].water_level_cm` | `number \| null` | Nível da água em cm. `null` quando `sem_sinal` |
| `sensors[].status` | `string` | `livre`, `atencao`, `evitar`, `bloqueada` ou `sem_sinal` |
| `sensors[].last_reading_at` | `string \| null` | Data da última leitura. `null` se a via nunca enviou leitura |

Casos de `sem_sinal`:

| `last_reading_at` | Significado |
|---|---|
| `null` | Sensor cadastrado mas nunca enviou leitura |
| data | Sensor parou de enviar; mostre "última leitura há X min" |

## Erros

| Status | `detail` | Quando |
|---|---|---|
| `503` | `"Banco de dados indisponível"` | Falha ao acessar o Supabase |

## Exemplo

```js
async function loadStatus() {
  const overview = await api("/analysis/status");

  const recommended = overview.sensors.find((item) => item.sensor_id === overview.recommended_sensor_id);

  return { overview, recommended };
}

setInterval(loadStatus, 10000);
```
