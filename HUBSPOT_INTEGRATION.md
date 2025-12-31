# HubSpot Integration Guide

## Overview

This module automatically creates HubSpot deals from Portal Base (Base.gov.pt) announcements, with full company management and data enrichment.

## Features

- ✅ Creates deals from public procurement announcements
- ✅ Finds or creates companies by NIF (Portuguese tax ID)
- ✅ Associates deals with companies automatically
- ✅ Enriches companies with Base.gov.pt contract statistics
- ✅ Uses correct pipeline and stage ("concursos" → "Alerta de publicação da plataforma")

## Deal Properties

| Property | Source | Description |
|----------|--------|-------------|
| `dealname` | `descricaoAnuncio` | Announcement description (max 100 chars) |
| `numero_de_anuncio` | `nAnuncio` | Announcement ID (e.g., 31213/2025) |
| `descricao_do_procedimento` | `descricaoAnuncio` | Full description (max 500 chars) |
| `tipo` | `modeloAnuncio` | Procedure type (e.g., Concurso público) |
| `tipo_anuncio` | `tipoActo` | Announcement type (e.g., Anúncio de procedimento) |
| `entidade_contratante` | `designacaoEntidade` | Contracting entity name |
| `nif_entidade` | `nifEntidade` | Entity NIF |
| `codigos_cpv` | `CPVs` | CPV codes (first 5) |
| `ver_anuncio` | `url` | Link to DR announcement PDF |
| `documentos` | `PecasProcedimento` | Link to tender documents |
| `data_de_publicacao` | `dataPublicacao` | Publication date |
| `data_limite_submissao` | Calculated | Submission deadline |
| `preco_eur` / `amount` | `PrecoBase` | Base price in EUR |
| `local_execucao` | `localExecucao` | Execution location |

## Company Properties

| Property | Source | Description |
|----------|--------|-------------|
| `name` | `designacaoEntidade` | Entity name |
| `nif` | `nifEntidade` | NIF (internal) |
| `num_contrib` | `nifEntidade` | Número de Contribuinte (UI field) |
| `country` | `descPais` | Country (Portugal) |
| `annualrevenue` | `totAdjudicanteValorContratIni` | Total contract value |
| `industry` | Auto | HOSPITAL_HEALTH_CARE or GOVERNMENT_ADMINISTRATION |
| `type` | Auto | PROSPECT |
| `description` | API stats | Contract statistics |
| `observacoes_adicionais` | Auto | Import source note |

## Configuration

### Environment Variables

```bash
HUBSPOT_API_TOKEN=your_token_here
```

### Pipeline Configuration

```python
PIPELINE_NAME = "concursos"
STAGE_NAME = "Alerta de publicação da plataforma"
```

## Key Functions

### `create_deal_from_announcement(announcement, api_token, associate_company=True)`

Creates a HubSpot deal from an announcement. If `associate_company=True`, also finds/creates the contracting entity as a company.

### `find_or_create_company(nif, entity_name, api_token)`

Searches for an existing company by NIF. If not found, creates a new one with enriched data from Base.gov.pt API.

### `check_deal_exists(n_anuncio, api_token)`

Checks if a deal already exists for the given announcement number.

## Saved Search: Biogerm

### Keywords
```
meios de cultura, reagentes, ars centro, serviços análises, 
alimentos análise, legionella, microbiológico
```

### CPV Codes

| Code | Description |
|------|-------------|
| 33696500-0 | Reagentes de laboratório |
| 33000000-0 | Equipamento médico, medicamentos e produtos para cuidados pessoais |
| 24931250-6 | Meios de cultura |
| 33600000-6 | Produtos farmacêuticos |
| 90000000-7 | Serviços relativos a águas residuais, resíduos, limpeza e ambiente |
| 85000000-9 | Serviços saúde e acção social |

## Daily Automation

The `daily-sync.yml` GitHub Action runs daily to:

1. Fetch new announcements from Base.gov.pt
2. Filter by saved search criteria (Biogerm)
3. Create deals in HubSpot "concursos" pipeline
4. Create/associate companies by NIF
5. Skip already-processed announcements

## Price Format

The integration handles Portuguese price format:
- Input: `1.234.567,89` (dots as thousands, comma as decimal)
- Output: `1234567.89` (standard float)

## Troubleshooting

### Deal prices are wrong (100x too high)
The `format_price()` function was fixed to handle Portuguese format. Run the price correction script if needed.

### Company not found by NIF
The system searches by the `nif` property. Make sure the company was created through this integration.

### Duplicate companies
The integration caches company lookups. If duplicates exist, they were likely created manually.
