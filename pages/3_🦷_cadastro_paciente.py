import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import re

# ==========================
# 🎨 CONFIGURAÇÃO E DESIGN FAO/UFAM
# ==========================
st.set_page_config(
    page_title="Cadastro de Pacientes - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS de Alta Fidelidade (Inter Font + Blue Gradient)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Reset de Fonte Global */
        html, body, [class*="css"], .stMarkdown { font-family: 'Inter', sans-serif !important; }

        /* Cabeçalho Institucional */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%) !important;
            padding: 1.5rem 2rem !important;
            border-radius: 15px !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 4px 15px rgba(0,74,153,0.2) !important;
            color: white !important;
        }
        .main-header h1 { 
            color: white !important; 
            font-weight: 700 !important; 
            font-size: 1.8rem !important; 
            margin: 0 !important;
            border: none !important;
        }

        /* Títulos de Seção */
        .section-title {
            font-size: 1rem !important;
            font-weight: 700 !important;
            color: #004a99 !important;
            text-transform: uppercase !important;
            margin-bottom: 15px !important;
            border-left: 4px solid #004a99 !important;
            padding-left: 10px !important;
        }

        /* Estilização de Botões */
        .stButton > button {
            background-color: #004a99 !important;
            color: white !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            height: 45px !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background-color: #003366 !important;
            box-shadow: 0 4px 10px rgba(0,74,153,0.3) !important;
        }

        /* Estilo dos Cards (Expanders) */
        .stExpander {
            background-color: #f8fafc !important;
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
            margin-bottom: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------ Sidebar Institucional ------------------
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.caption("Sistema de Gestão de Prontuários")
    st.markdown("<br>", unsafe_allow_html=True)

# ------------------ Google Sheets ------------------
def conectar_planilha():
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    service_account_info = {k: v.replace('\\n','\n') if k=="private_key" else v for k,v in st.secrets["gcp_service_account"].items()}
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").sheet1

def gerar_proximo_id(sheet):
    dados = sheet.get_all_values()
    if len(dados) <= 1:
        return 1
    ids = [int(row[0]) for row in dados[1:] if row[0].isdigit()]
    return max(ids) + 1 if ids else 1

def calcular_idade(data_nasc):
    hoje = datetime.date.today()
    return hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))

# ------------------ Inicializar session_state ------------------
campos = ["nome","fao","data","sexo","filiacao","endereco","telefone","tipo_fissura","historia"]
for campo in campos:
    if campo not in st.session_state:
        if campo == "data":
            st.session_state[campo] = datetime.date(2000,1,1)
        else:
            st.session_state[campo] = ""

if "sucesso" not in st.session_state:
    st.session_state.sucesso = False

if "limpar_form" not in st.session_state:
    st.session_state.limpar_form = False

# ------------------ Resetar formulário ------------------
if st.session_state.limpar_form:
    for campo in campos:
        if campo == "data":
            st.session_state[campo] = datetime.date(2000,1,1)
        else:
            st.session_state[campo] = ""
    st.session_state.limpar_form = False

# ------------------ UI Principal ------------------
st.markdown('<div class="main-header"><h1>🦷 Cadastro de Novo Paciente</h1></div>', unsafe_allow_html=True)

# Botão Voltar (Lógica Mantida)
# Importante: Como não posso mexer na lógica, mantive o switch_page para a página com emoji
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ Formulário ------------------
with st.form("include_paciente", clear_on_submit=False):
    
    st.markdown('<p class="section-title">👤 Identificação e Dados Pessoais</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome Completo *", key="nome", placeholder="Digite o nome completo")
        fao = st.text_input("FAO (Nº Prontuário)", placeholder="00000/00", key="fao")
        data_nasc = st.date_input("Data de Nascimento *",
                                  value=st.session_state.data,
                                  min_value=datetime.date(1900,1,1),
                                  max_value=datetime.date.today(),
                                  key="data", format="DD/MM/YYYY")
        sexo = st.selectbox("Sexo *", ["", "Masculino", "Feminino"], key="sexo")
    with col2:
        filiacao = st.text_input("Filiação (Nome da Mãe/Pai)", key="filiacao")
        endereco = st.text_input("Endereço Residencial", key="endereco")
        telefone = st.text_input("Telefone de Contato", placeholder="(92) 99999-9999", key="telefone")
    
    st.markdown('<p class="section-title">⚕️ Avaliação Clínica Inicial</p>', unsafe_allow_html=True)
    tipo_fissura = st.selectbox(
        "Classificação da Fissura",
        ["", "Pré-forame Unilateral Direita", "Pré-forame Unilateral Esquerda", "Pré-forame Bilateral",
         "Transforame Unilateral Direita", "Transforame Unilateral Esquerda", "Transforame Bilateral",
         "Pós-forame Completa", "Pós-forame Incompleta", "Fissura Rara da Face", "Fissura Mediana",
         "Não Especificado", "Outros"],
        key="tipo_fissura"
    )
    historia = st.text_area("Histórico do Tratamento / Observações Iniciais", key="historia", height=150)

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn, _ = st.columns([1, 2])
    submit = c_btn.form_submit_button("💾 SALVAR CADASTRO")

# ------------------ Processamento ------------------
if submit:
    erros = []
    if not nome.strip(): erros.append("Nome")
    if not data_nasc: erros.append("Data de Nascimento")
    if not sexo.strip(): erros.append("Sexo")

    if erros:
        st.error(f"⚠️ Por favor, preencha os campos obrigatórios: {', '.join(erros)}")
    else:
        with st.spinner("Sincronizando com o banco de dados..."):
            planilha = conectar_planilha()
            novo_id = gerar_proximo_id(planilha)
            idade = calcular_idade(data_nasc)
            nova_linha = [
                str(novo_id), nome, idade, data_nasc.strftime("%d/%m/%Y"), sexo,
                filiacao, endereco, telefone, fao, tipo_fissura, historia, "Ativo"
            ]
            planilha.append_row(nova_linha, value_input_option="USER_ENTERED")

            st.session_state.sucesso = True
            st.session_state.limpar_form = True
            st.rerun()

# Mensagem de sucesso persistente
if st.session_state.sucesso:
    st.toast("✅ Paciente cadastrado com sucesso!", icon="🎉")
    st.success("✅ Paciente inserido no sistema com sucesso!")
    st.session_state.sucesso = False