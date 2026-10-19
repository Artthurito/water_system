# Water System — Monitoramento de Alagamentos Urbanos

Sistema de monitoramento em tempo real do nível de água em vias públicas, desenvolvido para a
disciplina de UPX (Facens) com foco em **mobilidade urbana**. Sensores a laser medem o acúmulo de
água em cada rua, uma API analisa as leituras e um painel web mostra a situação de cada via, o
histórico e qual caminho está em melhores condições de passagem.

> **Status:** em desenvolvimento. O protótipo é uma maquete com 3 vias monitoradas.

## Sumário

- [O problema](#o-problema)
- [Como funciona](#como-funciona)
- [Situação das vias](#situação-das-vias)
- [Arquitetura e tecnologias](#arquitetura-e-tecnologias)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como executar](#como-executar)
- [API](#api)
- [Relatório do projeto](#relatório-do-projeto)

## O problema

Na maioria das cidades, uma via alagada só é identificada quando já está intransitável. Nesse
ponto, motoristas e pedestres já estão expostos ao risco e não há tempo para escolher outra rota.
Além disso, a prefeitura raramente tem dados concretos sobre **onde** e **com que frequência** os
alagamentos acontecem.

O projeto propõe uma abordagem **preventiva**: acompanhar o nível da água continuamente e avisar
antes que a via fique bloqueada, guardando o histórico para apoiar o planejamento urbano.

## Como funciona

```
 ┌──────────────┐  POST /readings   ┌──────────────┐        ┌──────────────┐
 │ ESP32 + laser│ ────────────────▶ │  API FastAPI │ ─────▶ │   Supabase   │
 │  (1 por via) │   {distance_cm}   │  (análise)   │        │  (Postgres)  │
 └──────────────┘                   └──────────────┘        └──────────────┘
                                           ▲
                                           │ GET /analysis/status, /readings
                                    ┌──────────────┐
                                    │ Painel Dash  │
                                    └──────────────┘
```

1. **Medição:** cada sensor fica instalado acima da via e mede a distância até a superfície. Quando
   a água sobe, essa distância diminui.
2. **Envio:** a cada 5–10 s, o ESP32 envia a leitura para a API, identificado por uma chave própria.
3. **Análise:** a API converte a distância em nível de água (`altura de instalação − distância`),
   suaviza o ruído do laser com uma média móvel das últimas 5 leituras e classifica a via.
4. **Armazenamento:** cada leitura é gravada com o nível calculado e a situação da via.
5. **Visualização:** o painel atualiza a cada 5 s, mostrando a situação atual de cada via, o
   caminho recomendado e gráficos com o histórico.

## Situação das vias

Cada via é classificada de acordo com o que a pessoa deve fazer ao passar por ela:

| Situação | Significado | Ação esperada |
|---|---|---|
| 🟢 **Livre** | Sem acúmulo relevante de água | Passagem normal |
| 🟡 **Atenção** | Lâmina d'água na pista, ainda transitável | Passar com cuidado, reduzir velocidade |
| 🟠 **Evitar** | Água em nível perigoso para pedestres e veículos baixos | Preferir rota alternativa |
| 🔴 **Bloqueada** | Via intransitável | Não passar |
| ⚪ **Sem sinal** | Sensor sem leitura há mais de 2 minutos | Situação desconhecida |

Os limites de cada situação (em cm) são configurados por via e calibrados nos testes com a maquete.
O **caminho recomendado** é a via com menor nível de água entre as que têm sinal e não estão bloqueadas.

## Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

```
<type>(<scope>): <descricao>
```

| Tipo | Uso |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correcao de bug |
| `refactor` | Refatoracao sem mudanca de comportamento |
| `style` | Formatacao, lint |
| `test` | Testes |
| `docs` | Documentacao |
| `chore` | Tarefas de infra/config |

Exemplos:

```
feat(auth): add refresh token flow
fix(registration): validate CPF before submission
refactor(tenant): extract connection pool to service
```

## Arquitetura e tecnologias

| Parte | Tecnologias |
|---|---|
| Sensores | ESP32, sensor de distância a laser TOF10120 |
| Backend (`sys_backend`) | Python 3.11+, FastAPI, Pydantic, supabase-py |
| Banco de dados | Supabase (PostgreSQL) |
| Frontend (`sys_frontend`) | Python 3.11+, Dash, Plotly, dash-bootstrap-components |

- Apenas o backend acessa o banco. Sensores e painel nunca recebem credenciais do Supabase.
- Cada sensor tem uma chave de API própria; o banco guarda somente o hash dessa chave.
- Os endpoints de consulta são públicos, pois o painel não exige login.

## Estrutura do repositório

```
water_system/
├── README.md
├── agents.md                 # convenções de código do projeto
├── sys_backend/              # API FastAPI
│   ├── main.py
│   ├── sql/schema.sql        # tabelas do Supabase
│   ├── scripts/              # simulador de sensor
│   ├── app/
│   │   ├── core/             # configuração, conexão com o banco, autenticação
│   │   ├── domain/           # enums e erros compartilhados
│   │   └── modules/          # sensors, readings, analysis (controller, schema, service)
│   └── tests/
└── sys_frontend/             # painel Dash
    ├── app.py
    └── src/
        ├── services/         # cliente HTTP da API
        ├── components/       # cards e gráficos
        ├── layout.py
        └── callbacks.py
```

## Como executar

### Pré-requisitos

- Python 3.11 ou superior
- Um projeto no [Supabase](https://supabase.com) (plano gratuito)

### 1. Banco de dados

No **SQL Editor** do Supabase, execute o conteúdo de `sys_backend/sql/schema.sql`.

### 2. Backend

```bash
cd sys_backend
python -m venv .venv
.venv\Scripts\activate          # Windows  |  source .venv/bin/activate (Linux/macOS)
pip install -r requirements.txt
cp .env.example .env            # preencha SUPABASE_URL, SUPABASE_SERVICE_KEY e ADMIN_API_KEY
uvicorn main:app --reload
```

A documentação interativa fica em <http://localhost:8000/docs>.

#### Modo do banco (`DB_MODE`)

| Valor | Comportamento |
|---|---|
| `supabase` (padrão) | Usa o Supabase. Exige `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` |
| `cache` | Guarda sensores e leituras em memória. Não precisa do Supabase nem do passo 1, mas os dados são perdidos ao reiniciar a API e não são compartilhados entre workers do `uvicorn` |

### 3. Cadastrar as vias

Em `/docs`, clique em **Authorize**, informe a `X-Admin-Key` e use `POST /sensors` para cadastrar
cada via. Guarde a `api_key` retornada: ela aparece **uma única vez** e deve ser gravada no ESP32
correspondente.

### 4. Frontend

```bash
cd sys_frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # API_URL=http://localhost:8000
python app.py
```

O painel fica em <http://localhost:8050>.

### 5. Testar sem o hardware

```bash
cd sys_backend
python scripts/simulate_sensor.py --api-key ws_... --interval 5
```

O simulador envia leituras que sobem e descem gradualmente, imitando um alagamento e o escoamento.

### Testes automatizados

```bash
cd sys_backend
pytest
```

## API

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| `POST` | `/sensors` | `X-Admin-Key` | Cadastra uma via e gera a chave do sensor |
| `GET` | `/sensors` | — | Lista as vias cadastradas |
| `GET` | `/sensors/{id}` | — | Detalha uma via |
| `POST` | `/readings` | `X-API-Key` | Recebe uma leitura do sensor |
| `GET` | `/readings` | — | Histórico de leituras (`sensor_id`, `since`, `limit`) |
| `GET` | `/analysis/status` | — | Situação atual das vias e caminho recomendado |

Exemplo de envio feito pelo ESP32:

```http
POST /readings
X-API-Key: ws_3f9c...
Content-Type: application/json

{ "distance_cm": 14.2 }
```

## Relatório do projeto

Texto da primeira parte do relatório entregue na disciplina.

<details>
<summary><strong>1. Objetivo geral</strong></summary>

O projeto tem como finalidade reduzir os riscos associados a alagamentos
urbanos por meio de um sistema de monitoramento em tempo real do nível de água
em vias públicas, utilizando sensores de distância a laser instalados em pontos
críticos e conectados a uma plataforma em nuvem. Ao coletar, transmitir e visualizar
esses dados de forma contínua, o sistema busca informar motoristas, pedestres e
órgãos públicos sobre a condição de trafegabilidade das ruas, permitindo decisões
mais seguras tanto no deslocamento imediato quanto no planejamento urbano de
longo prazo.

Diferentemente de abordagens que atuam apenas após a ocorrência do
problema, o sistema propõe uma resposta preventiva: ao identificar o acúmulo de
água antes que a via se torne intransitável, o projeto reduz a exposição de pessoas
e veículos a situações de risco e fornece à administração pública uma base de
dados concreta sobre onde e com que frequência os alagamentos ocorrem.

</details>

<details>
<summary><strong>2. Revisão de literatura e estado da arte</strong></summary>

Os alagamentos urbanos não afetam somente a região onde ocorre o
acúmulo de água. Quando uma via fica parcialmente ou totalmente bloqueada,
outros trajetos também podem ser prejudicados, aumentando o tempo de
deslocamento e dificultando o acesso a determinados locais. Morelli e Cunha (2021),
em um estudo sobre vulnerabilidade de redes viárias a enchentes urbanas,
analisaram justamente como a interrupção de ruas pode aumentar os caminhos que
precisam ser percorridos dentro de uma cidade. O trabalho utilizou informações da
própria rede viária e da distribuição das viagens para avaliar os efeitos dessas
interrupções. Alabbad et al. (2021) chegaram a uma questão semelhante ao estudar
cidades do estado de Iowa, nos Estados Unidos. Ao comparar cenários de
inundação, os autores observaram que o fechamento de vias pode modificar
inclusive os menores caminhos disponíveis para hospitais e outros serviços
essenciais.

Saber quais vias estão sendo afetadas depende, antes de tudo, de conseguir
acompanhar o nível da água. Entre as tecnologias utilizadas para essa finalidade
estão os sensores conectados à Internet das Coisas, ou IoT. Arshad et al. (2019)
realizaram uma revisão sistemática sobre o uso de sensores e visão computacional
no monitoramento de enchentes. Após o processo de seleção, os autores
analisaram 91 trabalhos relacionados ao tema e encontraram aplicações que
envolviam medição do nível da água, sistemas de alerta e mapeamento de áreas
inundadas. Van Ackere et al. (2019) também discutem essa integração entre
sensores, comunicação e processamento de dados por meio do conceito de Internet
of Floods. Nesse caso, a principal ideia é fazer com que as informações coletadas
no ambiente possam ser transmitidas e utilizadas em um intervalo próximo ao tempo
real.

A maneira de realizar a medição também é um ponto importante. Sekiya et al.
(2022) fizeram testes com sensores a laser e ultrassônicos sem contato direto com a
água. Os equipamentos foram avaliados tanto com a água parada quanto em
movimento, e os dois tipos de sensor conseguiram identificar alterações no nível,
apesar de apresentarem diferenças na variação dos resultados. Esse tipo de teste
mostra que a escolha e a instalação do sensor podem influenciar a qualidade das
informações obtidas.

Ranieri et al. (2024) aprofundaram essa questão ao comparar sensores
LiDAR e ultrassônicos para medição do nível da água. Os testes foram realizados
em ambiente controlado, alterando fatores como distância do sensor, inclinação e
turbidez da água. Os resultados indicaram que essas condições podem interferir na
medição e que cada tecnologia possui vantagens dependendo da situação. Para um
sistema de monitoramento, isso reforça a necessidade de realizar testes e
calibrações antes de considerar os valores obtidos como confiáveis.
Existem também trabalhos que aplicam esses conceitos em protótipos
relativamente simples. Sihombing et al. (2022) desenvolveram um sistema para
acompanhar o nível da água em uma estrutura de drenagem utilizando um sensor
ultrassônico. Além da medição, o protótipo utilizava níveis de classificação, como
baixo, médio e alto, para facilitar a interpretação da situação. Zakaria, Jabbar e
Sulaiman (2023) seguiram uma proposta parecida, mas utilizando comunicação
LoRaWAN. O sistema desenvolvido por eles utilizava um sensor ultrassônico
HC-SR04 ligado a um Arduino e classificava a condição observada em quatro
estados de risco: seguro, alerta, cautela e perigo. As informações eram enviadas
para plataformas digitais, onde poderiam ser acompanhadas remotamente.

Uma solução ainda mais próxima dos componentes considerados para este
projeto foi apresentada por Lias e Kumaran (2024). Os autores utilizaram um ESP32
e um sensor de distância a laser TOF10120 para medir o nível da água. O protótipo
separava as medições em diferentes faixas de risco e utilizava a conexão sem fio do
ESP32 para disponibilizar as informações pelo aplicativo Blynk. Além disso, foram
utilizados indicadores visuais e um alarme sonoro. O trabalho é interessante para
esta pesquisa porque demonstra, na prática, a possibilidade de combinar um
microcontrolador conectado à internet com um sensor de distância a laser para
acompanhar diferentes níveis de água.

Faudzi, Raslan e Alias (2023) propuseram um sistema que reúne dados de
um pluviômetro e do nível da água e transmite essas informações através de uma
rede GSM. Os valores podem ser armazenados em nuvem e apresentados em um
painel desenvolvido com Grafana. No estudo, esses dados ainda foram utilizados
em um modelo de previsão, mostrando que informações de chuva e de nível da
água podem ser trabalhadas em conjunto.

Os trabalhos analisados mostram que não existe somente uma forma de
construir um sistema de monitoramento de alagamentos. Alguns utilizam sensores
ultrassônicos, outros sensores a laser, e os meios de comunicação também variam
entre Wi-Fi, redes móveis e LoRaWAN. O mesmo acontece com a apresentação das
informações, que pode ser feita por aplicativos, painéis web, alertas ou sistemas
mais completos de apoio à decisão. Apesar dessas diferenças, um ponto em comum
entre os estudos é a tentativa de transformar uma medição realizada no ambiente
em uma informação que possa ser consultada e compreendida pelo usuário.

Dentro desse contexto, o projeto proposto pelo grupo reúne conceitos que já
aparecem na literatura, porém em uma escala adequada ao desenvolvimento
acadêmico. A maquete permitirá representar diferentes condições de alagamento
em mais de uma via, enquanto os sensores realizarão as medições do nível da água
e da quantidade de chuva. Esses dados serão transmitidos para uma plataforma
web, onde poderão ser apresentados de forma que o usuário consiga comparar a
situação das ruas e identificar qual caminho apresenta melhores condições de
passagem.

Assim, a proposta não parte da ideia de criar uma tecnologia completamente
nova, mas de integrar recursos que já demonstraram aplicação em estudos
anteriores. O diferencial está em reunir o monitoramento do nível da água, a
medição da chuva e a visualização das condições de diferentes trajetos em uma
mesma proposta voltada à mobilidade urbana. A maquete funciona como uma forma
de testar essa integração e observar suas possibilidades e limitações antes de
pensar em uma aplicação de maior escala.

</details>

<details>
<summary><strong>3. Objetivos específicos</strong></summary>

Para alcançar o objetivo geral proposto, o projeto foi estruturado em etapas. A
primeira delas consiste no desenvolvimento de três sensores de distância a laser
instalados em ruas distintas ao longo de um trajeto da cidade, configurados para
medir continuamente a variação do nível de água acumulada na via.

Na sequência, prevê a implementação da comunicação em nuvem, por meio
de chaves de API que permitam o envio automático e periódico das leituras dos
sensores para um servidor remoto, garantindo que os dados coletados estejam
disponíveis para consulta em tempo real e de forma automática. Portanto, será
fundamental o desenvolvimento da plataforma web de visualização, responsável por
receber os dados enviados pelos sensores e apresentá-los em formato gráfico,
permitindo acompanhar tanto a situação atual de cada via quanto o histórico de
ocorrências ao longo do tempo.

O projeto busca também validar a precisão e a confiabilidade do sistema por
meio de testes reais, comparando as medições registradas pelos sensores com o
nível de água observado nas vias monitoradas, de modo a verificar se os dados
gerados são confiáveis para influenciar decisões de trânsito e de gestão pública.
Além disso, o objetivo é demonstrar a aplicabilidade dos dados para tomada
de decisão, tanto no âmbito público, fornecendo à prefeitura de Sorocaba
informações concretas sobre os pontos de alagamento recorrente e sua frequência,
quanto no âmbito individual, avaliando a possibilidade de integração com aplicativos
de mapeamento de rotas para sugerir trajetos alternativos mais seguros aos
usuários.

Por fim, o projeto objetiva posicionar a solução como um modelo replicável e
de baixo custo, capaz de ser expandido para outras vias e regiões da cidade,
apresentando-se como alternativa acessível para municípios que enfrentam
problemas recorrentes de alagamento e não dispõem de infraestrutura de
monitoramento adequada.

</details>

<details>
<summary><strong>4. Justificativa</strong></summary>

Os alagamentos urbanos representam um problema recorrente em diversas
cidades, podendo comprometer a mobilidade, causar danos materiais e colocar
motoristas e pedestres em situações de risco. Em fevereiro de 2025, por exemplo,
fortes chuvas provocaram alagamentos em diferentes pontos da Marginal Tietê, em
São Paulo, deixando trechos da via intransitáveis e causando congestionamentos e
interrupções no trânsito (CNN BRASIL, 2025a). Em muitos casos, a identificação de
uma via alagada ocorre somente quando o problema já está acontecendo,
dificultando a escolha antecipada de rotas alternativas. Dessa forma, o projeto busca
contribuir para o acompanhamento dessas situações e para a disponibilização de
informações que possam auxiliar na tomada de decisões mais seguras.

A proposta apresenta potencial por utilizar tecnologias acessíveis e de fácil
integração, permitindo o desenvolvimento de uma solução de monitoramento que
possa ser testada inicialmente em escala reduzida. Além disso, a estrutura do
projeto possibilita futuras expansões, tanto em relação à quantidade de pontos
monitorados quanto às formas de utilização das informações obtidas.

O projeto é importante para o alcance do objetivo proposto porque permite
transformar informações obtidas diretamente no ambiente monitorado em dados
acessíveis aos usuários. Dessa maneira, torna-se possível acompanhar situações
de risco de forma mais rápida, auxiliando motoristas e pedestres na escolha de
trajetos mais seguros. Ao mesmo tempo, o registro dessas informações ao longo do
tempo pode contribuir para a identificação de locais onde os alagamentos ocorrem
com maior frequência, fornecendo dados que possam servir de apoio para órgãos
públicos no planejamento de ações relacionadas à drenagem, manutenção e
infraestrutura urbana.

A ideia do projeto surgiu a partir da necessidade de buscar uma forma
preventiva de lidar com situações de alagamento. Em vez de depender somente da
identificação do problema quando uma via já está comprometida, a proposta busca
permitir que alterações nas condições do local sejam identificadas e disponibilizadas
de maneira mais rápida. A utilização de tecnologias para esse tipo de prevenção já
pode ser observada em iniciativas recentes. Em Santo André, por exemplo, foi
anunciada em 2025 a implementação de um sistema que utiliza dados em tempo
real para identificar a probabilidade de alagamentos e auxiliar na realização de
ações preventivas (CNN BRASIL, 2025b). Dessa forma, o projeto procura
demonstrar como o uso da tecnologia pode contribuir para o acompanhamento de
problemas urbanos e para a redução da exposição de pessoas a situações de risco.

O diferencial da proposta está na integração entre o monitoramento do
ambiente e a disponibilização digital das informações, utilizando componentes
relativamente acessíveis e uma estrutura que pode ser ampliada futuramente. Além
de permitir o acompanhamento da situação atual das vias, o armazenamento dos
dados pode possibilitar a criação de um histórico de ocorrências, aumentando a
utilidade das informações para análises futuras e tornando a solução potencialmente
aplicável a outros pontos da cidade.

</details>
