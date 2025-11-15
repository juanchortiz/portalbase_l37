# Database Sync Guide

Este guia explica como sincronizar o banco de dados local (com buscas salvas) com o GitHub Actions para que a automação diária funcione.

## 🎯 Objetivo

Garantir que a busca "Biogerm" (ou outra busca configurada) esteja disponível no GitHub Actions para a automação diária funcionar.

## 📋 Pré-requisitos

1. ✅ Você já salvou a busca "Biogerm" na app Streamlit localmente
2. ✅ O banco `base_cache.db` existe localmente
3. ✅ Você tem acesso ao repositório GitHub

## 🚀 Métodos de Sincronização

### Método 1: Primeira Execução Automática (Recomendado - Mais Simples)

**Como funciona:**
- Na primeira execução do workflow, se não houver buscas salvas, ele cria automaticamente a busca "Biogerm" com filtros vazios
- Você então configura os filtros na app Streamlit
- O banco persiste automaticamente entre execuções via artifacts

**Passos:**
1. Vá para: https://github.com/juanchortiz/portalbase_l37/actions
2. Clique em "Daily Portal Base Sync"
3. Clique em "Run workflow" → "Run workflow"
4. Na primeira execução, a busca "Biogerm" será criada automaticamente (com filtros vazios)
5. **IMPORTANTE:** Configure os filtros na app Streamlit e salve novamente como "Biogerm"
6. Execute o workflow novamente manualmente para sincronizar a busca configurada

**Vantagens:**
- ✅ Não precisa fazer commit do banco
- ✅ Mais seguro (banco não fica no git)
- ✅ Simples

**Desvantagens:**
- ⚠️ Na primeira execução, vai processar TODOS os anúncios (filtros vazios)
- ⚠️ Precisa configurar os filtros depois

---

### Método 2: Script de Sincronização Simples (Recomendado para Configuração Inicial)

**Como funciona:**
- Faz commit temporário do banco no GitHub
- O workflow baixa o banco do repositório
- Remove o banco do tracking para não aparecer em commits futuros

**Passos:**
1. Configure e salve a busca "Biogerm" na app Streamlit localmente
2. Execute o script:
   ```bash
   python sync_db_simple.py
   ```
3. O script vai:
   - Fazer commit do banco
   - Fazer push para GitHub
   - Remover o banco do tracking (mas mantém no histórico)
4. O próximo workflow run vai baixar o banco e usar suas buscas salvas

**Vantagens:**
- ✅ Sincroniza a busca já configurada
- ✅ Funciona imediatamente
- ✅ Remove o banco do tracking após sync

**Desvantagens:**
- ⚠️ O banco fica no histórico do git (pode ser removido depois com `git filter-branch`)

---

### Método 3: Script com Instruções (Alternativa)

**Como funciona:**
- Mostra instruções detalhadas sobre como fazer upload manual

**Passos:**
1. Execute:
   ```bash
   python sync_db_to_github.py
   ```
2. Siga as instruções exibidas

**Vantagens:**
- ✅ Não modifica o repositório
- ✅ Mostra todas as opções disponíveis

**Desvantagens:**
- ⚠️ Requer ação manual adicional

---

## 🔄 Após a Sincronização

Depois de sincronizar o banco:

1. **O workflow diário vai funcionar automaticamente:**
   - Baixa o banco do artifact (ou repositório)
   - Usa a busca "Biogerm" configurada
   - Filtra os anúncios
   - Cria deals no HubSpot
   - Faz upload do banco atualizado

2. **O banco persiste entre execuções:**
   - Cada execução baixa o artifact da execução anterior
   - Processa novos anúncios
   - Faz upload do banco atualizado
   - Ciclo se repete automaticamente

## ⚙️ Configuração da Busca "Biogerm"

Para configurar os filtros da busca "Biogerm":

1. Abra a app Streamlit localmente
2. Configure os filtros desejados:
   - Keywords
   - CPV codes
   - Location
   - Fornecedor NIF
   - Date range
3. Clique em "💾 Saved Searches" no sidebar
4. Digite "Biogerm" no campo de nome
5. Clique em "Save Search"
6. Execute o Método 2 acima para sincronizar

## 🔍 Verificar se Funcionou

Para verificar se a sincronização funcionou:

1. Vá para: https://github.com/juanchortiz/portalbase_l37/actions
2. Execute o workflow manualmente
3. Veja os logs - deve mostrar:
   ```
   ✅ Loaded filters: ['keyword', 'fornecedor_nif', 'location', 'cpv_codes']
   ```
4. Se mostrar "Saved search 'Biogerm' not found!", a sincronização não funcionou

## 🛠️ Troubleshooting

### Problema: "Saved search 'Biogerm' not found!"

**Solução:**
- Execute o Método 2 (`sync_db_simple.py`) para sincronizar o banco
- Ou execute o workflow manualmente na primeira vez (Método 1)

### Problema: "Artifact not found"

**Solução:**
- Isso é normal na primeira execução
- O workflow vai criar o artifact automaticamente
- Execuções seguintes vão baixar o artifact

### Problema: Busca tem filtros vazios

**Solução:**
- Configure os filtros na app Streamlit
- Salve novamente como "Biogerm"
- Execute o Método 2 para sincronizar novamente

## 📝 Notas Importantes

1. **O banco está no `.gitignore`** - não será commitado normalmente
2. **O Método 2 faz commit temporário** - o banco fica no histórico do git
3. **Artifacts expiram após 7 dias** (configurado no workflow) - mas são renovados a cada execução
4. **A busca é criada automaticamente na primeira execução** - mas com filtros vazios (processa tudo)

## ✅ Checklist

Antes de ativar a automação diária:

- [ ] Busca "Biogerm" configurada e salva localmente
- [ ] Banco sincronizado com GitHub (Método 1 ou 2)
- [ ] Workflow executado manualmente uma vez para testar
- [ ] Logs mostram que a busca foi encontrada
- [ ] Filtros estão corretos (não vazios)
- [ ] HubSpot token configurado nos secrets do GitHub
- [ ] Workflow agendado para rodar diariamente às 17:30 UTC

---

**Pronto!** 🎉 A automação diária deve funcionar agora!

