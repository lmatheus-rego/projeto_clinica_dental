import streamlit as st
from datetime import datetime
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
    page_title="Evolução - Céu da Boca", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Profissional
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Padrão Dashboard */
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

        /* Estilo de Prontuário */
        .patient-summary {
            background-color: #f8fafc;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            margin-bottom: 20px;
        }
        .record-label { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .record-value { color: #1e293b; font-size: 1rem; font-weight: 600; margin-bottom: 10px; }

        /* Cards de Evolução */
        .evolution-card {
            background-color: white;
            padding: 12px;
            border-radius: 10px;
            border-left: 5px solid #004a99;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        div.stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
        .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================
# Funções de Sistema
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
    
    # Carregar DF principal para nomes na sidebar
    df_pacientes = pd.DataFrame(sh.sheet1.get_all_records())
    df_pacientes.columns = df_pacientes.columns.str.strip().str.upper()
    
    aba_registros = sh.worksheet("Registros")
    aba_fila = sh.worksheet("Fila")
    
    return sh, df_pacientes, aba_registros, aba_fila

# ==========================
# Inicialização e Sidebar
# ==========================
sh, df_pacientes, aba_registros, aba_fila = carregar_dados()

with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje_data = datetime.now().date()
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
        <h1>🦷 Evolução do Tratamento</h1>
        <p>Registro Clínico | Faculdade de Odontologia - UFAM</p>
    </div>
""", unsafe_allow_html=True)

# Botão Voltar
c_nav, _ = st.columns([1, 3])
if c_nav.button("⬅️ Voltar para Lista"):
    st.query_params.clear()
    delete_page("1_🏠_home", "evolucao_tratamento")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# Captura ID do Paciente
id_paciente_str = str(st.query_params.get("idpaciente", "")).strip()
if not id_paciente_str:
    st.error("ID do paciente não identificado.")
    st.stop()

paciente_info = df_pacientes[df_pacientes["ID"].astype(str) == id_paciente_str].iloc[0]

# ==========================
# Resumo do Paciente
# ==========================
with st.container():
    st.markdown(f"### Paciente: {paciente_info.get('NOME')}")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<p class="record-label">Prontuário FAO</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="record-value">{paciente_info.get("FAO", "-")}</p>', unsafe_allow_html=True)
    with col2:
        st.markdown('<p class="record-label">Idade</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="record-value">{paciente_info.get("IDADE", "-")} anos</p>', unsafe_allow_html=True)
    with col3:
        st.markdown('<p class="record-label">Gênero</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="record-value">{paciente_info.get("SEXO", "-")}</p>', unsafe_allow_html=True)
    with col4:
        status_val = paciente_info.get('STATUS','').upper()
        st_color = "#10b981" if "ATIVO" in status_val else "#94a3b8"
        st.markdown('<p class="record-label">Status</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="record-value" style="color:{st_color}">{status_val}</p>', unsafe_allow_html=True)

with st.expander("🩺 Ver Dados Clínicos Completos", expanded=False):
    c_clin1, c_clin2 = st.columns(2)
    with c_clin1:
        st.markdown(f"**Tipo de Fissura:** {paciente_info.get('TIPO_FISSURA','-')}")
        st.markdown(f"**Necessidades Cirúrgicas:** {paciente_info.get('NECES_CIRUR','-')}")
        st.markdown(f"**Necessidades Ortodônticas:** {paciente_info.get('NECES_ORTO','-')}")
    with c_clin2:
        st.markdown(f"**Diagnóstico:** {paciente_info.get('DIAGNOSTICO','-')}")
        st.markdown(f"**Plano de Tratamento:** {paciente_info.get('PLANO_TRATAMENTO','-')}")
        st.markdown(f"**História do Tratamento:**")
        st.caption(paciente_info.get('HISTORIA_TRATAMENTO','-'))

st.markdown("---")

# ==========================
# Cadastro de Nova Evolução
# ==========================
st.markdown("#### 📝 Nova Evolução")
c_form1, c_form2 = st.columns([3, 1])
with c_form1:
    descricao_evolucao = st.text_area("Descrição do atendimento", placeholder="Descreva os procedimentos realizados hoje...", height=120, label_visibility="collapsed")
with c_form2:
    data_evolucao = st.date_input("Data do Registro", value=datetime.now(), format="DD/MM/YYYY")
    
    # Capturar usuário
    user = st.user.email if hasattr(st, "user") else "Usuário"
    
    if st.button("💾 Salvar Evolução", use_container_width=True):
        if not descricao_evolucao.strip():
            st.warning("Descreva a evolução antes de salvar.")
        else:
            try:
                aba_registros.append_row([
                    id_paciente_str,
                    data_evolucao.strftime("%d/%m/%Y"),
                    descricao_evolucao.strip(),
                    user
                ])
                
                # Marcar como atendido na fila se existir agendamento hoje
                registros_fila = aba_fila.get_all_records()
                for i, row in enumerate(registros_fila, start=2):
                    if str(row.get("PACIENTE_ID")).strip() == id_paciente_str:
                        # Verifica se a data na fila coincide (tratando formatos)
                        try:
                            f_date = datetime.strptime(str(row.get("DATA")), "%d/%m/%Y").date()
                            if f_date == data_evolucao:
                                aba_fila.update_cell(i, 3, "ATENDIDO") # Coluna 3 = STATUS
                                break
                        except: continue
                
                st.toast("Evolução salva com sucesso!", icon="✅")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ==========================
# Histórico de Evoluções
# ==========================
st.markdown("#### 📜 Histórico de Evoluções")
try:
    registros = pd.DataFrame(aba_registros.get_all_records())
    if not registros.empty and "PACIENTE_ID" in registros.columns:
        registros.columns = registros.columns.str.strip().str.upper()
        df_p = registros[registros["PACIENTE_ID"].astype(str) == id_paciente_str].copy()
        
        if not df_p.empty:
            df_p["DATA_REGISTRO"] = pd.to_datetime(df_p["DATA_REGISTRO"], dayfirst=True, errors="coerce")
            df_p = df_p.sort_values(by="DATA_REGISTRO", ascending=False)

            for _, row in df_p.iterrows():
                dt = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else "S/D"
                st.markdown(f"""
                    <div class="evolution-card">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span style="font-weight:700; color:#004a99;">📅 {dt}</span>
                            <span style="font-size:0.8rem; color:#64748b;">👤 {row.get('USUARIO','-')}</span>
                        </div>
                        <div style="color:#1e293b; font-size:0.95rem; line-height:1.4;">
                            {row.get('EVOLUCAO','-')}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma evolução registrada anteriormente.")
except Exception as e:
    st.error(f"Erro ao carregar histórico: {e}")