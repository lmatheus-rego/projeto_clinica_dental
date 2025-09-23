import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import re

st.set_page_config(page_title="Cadastro de Pacientes", page_icon="🦷", layout="wide")
st.markdown("<h2 style='text-align: center; color: #2C3E50;'>🦷 Cadastro de Pacientes</h2>", unsafe_allow_html=True)

# -------------------------
# Conexão com Google Sheets
# -------------------------
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

# -------------------------
# Funções auxiliares
# -------------------------
def gerar_proximo_id(sheet):
    dados = sheet.get_all_values()
    if len(dados) <= 1:
        return 1
    ids = [int(row[0]) for row in dados[1:] if row[0].isdigit()]
    return max(ids) + 1 if ids else 1

def calcular_idade(data_nasc):
    hoje = datetime.date.today()
    return hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))

def resetar_formulario():
    for key in [
        "input_nome", "input_fao", "input_data", "input_sexo",
        "input_filiacao", "input_endereco", "input_telefone",
        "input_tipo_fissura", "input_historia"
    ]:
        if key in st.session_state:
            del st.session_state[key]

# -------------------------
# Formulário
# -------------------------
with st.form(key="include_paciente"):
    with st.expander("📋 Dados Pessoais", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome *", key="input_nome")
            fao_raw = st.text_input("FAO *", key="input_fao", placeholder="12345/67")
            data_nasc = st.date_input("Data de Nascimento *", value=datetime.date(2000, 1, 1), 
                                      min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today(),
                                      key="input_data", format="DD/MM/YYYY")
            sexo = st.selectbox("Sexo", ["", "Masculino", "Feminino"], key="input_sexo")
        with col2:
            filiacao = st.text_input("Filiação", key="input_filiacao")
            endereco = st.text_input("Endereço", key="input_endereco")
            telefone_raw = st.text_input("Telefone *", key="input_telefone", placeholder="(92) 99999-9999")

    with st.expander("⚕️ Dados Clínicos", expanded=True):
        tipo_fissura = st.text_input("Tipo de Fissura", key="input_tipo_fissura")
        historia = st.text_area("História do Tratamento", key="input_historia")

    submit = st.form_submit_button("✅ Salvar Paciente", use_container_width=True)

# -------------------------
# Processamento
# -------------------------
if submit:
    # Formatadores
    fao = re.sub(r"\D", "", fao_raw)
    if len(fao) > 5:
        fao = f"{fao[:5]}/{fao[5:7]}"

    tel = re.sub(r"\D", "", telefone_raw)
    if len(tel) == 11:
        telefone = f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
    elif len(tel) == 10:
        telefone = f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"
    else:
        telefone = ""

    # Validação
    if not nome.strip():
        st.error("⚠️ O campo **Nome** é obrigatório.")
    elif not data_nasc:
        st.error("⚠️ O campo **Data de Nascimento** é obrigatório.")
    elif not telefone:
        st.error("⚠️ O campo **Telefone** é obrigatório.")
    elif not fao or len(fao) < 8:
        st.error("⚠️ O campo **FAO** é obrigatório e deve estar no formato 12345/67.")
    else:
        planilha = conectar_planilha()
        novo_id = gerar_proximo_id(planilha)
        idade = calcular_idade(data_nasc)

        nova_linha = [
            str(novo_id), nome, idade, data_nasc.strftime("%d/%m/%Y"), sexo,
            filiacao, endereco, telefone, fao, tipo_fissura, historia, "Ativo"
        ]
        planilha.append_row(nova_linha, value_input_option="USER_ENTERED")

        st.success("✅ Paciente cadastrado com sucesso!")
        resetar_formulario()
        st.rerun()
