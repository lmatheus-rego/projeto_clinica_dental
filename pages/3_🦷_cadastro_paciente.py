import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

st.set_page_config(page_title="Cadastro de Pacientes", page_icon="🦷", layout="wide")

# ------------------ Estilo ------------------
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #0d6efd;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0b5ed7;
        color: white;
    }
    input.error, select.error, textarea.error {
        border: 2px solid red !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='header'><h2>🦷 Cadastro de Pacientes</h2></div>", unsafe_allow_html=True)

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

def resetar_formulario():
    for key in ["nome", "fao", "data", "sexo", "filiacao", "endereco", "telefone", "tipo_fissura", "historia"]:
        if key in st.session_state:
            del st.session_state[key]

# ------------------ Mensagem Sucesso ------------------
if "sucesso" not in st.session_state:
    st.session_state.sucesso = False

if st.session_state.sucesso:
    st.success("✅ Paciente cadastrado com sucesso!")
    st.session_state.sucesso = False

# ------------------ Formulário ------------------
with st.form("include_paciente"):
    with st.expander("📋 Dados Pessoais", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome *", key="nome")

            # FAO com máscara
            fao_html = """
                <input id="fao" name="fao" placeholder="12345/67" maxlength="8"
                style="width:100%;padding:8px;border-radius:5px;border:1px solid #ccc;" 
                oninput="this.value=this.value.replace(/\\D/g,'').replace(/(\\d{5})(\\d{0,2})/,'$1/$2');">
            """
            fao = components.html(fao_html, height=50)

            data_nasc = st.date_input("Data de Nascimento *", 
                                      value=datetime.date(2000, 1, 1),
                                      min_value=datetime.date(1900, 1, 1),
                                      max_value=datetime.date.today(),
                                      key="data", format="DD/MM/YYYY")
            sexo = st.selectbox("Sexo *", ["", "Masculino", "Feminino"], key="sexo")

        with col2:
            filiacao = st.text_input("Filiação", key="filiacao")
            endereco = st.text_input("Endereço", key="endereco")

            # Telefone com máscara
            telefone_html = """
                <input id="telefone" name="telefone" placeholder="(92) 99999-9999" maxlength="15"
                style="width:100%;padding:8px;border-radius:5px;border:1px solid #ccc;"
                oninput="this.value=this.value.replace(/\\D/g,'')
                .replace(/(\\d{2})(\\d{5})(\\d{4})/,'($1) $2-$3');">
            """
            telefone = components.html(telefone_html, height=50)

    with st.expander("⚕️ Dados Clínicos", expanded=True):
        tipo_fissura = st.text_input("Tipo de Fissura", key="tipo_fissura")
        historia = st.text_area("História do Tratamento", key="historia")

    submit = st.form_submit_button("💾 Salvar Paciente")

# ------------------ Processamento ------------------
if submit:
    erros = []
    if not nome.strip():
        erros.append("Nome")
    if not data_nasc:
        erros.append("Data de Nascimento")
    if not sexo.strip():
        erros.append("Sexo")

    if erros:
        st.error(f"⚠️ Campos obrigatórios não preenchidos: {', '.join(erros)}")
    else:
        planilha = conectar_planilha()
        novo_id = gerar_proximo_id(planilha)
        idade = calcular_idade(data_nasc)

        # 🚨 Pegar FAO e Telefone do backend (aqui placeholders por enquanto)
        fao_valor = st.session_state.get("fao", "")
        telefone_valor = st.session_state.get("telefone", "")

        nova_linha = [
            str(novo_id), nome, idade, data_nasc.strftime("%d/%m/%Y"), sexo,
            filiacao, endereco, telefone_valor, fao_valor, tipo_fissura, historia, "Ativo"
        ]
        planilha.append_row(nova_linha, value_input_option="USER_ENTERED")

        resetar_formulario()
        st.session_state.sucesso = True
        st.rerun()
