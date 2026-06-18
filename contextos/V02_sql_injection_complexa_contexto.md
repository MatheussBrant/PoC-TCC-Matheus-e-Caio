# V02 - SQL Injection complexa

## Descrição da vulnerabilidade

Este caso representa uma SQL Injection mais complexa em uma aplicação Flask. A consulta permite que `tabela`, `campo` e `valor` sejam recebidos pela requisição HTTP e usados para montar dinamicamente uma instrução SQL.

A vulnerabilidade não está apenas no valor pesquisado. Como os nomes da tabela e do campo também vêm da entrada do usuário, a correção precisa controlar identificadores SQL e não apenas parametrizar valores.

## Contrato funcional que deve ser preservado

A função pública `buscar_registros(tabela, campo, valor)` deve continuar existindo com a mesma assinatura.

O banco de teste usado nesta PoC possui a tabela:

```sql
CREATE TABLE documentos_tcc (
    id INTEGER PRIMARY KEY,
    titulo TEXT,
    aluno TEXT
)
```

A busca legítima principal usada no experimento é:

```python
buscar_registros(
    tabela="documentos_tcc",
    campo="aluno",
    valor="Matheus"
)
```

Portanto, a correção deve aceitar explicitamente a combinação:

```text
tabela: documentos_tcc
campo: aluno
```

Não invente campos que não existem no schema da PoC, como `autor`, `orientador` ou `ano`.

## Código vulnerável

O padrão vulnerável é:

```python
filtro = montar_filtro(campo, valor)
query = f"SELECT * FROM {tabela} WHERE {filtro}"
cursor.execute(query)
```

## Impacto

A vulnerabilidade pode permitir:

* alteração da lógica da consulta SQL;
* retorno de registros não autorizados;
* consulta a tabelas internas;
* enumeração de dados acadêmicos;
* vazamento de informações sensíveis.

## Correção esperada

A correção deve tratar separadamente cada tipo de entrada:

* `valor` deve ser parametrizado com placeholder `?`;
* `tabela` não deve ser usada livremente;
* `campo` não deve ser usado livremente;
* se a função `buscar_registros(tabela, campo, valor)` for preservada, a melhor correção é usar um mapa de consultas fixas ou uma allowlist rígida de tabelas e campos permitidos;
* para evitar alerta do Bandit, prefira mapa de queries fixas em vez de montar SQL com f-string.

Uma correção compatível com o contrato desta PoC pode usar um mapa fixo como:

```python
CONSULTAS_PERMITIDAS = {
    ("documentos_tcc", "aluno"): "SELECT * FROM documentos_tcc WHERE aluno = ?",
    ("documentos_tcc", "titulo"): "SELECT * FROM documentos_tcc WHERE titulo = ?",
}
```

Depois, o valor deve ser passado separadamente:

```python
cursor.execute(query, (valor,))
```

## Critério de correção

A correção é considerada adequada quando:

1. Valores vindos do usuário são passados separadamente para `cursor.execute`.
2. Tabelas e campos são validados por allowlist rígida ou substituídos por consultas fixas.
3. Entradas maliciosas em `valor` não retornam todos os registros.
4. Tabelas não permitidas são rejeitadas.
5. Campos não permitidos são rejeitados.
6. `buscar_registros("documentos_tcc", "aluno", "Matheus")` retorna apenas o documento de Matheus.
7. `buscar_registros("documentos_tcc", "aluno", "' OR '1'='1")` retorna lista vazia.
8. Tabelas como `sqlite_master` são rejeitadas com `ValueError`.
9. Campos como `1=1 --` são rejeitados com `ValueError`.
