import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# Função para deletar páginas do menu lateral
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()  # Remove parâmetros da URL

    # Deleta a página atual (Ficha Clínica) do menu lateral
    delete_page("1_🏠_home", "evolucao_tratamento")

    # Redireciona para a lista de pacientes
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")
st.title("🦷 Inserir Evolução no Tratamento")

# ID da pasta no Google Drive
PASTA_DRIVE_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"

# Obter o ID do paciente via query string
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

try:
    id_paciente = int(id_paciente_str)
except ValueError:
    id_paciente = None

# --- Função para carregar dados da planilha ---
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

    df = sheet.get_all_records()
    df = pd.DataFrame(df)
    return df, sheet, credentials

df, sheet, credentials = carregar_dados()
df.columns = df.columns.str.strip().str.upper()

# Encontrar paciente
paciente_df = df[df["ID"].astype(str) == id_paciente_str]
if paciente_df.empty:
    st.error("❌ Paciente não encontrado.")
    st.stop()

paciente_info = paciente_df.iloc[0]
sexo_opcoes = ["Masculino", "Feminino"]
status_opcoes = ["Ativo", "Inativo", "Ausente"]
# Exibição
st.write("______________________________")
st.markdown("<h2 style='text-align:center;'>📋 Dados E Registros do Paciente</h2><hr>", unsafe_allow_html=True)

espaco, col1, col2, col3, espaco2 = st.columns([1, 2, 2, 2, 1])

with col1:
    st.markdown(f"<h5 style='text-align:center;'>👤<br>{paciente_info['NOME']}</h4>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h5 style='text-align:center;'>🧭<br>FAO: {paciente_info['FAO']}</h4>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h5 style='text-align:center;'>🎂<br>{paciente_info['IDADE']} anos</h4>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"<h6 style='text-align:center;'>🧬 Tipo de Fissura</h5><p style='text-align:center;'>{paciente_info.get('TIPO_FISSURA', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📋 Plano de Tratamento</h5><p style='text-align:center;'>{paciente_info.get('PLANO_TRATAMENTO', '')}</p>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<h6 style='text-align:center;'>📝 Diagnóstico</h5><p style='text-align:center;'>{paciente_info.get('DIAGNOSTICO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>🧩 Características Oclusais</h5><p style='text-align:center;'>{paciente_info.get('CARAC_OCLUSAIS', '')}</p>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<h6 style='text-align:center;'>🪥 Necessidades Odontológicas</h5><p style='text-align:center;'>{paciente_info.get('NECES_ODONTO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📜 Histórico do Tratamento</h5><p style='text-align:center;'>{paciente_info.get('HISTORIA_TRATAMENTO', '')}</p>", unsafe_allow_html=True)

with col4:
    st.markdown(f"<h6 style='text-align:center;'>🦷 Necessidades Ortodônticas</h5><p style='text-align:center;'>{paciente_info.get('NECES_ORTO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📌 Outros</h5><p style='text-align:center;'>{paciente_info.get('OUTROS', '')}</p>", unsafe_allow_html=True)

with col5:
    st.markdown(f"<h6 style='text-align:center;'>🔪 Necessidades Cirúrgicas</h5><p style='text-align:center;'>{paciente_info.get('NECES_CIRUR', '')}</p>", unsafe_allow_html=True)

st.write("______________________________")
st.write("**Registros de Tratamento:**")

