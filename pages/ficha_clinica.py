import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from streamlit_pdf_viewer import pdf_viewer
import urllib.request
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

# Obter o índice passado via query string (índice da linha)
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()
try:
    id_paciente = int(id_paciente_str)
except ValueError:
    id_paciente = None  # ou algum valor inválido


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

    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
    return df

df = carregar_dados()
df.columns = df.columns.str.strip().str.title()

paciente_df = df[df["Id"].astype(str) == id_paciente_str]

if paciente_df.empty:
    st.error("❌ Paciente não encontrado.")
    st.stop()

paciente = paciente_df.iloc[0]  # pega a linha do paciente correspondente
# Ações
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()  # Remove parâmetros da URL

    # Deleta a página atual (Ficha Clínica) do menu lateral
    delete_page("1_🏠_home", "ficha_clinica")

    # Redireciona para a lista de pacientes
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")
# Exibe os dados do paciente
st.title("🗂️ Ficha Clínica do Paciente")
col1, col2 = st.columns(2)

with col1:
    st.write(f"**Nome:** {paciente.get('Nome', '-')}")
    st.write(f"**Idade:** {paciente.get('Idade', '-')}")
    st.write(f"**Fao:** {paciente.get('Fao', '-')}")
    st.write(f"**Endereço:** {paciente.get('Endereco', '-')}")

with col2:
    st.write(f"**Data De Nascimento:** {paciente.get('Data', '-')}")
    st.write(f"**Sexo:** {paciente.get('Sexo', '-')}")
    st.write(f"**Filiação:** {paciente.get('Filiacao', '-')}")
    st.write(f"**Telefone:** {paciente.get('Telefone', '-')}")

st.markdown("___")

col1, col2 = st.columns(2)
with col1:
    st.write("**História Do Tratamento:**")
    st.write(paciente.get("Historia_Tratamento", "-"))
    st.write(f"**Necessidades Odontológicas:** {paciente.get('Neces_Odonto', '-')}") 
    st.write(f"**Necessidades Cirúrgicas:** {paciente.get('Neces_Cirur', '-')}") 

with col2:
    st.write(f"**Tipo De Fissura:** {paciente.get('Tipo De Fissura', '-')}")
    st.write(f"**Características Oclusais:** {paciente.get('Carac_Oclusais', '-')}")
    st.write(f"**Necessidades Ortodônticas:** {paciente.get('Neces_Orto', '-')}") 
    st.write(f"**Outros:** {paciente.get('Outros', '-')}") 

st.write("**Registro Clínico:**")
st.write(paciente.get("Registro Clínico", "-"))

# --- Função para listar arquivos PDF do paciente ---
def listar_pdfs_paciente(paciente_id_str: str):
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

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

    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    PASTA_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"  # ID da pasta no Google Drive

    query = f"'{PASTA_ID}' in parents and trashed=false and mimeType='application/pdf'"

    arquivos = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, webContentLink)',
            orderBy='name',
            pageToken=page_token
        ).execute()

        arquivos.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    tamanho_prefixo = 3 if int(paciente_id_str) < 10 else 4
    prefixo = f'P{paciente_id_str}#'

    arquivos_filtrados = []

    for arq in arquivos:
        if arq['name'][:tamanho_prefixo] == prefixo[:tamanho_prefixo]:
            arquivos_filtrados.append(arq)


    return arquivos_filtrados

# Exibir arquivos PDF do paciente
st.markdown("## 📄 Exames e Documentos")

arquivos = listar_pdfs_paciente(paciente_id_str=id_paciente_str)

if not arquivos:
    st.info("Nenhum arquivo PDF encontrado para este paciente.")
else:
    for arquivo in arquivos:
        nome = arquivo["name"]
        file_id = arquivo["id"]
        link = f"https://drive.google.com/file/d/{file_id}/preview"

        with st.expander(f"📎 {nome}"):
            st.components.v1.iframe(link, height=500)
