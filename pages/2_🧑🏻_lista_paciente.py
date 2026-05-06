import streamlit as st
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from datetime import date
import time

# Configuração da Página
st.set_page_config(layout="wide", page_title="Gestão de Pacientes", page_icon="🏥")

# ==========================
# Funções de Suporte (Páginas e Google Sheets)
# ==========================
def add_page(main_script_path_str, page_name):
    pages = get_pages(main_script_path_str)
    main_script_path = Path(main_script_path_str)
    pages_dir = main_script_path.parent / "pages"
    script_path = [f for f in list(pages_dir.glob("*.py")) + list(main_script_path.parent.glob("*.py"))
                   if f.name.find(page_name) != -1][0]
    script_path_str = str(script_path.resolve())
    pi, pn = page_icon_and_name(script_path)
    psh = calc_md5(script_path_str)
    pages[psh] = {
        "page_script_hash": psh, "page_name": pn, "icon": pi, "script_path": script_path_str,
    }
    _on_pages_changed.send()

def conectar_planilha():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    service_account_info = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(credentials)

def carregar_dados():
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    gc = conectar_planilha()
    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        df_p = pd.DataFrame(sh.worksheet("Pacientes").get_all_records())
        df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        return df_p, df_f, gc
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        st.stop()

# ==========================
# Estilização CSS Profissional
# ==========================
st.markdown("""
<style>
    /* Estilo para as linhas da lista */
    .patient-row {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        background-color: #f8f9fa;
        border-left: 5px solid #007bff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 2.2em;
        background-color: white;
        border: 1px solid #d1d3e2;
        color: #4e73df;
        font-size: 0.8rem;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #4e73df;
        color: white;
        border-color: #4e73df;
    }
    .badge-status {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
    }
    /* Cabeçalho da tabela */
    .table-header {
        font-weight: bold;
        color: #5a5c69;
        padding: 10px;
        background-color: #eaecf4;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização de Dados
df_pacientes, df_fila, gc = carregar_dados()
df_pacientes.columns = df_pacientes.columns.str.strip().str.title()
df_fila.columns = df_fila.columns.str.strip().str.upper()

# ==========================
# Sidebar: Fila de Hoje
# ==========================
st.sidebar.title("📅 Fila de Hoje")
hoje = date.today()
df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
fila_hoje = df_fila[df_fila["DATA"] == hoje]

if not fila_hoje.empty:
    for _, row in fila_hoje.iterrows():
        p_id = str(row["PACIENTE_ID"]).strip()
        p_info = df_pacientes[df_pacientes["Id"].astype(str).str.strip() == p_id]
        if not p_info.empty:
            nome = p_info.iloc[0]["Nome"]
            with st.sidebar.expander(f"👤 {nome}"):
                st.write(f"Status: {row['STATUS']}")
                if st.button("Ver Ficha", key=f"side_{p_id}"):
                    st.query_params = {"idpaciente": p_id}
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")
else:
    st.sidebar.info("Nenhum paciente para hoje.")

# ==========================
# Corpo Principal: Lista
# ==========================
st.title("📋 Gestão de Pacientes")

col_search, col_stats = st.columns([2, 1])
with col_search:
    busca = st.text_input("🔍 Localizar paciente:", placeholder="Nome, FAO ou documento...")
with col_stats:
    st.metric("Total de Pacientes", len(df_pacientes))

if busca:
    df_pacientes = df_pacientes[df_pacientes.apply(lambda r: r.astype(str).str.lower().str.contains(busca.lower()).any(), axis=1)]

# Cabeçalho da Lista
st.markdown("""
<div class="table-header">
    <div style="display: flex; width: 100%;">
        <div style="flex: 2.2;">PACIENTE / FAO</div>
        <div style="flex: 0.8;">IDADE</div>
        <div style="flex: 1.5;">TIPO DE FISSURA</div>
        <div style="flex: 5.5; text-align: center;">AÇÕES DISPONÍVEIS</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Loop da Lista
for idx, row in df_pacientes.iterrows():
    p_id = str(row.get("Id", "")).strip()
    nome = str(row.get("Nome", "-")).strip().upper()
    fao = row.get("Fao", "-")
    idade = row.get("Idade", "-")
    fissura = row.get("Tipo_Fissura", "-")
    
    # Container da Linha
    with st.container():
        # Usamos colunas do Streamlit para os botões funcionarem
        c1, c2, c3, c_actions = st.columns([2.2, 0.8, 1.5, 5.5])
        
        with c1:
            st.markdown(f"**{nome}**")
            st.caption(f"FAO: {fao}")
        with c2:
            st.markdown(f"{idade} anos")
        with c3:
            st.markdown(f"_{fissura}_")
        
        with c_actions:
            # Grid de botões interno
            b1, b2, b3, b4, b5 = st.columns(5)
            
            if b1.button("📄 Ficha", key=f"v_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page("1_🏠_home", "ficha_clinica")
                st.switch_page("pages/ficha_clinica.py")

            if b2.button("✏️ Editar", key=f"e_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page("1_🏠_home", "alterar_paciente")
                st.switch_page("pages/alterar_paciente.py")

            if b3.button("🧾 Exames", key=f"x_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page("1_🏠_home", "inserir_exames_e_diagnosticos")
                st.switch_page("pages/inserir_exames_e_diagnosticos.py")

            if b4.button("🦷 Evoluir", key=f"ev_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page("1_🏠_home", "evolucao_tratamento")
                st.switch_page("pages/evolucao_tratamento.py")

            if b5.button("📅 Agenda", key=f"ag_{p_id}_{idx}"):
                try:
                    sheet_f = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    # Verifica se já está agendado
                    existentes = pd.DataFrame(sheet_f.get_all_records())
                    if not existentes.empty:
                        existentes["DATA"] = pd.to_datetime(existentes["DATA"], dayfirst=True, errors="coerce").dt.date
                        ja_foi = not existentes[(existentes["PACIENTE_ID"].astype(str) == p_id) & (existentes["DATA"] == hoje)].empty
                    else:
                        ja_foi = False

                    if ja_foi:
                        st.toast(f"{nome} já está na fila!", icon="⚠️")
                    else:
                        sheet_f.append_row([p_id, hoje.strftime("%d/%m/%Y"), "AGENDADO"])
                        st.toast(f"{nome} agendado com sucesso!", icon="✅")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao agendar: {e}")

    st.markdown("---") # Linha divisória entre pacientes