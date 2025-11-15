# 🏗️ Portal Base - Complete Setup Explanation

Este documento explica **todo o sistema** de forma clara e completa, desde a arquitetura até como cada componente funciona.

---

## 📋 Índice

1. [Visão Geral do Sistema](#visão-geral-do-sistema)
2. [Arquitetura](#arquitetura)
3. [Componentes Principais](#componentes-principais)
4. [Fluxo de Dados](#fluxo-de-dados)
5. [Sistema de Cache](#sistema-de-cache)
6. [Automação Diária](#automação-diária)
7. [Integração HubSpot](#integração-hubspot)
8. [Configuração e Secrets](#configuração-e-secrets)

---

## 🎯 Visão Geral do Sistema

### O que este sistema faz?

Este sistema automatiza a busca e processamento de **anúncios de concursos públicos portugueses** do Base.gov.pt:

1. **App Web (Streamlit)**: Interface para pesquisar e filtrar contratos/anúncios
2. **Cache Local (SQLite)**: Armazena dados localmente para consultas rápidas
3. **Automação Diária (GitHub Actions)**: Busca novos anúncios automaticamente
4. **Integração HubSpot**: Cria deals no CRM para anúncios que atendem aos critérios

### Fluxo Simplificado

```
Base.gov.pt API
    ↓
[Cache SQLite] ←→ [App Streamlit] (pesquisa manual)
    ↓
[GitHub Actions] (automação diária)
    ↓
[Filtros Salvos] → [Novos Anúncios] → [HubSpot Deals]
```

---

## 🏛️ Arquitetura

### Componentes e suas Responsabilidades

```
┌─────────────────────────────────────────────────────────────┐
│                    PORTAL BASE SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │  Base.gov.pt │      │   HubSpot    │                     │
│  │     API      │      │     CRM      │                     │
│  └──────┬───────┘      └───────▲──────┘                     │
│         │                      │                              │
│         │                      │                              │
│  ┌──────▼──────────────────────┴──────┐                     │
│  │      CachedBaseAPIClient           │                     │
│  │  (Gerencia cache e API calls)      │                     │
│  └──────┬───────────────────┬────────┘                     │
│         │                   │                                │
│    ┌────▼────┐        ┌─────▼──────┐                       │
│    │ SQLite  │        │  Streamlit  │                       │
│    │  Cache  │        │     App     │                       │
│    │ (Local) │        │  (Web UI)   │                       │
│    └─────────┘        └─────────────┘                       │
│         │                                                    │
│         │                                                    │
│  ┌──────▼──────────────────────────┐                       │
│  │    GitHub Actions Workflow      │                       │
│  │  (Automação Diária)              │                       │
│  │                                  │                       │
│  │  • Baixa cache do artifact       │                       │
│  │  • Busca novos anúncios          │                       │
│  │  • Aplica filtros salvos         │                       │
│  │  • Cria deals no HubSpot         │                       │
│  │  • Faz upload do cache atualizado│                       │
│  └──────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes Principais

### 1. **`base_api_client.py`** - Cliente API Direto

**O que faz:**
- Comunica diretamente com a API do Base.gov.pt
- Faz requisições HTTP para buscar contratos e anúncios
- Não armazena dados (apenas busca)

**Principais métodos:**
- `get_contract_info()` - Busca informações de contratos
- `get_announcement_info()` - Busca informações de anúncios
- `get_entity_info()` - Busca informações de entidades

**Quando é usado:**
- Quando não há dados no cache
- Quando precisa buscar dados novos da API

---

### 2. **`cached_api_client.py`** - Cliente com Cache

**O que faz:**
- **Wrapper** do `BaseAPIClient` que adiciona cache
- Armazena dados em SQLite (`base_cache.db`)
- Evita chamadas repetidas à API
- Gerencia buscas salvas

**Estrutura do Banco de Dados:**

```sql
-- Tabela de contratos
contracts (
    id_contrato, data_publicacao, preco_contratual,
    tipo_contrato, cpv, local_execucao, raw_data, ...
)

-- Tabela de anúncios (procedimentos abertos)
announcements (
    n_anuncio, data_publicacao, tipo_anuncio,
    nif_entidade, raw_data, ...
)

-- Metadados do cache
cache_metadata (
    year, last_fetched, record_count
)

-- Buscas salvas (filtros reutilizáveis)
saved_searches (
    id, name, filters, created_at, last_used
)

-- Anúncios processados (para evitar duplicatas)
processed_announcements (
    n_anuncio, hubspot_deal_id, saved_search_name, processed_at
)

-- Logs de sincronização diária
daily_sync_log (
    sync_date, announcements_fetched, announcements_new,
    deals_created, deals_failed, sync_status, error_message
)
```

**Principais métodos:**
- `get_contracts_by_date()` - Busca contratos (com cache)
- `get_announcements_by_date()` - Busca anúncios (com cache)
- `save_search()` - Salva filtros como busca reutilizável
- `load_search()` - Carrega busca salva
- `is_announcement_processed()` - Verifica se anúncio já foi processado
- `mark_announcement_processed()` - Marca anúncio como processado

---

### 3. **`app.py`** - Aplicação Web Streamlit

**O que faz:**
- Interface web para pesquisar contratos e anúncios
- Permite filtrar por: keywords, CPV, location, fornecedor, datas
- Mostra estatísticas e analytics
- Permite salvar buscas para reutilização

**Funcionalidades principais:**

1. **Filtros:**
   - Date range (hoje, ontem, últimos 7/30 dias, customizado)
   - Keywords (comma-separated)
   - CPV codes (multi-select)
   - Location (multi-select)
   - Fornecedor NIF

2. **Visualizações:**
   - Tabela de resultados
   - Analytics (gráficos, estatísticas)
   - Detailed view (detalhes completos)

3. **Buscas Salvas:**
   - Salvar filtros com nome
   - Carregar busca salva
   - Deletar busca salva

**Fluxo no app:**
```
Usuário configura filtros
    ↓
app.py chama filter_contracts()
    ↓
Filtra dados do cache
    ↓
Mostra resultados na UI
```

---

### 4. **`filter_utils.py`** - Lógica de Filtragem

**O que faz:**
- Função `filter_contracts()` que aplica filtros
- Funciona tanto para contratos quanto anúncios
- Suporta múltiplos critérios simultaneamente

**Filtros suportados:**
- `keyword`: Busca em texto (comma-separated)
- `cpv_codes`: Lista de códigos CPV
- `location`: Lista de localizações
- `fornecedor_nif`: NIF do fornecedor
- `date_range`: Range de datas (aplicado separadamente)

---

### 5. **`daily_automation.py`** - Script de Automação

**O que faz:**
- Roda diariamente via GitHub Actions
- Busca novos anúncios da API
- Aplica filtros de busca salva
- Cria deals no HubSpot para anúncios que atendem aos critérios

**Fluxo do script:**

```
1. Carrega busca salva (ex: "Biogerm")
   ↓
2. Busca novos anúncios da API (últimos N dias)
   ↓
3. Armazena novos anúncios no cache
   ↓
4. Aplica filtros da busca salva
   ↓
5. Para cada anúncio filtrado:
   - Verifica se já foi processado
   - Verifica se já existe deal no HubSpot
   - Cria novo deal no HubSpot
   - Marca como processado
   ↓
6. Faz upload do cache atualizado
   ↓
7. Registra log da execução
```

**Configuração via Environment Variables:**
- `AUTOMATION_SAVED_SEARCH`: Nome da busca salva a usar (padrão: "Default Automation")
- `DAYS_TO_CHECK`: Quantos dias verificar (padrão: 1)

---

### 6. **`hubspot_automation.py`** - Integração HubSpot

**O que faz:**
- Cria deals no HubSpot a partir de anúncios
- Mapeia campos do anúncio para propriedades do deal
- Verifica se deal já existe (evita duplicatas)

**Mapeamento de campos:**
```
Anúncio → Deal Property
─────────────────────────
nAnuncio → deal_number
dataPublicacao → publication_date
PrecoBase → amount
TipoAnuncio → deal_type
nifEntidade → entity_nif
CPVs → cpv_codes
... (ver código para lista completa)
```

**Funções principais:**
- `create_deal_from_announcement()` - Cria deal
- `check_deal_exists()` - Verifica se deal existe
- `get_hubspot_token()` - Obtém token da API

---

### 7. **`.github/workflows/daily-sync.yml`** - Workflow GitHub Actions

**O que faz:**
- Executa `daily_automation.py` diariamente
- Gerencia artifacts (banco de dados)
- Configura ambiente Python

**Fluxo do workflow:**

```
1. Checkout do repositório
   ↓
2. Setup Python 3.11
   ↓
3. Instala dependências (requirements.txt)
   ↓
4. Baixa banco de dados do artifact anterior (se existir)
   ↓
5. Executa daily_automation.py
   - Com secrets: BASE_API_KEY, HUBSPOT_API_TOKEN, etc.
   ↓
6. Faz upload do banco atualizado como artifact
   ↓
7. Próxima execução baixa este artifact
```

**Agendamento:**
- **Cron**: `30 17 * * *` (17:30 UTC = 18:30 Portugal)
- **Manual**: Pode ser executado manualmente via GitHub UI

**Secrets necessários:**
- `BASE_API_KEY`: Token da API Base.gov.pt
- `HUBSPOT_API_TOKEN`: Token da API HubSpot
- `AUTOMATION_SAVED_SEARCH`: Nome da busca salva (opcional)
- `DAYS_TO_CHECK`: Dias para verificar (opcional)

---

### 8. **`config.py`** - Gerenciamento de Configuração

**O que faz:**
- Centraliza carregamento de API keys e tokens
- Suporta múltiplas fontes (Streamlit secrets, env vars, arquivo Secrets)

**Ordem de prioridade:**
1. Streamlit secrets (para Streamlit Cloud)
2. Environment variables
3. Arquivo `Secrets` local

**Funções:**
- `get_api_key()` - Obtém token Base.gov.pt
- `get_hubspot_token()` - Obtém token HubSpot

---

## 🔄 Fluxo de Dados

### Fluxo Completo: Do Anúncio ao Deal

```
┌─────────────────────────────────────────────────────────────┐
│ 1. BASE.GOV.PT PUBLICA NOVO ANÚNCIO                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. GITHUB ACTIONS EXECUTA (17:30 UTC)                       │
│    • Baixa cache do artifact anterior                       │
│    • Executa daily_automation.py                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SCRIPT BUSCA NOVOS ANÚNCIOS                              │
│    • Chama Base.gov.pt API                                  │
│    • Busca anúncios dos últimos N dias                      │
│    • Armazena no cache SQLite                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. APLICA FILTROS DA BUSCA SALVA                            │
│    • Carrega busca "Biogerm" do cache                       │
│    • Filtra anúncios por: CPV, keywords, location, etc.    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PARA CADA ANÚNCIO FILTRADO:                             │
│    • Verifica se já foi processado (processed_announcements)│
│    • Verifica se já existe deal no HubSpot                 │
│    • Se não existe: cria novo deal                          │
│    • Marca como processado                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. FAZ UPLOAD DO CACHE ATUALIZADO                           │
│    • Salva como artifact no GitHub Actions                  │
│    • Próxima execução baixa este artifact                   │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo no App Streamlit (Uso Manual)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USUÁRIO ABRE APP STREAMLIT                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. APP CARREGA DADOS DO CACHE                                │
│    • Lê base_cache.db                                        │
│    • Mostra estatísticas do cache                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. USUÁRIO CONFIGURA FILTROS                                │
│    • Seleciona CPV codes                                    │
│    • Digita keywords                                         │
│    • Seleciona location                                      │
│    • Define date range                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. APP APLICA FILTROS                                       │
│    • Chama filter_contracts()                                │
│    • Filtra dados do cache                                  │
│    • Mostra resultados                                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. USUÁRIO PODE:                                             │
│    • Ver analytics                                           │
│    • Ver detalhes completos                                 │
│    • Exportar CSV                                            │
│    • Salvar busca (para usar na automação)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Sistema de Cache

### Como Funciona o Cache?

**Objetivo:** Evitar chamadas repetidas à API e acelerar consultas.

**Estrutura:**
- **SQLite database** (`base_cache.db`)
- Armazena dados brutos da API em JSON
- Metadados de quando foi atualizado

### Estratégia de Cache

1. **Primeira busca:**
   - Dados não estão no cache
   - Faz chamada à API
   - Armazena no cache
   - Retorna dados

2. **Buscas subsequentes:**
   - Dados estão no cache
   - Retorna do cache (rápido!)
   - Não faz chamada à API

3. **Atualização:**
   - App verifica data do cache
   - Se cache antigo, atualiza automaticamente
   - GitHub Actions atualiza diariamente

### Persistência no GitHub Actions

**Problema:** GitHub Actions não mantém arquivos entre execuções.

**Solução:** Artifacts do GitHub Actions

```
Execução 1:
  • Cria base_cache.db
  • Faz upload como artifact "base-cache-db"

Execução 2:
  • Baixa artifact "base-cache-db"
  • Usa base_cache.db
  • Atualiza dados
  • Faz upload novamente

Execução 3:
  • Baixa artifact atualizado
  • Continua ciclo...
```

**Retenção:** Artifacts são mantidos por 7 dias (configurável).

---

## 🤖 Automação Diária

### O que Acontece Diariamente?

**Horário:** 17:30 UTC (18:30 Portugal) - após Base.gov.pt publicar novos anúncios

**Processo:**

1. **Download do Cache**
   ```
   Baixa base_cache.db do artifact anterior
   ```

2. **Busca Novos Anúncios**
   ```
   Chama API Base.gov.pt
   Busca anúncios dos últimos N dias (padrão: 1 dia)
   Armazena no cache
   ```

3. **Aplica Filtros**
   ```
   Carrega busca salva (ex: "Biogerm")
   Filtra anúncios novos pelos critérios
   ```

4. **Cria Deals no HubSpot**
   ```
   Para cada anúncio filtrado:
     - Verifica se já foi processado
     - Verifica se deal existe
     - Cria deal novo
     - Marca como processado
   ```

5. **Upload do Cache**
   ```
   Faz upload do cache atualizado
   Próxima execução usa este cache
   ```

### Logs e Monitoramento

**Tabela `daily_sync_log`:**
- `sync_date`: Data da sincronização
- `announcements_fetched`: Quantos anúncios foram buscados
- `announcements_new`: Quantos são novos
- `deals_created`: Quantos deals foram criados
- `deals_failed`: Quantos falharam
- `sync_status`: "success", "partial", ou "error"
- `error_message`: Mensagem de erro (se houver)

**Como verificar:**
- Logs do GitHub Actions
- Tabela `daily_sync_log` no banco

---

## 🔗 Integração HubSpot

### Como Funciona?

**Objetivo:** Criar deals automaticamente para anúncios relevantes.

**Processo:**

1. **Anúncio filtrado** → Atende aos critérios da busca salva
2. **Verificação de duplicata:**
   - Verifica `processed_announcements` (já processado?)
   - Verifica HubSpot API (deal já existe?)
3. **Criação do deal:**
   - Mapeia campos do anúncio para propriedades do deal
   - Cria deal via HubSpot API
   - Salva deal ID no banco
4. **Registro:**
   - Marca anúncio como processado
   - Salva deal ID
   - Registra qual busca salva foi usada

### Mapeamento de Campos

Ver `hubspot_automation.py` para lista completa. Exemplos:

- `nAnuncio` → `deal_number`
- `dataPublicacao` → `publication_date`
- `PrecoBase` → `amount`
- `TipoAnuncio` → `deal_type`
- `CPVs` → `cpv_codes` (lista)

### Evitar Duplicatas

**Duas camadas de proteção:**

1. **Banco local:** `processed_announcements` table
2. **HubSpot API:** Verifica se deal com mesmo `deal_number` existe

Se qualquer uma indicar que já existe, **pula** o anúncio.

---

## 🔐 Configuração e Secrets

### Secrets do GitHub Actions

**Onde configurar:**
- GitHub → Repositório → Settings → Secrets and variables → Actions

**Secrets necessários:**

1. **`BASE_API_KEY`**
   - Token da API Base.gov.pt
   - Obtido em: https://www.base.gov.pt/APIBase2

2. **`HUBSPOT_API_TOKEN`**
   - Token da API HubSpot
   - Obtido em: HubSpot → Settings → Integrations → Private Apps

3. **`AUTOMATION_SAVED_SEARCH`** (opcional)
   - Nome da busca salva a usar
   - Padrão: "Default Automation"
   - Exemplo: "Biogerm"

4. **`DAYS_TO_CHECK`** (opcional)
   - Quantos dias verificar
   - Padrão: 1
   - Exemplo: 3 (verifica últimos 3 dias)

### Configuração Local

**Arquivo `Secrets` (local):**
```
BASE_API_KEY:"seu_token_aqui"
HUBSPOT_API_TOKEN:"seu_token_aqui"
```

**Environment Variables:**
```bash
export BASE_API_KEY="seu_token_aqui"
export HUBSPOT_API_TOKEN="seu_token_aqui"
```

**Streamlit Secrets (para Streamlit Cloud):**
```toml
# .streamlit/secrets.toml
BASE_API_KEY = "seu_token_aqui"
HUBSPOT_API_TOKEN = "seu_token_aqui"
```

---

## 📁 Estrutura de Arquivos

```
Portal Base/
├── app.py                      # App Streamlit (interface web)
├── base_api_client.py          # Cliente API direto
├── cached_api_client.py        # Cliente com cache SQLite
├── config.py                   # Gerenciamento de configuração
├── filter_utils.py             # Lógica de filtragem
├── hubspot_automation.py       # Integração HubSpot
├── daily_automation.py         # Script de automação diária
├── sync_db_simple.py          # Script para sincronizar banco
├── sync_db_to_github.py       # Script alternativo de sync
│
├── .github/
│   └── workflows/
│       ├── daily-sync.yml      # Workflow GitHub Actions
│       └── upload-db.yml       # Workflow para upload manual
│
├── base_cache.db              # Banco SQLite (não commitado)
├── Secrets                     # API keys (não commitado)
├── requirements.txt           # Dependências Python
│
└── Documentação/
    ├── README.md
    ├── APP_GUIDE.md
    ├── DATABASE_SYNC_GUIDE.md
    └── SETUP_EXPLANATION.md (este arquivo)
```

---

## 🚀 Como Tudo Se Conecta

### Cenário 1: Uso Manual (App Streamlit)

```
Usuário → app.py
    ↓
app.py → cached_api_client.py
    ↓
cached_api_client.py → base_api_client.py (se não tem cache)
    ↓
base_api_client.py → Base.gov.pt API
    ↓
Dados retornam → cached_api_client.py (armazena no cache)
    ↓
app.py → filter_utils.py (aplica filtros)
    ↓
Resultados → Usuário vê na UI
```

### Cenário 2: Automação Diária

```
GitHub Actions (17:30 UTC)
    ↓
Baixa cache do artifact
    ↓
Executa daily_automation.py
    ↓
daily_automation.py → cached_api_client.py
    ↓
cached_api_client.py → base_api_client.py → Base.gov.pt API
    ↓
Novos anúncios → cache
    ↓
daily_automation.py → filter_utils.py (aplica filtros)
    ↓
Anúncios filtrados → hubspot_automation.py
    ↓
hubspot_automation.py → HubSpot API (cria deals)
    ↓
Cache atualizado → Upload como artifact
    ↓
Próxima execução usa cache atualizado
```

---

## ✅ Checklist de Setup Completo

### 1. Configuração Inicial

- [ ] Clonar repositório
- [ ] Instalar dependências (`pip install -r requirements.txt`)
- [ ] Configurar `BASE_API_KEY` (local ou GitHub secrets)
- [ ] Configurar `HUBSPOT_API_TOKEN` (local ou GitHub secrets)

### 2. App Streamlit

- [ ] Executar `streamlit run app.py`
- [ ] Testar busca manual
- [ ] Configurar e salvar busca "Biogerm" (ou outro nome)
- [ ] Verificar que busca foi salva

### 3. Sincronização do Banco

- [ ] Executar `python sync_db_simple.py` (ou método alternativo)
- [ ] Verificar que banco foi commitado/pushado

### 4. GitHub Actions

- [ ] Configurar secrets no GitHub
- [ ] Executar workflow manualmente (primeira vez)
- [ ] Verificar logs - busca "Biogerm" encontrada
- [ ] Verificar que deals foram criados no HubSpot

### 5. Verificação Final

- [ ] Workflow executa automaticamente às 17:30 UTC
- [ ] Deals são criados no HubSpot para novos anúncios
- [ ] Cache persiste entre execuções
- [ ] Logs mostram sucesso

---

## 🎓 Conceitos Importantes

### 1. **Cache vs API Direta**

- **Cache:** Rápido, mas pode estar desatualizado
- **API Direta:** Sempre atualizado, mas mais lento

**Solução:** Cache com atualização automática

### 2. **Artifacts do GitHub Actions**

- **Problema:** GitHub Actions não mantém arquivos entre execuções
- **Solução:** Artifacts (armazenamento temporário)
- **Limitação:** Expira após 7 dias (mas é renovado a cada execução)

### 3. **Buscas Salvas**

- **O que são:** Filtros reutilizáveis
- **Onde são usadas:** App Streamlit (manual) e automação (automático)
- **Como funcionam:** Armazenadas no banco SQLite

### 4. **Processamento Incremental**

- **Problema:** Não queremos processar o mesmo anúncio duas vezes
- **Solução:** Tabela `processed_announcements` marca o que já foi processado
- **Benefício:** Eficiência e evita duplicatas

---

## 🐛 Troubleshooting Comum

### Problema: "Saved search 'Biogerm' not found"

**Causa:** Banco não foi sincronizado com GitHub Actions

**Solução:**
1. Execute `python sync_db_simple.py`
2. Ou execute workflow manualmente (cria busca automaticamente na primeira vez)

### Problema: "Artifact not found"

**Causa:** Primeira execução (normal)

**Solução:** Não é um problema - workflow cria artifact automaticamente

### Problema: Deals duplicados no HubSpot

**Causa:** Anúncio foi processado duas vezes

**Solução:** Verificar `processed_announcements` table e lógica de verificação

### Problema: Cache desatualizado

**Causa:** Cache não foi atualizado recentemente

**Solução:** 
- App atualiza automaticamente se cache antigo
- GitHub Actions atualiza diariamente

---

## 📚 Próximos Passos

1. **Configurar busca "Biogerm"** com filtros corretos
2. **Sincronizar banco** com GitHub Actions
3. **Testar workflow** manualmente
4. **Verificar deals** criados no HubSpot
5. **Monitorar execuções** diárias

---

**Pronto!** 🎉 Agora você entende todo o sistema!

Para dúvidas específicas, consulte:
- `DATABASE_SYNC_GUIDE.md` - Como sincronizar banco
- `APP_GUIDE.md` - Como usar o app
- `README.md` - Visão geral do projeto

