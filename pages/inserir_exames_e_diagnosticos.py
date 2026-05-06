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
# 🎨 DESIGN SISTÊMICO FAO/UFAM
# ==========================
st.set_page_config(
    page_title="Atualizar Prontuário - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado de Alta Precisão
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        /* Reset de Fonte */
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Institucional Azul UFAM */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.5rem 2rem;
            border-radius: 15px;
            color: white !important;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,74,153,0.15);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.8rem; color: white !important; border: none; }
        .main-header p { margin: 5px 0 0 0; opacity: 0.9; font-size: 0.9rem; color: white !important; }

        /* Card de Resumo do Paciente */
        .patient-card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .label-micro { color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .value-bold { color: #1e293b; font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }

        /* Subtítulos de Seção */
        .form-section-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #004a99;
            margin: 2rem 0 1rem 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .form-section-title::after {
            content: "";
            flex-grow: 1;
            height: 1px;
            background: #e2e8f0;
        }

        /* Ajuste de Inputs e Botões */
        .stTextArea textarea { border-radius: 8px !important; border: 1px solid #cbd5e1 !important; }
        div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
        
        .stButton button {
            background-color: #004a99 !important;
            color: white !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.6rem 2rem !important;
            height: 50px !important;
            width: 100% !important;
            transition: all 0.3s ease;
        }
        .stButton button:hover { background-color: #003366 !important; box-shadow: 0 4px 12px rgba(0,74,153,0.3) !important; }
    </style>
""", unsafe_allow_html=True)

# ----------------- Funções de Dados -----------------
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

@st.cache_data(ttl=300)
def fetch_system_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    svc_info = {k: v.replace('\\n','\n') if k=='private_key' else v for k,v in st.secrets['gcp_service_account'].items()}
    creds = Credentials.from_service_account_info(svc_info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
    
    df_p = pd.DataFrame(sh.sheet1.get_all_records())
    df_p.columns = df_p.columns.str.strip().str.upper()
    df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
    df_f.columns = df_f.columns.str.strip().str.upper()
    return df_p, df_f, sh.sheet1, creds

df_p, df_f, sheet_ptr, google_creds = fetch_system_data()

# ----------------- Sidebar e Navegação -----------------
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.now().date()
    if not df_f.empty:
        df_f["DATA"] = pd.to_datetime(df_f["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_do_dia = df_f[df_f["DATA"] == hoje]
        for _, r in fila_do_dia.iterrows():
            p_id = str(r["PACIENTE_ID"]).strip()
            p_nome = df_p[df_p["ID"].astype(str).str.strip() == p_id]["NOME"].values
            st.info(f"👤 **{p_nome[0] if len(p_nome)>0 else p_id}**")
    st.markdown("---")
    if st.button("🔄 Sincronizar Dados"):
        st.cache_data.clear()
        st.rerun()

# Botão Voltar (Estilo Minimalista)
if st.button("⬅️ Voltar para Lista de Pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# ----------------- Identificação do Paciente -----------------
id_paciente_raw = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_raw, list): id_paciente_raw = id_paciente_raw[0]
id_paciente_raw = str(id_paciente_raw).strip()

paciente_data = df_p[df_p["ID"].astype(str) == id_paciente_raw]
if paciente_data.empty:
    st.error("❌ Paciente não localizado.")
    st.stop()

info = paciente_data.iloc[0]

# ----------------- Layout Principal -----------------
st.markdown(f"""
    <div class="main-header">
        <h1>📝 Atualizar Documentos e Diagnóstico</h1>
        <p>Edição de ficha clínica e anexo de documentos oficiais</p>
    </div>
""", unsafe_allow_html=True)

# Card de Identificação
st.markdown('<div class="patient-card">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<p class="label-micro">Paciente</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="value-bold">{info["NOME"]}</p>', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="label-micro">FAO</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="value-bold">{info["FAO"]}</p>', unsafe_allow_html=True)
with c3:
    st.markdown('<p class="label-micro">Idade</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="value-bold">{info["IDADE"]} anos</p>', unsafe_allow_html=True)
with c4:
    st.markdown('<p class="label-micro">Status</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="value-bold">{info["STATUS"]}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------- Formulário Clínico -----------------
DRIVE_FOLDER_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"

with st.form("edit_clinical_data"):
    st.markdown('<div class="form-section-title">🩺 Avaliação Clínica e Diagnóstico</div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        fissura = st.text_area("Tipo de Fissura", value=info.get("TIPO_FISSURA", ""), height=100)
        oclusais = st.text_area("Características Oclusais", value=info.get("CARAC_OCLUSAIS", ""), height=100)
        odonto = st.text_area("Necessidades Odontológicas", value=info.get("NECES_ODONTO", ""), height=100)
        plano = st.text_area("Plano de Tratamento", value=info.get("PLANO_TRATAMENTO", ""), height=100)
    
    with col_b:
        historia = st.text_area("Histórico do Tratamento", value=info.get("HISTORIA_TRATAMENTO", ""), height=100)
        orto = st.text_area("Necessidades Ortodônticas", value=info.get("NECES_ORTO", ""), height=100)
        cirur = st.text_area("Necessidades Cirúrgicas", value=info.get("NECES_CIRUR", ""), height=100)
        diagnostico = st.text_area("Diagnóstico Final", value=info.get("DIAGNOSTICO", ""), height=100)

    st.markdown('<div class="form-section-title">📂 Arquivos e Documentação</div>', unsafe_allow_html=True)
    
    outros = st.text_area("Observações Adicionais", value=info.get("OUTROS", ""), height=80)
    docs_upload = st.file_uploader("Anexar Exames (Apenas PDF)", type=["pdf"], accept_multiple_files=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_sub, _ = st.columns([1, 2])
    salvar = c_sub.form_submit_button("💾 Salvar Alterações no Prontuário")

# ----------------- Lógica de Salvamento -----------------
if salvar:
    with st.spinner("Sincronizando com a nuvem..."):
        try:
            # Update Local DF
            idx = paciente_data.index[0]
            df_p.at[idx, "TIPO_FISSURA"] = fissura
            df_p.at[idx, "HISTORIA_TRATAMENTO"] = historia
            df_p.at[idx, "NECES_ODONTO"] = odonto
            df_p.at[idx, "CARAC_OCLUSAIS"] = oclusais
            df_p.at[idx, "OUTROS"] = outros
            df_p.at[idx, "PLANO_TRATAMENTO"] = plano
            df_p.at[idx, "NECES_ORTO"] = orto
            df_p.at[idx, "NECES_CIRUR"] = cirur
            df_p.at[idx, "DIAGNOSTICO"] = diagnostico

            # Push to Google Sheets
            sheet_ptr.update([df_p.columns.values.tolist()] + df_p.values.tolist())

            # Push to Google Drive
            if docs_upload:
                drive_svc = build("drive", "v3", credentials=google_creds)
                for arq in docs_upload:
                    ts = datetime.now().strftime("%Y%m%d%H%M")
                    nome_f = f"P{id_paciente_raw}#{ts}_{arq.name}"
                    media = MediaIoBaseUpload(arq, mimetype="application/pdf")
                    meta = {"name": nome_f, "parents": [DRIVE_FOLDER_ID]}
                    drive_svc.files().create(body=meta, media_body=media).execute()

            st.toast("✅ Dados atualizados com sucesso!", icon="🎉")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")