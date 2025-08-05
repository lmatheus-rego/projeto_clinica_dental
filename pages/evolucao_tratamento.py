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

# Exibição
st.write("______________________________")
st.markdown("<h2 style='text-align:center;'>📋 Dados Pessoais do Paciente</h2><hr>", unsafe_allow_html=True)

espaco, col1, col2, col3, espaco2 = st.columns([1, 2, 2, 2, 1])

with col1:
    st.markdown(f"<h4 style='text-align:center;'>👤<br>{paciente_info['NOME']}</h4>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h4 style='text-align:center;'>🧭<br>FAO: {paciente_info['FAO']}</h4>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h4 style='text-align:center;'>🎂<br>{paciente_info['IDADE']} anos</h4>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.write("**Inserir/Alterar Diagnósticos**")

with st.form(key="diagnostico_paciente"):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        input_tipo_fissura = st.text_area("**Tipo de Fissura:**", value=paciente_info.get("TIPO_FISSURA", ""))
        input_historia_tratamento = st.text_area("**Histórico do Tratamento:**", value=paciente_info.get("HISTORIA_TRATAMENTO", ""))
    with col2:
        input_plano = st.text_area("**Plano de Tratamento:**", value=paciente_info.get("PLANO_TRATAMENTO", ""))
        input_diagnostico = st.text_area("**Diagnóstico:**", value=paciente_info.get("DIAGNOSTICO", ""))
    with col3:
        input_odonto = st.text_area("**Necessidades Odontológicas:**", value=paciente_info.get("NECES_ODONTO", ""))
        input_orto = st.text_area("**Necessidades Ortodônticas:**", value=paciente_info.get("NECES_ORTO", ""))
    with col4:
        input_cirur = st.text_area("**Necessidades Cirúrgicas:**", value=paciente_info.get("NECES_CIRUR", ""))
        input_oclusais = st.text_area("**Características Oclusais:**", value=paciente_info.get("CARAC_OCLUSAIS", ""))
    with col5:
        input_outros = st.text_area("**Outros:**", value=paciente_info.get("OUTROS", ""))
        input_docs = st.file_uploader("**Inserir Exames:**", type=["pdf"], accept_multiple_files=True)

    submit = st.form_submit_button("Confirmar")

if submit:
    # Atualiza os dados do paciente no dataframe
    idx = paciente_df.index[0]
    df.at[idx, "TIPO_FISSURA"] = input_tipo_fissura
    df.at[idx, "HISTORIA_TRATAMENTO"] = input_historia_tratamento
    df.at[idx, "NECES_ODONTO"] = input_odonto
    df.at[idx, "CARAC_OCLUSAIS"] = input_oclusais
    df.at[idx, "NECES_ODONTO"] = input_odonto
    df.at[idx, "OUTROS"] = input_outros
    df.at[idx, "PLANO_TRATAMENTO"] = input_plano
    df.at[idx, "NECES_ORTO"] = input_orto
    df.at[idx, "NECES_CIRUR"] = input_cirur
    df.at[idx, "DIAGNOSTICO"] = input_diagnostico

    # Atualiza a planilha com os dados modificados
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

    # Upload para o Google Drive
    if input_docs:
        drive_service = build("drive", "v3", credentials=credentials)
        for arquivo in input_docs:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            nome_arquivo = f"P{id_paciente}#{timestamp}_{arquivo.name}"

            media = MediaIoBaseUpload(arquivo, mimetype="application/pdf")
            file_metadata = {
                "name": nome_arquivo,
                "parents": [PASTA_DRIVE_ID]
            }

            drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()

    st.success("✅ Paciente atualizado com sucesso!")
