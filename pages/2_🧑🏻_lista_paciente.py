import streamlit as st
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from urllib.parse import urlencode

st.set_page_config(layout="wide", page_title="Lista de Pacientes")

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

def carregar_dados():
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
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
    return df

# CSS para os cards
st.markdown("""
<style>
.card {
    border-radius: 6px;
    border-width: thin;
    border-style: outset;
    padding: 1rem 1.2rem;
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}
.card:hover {
    box-shadow: 0 4px 18px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

df = carregar_dados()
df.columns = df.columns.str.strip().str.title()

st.markdown("## 📋 Lista de Pacientes")
busca = st.text_input("🔎 Buscar por nome, idade, FAO, etc:", placeholder="Digite aqui...")
if busca:
    busca_lower = busca.lower()
    df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(busca_lower).any(), axis=1)]

st.markdown("---")

colunas = st.columns(3)

for idx, row in df.iterrows():
    col = colunas[idx % 3]

    with col:
        with st.container():
            st.markdown(f"""
            <div class="card">
                🧑 <b>Nome: </b> {row.get("Nome", "-")}<br>
                🎂 <b>Idade: </b> {row.get("Idade", "-")} anos<br>
                🧭 <b>FAO: </b> {row.get("Fao", "-")}<br>
                💉 <b>Tipo de Fissura: </b> {row.get("Tipo_Fissura", "-")}<br>
                📌 <b>Status: </b> {row.get("Status", "-")}
            </div>
            """, unsafe_allow_html=True)

            with st.form(key=f"form_{idx}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    ver = st.form_submit_button("📄 Ficha Clinica", use_container_width=True)
                with col2:
                    editar = st.form_submit_button("✏️ Editar Dados Pessoais", use_container_width=True)
                with col3:
                    exames = st.form_submit_button("🧾 Editar infos Clinicas e Exames", use_container_width=True)


                if ver:
                    id_str = str(row.get("Id", "")).strip()
                    st.query_params = {"idpaciente": id_str}
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")

                elif editar:
                    id_str = str(row.get("Id", "")).strip()
                    st.query_params = {"idpaciente": id_str}
                    add_page("1_🏠_home", "alterar_paciente")
                    st.switch_page("pages/alterar_paciente.py")

                elif exames:
                    id_str = str(row.get("Id", "")).strip()
                    st.query_params = {"idpaciente": id_str}
                    add_page("1_🏠_home", "inserir_exames_e_diagnosticos")
                    st.switch_page("pages/inserir_exames_e_diagnosticos.py")

st.markdown("---")
st.caption(f"👥 Total de pacientes: **{len(df)}**")
