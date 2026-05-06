import streamlit as st
from datetime import datetime, date
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
import time
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# ==========================
# Configuração da Página
# ==========================
st.set_page_config(
    page_title="Evolução Clínica - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Profissional (UI/UX de Prontuário)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Gradient Padrão Profissional */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white !important;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; color: white !important; }
        .main-header p { margin: 0; opacity: 0.8; font-size: 0.85rem; color: white !important; }

        /* Container de Dados do Paciente */
        .patient-info-box {
            background-color: #f8fafc;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 0.9rem;
            font-weight: 700;
            color: #004a99;
            text-transform: uppercase;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 5px;
            margin-bottom: 15px;
            margin-top: 10px;
        }

        /* Labels e Valores Profissionais */
        .record-label { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
        .record-value { color: #1e293b; font-size: 0.95rem; font-weight: 500; margin-bottom: 12px; }

        /* Cards de Histórico */
        .evolution-card {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #004a99;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        
        div.stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
        .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================
# Funções de Sistema e Dados
# ==========================
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

@st.cache_resource
def conectar_google_sheets():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    service_account_info = {k: v.replace('\\n','\n') if k=='private_key' else v 
                            for k,v in st.secrets['gcp_service_account'].items()}
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc

def carregar_dados():
    gc = conectar_google_sheets()
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    df_p = pd.DataFrame(sh.sheet1.get_all_records())
    df_p.columns = df_p.columns.str.strip().str.upper()
    
    aba_registros = sh.worksheet("Registros")
    aba_fila = sh.worksheet("Fila")
    
    return sh, df_p, aba_registros, aba_fila

sh, df_pacientes, aba_registros, aba_fila = carregar_dados()

# ==========================
# Sidebar Institucional
# ==========================
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje_data = date.today()
    df_f = pd.DataFrame(aba_fila.get_all_records())
    if not df_f.empty:
        df_f.columns = df_f.columns.str.strip().str.upper()
        df_f["DATA"] = pd.to_datetime(df_f["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_f[df_f["DATA"] == hoje_data]
        for _, r in fila_hoje.iterrows():
            pid = str(r["PACIENTE_ID"]).strip()
            nome_p = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == pid]["NOME"].values
            st.info(f"👤 **{nome_p[0] if len(nome_p)>0 else pid}**")
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()

# ==========================
# Cabeçalho Principal
# ==========================
st.markdown("""
    <div class="main-header">
        <h1>🦷 Evolução no Tratamento</h1>
    </div>
""", unsafe_allow_html=True)

# Navegação
c_nav, _ = st.columns([1, 3])
if c_nav.button("⬅️ Voltar para Lista"):
    st.query_params.clear()
    delete_page("1_🏠_home", "evolucao_tratamento")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# Captura ID
id_paciente_str = str(st.query_params.get("idpaciente", "")).strip()
if not id_paciente_str:
    st.error("⚠️ Erro: Paciente não identificado nos parâmetros da página.")
    st.stop()

# Localizar Paciente
paciente_info = df_pacientes[df_pacientes["ID"].astype(str) == id_paciente_str].iloc[0]

# ==========================
# ILUSTRAÇÃO PROFISSIONAL DOS DADOS
# ==========================
st.markdown(f"### Paciente: {paciente_info.get('NOME')}")

def render_field(col, label, key):
    val = str(paciente_info.get(key, "Não informado")).strip()
    if val == "" or val == "nan": val = "Não informado"
    col.markdown(f'<p class="record-label">{label}</p><p class="record-value">{val}</p>', unsafe_allow_html=True)

# Card de Dados Cadastrais
with st.container():
    st.markdown('<p class="section-title">👤 Identificação e Contato</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    render_field(c1, "FAO", "FAO")
    render_field(c2, "Idade", "IDADE")
    render_field(c3, "Gênero/Sexo", "SEXO")
    render_field(c4, "Status", "STATUS")
    
    c5, c6, c7, c8 = st.columns(4)
    render_field(c5, "Data de Nascimento", "DATA")
    render_field(c6, "Telefone", "TELEFONE")
    render_field(c7, "Filiação", "FILIACAO")
    render_field(c8, "Endereço", "ENDERECO")

# Seção de Dados Clínicos (Expandida para Prontuário)
with st.expander("🩺 Ver Ficha Clínica e Planejamento", expanded=True):
    st.markdown('<p class="section-title">🦷 Condição Clínica</p>', unsafe_allow_html=True)
    cl1, cl2 = st.columns(2)
    render_field(cl1, "Tipo de Fissura", "TIPO_FISSURA")
    render_field(cl2, "Características Oclusais", "CARAC_OCLUSAIS")
    
    render_field(st, "História do Tratamento", "HISTORIA_TRATAMENTO")
    
    st.markdown('<p class="section-title">📋 Diagnóstico e Planejamento</p>', unsafe_allow_html=True)
    cl3, cl4 = st.columns(2)
    render_field(cl3, "Diagnóstico", "DIAGNOSTICO")
    render_field(cl4, "Plano de Tratamento", "PLANO_TRATAMENTO")
    
    st.markdown('<p class="section-title">⚡ Necessidades Específicas</p>', unsafe_allow_html=True)
    n1, n2, n3, n4 = st.columns(4)
    render_field(n1, "Necessidades Odontológicas", "NECES_ODONTO")
    render_field(n2, "Necessidades Ortodônticas", "NECES_ORTO")
    render_field(n3, "Necessidades Cirúrgicas", "NECES_CIRUR")
    render_field(n4, "Observações (Outros)", "OUTROS")

st.markdown("---")

# ==========================
# CADASTRO DE NOVA EVOLUÇÃO (Com bloqueio de data futura)
# ==========================
st.markdown("#### 📝 Registrar Nova Evolução")
c_form1, c_form2 = st.columns([3, 1])

with c_form1:
    descricao_evolucao = st.text_area("Descrição detalhada da evolução:", height=150, placeholder="Digite aqui os procedimentos realizados...")

with c_form2:
    # DATA RETROATIVA PERMITIDA / FUTURA BLOQUEADA
    data_evolucao = st.date_input(
        "Data da Evolução", 
        value=date.today(),
        max_value=date.today(), # Bloqueia datas futuras
        format="DD/MM/YYYY"
    )
    
    user = st.user.email if hasattr(st, "user") else "Usuário"
    
    if st.button("💾 Salvar Evolução", use_container_width=True):
        if not descricao_evolucao.strip():
            st.error("A descrição não pode estar vazia.")
        else:
            try:
                # Salvar Registro
                aba_registros.append_row([
                    id_paciente_str,
                    data_evolucao.strftime("%d/%m/%Y"),
                    descricao_evolucao.strip(),
                    user
                ])
                
                # Sincronizar Fila
                regs_f = aba_fila.get_all_records()
                for i, row in enumerate(regs_f, start=2):
                    if str(row.get("PACIENTE_ID")).strip() == id_paciente_str:
                        try:
                            f_date = datetime.strptime(str(row.get("DATA")), "%d/%m/%Y").date()
                            if f_date == data_evolucao:
                                aba_fila.update_cell(i, 3, "ATENDIDO")
                                break
                        except: continue
                
                st.toast("Evolução registrada com sucesso!", icon="✅")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ==========================
# HISTÓRICO DE EVOLUÇÕES
# ==========================
st.markdown("#### 📜 Histórico de Evoluções")
try:
    regs = pd.DataFrame(aba_registros.get_all_records())
    if not regs.empty:
        regs.columns = regs.columns.str.strip().str.upper()
        df_p = regs[regs["PACIENTE_ID"].astype(str) == id_paciente_str].copy()
        
        if not df_p.empty:
            df_p["DATA_REGISTRO"] = pd.to_datetime(df_p["DATA_REGISTRO"], dayfirst=True, errors="coerce")
            df_p = df_p.sort_values("DATA_REGISTRO", ascending=False)

            for _, row in df_p.iterrows():
                dt_str = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else "S/D"
                st.markdown(f"""
                    <div class="evolution-card">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span style="font-weight:700; color:#004a99;">📅 {dt_str}</span>
                            <span style="font-size:0.8rem; color:#64748b;">👤 {row.get('USUARIO','-')}</span>
                        </div>
                        <div style="color:#1e293b; font-size:0.95rem;">{row.get('EVOLUCAO','-')}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum registro de evolução encontrado para este paciente.")
except:
    st.error("Erro ao carregar histórico.")