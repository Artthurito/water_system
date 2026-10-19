# GET /sensors/{sensor_id} — Detalha uma via

Retorna os dados e os limites de uma via.

| | |
|---|---|
| Método | `GET` |
| Rota | `/sensors/{sensor_id}` |
| Autenticação | Nenhuma |
| Sucesso | `200 OK` |

## Funcionamento

Busca a via pelo `id`. Útil para uma tela de detalhe ou para desenhar as faixas de situação no
gráfico do [histórico](readings-list.md). A chave do sensor nunca é retornada.

## Request

```http
GET /sensors/1
```

### Path params

| Parâmetro | Tipo | Obrigatório | Regras |
|---|---|---|---|
| `sensor_id` | `integer` | Sim | ID de uma via cadastrada |

## Response `200`

```json
{
  "id": 1,
  "name": "Rua A",
  "install_height_cm": 20.0,
  "attention_cm": 2.0,
  "avoid_cm": 5.0,
  "blocked_cm": 8.0,
  "created_at": "2026-10-19T22:44:09.822902Z"
}
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

## Erros

| Status | `detail` | Quando |
|---|---|---|
| `404` | `"Sensor não encontrado"` | Não existe via com esse `id` |
| `422` | lista | `sensor_id` não é inteiro |
| `503` | `"Banco de dados indisponível"` | Falha ao acessar o Supabase |

Exemplo de `422` (`GET /sensors/abc`):

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "sensor_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer"
    }
  ]
}
```

## Exemplo

```js
async function loadSensor(sensorId) {
  try {
    return await api(`/sensors/${sensorId}`);
  } catch (error) {
    if (error.status === 404) {
      return null;
    }
    throw error;
  }
}
```
