def montar_prompt_simples(codigo: str) -> str:
    return f"""
Analise o trecho de código abaixo, identifique a vulnerabilidade de segurança e gere uma versão corrigida.

Responda apenas em JSON válido com os campos:
{{
"vulnerabilidade": "",
"explicacao": "",
"codigo_corrigido": "",
"justificativa": ""
}}

Código vulnerável:

```python
{codigo}
```

"""


def montar_prompt_raciocinio_guiado(codigo: str) -> str:
    return f"""
Analise o trecho de código abaixo seguindo estas etapas:

1. Identifique a vulnerabilidade.
2. Explique a causa da vulnerabilidade.
3. Descreva o impacto de segurança.
4. Gere uma versão corrigida do código.
5. Justifique por que a correção remove a vulnerabilidade.
6. Informe possíveis cuidados adicionais.

Responda apenas em JSON válido com os campos:
{{
"vulnerabilidade": "",
"causa": "",
"impacto": "",
"codigo_corrigido": "",
"justificativa": "",
"cuidados_adicionais": ""
}}

Código vulnerável:

```python
{codigo}
```

"""


def formatar_issue_sast(issue_sast: dict) -> str:
    return f"""
Tipo: {issue_sast.get("tipo", "")}
Severidade: {issue_sast.get("severidade", "")}
Arquivo: {issue_sast.get("arquivo", "")}
Linha: {issue_sast.get("linha", "")}
Mensagem: {issue_sast.get("mensagem", "")}
Regra: {issue_sast.get("regra", "")}
""".strip()


def montar_prompt_rag(codigo: str, issue_sast: dict, contexto: str) -> str:
    return f"""
Você é um assistente especializado em correção segura de código.

Use o contexto recuperado por RAG e o achado da ferramenta SAST para corrigir a vulnerabilidade.

Achado SAST:
{formatar_issue_sast(issue_sast)}

Contexto recuperado por RAG:
{contexto}

Tarefa:
Corrija o código abaixo considerando o contexto recuperado e o achado SAST.

Responda apenas em JSON válido com os campos:
{{
"vulnerabilidade": "",
"explicacao": "",
"codigo_corrigido": "",
"justificativa": "",
"cuidados_adicionais": ""
}}

Código vulnerável:

```python
{codigo}
```

"""


def montar_prompt_rag_raciocinio_guiado(codigo: str, issue_sast: dict, contexto: str) -> str:
    return f"""
Você é um assistente especializado em correção segura de código.

Use o contexto recuperado por RAG e o achado da ferramenta SAST para corrigir a vulnerabilidade.

Achado SAST:
{formatar_issue_sast(issue_sast)}

Contexto recuperado por RAG:
{contexto}

Analise o trecho de código abaixo seguindo estas etapas:

1. Identifique a vulnerabilidade com base no código, no contexto recuperado e no achado SAST.
2. Explique a causa da vulnerabilidade.
3. Descreva o impacto de segurança.
4. Gere uma versão corrigida do código.
5. Justifique por que a correção remove a vulnerabilidade.
6. Informe possíveis cuidados adicionais.

Responda apenas em JSON válido com os campos:
{{
"vulnerabilidade": "",
"causa": "",
"impacto": "",
"codigo_corrigido": "",
"justificativa": "",
"cuidados_adicionais": ""
}}

Código vulnerável:

```python
{codigo}
```

"""
