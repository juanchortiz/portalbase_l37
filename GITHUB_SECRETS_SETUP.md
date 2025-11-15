# Como Configurar GitHub Secrets

## Método 1: Interface Web do GitHub (Recomendado)

1. **Acesse seu repositório no GitHub**
   - Vá para: `https://github.com/juanchortiz/portalbase_l37`

2. **Vá para Settings → Secrets and variables → Actions**
   - Clique em "Settings" no topo do repositório
   - No menu lateral, clique em "Secrets and variables"
   - Clique em "Actions"

3. **Adicione cada secret:**
   
   Clique em "New repository secret" e adicione:

   ### Secret 1: BASE_API_KEY
   - **Name:** `BASE_API_KEY`
   - **Secret:** `[SEU_TOKEN_DA_API_BASE_GOV_PT]` (encontre no arquivo `Secrets` local ou no Streamlit Cloud)
   - Clique em "Add secret"

   ### Secret 2: HUBSPOT_API_TOKEN
   - **Name:** `HUBSPOT_API_TOKEN`
   - **Secret:** `[SEU_TOKEN_DO_HUBSPOT]` (encontre no arquivo `Secrets` local ou no HubSpot)
   - Clique em "Add secret"

   ### Secret 3: AUTOMATION_SAVED_SEARCH (Opcional)
   - **Name:** `AUTOMATION_SAVED_SEARCH`
   - **Secret:** `Default Automation`
   - Clique em "Add secret"

   ### Secret 4: DAYS_TO_CHECK (Opcional)
   - **Name:** `DAYS_TO_CHECK`
   - **Secret:** `1`
   - Clique em "Add secret"

4. **Verificar secrets configurados:**
   - Você deve ver todos os secrets listados na página
   - ⚠️ **Importante:** Uma vez adicionados, você não pode ver os valores novamente (apenas editar ou deletar)

## Método 2: Usando GitHub CLI (gh)

Se você tem GitHub CLI instalado:

```bash
# Autenticar com GitHub CLI (use seu próprio GitHub PAT)
gh auth login --with-token <<< "[SEU_GITHUB_PAT]"

# Adicionar secrets (substitua os valores pelos seus tokens reais)
gh secret set BASE_API_KEY --repo juanchortiz/portalbase_l37 --body "[SEU_TOKEN_DA_API_BASE_GOV_PT]"
gh secret set HUBSPOT_API_TOKEN --repo juanchortiz/portalbase_l37 --body "[SEU_TOKEN_DO_HUBSPOT]"
gh secret set AUTOMATION_SAVED_SEARCH --repo juanchortiz/portalbase_l37 --body "Default Automation"
gh secret set DAYS_TO_CHECK --repo juanchortiz/portalbase_l37 --body "1"
```

## Verificar se está funcionando

1. **Fazer push do código:**
   ```bash
   git add .
   git commit -m "Add daily automation workflow"
   git push
   ```

2. **Verificar no GitHub:**
   - Vá para a aba "Actions" do repositório
   - Você verá o workflow "Daily Portal Base Sync"
   - Pode clicar em "Run workflow" para testar manualmente

3. **Ver logs:**
   - Clique no workflow run
   - Veja os logs para verificar se está funcionando

## Troubleshooting

### "Secret not found"
- Verifique que o nome do secret está exatamente correto (case-sensitive)
- Verifique que está no repositório correto

### "Workflow not running"
- Verifique que o arquivo `.github/workflows/daily-sync.yml` está no repositório
- Verifique que fez push do código

### "API key not found"
- Verifique que o secret `BASE_API_KEY` está configurado
- Verifique que o valor está correto (sem espaços extras)

## Segurança

⚠️ **Importante:**
- Nunca commite tokens no código
- Use sempre GitHub Secrets para valores sensíveis
- O arquivo `Secrets` local está no `.gitignore` e não será commitado
- Sempre use placeholders em documentação pública
