import streamlit as st
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from datetime import date, datetime

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
# Função para carregar dados da planilha
# ==========================
def carregar_dados(aba="Pacientes"):
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

    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(aba)

    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
    return df

# ==========================
# CSS para estilizar os cards e sidebar
# ==========================
st.markdown("""
<style>
.card {
    border-radius: 6px;
    border-width: thin;
    border-style: outset;
    padding: 0.8rem 1rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}
.card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
button.stButton>button {
    font-size: 13px;
    padding: 0.25rem 0.5rem;
}
.sidebar-fila {
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# Carregar dados
# ==========================
df_pacientes = carregar_dados("Pacientes")
df_fila = carregar_dados("Fila")

df_pacientes.columns = df_pacientes.columns.str.strip().str.title()
df_fila.columns = df_fila.columns.str.strip().str.title()

# ==========================
# Filtrar fila de hoje
# ==========================
hoje = date.today()
df_fila["Data"] = pd.to_datetime(df_fila["Data"], dayfirst=True, errors="coerce").dt.date
fila_hoje = df_fila[df_fila["Data"] == hoje]

# ==========================
# Funções de formatação
# ==========================
def formatar_status(status):
    status = status.upper()
    if status == "ATENDIDO":
        return f"<span style='color:green;'>🟢 {status}</span>"
    elif status == "AGENDADO":
        return f"<span style='color:orange;'>🟡 {status}</span>"
    elif status == "CANCELADO":
        return f"<span style='color:red;'>🔴 {status}</span>"
    return status

def formatar_genero(genero, nome):
    if genero.lower() == "masculino":
        return f"<span style='color:blue;'>♂️ {nome}</span>"
    elif genero.lower() == "feminino":
        return f"<span style='color:deeppink;'>♀️ {nome}</span>"
    return nome

# ==========================
# Fila de Atendimento na Sidebar
# ==========================
st.sidebar.title("📅 Fila de Atendimento - Hoje")
if not fila_hoje.empty:
    for _, row in fila_hoje.iterrows():
        paciente_id = str(row.get("Paciente_Id", "")).strip()
        paciente = df_pacientes[df_pacientes["Id"].astype(str).str.strip() == paciente_id]

        if not paciente.empty:
            nome = paciente.iloc[0]["Nome"]
            status = str(row.get("Status", "Agendado")).capitalize()
            cor_status = "orange" if status.upper() == "AGENDADO" else "green" if status.upper() == "ATENDIDO" else "red"

            # Card com botões
            with st.sidebar.container():
                cols = st.columns([2,1,1,1])
                cols[0].markdown(f"<span class='sidebar-fila'>{nome}</span>", unsafe_allow_html=True)
                cols[1].markdown(f"<span style='color:{cor_status}; font-weight:bold; font-size:14px'>{status}</span>", unsafe_allow_html=True)
                
                # Botão Ficha Clínica
                if cols[2].button("📄", key=f"ficha_{paciente_id}"):
                    st.query_params = {"idpaciente": paciente_id}
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")
                
                # Botão Evolução
                if cols[3].button("🦷", key=f"evolucao_{paciente_id}"):
                    st.query_params = {"idpaciente": paciente_id}
                    add_page("1_🏠_home", "evolucao_tratamento")
                    st.switch_page("pages/evolucao_tratamento.py")
else:
    st.sidebar.info("⚠️ Nenhum paciente agendado para hoje.")

# ==========================
# Lista de Pacientes no corpo
# ==========================
st.markdown("## 📋 Lista de Pacientes")

busca = st.text_input("🔎 Buscar por nome, idade, FAO, etc:", placeholder="Digite aqui...")
df_display = df_pacientes.copy()
if busca:
    busca_lower = busca.lower()
    df_display = df_display[df_display.apply(lambda row: row.astype(str).str.lower().str.contains(busca_lower).any(), axis=1)]

colunas = st.columns(4)

# Renderizar cards de pacientes
for idx, row in df_display.iterrows():
    col = colunas[idx % 4]
    with col:
        with st.container():
            status_formatado = formatar_status(row.get("Status", "-"))
            genero_formatado = formatar_genero(row.get("Sexo", "-"), row.get("Nome", "-"))

            st.markdown(f"""
            <div class="card">
                <b>{genero_formatado}</b><br>
                🎂 <b>Idade:</b> {row.get("Idade", "-")} anos<br>
                🧭 <b>FAO:</b> {row.get("Fao", "-")}<br>
                💉 <b>Tipo de Fissura:</b> {row.get("Tipo_Fissura", "-")}<br>
                📌 <b>Status:</b> {status_formatado}
            </div>
            """, unsafe_allow_html=True)

            with st.form(key=f"form_{idx}"):
                bcol1, bcol2 = st.columns(2)
                bcol3, bcol4 = st.columns(2)

                # Primeira linha de botões
                with bcol1:
                    ver = st.form_submit_button("📄 Ficha Clínica", use_container_width=True)
                with bcol2:
                    editar = st.form_submit_button("✏️ Editar Dados Pessoais", use_container_width=True)
                with bcol3:
                    exames = st.form_submit_button("🧾 Inserir Docs e Exames", use_container_width=True)
                with bcol4:
                    evoluir = st.form_submit_button("🦷 Evoluir Tratamento", use_container_width=True)

                # Terceira linha: botão Agendar Hoje ocupando as duas colunas
                bcol5, bcol6 = st.columns([1,1])
                with bcol5:
                    agendar = st.form_submit_button("📅 Agendar Hoje", use_container_width=True)

                id_str = str(row.get("Id", "")).strip()
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
                    # Adiciona paciente na fila
                    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
                    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
                    gc = gspread.authorize(credentials)
                    sheet = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    sheet.append_row([id_str, hoje.strftime("%d/%m/%Y"), "AGENDADO"])
                    st.success(f"Paciente **{row.get('Nome')}** agendado para hoje ✅")
                    st.experimental_rerun()

st.markdown("---")
st.caption(f"👥 Total de pacientes: **{len(df_display)}**")
