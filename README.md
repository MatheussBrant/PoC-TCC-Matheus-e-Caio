# PoC-TCC-Matheus-e-Caio

PoC para avaliar correções de vulnerabilidades Python geradas por LLM.

O pipeline principal usa Bandit como ferramenta SAST para analisar os códigos
antes e depois das correções, executa os testes automatizados e consolida os
resultados em `outputs/resultados/`.

Casos atuais:

* V01 - SQL Injection simples
* V02 - SQL Injection complexa
* V03 - IDOR/BOLA
