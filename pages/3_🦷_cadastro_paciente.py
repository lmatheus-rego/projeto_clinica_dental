import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import re

st.set_page_config(page_title="Cadastro de Pacientes", page_icon="🦷", layout="wide")

# 🔹 Título
st.title("🦷 Cadastro de Pacientes")

# ------------------ Google Sheets ------------------
def conectar_planilha():
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    service_account_info = {k: v.replace('\\n','\n') if k=="private_key" else v for k,v in st.secrets["gcp_service_account"].items()}
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").sheet1

def gerar_proximo_id(sheet):
    dados = sheet.get_all_values()
    if len(dados) <= 1:
        return 1
    ids = [int(row[0]) for row in dados[1:] if row[0].isdigit()]
    return max(ids) + 1 if ids else 1

def calcular_idade(data_nasc):
    hoje = datetime.date.today()
    return hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))

# ------------------ Inicializar session_state ------------------
campos = ["nome","fao","data","sexo","filiacao","endereco","telefone","tipo_fissura","historia","sucesso"]
if "sucesso" not in st.session_state:
    st.session_state.sucesso = False

for campo in campos:
    if campo not in st.session_state:
        if campo == "data":
            st.session_state[campo] = datetime.date(2000,1,1)
        else:
            st.session_state[campo] = ""

# ------------------ Função para resetar formulário ------------------
def resetar_formulario():
    for campo in campos:
        if campo == "data":
            st.session_state[campo] = datetime.date(2000,1,1)
        elif campo != "sucesso":
            st.session_state[campo] = ""
    st.session_state.sucesso = True

# ------------------ Formulário ------------------
with st.form("include_paciente"):
    
    with st.expander("📋 Dados Pessoais", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome *", key="nome")
            fao = st.text_input("FAO", placeholder="12345/67", key="fao")
            data_nasc = st.date_input("Data de Nascimento *",
                                      value=st.session_state.data,
                                      min_value=datetime.date(1900,1,1),
                                      max_value=datetime.date.today(),
                                      key="data", format="DD/MM/YYYY")
            sexo = st.selectbox("Sexo *", ["", "Masculino", "Feminino"], key="sexo")
        with col2:
            filiacao = st.text_input("Filiação", key="filiacao")
            endereco = st.text_input("Endereço", key="endereco")
            telefone = st.text_input("Telefone", placeholder="(92) 99999-9999", key="telefone")
    
    with st.expander("⚕️ Dados Clínicos", expanded=True):
        tipo_fissura = st.text_input("Tipo de Fissura", key="tipo_fissura")
        historia = st.text_area("História do Tratamento", key="historia")

    submit = st.form_submit_button("💾 Salvar Paciente", on_click=resetar_formulario)

# ------------------ Mensagem de sucesso ------------------
if st.session_state.sucesso:
    st.success("✅ Paciente cadastrado com sucesso!")
    st.session_state.sucesso = False

# ------------------ Processamento ------------------
if submit:
    erros = []
    if not nome.strip():
        erros.append("Nome")
    if not data_nasc:
        erros.append("Data de Nascimento")
    if not sexo.strip():
        erros.append("Sexo")
    if fao.strip() and not re.fullmatch(r"\d{5}/\d{2}", fao.strip()):
        erros.append("FAO inválido (use formato 12345/67)")
    if telefone.strip() and not re.fullmatch(r"(\(\d{2}\)\d{8,9}|\(\d{2}\)\d{5}-\d{4}|\d{11})", telefone.strip()):
        erros.append("Telefone inválido (use formatos: 92999999999, (92)999999999, (92)99999-9999)")

    if erros:
        st.error(f"⚠️ Corrija os seguintes campos: {', '.join(erros)}")
    else:
        planilha = conectar_planilha()
        novo_id = gerar_proximo_id(planilha)
        idade = calcular_idade(data_nasc)

        nova_linha = [
            str(novo_id), nome, idade, data_nasc.strftime("%d/%m/%Y"), sexo,
            filiacao, endereco, telefone, fao, tipo_fissura, historia, "Ativo"
        ]
        planilha.append_row(nova_linha, value_input_option="USER_ENTERED")
