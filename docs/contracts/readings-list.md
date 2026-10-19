# GET /readings — Histórico de leituras

Retorna as leituras registradas a partir de uma data, em ordem cronológica. Serve para montar
gráficos de nível da água ao longo do tempo.

| | |
|---|---|
| Método | `GET` |
| Rota | `/readings` |
| Autenticação | Nenhuma |
| Sucesso | `200 OK` |

## Funcionamento

1. Se `sensor_id` for informado, confere se a via existe (senão, `404`).
2. Busca leituras com `created_at` ≥ `since`. Sem `since`, usa a **última hora**.
3. Se houver mais leituras que `limit`, mantém as **mais recentes**.
4. Retorna em ordem **crescente** de data (mais antiga primeiro), pronta para plotar.

Sem `sensor_id`, as leituras de todas as vias vêm misturadas na mesma lista; agrupe por `sensor_id`
no frontend.

## Request

```http
GET /readings?sensor_id=1&since=2026-10-19T21:00:00Z&limit=500
```

### Query params

| Parâmetro | Tipo | Obrigatório | Padrão | Regras |
|---|---|---|---|---|
| `sensor_id` | `integer` | Não | — | Filtra por via. Precisa existir |
| `since` | `string` (ISO 8601) | Não | Agora − 1 hora | Data inicial. Sem fuso, é tratada como UTC. Com fuso (`Z` ou `-03:00`), é convertida |
| `limit` | `integer` | Não | `500` | Entre `1` e `1000` |

Gere `since` com `toISOString()` para evitar problemas de fuso:

```js
const since = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();
```

## Response `200`

```json
[
  {
    "id": 1,
    "sensor_id": 1,
    "distance_cm": 14.2,
    "water_level_cm": 5.8,
    "status": "evitar",
    "created_at": "2026-10-19T22:44:09.908153Z"
  }
]
```

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `integer` | ID da leitura |
| `sensor_id` | `integer` | Via que enviou a leitura |
| `distance_cm` | `number` | Distância bruta medida pelo sensor até a superfície |
| `water_level_cm` | `number` | Nível da água calculado e suavizado (média móvel). Use este valor no gráfico |
| `status` | `string` | `livre`, `atencao`, `evitar` ou `bloqueada` no momento da leitura |
| `created_at` | `string` (datetime UTC) | Momento em que a leitura foi registrada |

Sem leituras no período, retorna `[]`.

Para desenhar as faixas de `atencao`, `evitar` e `bloqueada` no gráfico, use os limites da via em
[`GET /sensors/{sensor_id}`](sensors-get.md).

## Erros

| Status | `detail` | Quando |
|---|---|---|
| `404` | `"Sensor não encontrado"` | `sensor_id` informado não existe |
| `422` | lista | `sensor_id` não é inteiro, `since` não é uma data válida ou `limit` fora de 1–1000 |
| `503` | `"Banco de dados indisponível"` | Falha ao acessar o Supabase |

Exemplos de `422`:

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "limit"],
      "msg": "Input should be greater than or equal to 1",
      "ctx": { "ge": 1 }
    }
  ]
}
```

```json
{
  "detail": [
    {
      "type": "datetime_from_date_parsing",
      "loc": ["query", "since"],
      "msg": "Input should be a valid datetime or date, input is too short",
      "ctx": { "error": "input is too short" }
    }
  ]
}
```

## Exemplo

```js
async function loadHistory(sensorId, hours = 1) {
  const params = new URLSearchParams({
    sensor_id: sensorId,
    since: new Date(Date.now() - hours * 60 * 60 * 1000).toISOString(),
    limit: 1000,
  });

  const readings = await api(`/readings?${params}`);

  return readings.map((reading) => ({ x: new Date(reading.created_at), y: reading.water_level_cm }));
}
```
