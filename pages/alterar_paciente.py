import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

st.set_page_config(layout="centered")
st.title("Atualizar Documentos e Diagnóstico")

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
sexo_opcoes = ["Masculino", "Feminino"]

# Exibição
st.write("______________________________")
st.write(f"**Paciente:** {paciente_info['NOME']}")
st.write(f"**FAO:** {paciente_info['FAO']}")
st.write(f"**Tipo de Fissura:** {paciente_info['TIPO_FISSURA']}")
st.write("**História do Tratamento:**")
st.write(f"{paciente_info.get('HISTORIA', '')}")
st.write("______________________________")
st.write("**Inserir Exames e Diagnósticos**")

with st.form(key="diagnostico_paciente"):
    col1, col2 = st.columns(2)
    with col1:
        input_oclusais = st.text_area("**Características Oclusais:**", value=paciente_info.get("CARAC_OCLUSAIS", ""))
        input_odonto = st.text_area("**Necessidades Odontológicas:**", value=paciente_info.get("NECES_ODONTO", ""))
        input_outros = st.text_area("**Outros:**", value=paciente_info.get("OUTROS", ""))
        input_plano = st.text_area("**Plano de Tratamento:**", value=paciente_info.get("PLANO_TRATAMENTO", ""))
    with col2:
        input_orto = st.text_area("**Necessidades Ortodônticas:**", value=paciente_info.get("NECES_ORTO", ""))
        input_cirur = st.text_area("**Necessidades Cirúrgicas:**", value=paciente_info.get("NECES_CIRUR", ""))
        input_diagnostico = st.text_area("**Diagnóstico:**", value=paciente_info.get("DIAGNOSTICO", ""))
        input_docs = st.file_uploader("**Inserir Exames:**", type=["pdf"], accept_multiple_files=True)

    submit = st.form_submit_button("Confirmar")

if submit:
    # Atualizar planilha
    idx = paciente.index[0]
    dados.at[idx, "CARAC_OCLUSAIS"] = input_oclusais
    dados.at[idx, "NECES_ODONTO"] = input_odonto
    dados.at[idx, "OUTROS"] = input_outros
    dados.at[idx, "PLANO_TRATAMENTO"] = input_plano
    dados.at[idx, "NECES_ORTO"] = input_orto
    dados.at[idx, "NECES_CIRUR"] = input_cirur
    dados.at[idx, "DIAGNOSTICO"] = input_diagnostico
    sheet.update([dados.columns.values.tolist()] + dados.values.tolist())

    # Upload para o Google Drive
    if input_docs:
        for arquivo in input_docs:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            nome_arquivo = f"P{id}#{timestamp}_{arquivo.name}"

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

    st.success("Paciente atualizado com sucesso!")
