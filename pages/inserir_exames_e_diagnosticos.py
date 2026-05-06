import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import time
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# ==========================
# 🎨 Configuração e Design Elegante
# ==========================
st.set_page_config(
    page_title="Atualizar Diagnóstico - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profissional "Céu da Boca"
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            color: white !important;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.8rem; color: white !important; border: none; }

        .patient-box {
            background-color: #f8fafc;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-bottom: 1.5rem;
        }
        .record-label { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
        .record-value { color: #1e293b; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }

        .section-title {
            font-size: 1rem; font-weight: 700; color: #004a99;
            margin: 1.5rem 0 10px 0; border-left: 4px solid #004a99; padding-left: 10px;
        }
        
        div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
    </style>
""", unsafe_allow_html=True)

# ----------------- Funções Originais -----------------

def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

def carregar_dados():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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
    # Duas credenciais para evitar o erro 'AuthorizedSession'
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    creds_drive = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    
    gc = gspread.authorize(credentials)
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

    df = pd.DataFrame(sheet.get_all_records())
    df.columns = df.columns.str.strip().str.upper()
    return df, sheet, creds_drive

# ----------------- Gestão do ID (Solução do Erro) -----------------
# Pega o ID da URL se ele existir
id_url = st.query_params.get("idpaciente", "")
if isinstance(id_url, list): id_url = id_url[0]

# Salva na memória da sessão para não perder no clique do botão
if id_url:
    st.session_state.id_persistente = str(id_url).strip()

if "id_persistente" in st.session_state:
    id_paciente_str = st.session_state.id_persistente
else:
    st.error("❌ Paciente não localizado nos parâmetros.")
    st.stop()

# ----------------- Interface e Dados -----------------
df, sheet, credentials_drive = carregar_dados()

# Botão Voltar Original
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    if "id_persistente" in st.session_state: del st.session_state.id_persistente
    delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# Filtro do Paciente
paciente_df = df[df["ID"].astype(str) == id_paciente_str]
if paciente_df.empty:
    st.error(f"❌ Paciente ID {id_paciente_str} não encontrado na planilha.")
    st.stop()

paciente_info = paciente_df.iloc[0]

# Cabeçalho Visual
st.markdown(f"""
    <div class="main-header">
        <h1>📝 Atualizar Documentos e Diagnóstico</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="patient-box">', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.markdown(f'<p class="record-label">Paciente</p><p class="record-value">{paciente_info["NOME"]}</p>', unsafe_allow_html=True)
c2.markdown(f'<p class="record-label">FAO</p><p class="record-value">{paciente_info["FAO"]}</p>', unsafe_allow_html=True)
c3.markdown(f'<p class="record-label">Idade</p><p class="record-value">{paciente_info["IDADE"]} anos</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------- Formulário -----------------
PASTA_DRIVE_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"

with st.form(key="diagnostico_paciente"):
    st.markdown('<p class="section-title">🩺 Avaliação Clínica</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        input_tipo_fissura = st.text_area("**Tipo de Fissura:**", value=paciente_info.get("TIPO_FISSURA", ""), height=100)
        input_oclusais = st.text_area("**Características Oclusais:**", value=paciente_info.get("CARAC_OCLUSAIS", ""), height=100)
        input_odonto = st.text_area("**Necessidades Odontológicas:**", value=paciente_info.get("NECES_ODONTO", ""), height=100)
        input_outros = st.text_area("**Outros:**", value=paciente_info.get("OUTROS", ""), height=100)
        input_plano = st.text_area("**Plano de Tratamento:**", value=paciente_info.get("PLANO_TRATAMENTO", ""), height=100)
    with col2:
        input_historia_tratamento = st.text_area("**Histórico do Tratamento:**", value=paciente_info.get("HISTORIA_TRATAMENTO", ""), height=100)
        input_orto = st.text_area("**Necessidades Ortodônticas:**", value=paciente_info.get("NECES_ORTO", ""), height=100)
        input_cirur = st.text_area("**Necessidades Cirúrgicas:**", value=paciente_info.get("NECES_CIRUR", ""), height=100)
        input_diagnostico = st.text_area("**Diagnóstico:**", value=paciente_info.get("DIAGNOSTICO", ""), height=100)
        input_docs = st.file_uploader("**Inserir Exames (PDF):**", type=["pdf"], accept_multiple_files=True)

    submit = st.form_submit_button("Confirmar")

if submit:
    with st.spinner("Salvando alterações..."):
        try:
            # 1. Atualizar Planilha
            idx = paciente_df.index[0]
            updates = {
                "TIPO_FISSURA": input_tipo_fissura,
                "HISTORIA_TRATAMENTO": input_historia_tratamento,
                "NECES_ODONTO": input_odonto,
                "CARAC_OCLUSAIS": input_oclusais,
                "OUTROS": input_outros,
                "PLANO_TRATAMENTO": input_plano,
                "NECES_ORTO": input_orto,
                "NECES_CIRUR": input_cirur,
                "DIAGNOSTICO": input_diagnostico
            }
            for col, val in updates.items():
                df.at[idx, col] = val
            
            sheet.update([df.columns.values.tolist()] + df.values.tolist())

            # 2. Upload para o Drive (Com credencial limpa)
            if input_docs:
                drive_service = build("drive", "v3", credentials=credentials_drive, static_discovery=False)
                for arquivo in input_docs:
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    nome_arquivo = f"P{id_paciente_str}#{timestamp}_{arquivo.name}"
                    media = MediaIoBaseUpload(io.BytesIO(arquivo.read()), mimetype="application/pdf")
                    meta = {"name": nome_arquivo, "parents": [PASTA_DRIVE_ID]}
                    drive_service.files().create(body=meta, media_body=media).execute()

            st.success("✅ Paciente atualizado com sucesso!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")