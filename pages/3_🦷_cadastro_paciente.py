import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Cadastro de Pacientes")
st.title("Cadastro de Paciente")

# Autenticação Google Sheets
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
    planilha = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
    return planilha.sheet1

# Geração de ID automático
def gerar_proximo_id(sheet):
    dados = sheet.get_all_values()
    if len(dados) <= 1:
        return 1  # Primeira linha é o cabeçalho
    ids = [int(row[0]) for row in dados[1:] if row[0].isdigit()]
    return max(ids) + 1 if ids else 1

# Formulário
col1, col2 = st.columns(2)

with st.form(key="include_paciente"):
    with col1:
        input_name = st.text_input(label="Nome")
        input_fao = st.text_input(label="FAO", placeholder="xxxxx/xx")
        input_idade = st.number_input(label="Idade", format="%d", step=1)
        input_data = st.date_input("Data de Nascimento", format="DD/MM/YYYY")
        input_sexo = st.selectbox("Sexo", ["Masculino", "Feminino"], placeholder="Selecione")

    with col2:
        input_filiacao = st.text_input(label="Filiação")
        input_endereco = st.text_input(label="Endereço")
        input_telefone = st.text_input(label="Telefone", placeholder="(92)XXXXX-XXXX")
        input_tipo_fissura = st.text_input(label="Tipo de Fissura")
        input_historia_tratamento = st.text_area(label="História do Tratamento")

    input_button_submit = st.form_submit_button("Enviar")

# Envio para a planilha
if input_button_submit:
    planilha = conectar_planilha()
    novo_id = gerar_proximo_id(planilha)

    nova_linha = [
        str(novo_id),
        input_name,
        input_idade,
        input_data.strftime("%d/%m/%Y"),
        input_sexo,
        input_filiacao,
        input_endereco,
        input_telefone,
        input_fao,
        input_tipo_fissura,
        input_historia_tratamento,
        "Ativo"
    ]

    planilha.append_row(nova_linha, value_input_option="USER_ENTERED")
    st.success("✅ Paciente cadastrado com sucesso!")
    st.experimental_rerun()
