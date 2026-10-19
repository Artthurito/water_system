# POST /readings — Recebe uma leitura do sensor

Endpoint chamado pelo **ESP32** (ou pelo `scripts/simulate_sensor.py`) para enviar uma medição.
O frontend **não** deve chamá-lo; ele está documentado aqui para explicar a origem dos dados
exibidos.

| | |
|---|---|
| Método | `POST` |
| Rota | `/readings` |
| Autenticação | Header `X-API-Key` (chave `ws_...` do sensor) |
| Sucesso | `201 Created` |

## Funcionamento

1. Identifica a via pela `X-API-Key` (o backend compara o hash da chave).
2. Valida a distância: `0 < distance_cm ≤ install_height_cm + 5` (tolerância
   `DISTANCE_TOLERANCE_CM`). Ex.: altura 20 cm → aceita até 25 cm.
3. Calcula o nível da água de cada medição: `max(0, install_height_cm − distance_cm)`.
4. Suaviza com **média móvel** da leitura atual + as 4 anteriores da via (`SMOOTHING_WINDOW = 5`).
5. Classifica o nível suavizado (`livre`, `atencao`, `evitar`, `bloqueada`) usando os limites da via.
6. Salva a leitura e retorna o registro criado.

`distance_cm` é salvo como foi recebido; `water_level_cm` e `status` são os valores suavizados.

## Request

```http
POST /readings
Content-Type: application/json
X-API-Key: ws_UqbNRRP8MDHUSZ16l9ZTJ9ceY6n2qtF6
```

```json
{ "distance_cm": 14.2 }
```

### Headers

| Header | Obrigatório | Descrição |
|---|---|---|
| `Content-Type` | Sim | `application/json` |
| `X-API-Key` | Sim | Chave retornada em [`POST /sensors`](sensors-create.md) |

### Body

| Campo | Tipo | Obrigatório | Regras |
|---|---|---|---|
| `distance_cm` | `number` | Sim | Distância do sensor até a superfície. `0 < distance_cm ≤ install_height_cm + 5` |

## Response `201`

```json
{
  "id": 1,
  "sensor_id": 1,
  "distance_cm": 14.2,
  "water_level_cm": 5.8,
  "status": "evitar",
  "created_at": "2026-10-19T22:44:09.908153Z"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `integer` | ID da leitura |
| `sensor_id` | `integer` | Via identificada pela chave |
| `distance_cm` | `number` | Distância recebida |
| `water_level_cm` | `number` | Nível da água suavizado, arredondado em 2 casas |
| `status` | `string` | `livre`, `atencao`, `evitar` ou `bloqueada` |
| `created_at` | `string` (datetime UTC) | Momento do registro |

## Erros

| Status | `detail` | Quando |
|---|---|---|
| `401` | `"X-API-Key ausente ou inválida"` | Header ausente ou chave não pertence a nenhuma via |
| `422` | texto: `"distance_cm deve ser maior que 0 e no máximo {limite} cm"` | Distância ≤ 0 ou acima da altura + tolerância |
| `422` | lista | `distance_cm` ausente, não numérico ou body inválido |
| `503` | `"Banco de dados indisponível"` | Falha ao acessar o Supabase |

Este é o único endpoint em que o `422` pode vir nos **dois formatos**:

```json
{ "detail": "distance_cm deve ser maior que 0 e no máximo 25.0 cm" }
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "distance_cm"],
      "msg": "Field required"
    }
  ]
}
```
