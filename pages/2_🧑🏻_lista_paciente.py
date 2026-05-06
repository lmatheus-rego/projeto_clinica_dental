import streamlit as st
import datetime
import pandas as pd
import time
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed

# ==========================
# Configuração da Página
# ==========================
st.set_page_config(
    page_title="Gestão Céu da Boca - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profissional de Alta Densidade (UI/UX)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Gradient Padrão Profissional */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.8rem; letter-spacing: -0.5px; }
        .main-header p { margin: 0; opacity: 0.8; font-size: 0.9rem; }

        /* Estilização da Tabela/Lista */
        .table-header {
            background-color: #f1f5f9;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: 700;
            color: #475569;
            font-size: 0.85rem;
            margin-bottom: 8px;
            display: flex;
        }

        /* Linha de Paciente Estreita */
        .patient-row {
            border-bottom: 1px solid #f1f5f9;
            padding: 6px 15px;
            transition: background 0.2s;
        }
        .patient-row:hover { background-color: #f8fafc; }

        /* Botões de Ação Compactos */
        div[data-testid="column"] button {
            font-size: 11px !important;
            padding: 2px 8px !important;
            height: 28px !important;
            min-height: 28px !important;
            border-radius: 6px !important;
        }

        /* Badges de Status e Gênero */
        .badge {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-m { background-color: #e0f2fe; color: #0369a1; }
        .badge-f { background-color: #fdf2f8; color: #be185d; }
    </style>
""", unsafe_allow_html=True)

# ==========================
# Funções de Dados e Páginas
# ==========================
@st.cache_data(ttl=300)
def carregar_dados():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        df_p = pd.DataFrame(sh.worksheet("Pacientes").get_all_records())
        df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        return df_p, df_f, gc
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame(), None

def add_page(main_script, page_name):
    # Simulação da função add_page para redirecionamento
    st.query_params["page"] = page_name

df_pacientes, df_fila, gc = carregar_dados()

# Padronização de Colunas
if not df_pacientes.empty:
    df_pacientes.columns = df_pacientes.columns.str.strip().str.upper()
    # Garante existência de colunas essenciais
    for col in ["NOME", "FAO", "IDADE", "SEXO", "STATUS", "TIPO_FISSURA"]:
        if col not in df_pacientes.columns: df_pacientes[col] = "-"

# ==========================
# Sidebar (Padrão Home)
# ==========================
with st.sidebar:
    st.markdown("### 🏛️ Institucional")
    st.caption("Universidade Federal do Amazonas\nFaculdade de Odontologia")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.date.today()
    
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA"] == hoje]
        if not fila_hoje.empty:
            for _, r in fila_hoje.iterrows():
                p_id = str(r["PACIENTE_ID"]).strip()
                p_nome = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == p_id]["NOME"].values
                nome = p_nome[0] if len(p_nome) > 0 else f"ID: {p_id}"
                st.info(f"👤 **{nome}**")
        else:
            st.write("Sem agendamentos.")
    
    st.markdown("---")
    if st.button("🔄 Atualizar Lista", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================
# Cabeçalho e Busca
# ==========================
st.markdown("""
    <div class="main-header">
        <h1>Céu da Boca — Gestão de Pacientes</h1>
        <p>FAO/UFAM | Sistema de Prontuários e Acompanhamento Clínico</p>
    </div>
""", unsafe_allow_html=True)

# Campo de Busca Integrado (Layout Profissional)
col_search, col_spacer = st.columns([1, 1])
with col_search:
    busca = st.text_input("🔍 Pesquisar na base de dados:", placeholder="Nome, FAO, Gênero ou Status...")

if busca:
    df_pacientes = df_pacientes[df_pacientes.apply(lambda r: r.astype(str).str.lower().str.contains(busca.lower()).any(), axis=1)]

# ==========================
# Lista de Pacientes (Layout de Prontuário)
# ==========================

# Cabeçalho da Lista
st.markdown("""
    <div class="table-header">
        <div style="flex: 2.5;">PACIENTE / FAO</div>
        <div style="flex: 0.6;">IDADE</div>
        <div style="flex: 0.6;">SEXO</div>
        <div style="flex: 1.5;">TIPO DE FISSURA</div>
        <div style="flex: 1.2;">STATUS</div>
        <div style="flex: 3.5; text-align: center;">AÇÕES</div>
    </div>
""", unsafe_allow_html=True)

# Linhas da Lista
for idx, row in df_pacientes.iterrows():
    p_id = str(row.get("ID", "")).strip()
    nome = str(row.get("NOME", "-")).strip().upper()
    fao = row.get("FAO", "-")
    idade = row.get("IDADE", "-")
    sexo = str(row.get("SEXO", "-")).upper()[:1] # M ou F
    fissura = row.get("TIPO_FISSURA", "-")
    status = row.get("STATUS", "-")

    # Container de linha para Streamlit
    with st.container():
        c1, c2, c3, c4, c5, c_btns = st.columns([2.5, 0.6, 0.6, 1.5, 1.2, 3.5])
        
        c1.markdown(f"**{nome}**<br><small style='color:gray'>FAO: {fao}</small>", unsafe_allow_html=True)
        c2.markdown(f"<div style='padding-top:8px'>{idade}a</div>", unsafe_allow_html=True)
        
        # Badge de Gênero
        g_class = "badge-m" if sexo == "M" else "badge-f"
        c3.markdown(f"<div style='padding-top:6px'><span class='badge {g_class}'>{sexo}</span></div>", unsafe_allow_html=True)
        
        c4.markdown(f"<div style='padding-top:8px; font-size:12px'>{fissura}</div>", unsafe_allow_html=True)
        
        # Cor por Status
        st_color = "#10b981" if "ATIVO" in str(status).upper() else "#64748b"
        c5.markdown(f"<div style='padding-top:8px; font-size:11px; color:{st_color}; font-weight:bold'>{status}</div>", unsafe_allow_html=True)

        # Botões Agrupados e Pequenos
        with c_btns:
            st.write("") # Alinhamento vertical
            b1, b2, b3, b4 = st.columns(4)
            
            if b1.button("📄 Ficha", key=f"f_{p_id}_{idx}"):
                st.query_params["idpaciente"] = p_id
                st.switch_page("pages/ficha_clinica.py")
            
            if b2.button("✏️ Edit", key=f"e_{p_id}_{idx}"):
                st.query_params["idpaciente"] = p_id
                st.switch_page("pages/alterar_paciente.py")
                
            if b3.button("🦷 Evol", key=f"ev_{p_id}_{idx}"):
                st.query_params["idpaciente"] = p_id
                st.switch_page("pages/evolucao_tratamento.py")
                
            if b4.button("📅 Agnd", key=f"ag_{p_id}_{idx}"):
                # Lógica rápida de agendamento
                try:
                    sheet_f = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    sheet_f.append_row([p_id, hoje.strftime("%d/%m/%Y"), "AGENDADO"])
                    st.toast(f"✅ {nome} agendado!", icon="📅")
                    time.sleep(0.5)
                    st.rerun()
                except: st.error("Erro ao agendar")

    st.markdown("<div class='patient-row'></div>", unsafe_allow_html=True)

# Rodapé
st.markdown("---")
st.caption(f"Exibindo {len(df_pacientes)} pacientes filtrados.")