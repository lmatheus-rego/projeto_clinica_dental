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
# 🔹 Configuração da Página e Estilo (UI/UX)
# --------------------------------------------
st.set_page_config(page_title="Ficha do Paciente - Céu da Boca", page_icon="🦷", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Estreito e Profissional */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 0.8rem 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        .main-header h1 { 
            margin: 0; 
            font-weight: 700; 
            font-size: 1.5rem; 
            color: white !important; 
        }

        /* Botões Estilizados */
        div.stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease;
        }
        
        /* Ajuste de containers de dados */
        .data-container {
            background-color: #f8fafc;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #004a99;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------
# 🔹 Fuso horário e Usuário
# --------------------------------------------
fuso_manaus = pytz.timezone("America/Manaus")
user_info = st.experimental_user
usuario_logado = user_info.get("email") or user_info.get("name") if user_info else "Usuário"

# --------------------------------------------
# 🔹 Funções auxiliares de Dados
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
    
    arquivos = []
    response = service.files().list(q=query, spaces='drive', fields='files(id, name, webContentLink)').execute()
    arquivos.extend(response.get('files', []))
    prefixo = f'P{paciente_id_str}#'
    return [arq for arq in arquivos if arq['name'].startswith(prefixo)]

# --------------------------------------------
# 🔹 Geração do PDF
# --------------------------------------------
def gerar_pdf_ficha(paciente, evolucoes, arquivos, usuario_logado):
    buffer = io.BytesIO()
    nome_paciente = paciente.get('Nome', 'Paciente')
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Ficha_{nome_paciente}", topMargin=1*cm)
    styles = getSampleStyleSheet()
    story = []

    logo_path = Path("assets/ceu_da_boca/logo_embedded.png")
    if logo_path.exists():
        story.append(Image(str(logo_path), width=8*cm, height=4*cm))
        story.append(Spacer(1, 10))

    story.append(Paragraph(f"<b>FICHA CLÍNICA: {nome_paciente.upper()}</b>", styles["Title"]))
    story.append(Paragraph(f"Gerado em: {datetime.datetime.now(fuso_manaus).strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Blocos de Dados no PDF
    for titulo, campos in {
        "🧾 Dados Cadastrais": ["Nome", "Idade", "Sexo", "Telefone", "Fao"],
        "🩺 Informações Clínicas": ["Tipo_Fissura", "Diagnostico", "Plano_Tratamento"]
    }.items():
        story.append(Paragraph(f"<b>{titulo}</b>", styles["Heading2"]))
        for c in campos:
            story.append(Paragraph(f"<b>{c}:</b> {paciente.get(c, '-')}", styles["Normal"]))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------
# 🔹 Interface do Usuário
# --------------------------------------------

# Cabeçalho Customizado
st.markdown("""
    <div class="main-header">
        <h1>🗂️ Detalhes do Prontuário</h1>
    </div>
""", unsafe_allow_html=True)

# Captura de ID
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list): id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

# Ações Superiores
c_nav1, c_nav2, c_nav3 = st.columns([1, 1, 1.5])
with c_nav1:
    if st.button("⬅️ Voltar para Lista", use_container_width=True):
        st.query_params.clear()
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# Carregamento de Dados
df = carregar_dados()
df.columns = df.columns.str.strip().str.title()
paciente_df = df[df["Id"].astype(str) == id_paciente_str]

if paciente_df.empty:
    st.error("❌ Paciente não encontrado na base de dados.")
    st.stop()

paciente = paciente_df.iloc[0]
df_evolucao = carregar_evolucoes()
arquivos = listar_pdfs_paciente(id_paciente_str)
evolucoes_paciente = df_evolucao[df_evolucao["PACIENTE_ID"].astype(str) == id_paciente_str] if "PACIENTE_ID" in df_evolucao.columns else pd.DataFrame()

with c_nav2:
    pdf_buffer = gerar_pdf_ficha(paciente, evolucoes_paciente, arquivos, usuario_logado)
    st.download_button(
        label="🖨️ Exportar PDF",
        data=pdf_buffer,
        file_name=f"Ficha_{paciente.get('Nome','paciente')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.markdown(f"### Paciente: **{paciente.get('Nome', 'Não Identificado')}**")
st.markdown("---")

# --------------------------------------------
# 🔹 Seções de Informação (Expanders)
# --------------------------------------------

with st.expander("👤 Dados Cadastrais", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Nome:** {paciente.get('Nome', '-')}")
        st.write(f"**FAO:** {paciente.get('Fao', '-')}")
        st.write(f"**Idade:** {paciente.get('Idade', '-')}")
    with col2:
        st.write(f"**Sexo:** {paciente.get('Sexo', '-')}")
        st.write(f"**Telefone:** {paciente.get('Telefone', '-')}")
        st.write(f"**Nascimento:** {paciente.get('Data', '-')}")

with st.expander("🦷 Avaliação Clínica", expanded=False):
    t_fissura = paciente.get('Tipo De Fissura') or paciente.get('Tipo_Fissura') or "-"
    st.info(f"**Tipo de Fissura:** {t_fissura}")
    
    c_clin1, c_clin2 = st.columns(2)
    with c_clin1:
        st.write("**História do Tratamento:**")
        st.caption(paciente.get("Historia_Tratamento", "Sem registro"))
        st.write("**Necessidades Ortodônticas:**")
        st.caption(paciente.get("Neces_Orto", "Sem registro"))
    with c_clin2:
        st.write("**Diagnóstico:**")
        st.caption(paciente.get("Diagnostico", "Sem registro"))
        st.write("**Plano de Tratamento:**")
        st.caption(paciente.get("Plano_Tratamento", "Sem registro"))

with st.expander("📜 Histórico de Evoluções", expanded=True):
    if not evolucoes_paciente.empty:
        evolucoes_paciente = evolucoes_paciente.sort_values(by="DATA_REGISTRO", ascending=False)
        for _, row in evolucoes_paciente.iterrows():
            data_s = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else "S/D"
            st.markdown(f"""
                <div class="data-container">
                    <small>📅 {data_s} | 👤 {row.get("USUARIO","")}</small><br>
                    <div style="margin-top:5px;">{row.get("EVOLUCAO","")}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma evolução registrada até o momento.")

with st.expander("📎 Documentos e Exames", expanded=False):
    if not arquivos:
        st.write("Nenhum documento PDF vinculado a este ID.")
    else:
        for arq in arquivos:
            with st.container():
                c_arq1, c_arq2 = st.columns([3, 1])
                c_arq1.write(f"📄 {arq['name']}")
                link_view = f"https://drive.google.com/file/d/{arq['id']}/preview"
                if c_arq2.button("Visualizar", key=arq['id']):
                    st.components.v1.iframe(link_view, height=600)