# Contexto — SQL Injection

A vulnerabilidade ocorre quando entradas não confiáveis são usadas para montar consultas SQL.

Neste cenário, o usuário controla:
- valor pesquisado;
- nome do campo;
- nome da tabela.

Correção esperada:
- usar consultas parametrizadas para valores;
- não concatenar diretamente valores vindos do usuário;
- validar nomes de tabelas por allowlist;
- validar nomes de campos por allowlist;
- rejeitar campos ou tabelas não previstos pela aplicação.

Apenas parametrizar o valor não é suficiente, porque campo e tabela também são controlados pela requisição.
