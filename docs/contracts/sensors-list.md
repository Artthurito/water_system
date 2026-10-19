# GET /sensors — Lista as vias

Retorna todas as vias cadastradas, com os limites usados para classificar cada situação.

| | |
|---|---|
| Método | `GET` |
| Rota | `/sensors` |
| Autenticação | Nenhuma |
| Sucesso | `200 OK` |

## Funcionamento

Lista todas as vias ordenadas por `id` (ordem de cadastro). Não traz a situação atual; para isso use
[`GET /analysis/status`](analysis-status.md). A chave do sensor nunca é retornada.

## Request

Sem parâmetros, sem body.

```http
GET /sensors
```

## Response `200`

```json
[
  {
    "id": 1,
    "name": "Rua A",
    "install_height_cm": 20.0,
    "attention_cm": 2.0,
    "avoid_cm": 5.0,
    "blocked_cm": 8.0,
    "created_at": "2026-10-19T22:44:09.822902Z"
  },
  {
    "id": 2,
    "name": "Rua B",
    "install_height_cm": 20.0,
    "attention_cm": 2.0,
    "avoid_cm": 5.0,
    "blocked_cm": 8.0,
    "created_at": "2026-10-19T22:44:09.873564Z"
  }
]
```

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `integer` | ID da via |
| `name` | `string` | Nome da via |
| `install_height_cm` | `number` | Distância do sensor até o chão seco |
| `attention_cm` | `number` | Nível de água a partir do qual a via fica `atencao` |
| `avoid_cm` | `number` | Nível a partir do qual a via fica `evitar` |
| `blocked_cm` | `number` | Nível a partir do qual a via fica `bloqueada` |
| `created_at` | `string` (datetime UTC) | Data do cadastro |

Sem vias cadastradas, retorna `[]`.

## Erros

| Status | `detail` | Quando |
|---|---|---|
| `503` | `"Banco de dados indisponível"` | Falha ao acessar o Supabase |

## Exemplo

```js
const sensors = await api("/sensors");

const sensorsById = Object.fromEntries(sensors.map((sensor) => [sensor.id, sensor]));
```
