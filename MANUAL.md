# Manual de Usuário - Ponto Digital

Este manual detalha como utilizar as funcionalidades do sistema Ponto Digital, tanto da perspectiva do funcionário quanto do administrador.

---

## 1. Para o Funcionário

### 1.1. Batendo o Ponto (Quiosque)

A interface principal para o registro de ponto é o arquivo `index.html`.

1.  **Iniciar:** A tela inicial exibe a data e hora. Toque em qualquer lugar para começar.
2.  **Posicionamento:** A câmera será ativada. Posicione seu rosto dentro da marcação oval no centro da tela.
3.  **Captura Automática:** O sistema iniciará uma contagem regressiva de 3 segundos e, em seguida, capturará uma série de fotos automaticamente. Mantenha-se parado e olhando para a câmera.
4.  **Confirmação:**
    -   **Sucesso:** Se seu rosto for reconhecido, uma mensagem de sucesso aparecerá com uma saudação, e o sistema voltará para a tela inicial após alguns segundos.
    -   **Falha:** Se não for reconhecido, uma mensagem de erro será exibida. Clique em "Tentar Novamente" para reiniciar o processo.

### 1.2. Consultando Seus Registros

Para consultar seu histórico, acesse o arquivo `login.html`.

1.  **Acesso:** Selecione a aba "Funcionário".
2.  **Login:** Digite seu nome completo, exatamente como foi cadastrado pelo administrador, e clique em "Ver Meus Registros".
3.  **Visualização:** Você será redirecionado para sua área pessoal, onde poderá ver:
    -   **Histórico Simples:** Uma lista de todos os seus registros de ponto.
    -   **Banco de Horas:** Uma aba com um relatório detalhado do seu saldo de horas mensal. Você pode selecionar o mês desejado para ver o extrato.

---

## 2. Para o Administrador

O painel administrativo (`admin.html`) é o centro de controle do sistema.

### 2.1. Acesso ao Painel

1.  **Acesso:** Abra o arquivo `login.html` e selecione a aba "Administrador".
2.  **Senha:** A senha padrão é `123456`. Digite-a e clique em "Entrar no Painel".
    -   **Importante:** É altamente recomendável alterar a senha padrão na seção "Configurações" após o primeiro acesso.
    -   **Modo Demo:** Se o painel for acessado sem conexão com o servidor, ele entrará em "Modo de Demonstração", permitindo a navegação pela interface com dados de exemplo.

### 2.2. Dashboard (Visão Geral)

A tela inicial do painel administrativo oferece uma visão geral do sistema:

-   **Cards de Status:** Mostram o total de funcionários cadastrados e o número de registros feitos no dia.
-   **Alertas:**
    -   **Funcionários Ausentes:** Lista os funcionários que ainda não bateram o ponto no dia. Permite enviar um lembrete por e-mail (requer configuração SMTP).
    -   **Registros Incompletos:** Alerta sobre dias (nos últimos 7 dias) em que um funcionário tem um número ímpar de registros (ex: esqueceu de bater a saída). Clicar em "Ver" leva diretamente para os registros do dia em questão.
-   **Gráficos:**
    -   **Frequência Semanal:** Gráfico de barras com o total de registros por dia na última semana.
    -   **Pontualidade Hoje:** Gráfico de pizza mostrando a proporção de funcionários que registraram o ponto no horário, atrasados ou que estão ausentes.
-   **Últimos Registros:** Uma tabela com os 5 registros de ponto mais recentes.

### 2.3. Gerenciando Funcionários

Nesta seção, você pode gerenciar a base de colaboradores.

-   **Cadastrar Novo Funcionário:**
    1.  Clique em "Novo Funcionário".
    2.  Preencha o nome, cargo e e-mail.
    3.  Para a foto, você pode "Abrir Câmera" para tirar uma foto na hora ou "Upload" para enviar um arquivo de imagem.
    4.  Clique em "Salvar Funcionário".
-   **Editar/Excluir:** Na lista de funcionários, use os ícones de lápis (editar) ou lixeira (excluir) para gerenciar um cadastro existente.
-   **Ver Perfil:** Clique no nome de um funcionário para acessar sua página de perfil, que contém seu histórico completo de pontos e o relatório de banco de horas.

### 2.4. Histórico de Pontos (Registros)

Esta tela exibe todos os registros de ponto de todos os funcionários e oferece ferramentas poderosas:

-   **Filtrar:** Use os campos de "Data Início" and "Data Fim" para buscar registros em um período específico.
-   **Editar um Registro:** Clique no ícone de lápis ao lado de um registro para abrir a janela de edição. Você pode ajustar a data e a hora ou adicionar uma observação (ex: "Ajuste manual por esquecimento.").
-   **Exportar Dados:** Após filtrar o período desejado, você pode exportar os dados nos formatos **CSV**, **Excel (XLS)** ou **PDF**, ideal para relatórios e contabilidade.

### 2.5. Configurações

Personalize o funcionamento do sistema.

-   **Aparência:** Ative ou desative o "Modo Escuro" para a interface.
-   **Configurações Gerais:**
    -   **Horário Limite para Atraso:** Defina o horário a partir do qual um registro é considerado "atrasado" no gráfico de pontualidade do dashboard.
    -   **Jornada de Trabalho Diária:** Informe a carga horária padrão (em horas, ex: `8` ou `7.5` para 7h30) para que o sistema calcule corretamente o banco de horas.
-   **Configurações de Segurança:**
    -   **Alterar Senha de Administrador:** Altere a senha de acesso ao painel.
    -   **Configuração SMTP:** Preencha os dados do seu servidor de e-mail (servidor, porta, e-mail e senha) para habilitar o envio de lembretes de ponto para funcionários ausentes.

### 2.6. Manual

Esta seção dentro do painel oferece um resumo rápido das funcionalidades, servindo como um guia de referência ágil.

---

## 3. Solução de Problemas Comuns

-   **"Rosto não reconhecido"**:
    -   Verifique se a iluminação do ambiente está adequada.
    -   Tente se aproximar ou afastar um pouco da câmera.
    -   Certifique-se de que não há acessórios cobrindo o rosto (óculos de sol, boné muito baixo).
    -   Se o problema persistir, peça ao administrador para verificar se a sua foto de cadastro está nítida e atual.

-   **"Erro de conexão com o servidor"**:
    -   Verifique se o script `app.py` está em execução no terminal do servidor.
    -   Confirme se o computador/quiosque está na mesma rede que o servidor.
    -   Verifique se nenhum firewall está bloqueando a porta `5000`.