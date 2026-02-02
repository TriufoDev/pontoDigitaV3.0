# backend/app.py
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import face_recognition
import numpy as np
import base64
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from PIL import Image
import calendar
import io
from flask_cors import CORS # Para permitir requisições do frontend

# --- CONFIGURAÇÃO ---
app = Flask(__name__)
CORS(app) # Habilita o CORS para todas as rotas

DB_FILE = "ponto.db"
KNOWN_FACES_DIR = "known_faces"
CONFIG_FILE = 'config.ini'

# --- GERENCIAMENTO DE CONFIGURAÇÃO E SENHA ---
def get_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config

def save_config(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def init_config():
    """Inicializa o config.ini com uma senha padrão se não existir."""
    if not os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()
        config['ADMIN'] = {'password_hash': generate_password_hash('123456')}
        save_config(config)
        print("Arquivo 'config.ini' criado com senha padrão '123456'.")
# --- BANCO DE DADOS ---
def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            observacao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cargo TEXT,
            email TEXT
        )
    ''')
    # Adiciona a coluna 'observacao' se ela não existir, para não quebrar bancos de dados existentes
    cursor.execute("PRAGMA table_info(registros)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'observacao' not in columns:
        cursor.execute("ALTER TABLE registros ADD COLUMN observacao TEXT")
        print("Coluna 'observacao' adicionada à tabela 'registros'.")
    
    cursor.execute("PRAGMA table_info(funcionarios)")
    columns_func = [info[1] for info in cursor.fetchall()]
    if 'email' not in columns_func:
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN email TEXT")
        print("Coluna 'email' adicionada à tabela 'funcionarios'.")

    conn.commit()
    conn.close()

# --- LÓGICA DE RECONHECIMENTO FACIAL ---
def load_known_faces():
    """Carrega os rostos conhecidos da pasta known_faces."""
    known_face_encodings = []
    known_face_names = []
    print("Carregando rostos conhecidos...")
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.endswith((".jpg", ".png")):
            path = os.path.join(KNOWN_FACES_DIR, filename)
            name = os.path.splitext(filename)[0].replace("_", " ").title()
            
            try:
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(name)
                    print(f"Rosto de {name} carregado com sucesso.")
                else:
                    print(f"AVISO: Nenhum rosto encontrado em {filename}.")
            except Exception as e:
                print(f"Erro ao carregar {filename}: {e}")

    return known_face_encodings, known_face_names

# Carrega os rostos na inicialização do servidor
known_face_encodings, known_face_names = load_known_faces()

# --- ROTAS DA API ---
@app.route('/clock_in', methods=['POST'])
def clock_in():
    """Recebe imagens, tenta reconhecer o rosto em qualquer uma delas e registra o ponto."""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Dados não enviados"}), 400

    # Suporte para lista de imagens ('images') ou única imagem ('image') para compatibilidade
    images_list = []
    if 'images' in data:
        images_list = data['images']
    elif 'image' in data:
        images_list = [data['image']]
    else:
        return jsonify({"status": "error", "message": "Nenhuma imagem enviada"}), 400

    # Itera sobre as imagens recebidas (tentativa múltipla)
    for img_str in images_list:
        try:
            # Decodifica a imagem Base64
            if ',' in img_str:
                img_str = img_str.split(',')[1]
            
            image_data = base64.b64decode(img_str)
            image = Image.open(io.BytesIO(image_data))
            unknown_image_np = np.array(image)

            # Encontra rostos
            face_locations = face_recognition.face_locations(unknown_image_np)
            face_encodings = face_recognition.face_encodings(unknown_image_np, face_locations)

            if not face_encodings:
                continue # Tenta a próxima imagem se não achar rosto nesta

            # Compara com rostos conhecidos
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                    # Registra o ponto no banco de dados
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO registros (nome, timestamp) VALUES (?, ?)", (name, timestamp))
                    conn.commit()
                    conn.close()

                    print(f"Ponto registrado para: {name} em {timestamp}")
                    return jsonify({"status": "success", "message": f"Ponto registrado para {name}!"})
        except Exception as e:
            print(f"Erro ao processar frame: {e}")
            continue

    return jsonify({"status": "error", "message": "Usuário não reconhecido após múltiplas tentativas."})

# --- NOVAS ROTAS ADMINISTRATIVAS ---

@app.route('/api/login/admin', methods=['POST'])
def login_admin():
    data = request.get_json()
    password = data.get('senha')

    if not password:
        return jsonify({"status": "error", "message": "Senha é obrigatória"}), 400

    config = get_config()
    password_hash = config.get('ADMIN', 'password_hash')

    if check_password_hash(password_hash, password):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Senha incorreta"}), 401

@app.route('/api/admin/change-password', methods=['POST'])
def change_admin_password():
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios"}), 400

    config = get_config()
    password_hash = config.get('ADMIN', 'password_hash')

    if not check_password_hash(password_hash, old_password):
        return jsonify({"status": "error", "message": "Senha atual incorreta"}), 401

    config.set('ADMIN', 'password_hash', generate_password_hash(new_password))
    save_config(config)
    return jsonify({"status": "success", "message": "Senha alterada com sucesso!"})

@app.route('/api/admin/smtp-config', methods=['GET', 'POST'])
def manage_smtp_config():
    config = get_config()
    if request.method == 'POST':
        data = request.get_json()
        if 'SMTP' not in config:
            config['SMTP'] = {}
        config['SMTP']['server'] = data.get('server', '')
        config['SMTP']['port'] = data.get('port', '')
        config['SMTP']['email'] = data.get('email', '')
        config['SMTP']['password'] = data.get('password', '')
        save_config(config)
        return jsonify({"status": "success", "message": "Configurações de SMTP salvas!"})
    else:
        smtp_config = {}
        if 'SMTP' in config:
            smtp_config = {k: v for k, v in config['SMTP'].items()}
        return jsonify(smtp_config)

@app.route('/api/admin/settings', methods=['GET', 'POST'])
def manage_general_settings():
    config = get_config()
    if request.method == 'POST':
        data = request.get_json()
        if 'SETTINGS' not in config:
            config['SETTINGS'] = {}
        config['SETTINGS']['late_limit'] = data.get('late_limit', '08:15')
        config['SETTINGS']['workday_hours'] = data.get('workday_hours', '8')
        save_config(config)
        return jsonify({"status": "success", "message": "Configurações gerais salvas!"})
    else:
        settings = {}
        if 'SETTINGS' in config:
            settings = {k: v for k, v in config['SETTINGS'].items()}
        else:
            settings = {'late_limit': '08:15', 'workday_hours': '8'}
        
        if 'workday_hours' not in settings:
            settings['workday_hours'] = '8'

        return jsonify(settings)

@app.route('/api/admin/send-reminder', methods=['POST'])
def send_reminder():
    data = request.get_json()
    nome = data.get('nome')
    email_dest = data.get('email')
    
    if not email_dest:
         return jsonify({"status": "error", "message": "Funcionário sem e-mail cadastrado."}), 400

    config = get_config()
    if 'SMTP' not in config:
        return jsonify({"status": "error", "message": "SMTP não configurado. Vá em Configurações."}), 400
        
    smtp_server = config['SMTP'].get('server')
    smtp_port = config['SMTP'].get('port')
    sender_email = config['SMTP'].get('email')
    sender_password = config['SMTP'].get('password')
    
    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        return jsonify({"status": "error", "message": "Configurações de SMTP incompletas."}), 400

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email_dest
        msg['Subject'] = "Lembrete de Ponto - Ponto Digital"
        
        body = f"Olá {nome},\n\nNotamos que você ainda não registrou seu ponto hoje. Por favor, regularize assim que possível.\n\nAtenciosamente,\nGestão."
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email_dest, text)
        server.quit()
        
        return jsonify({"status": "success", "message": f"Lembrete enviado para {nome}."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro ao enviar e-mail: {str(e)}"}), 500

@app.route('/api/login/funcionario', methods=['POST'])
def login_funcionario():
    data = request.get_json()
    nome = data.get('nome')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM funcionarios WHERE nome = ?", (nome,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({"status": "success", "nome": user[0]})
    return jsonify({"status": "error", "message": "Usuário não encontrado"}), 401

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Retorna dados para o dashboard."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Total de funcionários
    cursor.execute("SELECT COUNT(*) FROM funcionarios")
    total_funcionarios = cursor.fetchone()[0]
    
    # Registros de hoje
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM registros WHERE timestamp LIKE ?", (f'{today}%',))
    registros_hoje = cursor.fetchone()[0]
    
    # Últimos 5 registros
    cursor.execute("SELECT nome, timestamp FROM registros ORDER BY id DESC LIMIT 5")
    ultimos_registros = cursor.fetchall()
    
    # --- Funcionários Ausentes Hoje ---
    cursor.execute("SELECT nome, email FROM funcionarios")
    all_employees_data = cursor.fetchall()
    all_employees_dict = {row[0]: row[1] for row in all_employees_data}

    cursor.execute("SELECT DISTINCT nome FROM registros WHERE timestamp LIKE ?", (f'{today}%',))
    present_employees = [row[0] for row in cursor.fetchall()]

    absent_names = sorted(list(set(all_employees_dict.keys()) - set(present_employees)))
    absent_employees = [{"nome": name, "email": all_employees_dict.get(name)} for name in absent_names]

    # --- Dados do Gráfico (Últimos 7 dias) ---
    seven_days_ago = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
    
    # Consulta agrupada por data (YYYY-MM-DD)
    cursor.execute("""
        SELECT substr(timestamp, 1, 10) as date, COUNT(*) 
        FROM registros 
        WHERE timestamp >= ? 
        GROUP BY date 
        ORDER BY date ASC
    """, (f"{seven_days_ago} 00:00:00",))
    
    daily_counts_db = dict(cursor.fetchall())
    
    chart_labels = []
    chart_values = []
    
    # Garante que todos os 7 dias apareçam, mesmo com 0 registros
    for i in range(7):
        day_date = datetime.now() - timedelta(days=6-i)
        day_str = day_date.strftime('%Y-%m-%d')
        label = day_date.strftime('%d/%m') # Formato DD/MM para o gráfico
        
        chart_labels.append(label)
        chart_values.append(daily_counts_db.get(day_str, 0))

    # --- Dados do Gráfico de Pizza (Pontualidade Hoje) ---
    # Considera 08:15 como limite para atraso (Exemplo)
    config = get_config()
    late_limit_time = "08:15"
    if 'SETTINGS' in config and 'late_limit' in config['SETTINGS']:
        late_limit_time = config['SETTINGS']['late_limit']

    limit_time_str = f"{today} {late_limit_time}:00"
    limit_time = datetime.strptime(limit_time_str, '%Y-%m-%d %H:%M:%S')
    
    cursor.execute("SELECT nome, MIN(timestamp) FROM registros WHERE timestamp LIKE ? GROUP BY nome", (f'{today}%',))
    first_checkins = cursor.fetchall()
    
    on_time = 0
    late = 0
    
    for row in first_checkins:
        try:
            ts = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            if ts <= limit_time:
                on_time += 1
            else:
                late += 1
        except:
            pass
            
    absent = total_funcionarios - (on_time + late)
    if absent < 0: absent = 0

    # --- Registros Incompletos (Últimos 7 dias, exceto hoje) ---
    incomplete_records = []
    start_check_date = datetime.now() - timedelta(days=7)
    end_check_date = datetime.now() - timedelta(days=1)
    
    start_str = start_check_date.strftime('%Y-%m-%d')
    end_str = end_check_date.strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT nome, substr(timestamp, 1, 10) as date, COUNT(*) 
        FROM registros 
        WHERE timestamp >= ? AND timestamp <= ?
        GROUP BY nome, date
    """, (f"{start_str} 00:00:00", f"{end_str} 23:59:59"))
    
    rows = cursor.fetchall()
    for row in rows:
        nome, date, count = row
        if count % 2 != 0:
            incomplete_records.append({"nome": nome, "data": date})

    conn.close()
    return jsonify({
        "total_funcionarios": total_funcionarios,
        "registros_hoje": registros_hoje,
        "ultimos_registros": ultimos_registros,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "funcionarios_ausentes": absent_employees,
        "registros_incompletos": incomplete_records,
        "pie_chart": {
            "labels": ["No Horário", "Atrasado", "Ausente"],
            "values": [on_time, late, absent]
        }
    })

@app.route('/api/funcionarios', methods=['GET', 'POST'])
def manage_funcionarios():
    """Gerencia funcionários (Listar e Criar)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.get_json()
        nome = data.get('nome')
        cargo = data.get('cargo')
        email = data.get('email')
        image_data = data.get('image') # Base64

        if not nome or not image_data:
            return jsonify({"status": "error", "message": "Nome e foto são obrigatórios"}), 400

        # Salvar no Banco
        cursor.execute("INSERT INTO funcionarios (nome, cargo, email) VALUES (?, ?, ?)", (nome, cargo, email))
        conn.commit()
        
        # Salvar Imagem
        try:
            # Remove cabeçalho do base64 se existir
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            img_bytes = base64.b64decode(image_data)
            filename = f"{nome.replace(' ', '_').lower()}.jpg"
            filepath = os.path.join(KNOWN_FACES_DIR, filename)
            
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            
            # Recarregar rostos na memória
            global known_face_encodings, known_face_names
            known_face_encodings, known_face_names = load_known_faces()
            
        except Exception as e:
            return jsonify({"status": "error", "message": f"Erro ao salvar imagem: {str(e)}"}), 500

        conn.close()
        return jsonify({"status": "success", "message": "Funcionário cadastrado com sucesso!"})

    else: # GET
        cursor.execute("SELECT id, nome, cargo, email FROM funcionarios")
        funcionarios = [{"id": row[0], "nome": row[1], "cargo": row[2], "email": row[3]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(funcionarios)

@app.route('/api/funcionarios/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_funcionario(id):
    """Atualiza ou deleta um funcionário."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Pega o nome do funcionário para poder achar o arquivo de imagem
    cursor.execute("SELECT nome FROM funcionarios WHERE id = ?", (id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"status": "error", "message": "Funcionário não encontrado"}), 404
    
    old_name = result[0]
    old_filename = f"{old_name.replace(' ', '_').lower()}.jpg"
    old_filepath = os.path.join(KNOWN_FACES_DIR, old_filename)

    if request.method == 'PUT':
        data = request.get_json()
        new_name = data.get('nome')
        new_cargo = data.get('cargo')
        new_email = data.get('email')

        if not new_name:
            conn.close()
            return jsonify({"status": "error", "message": "Nome é obrigatório"}), 400

        cursor.execute("UPDATE funcionarios SET nome = ?, cargo = ?, email = ? WHERE id = ?", (new_name, new_cargo, new_email, id))
        conn.commit()

        # Se o nome mudou, renomeia o arquivo de imagem e recarrega os rostos
        if new_name != old_name:
            new_filename = f"{new_name.replace(' ', '_').lower()}.jpg"
            new_filepath = os.path.join(KNOWN_FACES_DIR, new_filename)
            try:
                if os.path.exists(old_filepath):
                    os.rename(old_filepath, new_filepath)
                
                # Recarregar rostos na memória
                global known_face_encodings, known_face_names
                known_face_encodings, known_face_names = load_known_faces()
            except Exception as e:
                print(f"Erro ao renomear arquivo de imagem: {e}")

        conn.close()
        return jsonify({"status": "success", "message": "Funcionário atualizado"})

    if request.method == 'DELETE':
        # Remove do banco
        cursor.execute("DELETE FROM funcionarios WHERE id = ?", (id,))
        # Também remove os registros de ponto associados
        cursor.execute("DELETE FROM registros WHERE nome = ?", (old_name,))
        conn.commit()
        
        # Deleta o arquivo de imagem
        try:
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
                # Recarregar rostos na memória
                global known_face_encodings, known_face_names
                known_face_encodings, known_face_names = load_known_faces()
                print(f"Imagem {old_filename} removida.")
        except Exception as e:
            print(f"Erro ao remover imagem {old_filename}: {e}")

        conn.close()
        return jsonify({"status": "success", "message": "Funcionário e seus registros foram removidos"})
        
@app.route('/api/funcionarios/<int:id>/profile', methods=['GET'])
def get_employee_profile(id):
    """Retorna o perfil completo de um funcionário."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Buscar dados do funcionário
    cursor.execute("SELECT id, nome, cargo, email FROM funcionarios WHERE id = ?", (id,))
    funcionario_data = cursor.fetchone()
    if not funcionario_data:
        conn.close()
        return jsonify({"status": "error", "message": "Funcionário não encontrado"}), 404

    funcionario = {
        "id": funcionario_data[0],
        "nome": funcionario_data[1],
        "cargo": funcionario_data[2],
        "email": funcionario_data[3]
    }

    # Buscar registros do funcionário
    cursor.execute("SELECT timestamp, observacao FROM registros WHERE nome = ? ORDER BY timestamp DESC", (funcionario['nome'],))
    registros_data = cursor.fetchall()
    registros = [{"timestamp": row[0], "observacao": row[1]} for row in registros_data]

    conn.close()

    return jsonify({
        "funcionario": funcionario,
        "registros": registros
    })

@app.route('/api/report/employee', methods=['GET'])
def get_employee_report_data():
    """Retorna os registros de um funcionário para um mês específico."""
    employee_name = request.args.get('name')
    month = request.args.get('month') # Esperado no formato 'YYYY-MM'

    if not employee_name or not month:
        return jsonify({"status": "error", "message": "Nome do funcionário e mês são obrigatórios"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Usar LIKE para pegar todos os dias do mês
    query = "SELECT timestamp FROM registros WHERE nome = ? AND timestamp LIKE ? ORDER BY timestamp ASC"
    params = (employee_name, f'{month}%')
    
    cursor.execute(query, params)
    registros = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(registros)

def format_timedelta(td):
    """Formats a timedelta object into a signed HH:MM string."""
    if td is None:
        return "00:00"
    total_seconds = int(td.total_seconds())
    sign = '-' if total_seconds < 0 else '+'
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"

@app.route('/api/report/time-bank', methods=['GET'])
def get_time_bank():
    employee_name = request.args.get('name')
    month = request.args.get('month') # YYYY-MM

    if not employee_name or not month:
        return jsonify({"status": "error", "message": "Nome do funcionário e mês são obrigatórios"}), 400

    config = get_config()
    workday_hours_str = config.get('SETTINGS', 'workday_hours', fallback='8')
    try:
        workday_hours = float(workday_hours_str)
    except ValueError:
        workday_hours = 8.0
    
    standard_workday = timedelta(hours=workday_hours)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    query = "SELECT timestamp FROM registros WHERE nome = ? AND timestamp LIKE ? ORDER BY timestamp ASC"
    params = (employee_name, f'{month}%')
    
    cursor.execute(query, params)
    registros = [datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') for row in cursor.fetchall()]
    conn.close()

    from collections import defaultdict
    daily_records = defaultdict(list)
    for reg in registros:
        daily_records[reg.date()].append(reg)

    daily_summary = []
    total_balance = timedelta(0)

    year, month_num = map(int, month.split('-'))
    num_days = calendar.monthrange(year, month_num)[1]

    for day_num in range(1, num_days + 1):
        current_date = datetime(year, month_num, day_num).date()
        day_records = sorted(daily_records.get(current_date, []))
        
        day_info = {
            "date": current_date.strftime('%Y-%m-%d'),
            "worked_duration": timedelta(0),
            "balance": None,
            "status": "Folga"
        }

        if day_records:
            if len(day_records) % 2 == 0:
                worked_today = timedelta(0)
                for i in range(0, len(day_records), 2):
                    worked_today += (day_records[i+1] - day_records[i])
                
                day_info["worked_duration"] = worked_today
                if current_date.weekday() < 5: # Mon-Fri
                    day_balance = worked_today - standard_workday
                    total_balance += day_balance
                    day_info["balance"] = day_balance
                    day_info["status"] = "Completo"
                else:
                    total_balance += worked_today
                    day_info["balance"] = worked_today
                    day_info["status"] = "Fim de Semana"
            else:
                day_info["status"] = "Incompleto"
        
        day_info["worked_hours"] = format_timedelta(day_info["worked_duration"])
        day_info["balance_hours"] = format_timedelta(day_info["balance"])
        del day_info["worked_duration"]
        del day_info["balance"]
        
        daily_summary.append(day_info)

    return jsonify({
        "total_balance_hours": format_timedelta(total_balance),
        "daily_summary": daily_summary
    })

@app.route('/api/registros/<nome>', methods=['GET'])
def get_historico_funcionario(nome):
    """Retorna o histórico de pontos de um funcionário específico."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp FROM registros WHERE nome = ? ORDER BY id DESC", (nome,))
    registros = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(registros)

@app.route('/api/registros', methods=['GET'])
def get_all_registros():
    """Retorna registros. Se 'page' for fornecido, retorna paginado. Caso contrário, retorna todos."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    base_query = "FROM registros"
    params = []
    where_clauses = []

    if start_date:
        where_clauses.append("timestamp >= ?")
        params.append(f"{start_date} 00:00:00")

    if end_date:
        where_clauses.append("timestamp <= ?")
        params.append(f"{end_date} 23:59:59")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    # Se paginação for solicitada
    if page is not None:
        # Conta total de registros
        cursor.execute(f"SELECT COUNT(*) {base_query}", params)
        total_records = cursor.fetchone()[0]

        # Busca dados da página
        offset = (page - 1) * per_page
        cursor.execute(f"SELECT id, nome, timestamp, observacao {base_query} ORDER BY id DESC LIMIT ? OFFSET ?", params + [per_page, offset])
        registros = [{"id": row[0], "nome": row[1], "timestamp": row[2], "observacao": row[3]} for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({
            "data": registros,
            "total": total_records,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_records + per_page - 1) // per_page
        })
    else:
        # Retorna tudo (para exportação)
        cursor.execute(f"SELECT id, nome, timestamp, observacao {base_query} ORDER BY id DESC", params)
        registros = [{"id": row[0], "nome": row[1], "timestamp": row[2], "observacao": row[3]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(registros)

@app.route('/api/registros/<int:id>', methods=['PUT', 'DELETE'])
def manage_registro(id):
    """Permite que um admin edite ou delete um registro de ponto específico."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if request.method == 'PUT':
        data = request.get_json()
        new_timestamp = data.get('timestamp')
        observacao = data.get('observacao')

        if not new_timestamp:
            conn.close()
            return jsonify({"status": "error", "message": "Timestamp é obrigatório"}), 400
        
        try:
            # Valida o formato do timestamp
            datetime.strptime(new_timestamp, '%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE registros SET timestamp = ?, observacao = ? WHERE id = ?", (new_timestamp, observacao, id))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "Registro atualizado"})
        except ValueError:
            conn.close()
            return jsonify({"status": "error", "message": "Formato de timestamp inválido. Use YYYY-MM-DD HH:MM:SS"}), 400
        except Exception as e:
            conn.close()
            return jsonify({"status": "error", "message": f"Erro ao atualizar: {e}"}), 500

    if request.method == 'DELETE':
        cursor.execute("DELETE FROM registros WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Registro removido"})


if __name__ == '__main__':
    init_config()
    init_db()
    # O host='0.0.0.0' permite que o servidor seja acessível na sua rede local
    app.run(host='0.0.0.0', port=5000, debug=True)
