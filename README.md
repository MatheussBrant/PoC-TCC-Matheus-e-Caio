# PoC-TCC-Matheus-e-Caio

PoC para avaliar correções de vulnerabilidades Python geradas por LLM, combinando Bandit, chamadas à API da OpenAI, testes automatizados e métricas de avaliação.

## Casos avaliados

```text
V01 - SQL Injection simples
V02 - SQL Injection complexa
V03 - IDOR/BOLA
```

## Requisitos

- Python 3
- `pip`
- chave da API da OpenAI

As dependências do projeto estão em `requirements.txt`.

## Preparar o ambiente

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configurar variáveis de ambiente

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Edite o `.env`:

```text
OPENAI_API_KEY=<sua_chave>
OPENAI_MODEL=gpt-4.1-mini
BANDIT_CMD=bandit
```

Se o comando `bandit` não estiver disponível no terminal, use o caminho do ambiente virtual:

```text
BANDIT_CMD=.venv/bin/bandit
```

## Rodar o pipeline completo

Execute a partir da raiz do projeto:

```bash
python scripts/run_pipeline.py
```

O pipeline executa:

```text
1. Bandit antes da correção
2. Construção dos prompts
3. Chamada à LLM
4. Salvamento do código corrigido
5. Bandit depois da correção
6. Execução dos testes automatizados
7. Consolidação das execuções
8. Cálculo das métricas
```

Estratégias de prompt:

```text
P1 = prompt simples
P2 = raciocínio guiado
P3 = RAG com contexto recuperado e achado SAST
P4 = RAG com contexto recuperado, achado SAST e raciocínio guiado
```

## Regerar CSVs e métricas sem chamar a LLM

Quando `outputs/resultados/execucoes.json` já existir, gere novamente os CSVs e as métricas com:

```bash
python scripts/summarize_results.py
```

Esse comando não chama a LLM. Ele apenas recalcula os campos derivados e regrava os arquivos consolidados.

## Artefatos gerados

Os artefatos seguem o padrão:

```text
<CASO>_<OWASP>_<VULN>_<PROMPT>_<EXECUCAO>_<ARTEFATO>.<extensao>
```

Exemplos:

```text
outputs/bandit_antes/V01_A05_SQLI_BASE_E01_sast_antes.json
outputs/codigos_corrigidos/V01_A05_SQLI_P1_E01_codigo.py
outputs/bandit_depois/V01_A05_SQLI_P1_E01_sast_depois.json
outputs/testes/V01_A05_SQLI_P1_E01_testes.json
```

O diretório `outputs/resultados/` contém apenas arquivos consolidados:

```text
execucoes.json
execucoes.csv
metricas.json
metricas.csv
metricas_por_prompt.csv
metricas_por_caso.csv
```

O pipeline não gera JSON individual por tentativa em `outputs/resultados/`.

## Métricas calculadas

Para cada tentativa:

```text
S_i = 1 se a issue original deixou de ser detectada após a correção
T_i = 1 se todos os testes passaram
N_i = 1 se nenhuma nova issue foi introduzida
```

A correção adequada é:

```text
correcao_adequada = (issue_sumiu ou nao_havia_issue_inicial) and T_i and N_i
```

Quando o Bandit não detecta issue antes da correção, a correção pode ser
considerada adequada pelos testes automatizados, desde que eles passem e nenhuma
nova issue seja introduzida. Nesses casos, `S_i` permanece `0`, pois não havia
issue SAST inicial a remover, mas `correcao_adequada` pode ser `true`.

Métricas agregadas:

```text
TCBS  = Taxa de Correção Bem-Sucedida
TRI   = Taxa de Remoção de Issues
TPF   = Taxa de Preservação Funcional
TNINI = Taxa de Não Introdução de Novas Issues
TFF   = Taxa de Falha Funcional
```

Todas variam entre `0` e `1`. Para `TCBS`, `TRI`, `TPF` e `TNINI`, quanto maior, melhor. Para `TFF`, quanto menor, melhor.

## Scripts principais

```text
scripts/artifact_naming.py   -> metadados dos casos e nomes dos artefatos
scripts/bandit_client.py     -> execução do Bandit
scripts/calculate_metrics.py -> cálculo das métricas
scripts/openai_client.py     -> chamada à API da OpenAI
scripts/prompt_builder.py    -> montagem dos prompts
scripts/run_pipeline.py      -> execução completa da PoC
scripts/run_tests.py         -> execução dos testes sobre códigos corrigidos
scripts/summarize_results.py -> regeneração dos CSVs e métricas
```
