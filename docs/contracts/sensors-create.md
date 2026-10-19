# POST /sensors — Cadastra uma via

Cria o sensor de uma via e gera a chave que será gravada no ESP32. Uso exclusivo da tela de
administração.

| | |
|---|---|
| Método | `POST` |
| Rota | `/sensors` |
| Autenticação | Header `X-Admin-Key` |
| Sucesso | `201 Created` |

## Funcionamento

1. Valida a `X-Admin-Key` contra a `ADMIN_API_KEY` do backend.
2. Valida os campos e a ordem dos limites.
3. Gera uma chave aleatória com prefixo `ws_` e salva apenas o hash dela no banco.
4. Retorna a via criada com a chave em texto puro em `api_key`.

A `api_key` aparece **somente nesta resposta**. Não há como consultá-la depois. Mostre-a ao usuário
com destaque e um botão de copiar, avisando que deve ser gravada no ESP32. Se for perdida, é preciso
cadastrar a via de novo.

## Request

```http
POST /sensors
Content-Type: application/json
X-Admin-Key: <ADMIN_API_KEY>
```

```json
{
  "name": "Rua A",
  "install_height_cm": 20,
  "attention_cm": 2,
  "avoid_cm": 5,
  "blocked_cm": 8
}
```

### Headers

| Header | Obrigatório | Descrição |
|---|---|---|
| `Content-Type` | Sim | `application/json` |
| `X-Admin-Key` | Sim | Chave de administração. Peça ao usuário; não deixe fixa no código |

### Body

| Campo | Tipo | Obrigatório | Regras |
|---|---|---|---|
| `name` | `string` | Sim | 1 a 80 caracteres. Espaços nas pontas são removidos |
| `install_height_cm` | `number` | Sim | > 0. Distância do sensor até o chão seco |
| `attention_cm` | `number` | Sim | > 0. Nível de água que coloca a via em `atencao` |
| `avoid_cm` | `number` | Sim | > 0. Nível que coloca a via em `evitar` |
| `blocked_cm` | `number` | Sim | > 0. Nível que coloca a via em `bloqueada` |

Regras entre campos:

```
0 < attention_cm < avoid_cm < blocked_cm < install_height_cm
```

Validar essas regras também no formulário evita idas desnecessárias ao servidor.

## Response `201`

```json
{
  "id": 1,
  "name": "Rua A",
  "install_height_cm": 20.0,
  "attention_cm": 2.0,
  "avoid_cm": 5.0,
  "blocked_cm": 8.0,
  "created_at": "2026-10-19T22:44:09.822902Z",
  "api_key": "ws_UqbNRRP8MDHUSZ16l9ZTJ9ceY6n2qtF6"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `integer` | ID da via criada |
| `name` | `string` | Nome salvo (sem espaços nas pontas) |
| `install_height_cm` | `number` | Altura de instalação |
| `attention_cm` | `number` | Limite de `atencao` |
| `avoid_cm` | `number` | Limite de `evitar` |
| `blocked_cm` | `number` | Limite de `bloqueada` |
| `created_at` | `string` (datetime UTC) | Data do cadastro |
| `api_key` | `string` | Chave do sensor (`ws_` + 32 caracteres). **Exibida só aqui** |

## Erros

| Status | `detail` | Quando |
|---|---|---|
| `401` | `"X-Admin-Key ausente ou inválida"` | Header ausente ou com valor diferente da `ADMIN_API_KEY` |
| `422` | lista | Campo ausente, tipo errado, valor ≤ 0, nome vazio/longo, limites fora de ordem ou body não é JSON válido |
| `503` | `"Banco de dados indisponível"` | Falha ao acessar o Supabase |

### Exemplos de `422`

Limites fora de ordem (`loc` é só `["body"]`, pois envolve mais de um campo):

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, Os limites devem respeitar attention_cm < avoid_cm < blocked_cm",
      "ctx": { "error": {} }
    }
  ]
}
```

`blocked_cm` maior ou igual à altura:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, blocked_cm deve ser menor que install_height_cm",
      "ctx": { "error": {} }
    }
  ]
}
```

Campos inválidos e ausentes (vários erros na mesma resposta):

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "ctx": { "min_length": 1 }
    },
    {
      "type": "float_parsing",
      "loc": ["body", "install_height_cm"],
      "msg": "Input should be a valid number, unable to parse string as a number"
    },
    {
      "type": "missing",
      "loc": ["body", "attention_cm"],
      "msg": "Field required"
    }
  ]
}
```

Valor menor ou igual a zero:

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

As validações de campo (tipo, ausência, > 0) rodam antes das regras entre campos. Por isso, os erros
de `loc: ["body"]` só aparecem quando todos os campos individuais estão válidos.

## Exemplo

```js
async function createSensor(form, adminKey) {
  const payload = {
    name: form.name.value.trim(),
    install_height_cm: Number(form.install_height_cm.value),
    attention_cm: Number(form.attention_cm.value),
    avoid_cm: Number(form.avoid_cm.value),
    blocked_cm: Number(form.blocked_cm.value),
  };

  try {
    const sensor = await api("/sensors", {
      method: "POST",
      body: payload,
      headers: { "X-Admin-Key": adminKey },
    });

    return sensor.api_key;
  } catch (error) {
    if (error.status === 401) {
      sessionStorage.removeItem("adminKey");
    }

    if (error.status === 422 && Array.isArray(error.detail)) {
      for (const item of error.detail) {
        const field = item.loc[1];
        if (field && form[field]) {
          form[field].setCustomValidity(item.msg);
          form[field].reportValidity();
        }
      }
    }

    throw error;
  }
}
```
