import streamlit as st
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from datetime import date
import time

# Configuração da Página
st.set_page_config(layout="wide", page_title="Lista de Pacientes")

# ==========================
# Função para adicionar páginas dinamicamente
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
        "page_script_hash": psh,
        "page_name": pn,
        "icon": pi,
        "script_path": script_path_str,
    }
    _on_pages_changed.send()

# ==========================
# Função para conectar Google Sheets
# ==========================
def conectar_planilha():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

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
    gc = gspread.authorize(credentials)
    return gc

# ==========================
# Função para carregar dados
# ==========================
def carregar_dados():
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    gc = conectar_planilha()
    
    max_retries = 5
    delay_segundos = 1
    
    for attempt in range(max_retries):
        try:
            sheet_pacientes = gc.open_by_key(SPREADSHEET_ID).worksheet("Pacientes")
            dados_pacientes = sheet_pacientes.get_all_records()
            df_pacientes = pd.DataFrame(dados_pacientes)

            sheet_fila = gc.open_by_key(SPREADSHEET_ID).worksheet("Fila")
            dados_fila = sheet_fila.get_all_records()
            df_fila = pd.DataFrame(dados_fila)

            return df_pacientes, df_fila, gc
        except Exception:
            time.sleep(delay_segundos)
    
    st.error("❌ Erro ao carregar dados.")
    st.stop()

# ==========================
# CSS Personalizado
# ==========================
st.markdown("""
<style>
    .badge {
        font-size: 11px;
        font-weight: 600;
        text-align: center;
        border-radius: 6px;
        padding: 2px 6px;
        display: inline-block;
        min-width: 70px;
    }
    /* Reduzir o espaço entre elementos da lista */
    .stForm {
        border: none !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Carregar dados
df_pacientes, df_fila, gc = carregar_dados()
df_pacientes.columns = df_pacientes.columns.str.strip().str.title()
df_fila.columns = df_fila.columns.str.strip().str.upper()

# ==========================
# Sidebar - Fila de Atendimento
# ==========================
st.sidebar.markdown("### 📅 Fila de Atendimento - Hoje")
hoje = date.today()
df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
fila_hoje = df_fila[df_fila["DATA"] == hoje]

if not fila_hoje.empty:
    for _, row in fila_hoje.iterrows():
        paciente_id = str(row["PACIENTE_ID"]).strip()
        paciente = df_pacientes[df_pacientes["Id"].astype(str).str.strip() == paciente_id]
        if not paciente.empty:
            nome_paciente = paciente.iloc[0]["Nome"]
            status = row["STATUS"].upper()
            cor_status = {"AGENDADO":"#FFD700", "ATENDIDO":"#4CAF50", "CANCELADO":"#F44336"}.get(status, "#6c757d")
            
            with st.sidebar.container():
                c1, c2 = st.columns([3,1])
                c1.markdown(f"**{nome_paciente}**")
                c2.markdown(f"<div class='badge' style='background-color:{cor_status}; color:white'>{status}</div>", unsafe_allow_html=True)
                
                b1, b2 = st.columns(2)
                if b1.button("📄", key=f"sidebar_f_{paciente_id}"):
                    st.query_params = {"idpaciente": paciente_id}
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")
                if b2.button("🦷", key=f"sidebar_e_{paciente_id}"):
                    st.query_params = {"idpaciente": paciente_id}
                    add_page("1_🏠_home", "evolucao_tratamento")
                    st.switch_page("pages/evolucao_tratamento.py")
            st.sidebar.markdown("---")
else:
    st.sidebar.info("⚠️ Fila vazia hoje.")

# ==========================
# Título e Busca
# ==========================
st.markdown("## 📋 Lista de Pacientes")
busca = st.text_input("🔎 Buscar por nome, idade, FAO, etc:", placeholder="Digite para filtrar...")

if busca:
    busca_lower = busca.lower()
    df_pacientes = df_pacientes[df_pacientes.apply(lambda row: row.astype(str).str.lower().str.contains(busca_lower).any(), axis=1)]

# ==========================
# Cabeçalho da Tabela
# ==========================
st.markdown("---")
h_col1, h_col2, h_col3, h_col4 = st.columns([2.5, 1, 1.5, 4.5])
h_col1.markdown("**Paciente / FAO**")
h_col2.markdown("**Idade**")
h_col3.markdown("**Fissura / Status**")
h_col4.markdown("**Ações Disponíveis**")
st.markdown("---")

# ==========================
# Loop de Pacientes (Lista)
# ==========================
for idx, row in df_pacientes.iterrows():
    # Colunas principais da linha
    c1, c2, c3, c4 = st.columns([2.5, 1, 1.5, 4.5])
    
    id_str = str(row.get("Id", "")).strip()
    nome = row.get('Nome', '-')
    fao = row.get('Fao', '-')
    
    with c1:
        st.markdown(f"**{nome}**")
        st.caption(f"🪪 FAO: {fao}")
        
    with c2:
        st.markdown(f"{row.get('Idade', '-')} anos")
        
    with c3:
        st.markdown(f"{row.get('Tipo_Fissura', '-')}")
        st.caption(f"Status: {row.get('Status', '-')}")

    with c4:
        # Formulário para conter os botões de ação na mesma linha
        with st.form(key=f"form_row_{idx}"):
            b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns(5)
            
            # Botões com ícones e tooltips
            ver = b_col1.form_submit_button("📄", help="Ver Ficha Clínica")
            editar = b_col2.form_submit_button("✏️", help="Editar Dados")
            exames = b_col3.form_submit_button("🧾", help="Dados Clínicos / Exames")
            evoluir = b_col4.form_submit_button("🦷", help="Evolução do Tratamento")
            agendar = b_col5.form_submit_button("📅", help="Agendar para Hoje")

            # Lógica das Ações
            if ver:
                st.query_params = {"idpaciente": id_str}
                add_page("1_🏠_home", "ficha_clinica")
                st.switch_page("pages/ficha_clinica.py")
            
            elif editar:
                st.query_params = {"idpaciente": id_str}
                add_page("1_🏠_home", "alterar_paciente")
                st.switch_page("pages/alterar_paciente.py")
            
            elif exames:
                st.query_params = {"idpaciente": id_str}
                add_page("1_🏠_home", "inserir_exames_e_diagnosticos")
                st.switch_page("pages/inserir_exames_e_diagnosticos.py")
            
            elif evoluir:
                st.query_params = {"idpaciente": id_str}
                add_page("1_🏠_home", "evolucao_tratamento")
                st.switch_page("pages/evolucao_tratamento.py")
            
            elif agendar:
                try:
                    sheet_fila = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    # Verifica duplicidade
                    registros = sheet_fila.get_all_records()
                    df_check = pd.DataFrame(registros)
                    df_check["DATA"] = pd.to_datetime(df_check["DATA"], dayfirst=True, errors="coerce").dt.date
                    
                    ja_existe = not df_check[(df_check["PACIENTE_ID"].astype(str) == id_str) & (df_check["DATA"] == hoje)].empty
                    
                    if ja_existe:
                        st.warning(f"⚠️ {nome} já agendado.")
                    else:
                        sheet_fila.append_row([id_str, hoje.strftime("%d/%m/%Y"), "AGENDADO"])
                        st.success(f"✅ {nome} agendado!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao agendar: {e}")

    # Linha divisória fina entre pacientes
    st.markdown("<hr style='margin:0; padding:0; opacity:0.15'>", unsafe_allow_html=True)

# Rodapé
st.markdown("---")
st.caption(f"👥 Total de pacientes: **{len(df_pacientes)}**")