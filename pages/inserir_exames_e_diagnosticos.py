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
# 🎨 Configuração e Design
# ==========================
st.set_page_config(
    page_title="Atualizar Prontuário - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS de Alta Precisão (Inter Font + Blue Gradient)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Institucional */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white !important;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; color: white !important; }
        .main-header p { margin: 0; opacity: 0.8; font-size: 0.85rem; color: white !important; }

        /* Box de Informação do Paciente */
        .patient-summary {
            background-color: #f8fafc;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-bottom: 1.5rem;
        }
        .record-label { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
        .record-value { color: #1e293b; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }

        /* Seções do Formulário */
        .section-header {
            font-size: 1rem;
            font-weight: 700;
            color: #004a99;
            margin: 1.5rem 0 1rem 0;
            padding-left: 10px;
            border-left: 4px solid #004a99;
        }

        /* Botões */
        div.stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            height: 45px !important;
        }
        
        /* Limpar bordas do form */
        div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
    </style>
""", unsafe_allow_html=True)

# ----------------- Funções de Navegação -----------------
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# ----------------- Carregamento de Dados -----------------
@st.cache_data(ttl=300)
def carregar_dados_sistema():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    service_account_info = {k: v.replace('\\n','\n') if k=='private_key' else v 
                            for k,v in st.secrets['gcp_service_account'].items()}
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    df_p = pd.DataFrame(sh.sheet1.get_all_records())
    df_p.columns = df_p.columns.str.strip().str.upper()
    
    df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
    df_f.columns = df_f.columns.str.strip().str.upper()
    
    return df_p, df_f, sh.sheet1, credentials

df, df_fila, sheet_original, creds = carregar_dados_sistema()

# ----------------- Sidebar Institucional -----------------
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.now().date()
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hj = df_fila[df_fila["DATA"] == hoje]
        for _, r in fila_hj.iterrows():
            pid = str(r["PACIENTE_ID"]).strip()
            nome_p = df[df["ID"].astype(str).str.strip() == pid]["NOME"].values
            st.info(f"👤 **{nome_p[0] if len(nome_p)>0 else pid}**")
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()

# ----------------- Lógica de Redirecionamento -----------------
c_back, _ = st.columns([1, 4])
if c_back.button("⬅️ Lista de Pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# ----------------- Processamento do Paciente -----------------
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list): id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

paciente_df = df[df["ID"].astype(str) == id_paciente_str]
if paciente_df.empty:
    st.error("❌ Paciente não encontrado na base de dados.")
    st.stop()

paciente_info = paciente_df.iloc[0]

# ----------------- Cabeçalho e Identificação -----------------
st.markdown(f"""
    <div class="main-header">
        <h1>📝 Atualizar Documentos e Diagnóstico</h1>
        <p>Prontuário Digital | Edição de Dados Clínicos</p>
    </div>
""", unsafe_allow_html=True)

# Resumo em Card
st.markdown('<div class="patient-summary">', unsafe_allow_html=True)
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
    st.markdown('<p class="record-label">Status Atual</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="record-value">{paciente_info["STATUS"]}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------- Formulário Elegante -----------------
PASTA_DRIVE_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"

with st.form(key="diagnostico_paciente"):
    st.markdown('<p class="section-header">🩺 Avaliação Clínica</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fissura = st.text_area("Tipo de Fissura", value=paciente_info.get("TIPO_FISSURA", ""), height=100)
        oclusais = st.text_area("Características Oclusais", value=paciente_info.get("CARAC_OCLUSAIS", ""), height=100)
        odonto = st.text_area("Necessidades Odontológicas", value=paciente_info.get("NECES_ODONTO", ""), height=100)
        plano = st.text_area("Plano de Tratamento", value=paciente_info.get("PLANO_TRATAMENTO", ""), height=100)
    
    with col2:
        historia = st.text_area("Histórico do Tratamento", value=paciente_info.get("HISTORIA_TRATAMENTO", ""), height=100)
        orto = st.text_area("Necessidades Ortodônticas", value=paciente_info.get("NECES_ORTO", ""), height=100)
        cirur = st.text_area("Necessidades Cirúrgicas", value=paciente_info.get("NECES_CIRUR", ""), height=100)
        diagnostico = st.text_area("Diagnóstico", value=paciente_info.get("DIAGNOSTICO", ""), height=100)

    st.markdown('<p class="section-header">📂 Documentos e Outros</p>', unsafe_allow_html=True)
    outros = st.text_area("Outras Informações", value=paciente_info.get("OUTROS", ""), height=80)
    docs = st.file_uploader("Inserir Exames (PDF)", type=["pdf"], accept_multiple_files=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn, _ = st.columns([1, 2])
    submit = c_btn.form_submit_button("💾 Salvar Alterações")

# ----------------- Processamento do Submit -----------------
if submit:
    with st.spinner("Salvando dados e enviando arquivos..."):
        try:
            # Atualização do DataFrame
            idx = paciente_df.index[0]
            df.at[idx, "TIPO_FISSURA"] = fissura
            df.at[idx, "HISTORIA_TRATAMENTO"] = historia
            df.at[idx, "NECES_ODONTO"] = odonto
            df.at[idx, "CARAC_OCLUSAIS"] = oclusais
            df.at[idx, "OUTROS"] = outros
            df.at[idx, "PLANO_TRATAMENTO"] = plano
            df.at[idx, "NECES_ORTO"] = orto
            df.at[idx, "NECES_CIRUR"] = cirur
            df.at[idx, "DIAGNOSTICO"] = diagnostico

            # Atualização no Google Sheets
            sheet_original.update([df.columns.values.tolist()] + df.values.tolist())

            # Upload de arquivos para o Drive
            if docs:
                drive_service = build("drive", "v3", credentials=creds)
                for arquivo in docs:
                    ts = datetime.now().strftime("%Y%m%d%H%M%S")
                    nome_f = f"P{id_paciente_str}#{ts}_{arquivo.name}"
                    media = MediaIoBaseUpload(arquivo, mimetype="application/pdf")
                    meta = {"name": nome_f, "parents": [PASTA_DRIVE_ID]}
                    drive_service.files().create(body=meta, media_body=media).execute()

            st.toast("✅ Alterações salvas com sucesso!", icon="🎉")
            time.sleep(1.5)
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")