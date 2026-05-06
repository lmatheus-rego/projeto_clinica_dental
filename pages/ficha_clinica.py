import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import io
import datetime
import pytz
from pathlib import Path

# --------------------------------------------
# 🔹 Configuração da Página e UI (CSS Forçado)
# --------------------------------------------
st.set_page_config(page_title="Ficha do Paciente - Céu da Boca", page_icon="🦷", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        /* Reset de fontes e fundo */
        * { font-family: 'Inter', sans-serif; }
        
        /* CABEÇALHO ULTRA ESTREITO */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 5px 20px; /* Padding mínimo para ser estreito */
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            height: 50px; /* Altura fixa para garantir que seja estreito */
        }
        
        .main-header h1 { 
            margin: 0 !important; 
            font-weight: 700 !important; 
            font-size: 1.3rem !important; 
            color: #FFFFFF !important; /* Branco absoluto */
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }

        /* Ajuste de Botões Padrão Profissional */
        div.stButton > button {
            border-radius: 6px !important;
            height: 35px;
            font-size: 14px;
            font-weight: 600;
            background-color: white;
            color: #004a99;
            border: 1px solid #004a99;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background-color: #004a99;
            color: white;
        }

        /* Estilo dos Expanders */
        .stExpander {
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            margin-bottom: 10px !important;
        }
        
        /* Remove o espaço em branco exagerado do topo do Streamlit */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------
# 🔹 Funções de Dados (Sem alterações na lógica)
# --------------------------------------------
def get_credentials(scopes):
    service_account_info = dict(st.secrets["gcp_service_account"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(service_account_info, scopes=scopes)

@st.cache_data(ttl=300)
def carregar_dados():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = get_credentials(scopes)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").sheet1
    return pd.DataFrame(sheet.get_all_records())

@st.cache_data(ttl=300)
def carregar_evolucoes():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = get_credentials(scopes)
    gc = gspread.authorize(credentials)
    registros_sheet = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Registros")
    df = pd.DataFrame(registros_sheet.get_all_records())
    if "DATA_REGISTRO" in df.columns:
        df["DATA_REGISTRO"] = pd.to_datetime(df["DATA_REGISTRO"], format="%d/%m/%Y", errors="coerce")
    return df

def listar_pdfs_paciente(paciente_id_str: str):
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = get_credentials(SCOPES)
    service = build('drive', 'v3', credentials=creds)
    PASTA_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"
    query = f"'{PASTA_ID}' in parents and trashed=false and mimeType='application/pdf'"
    response = service.files().list(q=query, fields='files(id, name, webContentLink)').execute()
    arquivos = response.get('files', [])
    prefixo = f'P{paciente_id_str}#'
    return [arq for arq in arquivos if arq['name'].startswith(prefixo)]

def gerar_pdf_ficha(paciente, evolucoes, usuario_logado):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Ficha: {paciente.get('Nome')}", styles['Title'])]
    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------
# 🔹 Interface do Usuário
# --------------------------------------------

# Cabeçalho Estreito (Substitui o st.title)
st.markdown("""
    <div class="main-header">
        <h1>🗂️ Ficha Detalhada do Paciente</h1>
    </div>
""", unsafe_allow_html=True)

# Captura de ID dos Query Params
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list): id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

# Barra de Ações (Voltar e Imprimir)
c_nav1, c_nav2, _ = st.columns([1, 1, 2])

# Carregar dados
df = carregar_dados()
df.columns = df.columns.str.strip().str.title()
paciente_df = df[df["Id"].astype(str) == id_paciente_str]

if paciente_df.empty:
    st.error("❌ Paciente não encontrado.")
    if st.button("Voltar"): st.switch_page("pages/2_🧑🏻_lista_paciente.py")
    st.stop()

paciente = paciente_df.iloc[0]

with c_nav1:
    if st.button("⬅️ Voltar para Lista", use_container_width=True):
        st.query_params.clear()
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")

with c_nav2:
    if st.button("🖨️ Gerar PDF", use_container_width=True):
        st.toast("Preparando documento...")
        # Lógica de download aqui...

st.markdown(f"### Paciente: **{paciente.get('Nome')}**")

# --------------------------------------------
# 🔹 Organização dos Dados
# --------------------------------------------

with st.expander("🧾 Dados Pessoais", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Nome:** {paciente.get('Nome', '-')}")
        st.write(f"**Idade:** {paciente.get('Idade', '-')}")
        st.write(f"**Sexo:** {paciente.get('Sexo', '-')}")
    with col2:
        st.write(f"**FAO:** {paciente.get('Fao', '-')}")
        st.write(f"**Telefone:** {paciente.get('Telefone', '-')}")
        st.write(f"**Endereço:** {paciente.get('Endereco', '-')}")

with st.expander("🩺 Informações Clínicas", expanded=False):
    t_fissura = paciente.get('Tipo De Fissura') or paciente.get('Tipo_Fissura') or "-"
    st.info(f"**Tipo de Fissura:** {t_fissura}")
    
    c_clin1, c_clin2 = st.columns(2)
    with c_clin1:
        st.markdown("**Diagnóstico:**")
        st.write(paciente.get("Diagnostico", "-"))
    with c_clin2:
        st.markdown("**Plano de Tratamento:**")
        st.write(paciente.get("Plano_Tratamento", "-"))

with st.expander("📜 Evoluções Recentes", expanded=True):
    df_evol = carregar_evolucoes()
    evolucoes = df_evol[df_evol["PACIENTE_ID"].astype(str) == id_paciente_str] if not df_evol.empty else pd.DataFrame()
    
    if not evolucoes.empty:
        for _, row in evolucoes.sort_values("DATA_REGISTRO", ascending=False).iterrows():
            data_f = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else "S/D"
            st.markdown(f"""
                <div style="background-color:white; padding:10px; border-radius:5px; border-left:4px solid #004a99; margin-bottom:10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <small style="color:#64748b;">📅 {data_f}</small><br>
                    {row.get('EVOLUCAO', '-')}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma evolução registrada.")

with st.expander("📎 Arquivos e Documentos", expanded=False):
    arquivos = listar_pdfs_paciente(id_paciente_str)
    if arquivos:
        for arq in arquivos:
            col_a1, col_a2 = st.columns([4, 1])
            col_a1.write(f"📄 {arq['name']}")
            if col_a2.button("Abrir", key=arq['id']):
                st.markdown(f"[Clique aqui para abrir o arquivo]({arq.get('webContentLink')})")
    else:
        st.caption("Nenhum documento encontrado.")