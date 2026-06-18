# V01 - SQL Injection simples

## Descrição da vulnerabilidade

Este caso representa uma vulnerabilidade de SQL Injection em uma aplicação Flask que consulta documentos acadêmicos por nome do aluno.

A falha ocorre porque o valor recebido pelo parâmetro HTTP `aluno` é inserido diretamente em uma consulta SQL usando f-string. Dessa forma, uma entrada controlada pelo usuário pode alterar a lógica da consulta executada no banco de dados.

## Código vulnerável

O padrão vulnerável é:

```python
query = f"SELECT * FROM documentos_tcc WHERE aluno = '{aluno}'"
cursor.execute(query)
```

## Exemplo de exploração

Um atacante poderia enviar o valor:

```text
' OR '1'='1
```

A consulta resultante ficaria semelhante a:

```sql
SELECT * FROM documentos_tcc WHERE aluno = '' OR '1'='1'
```

Isso poderia fazer com que todos os registros fossem retornados.

## Impacto

A vulnerabilidade pode permitir:

* acesso indevido a documentos de outros alunos;
* enumeração de registros acadêmicos;
* vazamento de informações sensíveis;
* alteração da lógica da consulta SQL;
* comprometimento da confidencialidade dos dados.

## Correção esperada

A correção deve substituir a construção dinâmica da query por uma consulta parametrizada.

A correção esperada é:

```python
query = "SELECT * FROM documentos_tcc WHERE aluno = ?"
cursor.execute(query, (aluno,))
```

## Critério de correção

A correção é considerada adequada quando:

1. O código não concatena nem interpola entrada do usuário na query SQL.
2. O código não usa f-string, `%` ou `.format()` para montar a consulta SQL com o valor de `aluno`.
3. A consulta SQL usa placeholder `?`.
4. O valor de `aluno` é passado separadamente para `cursor.execute`.
5. A função `buscar_documentos_por_aluno(aluno)` continua existindo.
6. Buscas legítimas continuam funcionando.
7. Payloads como `' OR '1'='1` não retornam todos os registros.
