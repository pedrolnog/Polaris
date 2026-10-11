# Polaris

> **Plataforma de Observabilidade e Inventário de Redes Locais**

O **Polaris** é uma ferramenta de observabilidade de infraestrutura voltada para **home labs, laboratórios de estudo e pequenas equipes de TI**. Seu objetivo é eliminar a perda de controle sobre dispositivos conectados em redes locais, monitorando a evolução do ambiente ao longo do tempo em vez de apenas tirar uma foto estática do momento.

A filosofia do projeto baseia-se em quatro pilares documentados no domínio:
- **Descoberta antes de configuração:** dispositivos e mudanças devem ser encontrados automaticamente.
- **Mudanças são mais importantes que estados:** entender *quando* um dispositivo entrou, mudou de IP ou caiu é mais valioso do que apenas listar quem está online agora.
- **Simplicidade antes de complexidade:** arquitetura enxuta, sem agentes externos instalados nas máquinas e sem dependências de soluções pesadas de monitoramento corporativo.
- **Contexto humano importa:** permitir que máquinas anônimas ganhem nomes legíveis e contexto organizacional.

---

## Como Funciona o Pipeline

O Polaris opera em ciclos automáticos em background (ou sob demanda via API) seguindo o seguinte fluxo:

```
[ Interfaces de Rede ] 
         │  (psutil + filtro RFC 1918)
         ▼
[ Varredura ARP L2 ] ──> Scapy envia broadcast e coleta respostas (MAC + IP)
         │
         ▼
[ Normalização & Persistência ] ──> Salva Scan bruto e faz UPSERT dos Devices no PostgreSQL
         │
         ▼
[ State-Diff Engine ] ──> Compara o scan atual com o histórico anterior da rede
         │
         ├─► [ 001 ] Dispositivo ficou Offline
         ├─► [ 002 ] Dispositivo mudou de IP
         ├─► [ 003 ] Dispositivo novo (primeira vez conectado)
         └─► [ 004 ] Dispositivo reconectou (estava offline e voltou)
         │
         ▼
[ Enriquecimento Assíncrono ] (Apenas para novos dispositivos - 003)
         ├─► Resolução DNS Reverso (Hostname)
         └─► Consulta de Fabricante (API MAC Lookup com concorrência controlada via Semaphore)
```

---

## O que Está Implementado (Versão 1.0)

### 1. Scanner de Rede (Camada 2)
- **Descoberta por ARP (`scapy`):** Envio de requisições ARP em broadcast para detecção rápida sem depender de resposta a ping (ICMP).
- **Detecção e Validação de Interfaces (`psutil` + `ipaddress`):**
  - Identificação automática das sub-redes ativas.
  - Filtro de segurança: descarta interfaces loopback, link-local (APIPA) e sub-redes com máscara mais aberta que `/20` para evitar travamentos ou varreduras acidentais de faixas gigantes (ex: `10.0.0.0/8`).

### 2. Motor de Mudanças (*State-Diff Engine*)
- Comparação do estado atual contra o catálogo da rede:
  - **`001` (Offline):** Dispositivo que estava ativo mas não respondeu ao scan atual.
  - **`002` (IP Alterado):** Dispositivo que renovou lease DHCP ou mudou endereço IP.
  - **`003` (Novo Dispositivo):** Endereço MAC descoberto pela primeira vez naquela rede.
  - **`004` (Reconectado):** Dispositivo previamente catalogado como offline que voltou a responder.

### 3. Enriquecimento de Metadados
- Disparado em background de forma não bloqueante para novos dispositivos:
  - **Hostname:** Resolução via DNS reverso com execução em thread pool do asyncio.
  - **Fabricante (MAC Vendor):** Consulta à API pública do *maclookup* utilizando sessão HTTP persistente (`httpx.AsyncClient`).
  - **Controle de Vazão:** Limitação de até 5 tarefas simultâneas via `asyncio.Semaphore` para evitar timeouts ou rate limits externos.

### 4. Banco de Dados e Persistência (PostgreSQL)
- Conexão e pooling gerenciados com `psycopg 3` (`ConnectionPool`).
- Modelo relacional estruturado:
  - `networks`: Redes identificadas por interface.
  - `devices`: Catálogo com restrição de unicidade `(network_id, mac_address)`, timestamps `first_seen`/`last_seen` e campos para personalização.
  - `scans`: Histórico cronológico de varreduras executadas e total de hosts encontrados.
  - `changes`: Trilha de auditoria cronológica das mudanças detectadas.
- Estratégia de UPSERT: atualiza `last_seen`, status e IP caso o MAC já exista, mantendo o histórico intacto.

### 5. API REST (FastAPI)
- **Ciclo de vida (`lifespan`):** Inicialização automática das tabelas e execução de loop contínuo de observabilidade a cada 30 segundos.
- **Endpoints organizados por domínio:**
  - `POST /scan?interface={nome}`: Força uma varredura manual de diagnóstico sob demanda.
  - `GET /scan/history`: Consulta o histórico de execuções de varredura.
  - `GET /networks`: Lista todas as redes registradas.
  - `GET /networks/{network_id}`: Detalhes de uma rede específica.
  - `GET /networks/{network_id}/devices`: Dispositivos pertencentes a uma rede.
  - `GET /devices`: Lista completa de dispositivos catalogados.
  - `GET /devices/{device_id}`: Detalhes de um dispositivo por UUID.
  - `PATCH /devices/{device_id}`: Atribui um nome customizado (`custom_name`) a um dispositivo.
  - `GET /changes?limit=50&offset=0`: Feed paginado com todas as alterações detectadas no ambiente.

---

## Decisões Arquiteturais Relevantes (ADRs do Projeto)

O desenvolvimento seguiu decisões estruturadas documentadas em ADRs:

- **ADR-001 (MAC Address como Identificador de Hardware):** IPs mudam constantemente em redes com DHCP. O MAC é o identificador estável para rastrear um dispositivo no tempo.
- **ADR-002 & ADR-009 (Mudanças antes de Estados):** O valor da ferramenta é histórico. Em vez de apenas sobrescrever dados, cada variação gera um registro imutável em `changes`.
- **ADR-005 (Simplicidade antes de Escalabilidade):** Foco em execução local leve para laboratórios; sem necessidade de brokers de mensagens (Kafka/RabbitMQ) ou orquestradores complexos para o MVP.
- **ADR-007 (Dispositivo vinculado à Rede):** No escopo atual, um dispositivo é associado à interface/rede onde foi observado (`UNIQUE (network_id, mac_address)`).

---

## Estrutura do Código

```
Polaris/
├── src/
│   ├── backend/
│   │   └── app/
│   │       ├── database/
│   │       │   ├── connection.py     # Pool de conexões psycopg 3 e queries
│   │       │   ├── db_models.py      # Schemas de leitura de banco
│   │       │   └── schema.sql        # DDL das tabelas (PostgreSQL)
│   │       ├── routers/
│   │       │   ├── changes_router.py # Endpoints de auditoria de eventos
│   │       │   ├── devices_router.py # Consulta e personalização de devices
│   │       │   ├── network_router.py # Gerenciamento de redes locais
│   │       │   └── scan_router.py    # Disparo e histórico de varreduras
│   │       ├── schemas/
│   │       │   └── models.py         # Modelos Pydantic v2 do domínio
│   │       ├── services/
│   │       │   ├── changes_service.py # Engine de detecção de diferenças (diff)
│   │       │   ├── device_service.py  # Enriquecimento assíncrono (DNS + Fabricante)
│   │       │   └── scan_service.py    # Orquestração do pipeline de scan
│   │       └── main.py               # Entrada FastAPI e loop de observabilidade
│   └── scanner/
│       ├── scan_models.py            # DTOs de dados brutos de rede
│       └── scanner.py                # Interação de baixo nível com Scapy e psutil
├── .env                              # Variáveis de ambiente
├── requirements.txt                  # Dependências do projeto
└── README.md
```

---

## Como Executar

### Pré-requisitos
- Python 3.12+ (ou compatível).
- PostgreSQL em execução.
- Permissões de Administrador / Root (necessário para manipulação de pacotes ARP brutos via Scapy e Npcap no Windows ou libpcap no Linux).

### 1. Configuração do Ambiente

Crie o arquivo `.env` na raiz do projeto com as credenciais do banco:
```env
DB_USER=seu_usuario
DB_PASS=sua_senha
```

Certifique-se de ter um banco criado no PostgreSQL chamado `polaris_db`. As tabelas são criadas automaticamente ao iniciar o serviço.

### 2. Instalação das Dependências

```bash
# Ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .\.venv\Scripts\activate

# Instalar dependências
pip install fastapi uvicorn psycopg[binary] psycopg-pool scapy psutil httpx pydantic uuid6 python-dotenv
```

### 3. Executando a Aplicação

Inicie o servidor (em terminal com privilégios de Administrador):
```bash
uvicorn src.backend.app.main:app --reload
```

A documentação interativa da API estará disponível em:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`

O loop em background começará a monitorar as interfaces locais automaticamente a cada 30 segundos.

---

## O que Vem a Seguir (Roadmap)

Conforme o planejamento de arquitetura e casos de uso do projeto:
- [ ] **Interface Gráfica (Frontend Web):** Dashboard para visualização da topologia, cartões de dispositivos e feed de mudanças em tempo real.
- [ ] **Categorização de Dispositivos:** Atribuição de categorias aos ativos (ex: Servidores, Impressoras, IoT, Roteadores).
- [ ] **Classificação de Severidade de Mudanças:** Atribuir peso aos eventos (`INFO`, `WARNING`, `CRITICAL`), permitindo alertas direcionados quando ativos críticos ficarem offline.
