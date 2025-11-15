# Atualizar GitHub Secrets para "Biogerm"

## ✅ Passo 1: Atualizar o Secret no GitHub

1. **Acesse as configurações de secrets:**
   - Vá para: https://github.com/juanchortiz/portalbase_l37/settings/secrets/actions

2. **Encontre o secret `AUTOMATION_SAVED_SEARCH`:**
   - Se já existe, clique nele e depois em "Update"
   - Se não existe, clique em "New repository secret"

3. **Configure o secret:**
   - **Name:** `AUTOMATION_SAVED_SEARCH`
   - **Secret:** `Biogerm` (exatamente como está escrito, case-sensitive)
   - Clique em "Update secret" ou "Add secret"

## ✅ Passo 2: Atualizar o Banco de Dados no GitHub Actions

O banco de dados local agora tem a busca "Biogerm", mas o GitHub Actions precisa ter acesso a ela também.

### Opção A: Fazer Upload Manual do Banco (Recomendado)

1. **Execute o workflow manualmente uma vez:**
   - Vá para: https://github.com/juanchortiz/portalbase_l37/actions
   - Clique em "Daily Portal Base Sync"
   - Clique em "Run workflow" → "Run workflow"
   - Isso criará um novo artifact com o banco de dados que inclui "Biogerm"

2. **Ou faça upload do banco atualizado:**
   - O banco `base_cache.db` local agora tem a busca "Biogerm"
   - O GitHub Actions baixará o artifact na próxima execução

### Opção B: Criar a Busca no GitHub Actions (Automático)

O workflow pode criar a busca automaticamente se ela não existir. Mas é melhor garantir que ela já existe.

## ✅ Passo 3: Verificar

Após atualizar o secret, execute o workflow novamente:
- Vá para: https://github.com/juanchortiz/portalbase_l37/actions
- Clique em "Run workflow"
- Verifique os logs para confirmar que encontrou a busca "Biogerm"

## 🔍 Troubleshooting

Se ainda der erro "Saved search 'Biogerm' not found":

1. **Verifique o nome do secret:**
   - Deve ser exatamente `AUTOMATION_SAVED_SEARCH` (case-sensitive)
   - O valor deve ser exatamente `Biogerm` (case-sensitive)

2. **Verifique se o banco tem a busca:**
   - O banco local tem a busca "Biogerm" ✅
   - O GitHub Actions precisa baixar o artifact atualizado

3. **Execute o workflow manualmente:**
   - Isso fará upload do banco atualizado como artifact
   - Próximas execuções usarão esse banco

