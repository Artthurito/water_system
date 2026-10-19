# Contratos da API — Water System

Contratos dos endpoints do backend (`sys_backend`) para o frontend em HTML, CSS e JavaScript.
Cada arquivo descreve um endpoint: funcionamento, request, response e erros.

## Índice

| Método | Rota | Uso no frontend | Autenticação | Contrato |
|---|---|---|---|---|
| `GET` | `/analysis/status` | Painel principal: situação atual de cada via | Nenhuma | [analysis-status.md](analysis-status.md) |
| `GET` | `/readings` | Gráficos e histórico de nível da água | Nenhuma | [readings-list.md](readings-list.md) |
| `GET` | `/sensors` | Lista de vias e seus limites | Nenhuma | [sensors-list.md](sensors-list.md) |
| `GET` | `/sensors/{sensor_id}` | Detalhe de uma via | Nenhuma | [sensors-get.md](sensors-get.md) |
| `POST` | `/sensors` | Tela de administração: cadastrar via | `X-Admin-Key` | [sensors-create.md](sensors-create.md) |
| `POST` | `/readings` | Não é chamado pelo frontend (uso do ESP32) | `X-API-Key` | [readings-create.md](readings-create.md) |

## Convenções gerais

### URL base

```
http://localhost:8000
```

Deixe a URL base em uma única constante no JavaScript. A documentação interativa (Swagger) fica em
`{URL_BASE}/docs` e o schema OpenAPI em `{URL_BASE}/openapi.json`.

### Formato

- Request e response em JSON (`Content-Type: application/json`).
- Medidas em **centímetros** (`number`, aceita decimais).
- Datas em ISO 8601, sempre em **UTC** com sufixo `Z` (ex.: `2026-10-19T22:44:09.822902Z`).
  `new Date(valor)` converte direto para o fuso do navegador.
- IDs são inteiros.

### Autenticação

| Header | Onde é usado | Origem do valor |
|---|---|---|
| `X-Admin-Key` | `POST /sensors` | Variável `ADMIN_API_KEY` do `.env` do backend |
| `X-API-Key` | `POST /readings` | Chave `ws_...` gerada no cadastro do sensor |

Os endpoints de consulta (`GET`) são públicos.

Não grave a `X-Admin-Key` no código do frontend: qualquer pessoa consegue ler o JavaScript no
navegador. Na tela de administração, peça a chave ao usuário em um campo de senha e mantenha-a no
máximo em `sessionStorage`.

### Situação da via (`status`)

| Valor | Significado | Regra |
|---|---|---|
| `livre` | Via transitável | nível < `attention_cm` |
| `atencao` | Água começando a acumular | `attention_cm` ≤ nível < `avoid_cm` |
| `evitar` | Evitar passar pela via | `avoid_cm` ≤ nível < `blocked_cm` |
| `bloqueada` | Via intransitável | nível ≥ `blocked_cm` |
| `sem_sinal` | Sensor sem leitura recente | Nenhuma leitura nos últimos 120 s (`STALE_AFTER_SECONDS`) ou nenhuma leitura registrada |

`sem_sinal` só aparece em [`GET /analysis/status`](analysis-status.md). Leituras salvas
(`/readings`) usam apenas os quatro primeiros valores.

### Formato de erro

Todo erro retorna um objeto com a chave `detail`, que pode ter **dois formatos**:

**1. Texto** — erros de regra de negócio (401, 404, 422 de leitura, 503):

```json
{ "detail": "Sensor não encontrado" }
```

**2. Lista** — erros de validação de entrada (422):

```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "attention_cm"],
      "msg": "Input should be greater than 0",
      "ctx": { "gt": 0.0 }
    }
  ]
}
```

| Campo | Descrição |
|---|---|
| `type` | Código do erro (`missing`, `greater_than`, `value_error`, `float_parsing`...) |
| `loc` | Onde está o erro: `["body", "campo"]`, `["query", "parametro"]` ou `["path", "parametro"]`. `["body"]` sozinho indica regra entre campos |
| `msg` | Mensagem em inglês (exceto regras próprias, em português, com prefixo `Value error, `) |
| `ctx` | Opcional. Dados extras da regra (ex.: `{ "gt": 0.0 }`) |

Use `loc[1]` para destacar o campo correspondente no formulário.

### Erros comuns a todos os endpoints

| Status | `detail` | Quando acontece |
|---|---|---|
| `503` | `"Banco de dados indisponível"` | Falha ao acessar o Supabase. Mostre uma mensagem de indisponibilidade e tente de novo depois |
| — | `fetch` lança `TypeError` | Backend fora do ar, URL errada ou bloqueio de CORS. Não há resposta HTTP |

### CORS

O backend ainda **não** habilita CORS. Se o frontend for aberto em outra origem (ex.: Live Server em
`http://127.0.0.1:5500` ou o arquivo direto via `file://`), o navegador bloqueia as chamadas e o
`fetch` lança `TypeError: Failed to fetch`. É preciso adicionar o `CORSMiddleware` no backend
liberando a origem do frontend.

### Cliente de referência

```js
const API_URL = "http://localhost:8000";

class ApiError extends Error {
  constructor(status, detail) {
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg.replace(/^Value error, /, "")).join("; ")
      : detail ?? "Erro inesperado";
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function api(path, { method = "GET", body, headers = {} } = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json", ...headers } : headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, data?.detail);
  }

  return data;
}
```

Os exemplos de cada contrato usam essa função `api()`.
