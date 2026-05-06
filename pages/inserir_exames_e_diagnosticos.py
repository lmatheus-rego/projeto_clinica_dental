import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import time
from pathlib import Path
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
    page_title="Exames e Diagnóstico - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profissional Padrão "Céu da Boca"
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Gradient */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white !important;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; color: white !important; border: none; }
        .main-header p { margin: 0; opacity: 0.8; font-size: 0.85rem; color: white !important; }

        /* Card de Informações do Paciente */
        .patient-box {
            background-color: #f8fafc;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-bottom: 1.5rem;
        }
        .record-label { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
        .record-value { color: #1e293b; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }

        /* Estilo do Formulário */
        div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
        
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            color: #004a99;
            margin: 1.5rem 0 10px 0;
            border-left: 4px solid #004a99;
            padding-left: 10px;
        }

        /* Botão Confirmar Original mas com Estilo */
        button[kind="primaryFormSubmit"] {
            background-color: #004a99 !important;
            color: white !important;
            width: 100% !important;
            height: 45px !important;
            font-weight: 700 !important;
        }
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
    
    # Credenciais para gspread
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    # Credenciais limpas para o Drive (Para evitar o erro AuthorizedSession)
    creds_drive = Credentials.from_service_account_info(service_account_info, scopes=scopes)

    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJj97cs" # Sua Planilha
    sheet = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").sheet1

    df = pd.DataFrame(sheet.get_all_records())
    df.columns = df.columns.str.strip().str.upper()
    
    # Carregar fila para a sidebar
    try:
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        df_fila = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        df_fila.columns = df_fila.columns.str.strip().str.upper()
    except:
        df_fila = pd.DataFrame()

    return df, df_fila, sheet, creds_drive

# ----------------- Execução de Dados -----------------
df, df_fila, sheet, credentials_drive = carregar_dados()

# Sidebar Padrão
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.now().date()
    if not df_fila.empty:
        df_fila["DATA_DT"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA_DT"] == hoje]
        for _, r in fila_hoje.iterrows():
            pid = str(r["PACIENTE_ID"]).strip()
            nome_p = df[df["ID"].astype(str).str.strip() == pid]["NOME"].values
            st.info(f"👤 **{nome_p[0] if len(nome_p)>0 else pid}**")
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()

# ----------------- Função Voltar Original -----------------
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# ----------------- Identificação -----------------
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list): id_paciente_str = id_paciente_str[0]
id_paciente_str = str(id_paciente_str).strip()

paciente_df = df[df["ID"].astype(str) == id_paciente_str]
if paciente_df.empty:
    st.error("❌ Paciente não encontrado.")
    st.stop()

paciente_info = paciente_df.iloc[0]

# UI de Identificação
st.markdown(f"""
    <div class="main-header">
        <h1>Atualizar Documentos e Diagnóstico</h1>
        <p>Prontuário Digital - Faculdade de Odontologia</p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="patient-box">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<p class="record-label">Paciente</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="record-value">{paciente_info["NOME"]}</p>', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="record-label">FAO</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="record-value">{paciente_info["FAO"]}</p>', unsafe_allow_html=True)
with c3:
    st.markdown('<p class="record-label">Idade</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="record-value">{paciente_info["IDADE"]} anos</p>', unsafe_allow_html=True)
with c4:
    st.markdown('<p class="record-label">Status</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="record-value">{paciente_info["STATUS"]}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------- Formulário (Estrutura Original) -----------------
PASTA_DRIVE_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"

with st.form(key="diagnostico_paciente"):
    st.markdown('<p class="section-title">🩺 Avaliação Clínica e Planejamento</p>', unsafe_allow_html=True)
    
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
        input_docs = st.file_uploader("**Inserir Exames:**", type=["pdf"], accept_multiple_files=True)

    submit = st.form_submit_button("Confirmar")

# ----------------- Lógica de Salvamento Original (Corrigida) -----------------
if submit:
    with st.spinner("Salvando alterações..."):
        try:
            # Atualiza os dados do paciente no dataframe
            idx = paciente_df.index[0]
            df.at[idx, "TIPO_FISSURA"] = input_tipo_fissura
            df.at[idx, "HISTORIA_TRATAMENTO"] = input_historia_tratamento
            df.at[idx, "NECES_ODONTO"] = input_odonto
            df.at[idx, "CARAC_OCLUSAIS"] = input_oclusais
            df.at[idx, "OUTROS"] = input_outros
            df.at[idx, "PLANO_TRATAMENTO"] = input_plano
            df.at[idx, "NECES_ORTO"] = input_orto
            df.at[idx, "NECES_CIRUR"] = input_cirur
            df.at[idx, "DIAGNOSTICO"] = input_diagnostico

            # Atualiza a planilha (Usando a lista de colunas para garantir ordem)
            sheet.update([df.columns.values.tolist()] + df.values.tolist())

            # Upload para o Google Drive com a credencial corrigida
            if input_docs:
                # build() agora usa a credencial limpa
                drive_service = build("drive", "v3", credentials=credentials_drive, static_discovery=False)
                for arquivo in input_docs:
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    nome_arquivo = f"P{id_paciente_str}#{timestamp}_{arquivo.name}"

                    # Leitura segura do arquivo para o Drive
                    media = MediaIoBaseUpload(io.BytesIO(arquivo.read()), mimetype="application/pdf")
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
            time.sleep(1.5)
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")