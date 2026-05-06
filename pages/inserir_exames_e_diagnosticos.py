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
# 🎨 PROTOCOLO DE DESIGN FAO/UFAM
# ==========================
st.set_page_config(
    page_title="Diagnóstico e Exames - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS de Alta Fidelidade - Forçando Sobrescrita
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Fonte Global */
        html, body, [class*="css"], .stMarkdown { font-family: 'Inter', sans-serif !important; }

        /* Cabeçalho Institucional Inviolável */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%) !important;
            padding: 1.5rem 2rem !important;
            border-radius: 15px !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 4px 15px rgba(0,74,153,0.2) !important;
        }
        .main-header h1 { 
            color: white !important; 
            font-weight: 700 !important; 
            font-size: 1.8rem !important; 
            margin: 0 !important;
            border: none !important;
        }
        .main-header p { 
            color: rgba(255,255,255,0.9) !important; 
            font-size: 0.9rem !important; 
            margin: 5px 0 0 0 !important;
        }

        /* Card de Resumo do Paciente (Estilo Prontuário) */
        .patient-info-card {
            background-color: #f8fafc !important;
            padding: 1.2rem !important;
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
            margin-bottom: 1.5rem !important;
            display: flex;
            justify-content: space-between;
        }
        .info-group { flex: 1; }
        .info-label { color: #64748b !important; font-size: 0.7rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
        .info-value { color: #1e293b !important; font-size: 1rem !important; font-weight: 700 !important; margin-top: 2px !important; }

        /* Títulos de Seção do Formulário */
        .form-section {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            color: #004a99 !important;
            margin: 2rem 0 1rem 0 !important;
            padding-left: 12px !important;
            border-left: 4px solid #004a99 !important;
        }

        /* Botões Estilizados */
        .stButton > button {
            background-color: #004a99 !important;
            color: white !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            height: 45px !important;
            width: 100% !important;
            border: none !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background-color: #003366 !important;
            box-shadow: 0 4px 10px rgba(0,74,153,0.3) !important;
        }

        /* Limpeza de containers do Streamlit */
        [data-testid="stForm"] { border: none !important; padding: 0 !important; }
        .stTextArea textarea { border-radius: 8px !important; background-color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# ----------------- Funções de Back-end -----------------

def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

@st.cache_data(ttl=300)
def carregar_dados_full():
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

df_p, df_f, sheet_ref, google_creds = carregar_dados_full()

# ----------------- Sidebar e Navegação -----------------

with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.now().date()
    if not df_f.empty:
        df_f["DATA"] = pd.to_datetime(df_f["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_atual = df_f[df_f["DATA"] == hoje]
        for _, r in fila_atual.iterrows():
            p_id = str(r["PACIENTE_ID"]).strip()
            p_nome = df_p[df_p["ID"].astype(str).str.strip() == p_id]["NOME"].values
            st.info(f"👤 **{p_nome[0] if len(p_nome)>0 else p_id}**")
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()

# Navegação de Retorno
c_nav, _ = st.columns([1, 4])
if c_nav.button("⬅️ Voltar para Lista"):
    st.query_params.clear()
    delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# ----------------- Processamento do Paciente -----------------

id_p_str = st.query_params.get("idpaciente", "")
if isinstance(id_p_str, list): id_p_str = id_p_str[0]
id_p_str = str(id_p_str).strip()

paciente_data = df_p[df_p["ID"].astype(str) == id_p_str]
if paciente_data.empty:
    st.error("❌ Erro Crítico: Paciente não localizado no banco de dados.")
    st.stop()

info = paciente_data.iloc[0]

# ----------------- UI Principal -----------------

st.markdown(f"""
    <div class="main-header">
        <h1>🧾 Atualizar Documentos e Diagnóstico</h1>
        <p>Preenchimento de ficha clínica especializada e upload de exames PDF</p>
    </div>
""", unsafe_allow_html=True)

# Card de Resumo (Visualmente Separado)
st.markdown(f"""
    <div class="patient-info-card">
        <div class="info-group">
            <div class="info-label">Paciente</div>
            <div class="info-value">{info['NOME']}</div>
        </div>
        <div class="info-group">
            <div class="info-label">FAO</div>
            <div class="info-value">{info['FAO']}</div>
        </div>
        <div class="info-group">
            <div class="info-label">Idade</div>
            <div class="info-value">{info['IDADE']} anos</div>
        </div>
        <div class="info-group">
            <div class="info-label">Status</div>
            <div class="info-value" style="color: #10b981;">{info['STATUS']}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ----------------- Formulário de Edição -----------------

DRIVE_FOLDER_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"

with st.form("diagnostico_fao_form"):
    st.markdown('<div class="form-section">🩺 Avaliação Clínica e Planejamento</div>', unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        fissura = st.text_area("Tipo de Fissura", value=info.get("TIPO_FISSURA", ""), height=100)
        oclusais = st.text_area("Características Oclusais", value=info.get("CARAC_OCLUSAIS", ""), height=100)
        odonto = st.text_area("Necessidades Odontológicas", value=info.get("NECES_ODONTO", ""), height=100)
        plano = st.text_area("Plano de Tratamento", value=info.get("PLANO_TRATAMENTO", ""), height=100)
    
    with col_r:
        historia = st.text_area("Histórico do Tratamento", value=info.get("HISTORIA_TRATAMENTO", ""), height=100)
        orto = st.text_area("Necessidades Ortodônticas", value=info.get("NECES_ORTO", ""), height=100)
        cirur = st.text_area("Necessidades Cirúrgicas", value=info.get("NECES_CIRUR", ""), height=100)
        diagnostico = st.text_area("Diagnóstico Final", value=info.get("DIAGNOSTICO", ""), height=100)

    st.markdown('<div class="form-section">📂 Documentação e Outros</div>', unsafe_allow_html=True)
    outros = st.text_area("Observações Adicionais", value=info.get("OUTROS", ""), height=80)
    docs_input = st.file_uploader("Anexar Exames (PDF)", type=["pdf"], accept_multiple_files=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn, _ = st.columns([1.2, 2.5])
    executar = c_btn.form_submit_button("💾 SALVAR ALTERAÇÕES")

# ----------------- Lógica de Persistência -----------------

if executar:
    with st.spinner("Sincronizando com a nuvem..."):
        try:
            # Sincronizar DataFrame
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

            # Atualizar Google Sheets
            sheet_ref.update([df_p.columns.values.tolist()] + df_p.values.tolist())

            # Upload Google Drive
            if docs_input:
                drive_svc = build("drive", "v3", credentials=google_creds)
                for arq in docs_input:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                    nome_final = f"P{id_p_str}#{timestamp}_{arq.name}"
                    media = MediaIoBaseUpload(arq, mimetype="application/pdf")
                    meta = {"name": nome_final, "parents": [DRIVE_FOLDER_ID]}
                    drive_svc.files().create(body=meta, media_body=media).execute()

            st.toast("✅ Dados atualizados com sucesso!", icon="🎉")
            time.sleep(1.2)
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")