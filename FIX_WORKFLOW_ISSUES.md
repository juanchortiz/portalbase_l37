# 🔧 Como Corrigir os Problemas do Workflow

## ✅ Status Atual

Baseado nos logs, o workflow **funcionou parcialmente**:

- ✅ Workflow executou com sucesso
- ✅ Busca "Biogerm" foi criada automaticamente (mas com filtros vazios)
- ✅ 146 novos anúncios encontrados
- ❌ HubSpot token não configurado → deals não foram criados
- ⚠️ Busca "Biogerm" local não está no GitHub Actions

---

## 🔴 Problema 1: HubSpot Token Não Configurado

### Solução:

1. **Vá para GitHub Secrets:**
   - https://github.com/juanchortiz/portalbase_l37/settings/secrets/actions

2. **Adicione o secret:**
   - Nome: `HUBSPOT_API_TOKEN`
   - Valor: Seu token do HubSpot

3. **Onde obter o token:**
   - HubSpot → Settings → Integrations → Private Apps
   - Crie uma Private App ou use um token existente
   - Permissões necessárias: `crm.objects.deals.write`

4. **Teste:**
   - Execute o workflow novamente
   - Deve criar deals agora

---

## 🔴 Problema 2: Busca "Biogerm" Local Não Está no GitHub Actions

### Situação:

- ✅ Você criou a busca "Biogerm" na app Streamlit **localmente**
- ❌ O banco local (2GB) não foi sincronizado com GitHub Actions
- ✅ O workflow criou uma busca "Biogerm" **automaticamente** (mas com filtros vazios)

### Solução: Sincronizar a Busca

**Opção A: Usar o banco do GitHub Actions (Recomendado)**

A busca "Biogerm" já existe no banco do GitHub Actions (criada automaticamente), mas com filtros vazios. Você precisa:

1. **Configurar os filtros na app Streamlit localmente:**
   - Abra a app
   - Configure CPVs, keywords, location, etc.
   - Salve como "Biogerm" (sobrescreve a busca existente)

2. **Sincronizar apenas a busca (não o banco inteiro):**
   ```bash
   # Criar script que exporta/importa apenas a busca
   python sync_search_only.py
   ```
   *(Vou criar este script)*

**Opção B: Sincronizar o banco completo (NÃO recomendado - 2GB é muito grande)**

O banco local tem 2GB, o que é muito grande para fazer commit. Mas se quiser tentar:

```bash
python sync_db_simple.py
```

⚠️ **Aviso:** Isso pode falhar ou ser muito lento devido ao tamanho.

---

## 🎯 Plano de Ação Recomendado

### Passo 1: Configurar HubSpot Token (5 minutos)

1. Vá para: https://github.com/juanchortiz/portalbase_l37/settings/secrets/actions
2. Adicione `HUBSPOT_API_TOKEN` com seu token
3. Execute o workflow novamente para testar

### Passo 2: Configurar Filtros da Busca "Biogerm" (10 minutos)

1. Abra a app Streamlit localmente
2. Configure os filtros:
   - CPV codes (selecionar os relevantes)
   - Keywords (se necessário)
   - Location (se necessário)
   - Fornecedor NIF (se necessário)
3. Salve como "Biogerm"

### Passo 3: Sincronizar a Busca (5 minutos)

Vou criar um script que exporta apenas a busca salva e a importa no banco do GitHub Actions via artifact.

### Passo 4: Testar (2 minutos)

1. Execute o workflow manualmente
2. Verifique os logs:
   - Deve encontrar a busca "Biogerm" com filtros corretos
   - Deve criar deals no HubSpot
   - Deve processar apenas anúncios que atendem aos filtros

---

## 📊 Resumo dos Problemas e Soluções

| Problema | Status | Solução |
|----------|--------|---------|
| HubSpot token não configurado | ❌ | Adicionar `HUBSPOT_API_TOKEN` nos secrets |
| Busca "Biogerm" local não sincronizada | ⚠️ | Sincronizar busca ou configurar no banco do GitHub |
| Filtros vazios (processa tudo) | ⚠️ | Configurar filtros e sincronizar |

---

## ✅ Checklist

- [ ] HubSpot token configurado nos GitHub Secrets
- [ ] Filtros da busca "Biogerm" configurados na app Streamlit
- [ ] Busca sincronizada com GitHub Actions
- [ ] Workflow testado manualmente
- [ ] Deals sendo criados no HubSpot
- [ ] Apenas anúncios relevantes sendo processados

---

**Próximo passo:** Vou criar o script `sync_search_only.py` para sincronizar apenas a busca salva (não o banco inteiro).

