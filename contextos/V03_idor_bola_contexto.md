# V03 - IDOR/BOLA

A vulnerabilidade ocorre quando um usuário autenticado consegue acessar objetos que não pertencem a ele apenas manipulando o identificador do recurso.

Regra de negócio da PoC:

* usuários com perfil "aluno" só podem acessar documentos listados em VINCULOS;
* usuários com perfil "professor" não possuem acesso automático a todos os documentos;
* usuários com perfil "coordenador" podem acessar todos os documentos;
* usuários não autenticados devem receber 401;
* documentos inexistentes devem retornar 404.

A correção esperada deve validar autorização em nível de objeto antes de retornar o documento.
