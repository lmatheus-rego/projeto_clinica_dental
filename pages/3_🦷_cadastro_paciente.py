import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import re

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

# Calcular idade automaticamente
def calcular_idade(data_nasc):
    hoje = datetime.date.today()
    return hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))

# Inicializar estado do formulário
if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "name": "",
        "fao": "",
        "data": datetime.date(2000, 1, 1),
        "sexo": "",
        "filiacao": "",
        "endereco": "",
        "telefone": "",
        "tipo_fissura": "",
        "historia": ""
    }

# Mensagem de sucesso persistente
if "sucesso" not in st.session_state:
    st.session_state.sucesso = False

if st.session_state.sucesso:
    st.success("✅ Paciente cadastrado com sucesso!")
    st.session_state.sucesso = False  # reseta depois de exibir

# Formulário
col1, col2 = st.columns(2)

with st.form(key="include_paciente"):
    with col1:
        input_name = st.text_input("Nome", value=st.session_state.form_data["name"])
        
        # FAO com máscara automática -> 12345/67
        fao_raw = st.text_input("FAO", value=st.session_state.form_data["fao"], placeholder="12345/67")
        fao_formatado = re.sub(r"\D", "", fao_raw)  # só números
        if len(fao_formatado) > 5:
            fao_formatado = f"{fao_formatado[:5]}/{fao_formatado[5:7]}"
        
        input_data = st.date_input(
            "Data de Nascimento",
            value=st.session_state.form_data["data"],
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
            format="DD/MM/YYYY"
        )
        input_sexo = st.selectbox("Sexo", ["", "Masculino", "Feminino"], index=0)

    with col2:
        input_filiacao = st.text_input("Filiação", value=st.session_state.form_data["filiacao"])
        input_endereco = st.text_input("Endereço", value=st.session_state.form_data["endereco"])
        
        # Telefone com máscara
        telefone_raw = st.text_input("Telefone", value=st.session_state.form_data["telefone"], placeholder="(92) 99999-9999")
        telefone_formatado = re.sub(r"\D", "", telefone_raw)  # remove não-dígitos
        if len(telefone_formatado) == 11:  # celular
            telefone_formatado = f"({telefone_formatado[:2]}) {telefone_formatado[2:7]}-{telefone_formatado[7:]}"
        elif len(telefone_formatado) == 10:  # fixo
            telefone_formatado = f"({telefone_formatado[:2]}) {telefone_formatado[2:6]}-{telefone_formatado[6:]}"

        input_tipo_fissura = st.text_input("Tipo de Fissura", value=st.session_state.form_data["tipo_fissura"])
        input_historia_tratamento = st.text_area("História do Tratamento", value=st.session_state.form_data["historia"])

    input_button_submit = st.form_submit_button("Enviar")

# Envio para a planilha com validação obrigatória
if input_button_submit:
    if not input_name.strip():
        st.warning("⚠️ O campo **Nome** é obrigatório.")
    elif not input_data:
        st.warning("⚠️ O campo **Data de Nascimento** é obrigatório.")
    elif not telefone_formatado:
        st.warning("⚠️ O campo **Telefone** é obrigatório.")
    elif not fao_formatado or len(fao_formatado) < 8:
        st.warning("⚠️ O campo **FAO** é obrigatório e deve estar no formato 12345/67.")
    else:
        planilha = conectar_planilha()
        novo_id = gerar_proximo_id(planilha)

        idade = calcular_idade(input_data)

        nova_linha = [
            str(novo_id),
            input_name,
            idade,
            input_data.strftime("%d/%m/%Y"),
            input_sexo,
            input_filiacao,
            input_endereco,
            telefone_formatado,
            fao_formatado,
            input_tipo_fissura,
            input_historia_tratamento,
            "Ativo"
        ]

        planilha.append_row(nova_linha, value_input_option="USER_ENTERED")
        st.session_state.sucesso = True

        # Limpar formulário
        st.session_state.form_data = {
            "name": "",
            "fao": "",
            "data": datetime.date(2000, 1, 1),
            "sexo": "",
            "filiacao": "",
            "endereco": "",
            "telefone": "",
            "tipo_fissura": "",
            "historia": ""
        }

        st.rerun()
