# Ponto Digital com Reconhecimento Facial

Este é um sistema de ponto eletrônico web moderno que utiliza reconhecimento facial para registrar a entrada e saída de funcionários. O sistema é composto por um backend em Python (Flask) e um frontend responsivo em HTML/JS com Tailwind CSS, projetado para ser executado em um quiosque (como um tablet) e gerenciado por um painel administrativo completo.

## 🚀 Funcionalidades

- **Reconhecimento Facial:** Registro de ponto automático ao reconhecer o rosto do funcionário.
- **Captura Automática:** O sistema detecta e captura fotos automaticamente após uma contagem regressiva.
- **Painel Administrativo Completo:**
  - Dashboard com visão geral (total de funcionários, registros do dia, gráficos de frequência e pontualidade).
  - Alertas para funcionários ausentes e registros de ponto incompletos.
  - Gestão de funcionários (cadastro com foto, edição, exclusão).
  - Histórico de ponto com filtros, edição manual de registros e exportação (CSV, Excel, PDF).
  - Relatório de Banco de Horas por funcionário.
  - Configurações do sistema (modo escuro, jornada de trabalho, senha do admin, SMTP).
- **Área do Funcionário:**
  - Login individual para consulta de histórico de ponto.
  - Acesso ao relatório de banco de horas.
- **Modo Offline/Demo:**
  - O painel administrativo permite acesso para demonstração mesmo sem conexão com o backend.
  - O cadastro de funcionários funciona offline, com sincronização posterior.

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python, Flask, SQLite, face_recognition, NumPy.
- **Frontend:** HTML5, JavaScript, Tailwind CSS (via CDN).

## 📋 Pré-requisitos

Antes de começar, você precisa ter instalado:
1. **Python 3.x**: [Download Python](https://www.python.org/downloads/)
2. **CMake**: Necessário para compilar a biblioteca `dlib` (dependência do `face_recognition`).
   - *Windows:* Instale o "Build Tools for Visual Studio" (ou a versão completa do Visual Studio) com a carga de trabalho "Desenvolvimento para desktop com C++".
   - *Linux:* `sudo apt-get install cmake`

## 🔧 Instalação

1. **Clone ou baixe este projeto** para uma pasta local (ex: `Documents\ponto`).

2. **Crie a pasta para as fotos:**
   No mesmo diretório do `app.py`, crie uma pasta chamada `known_faces`. É aqui que as fotos dos funcionários serão salvas.

3. **Instale as dependências do Python:**
   Abra o terminal na pasta do projeto e execute:
   ```bash
   pip install Flask face_recognition numpy flask_cors Pillow
   ```

## ▶️ Como Executar

### 1. Iniciar o Servidor (Backend)
Abra o terminal na pasta do projeto e execute:
```bash
python app.py
```
O servidor iniciará e ficará aguardando conexões. Você verá mensagens como `Running on http://0.0.0.0:5000`.

### 2. Acessar o Sistema (Frontend)
Você pode abrir os arquivos HTML diretamente no seu navegador (clique duplo ou arraste para o Chrome/Edge):

- **`index.html` (Quiosque de Ponto):**
  - Tela principal onde os funcionários batem o ponto.
  - Toque na tela para iniciar a câmera.
  - O sistema tira 3 fotos automaticamente e tenta reconhecer o rosto.

- **`admin.html` (Painel Administrativo):**
  - Gerencie funcionários e veja estatísticas.
  - **Senha padrão:** `123456`
  - Permite cadastrar novos funcionários tirando foto na hora ou enviando arquivo.

- **`funcionario.html` (Área do Funcionário):**
  - O funcionário digita seu nome para ver seus registros passados.

## 📝 Notas Importantes
- O navegador pedirá permissão para acessar a câmera. É necessário permitir para que o sistema funcione.
- Para o reconhecimento funcionar, o funcionário deve ser cadastrado previamente pelo painel administrativo com uma foto de rosto clara.