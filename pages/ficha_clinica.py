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
# 🔹 Configuração da Página e UI Profissional
# --------------------------------------------
st.set_page_config(page_title="Ficha do Paciente - Céu da Boca", page_icon="🦷", layout="wide")

fuso_manaus = pytz.timezone("America/Manaus")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }
        
        /* CABEÇALHO PROPORCIONAL */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; color: white; }

        /* NOME DO PACIENTE PROFISSIONAL */
        .patient-name-title {
            color: #1e293b;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 5px;
        }

        /* LABELS E VALORES */
        .record-label { color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
        .record-value { color: #1e293b; font-size: 1.05rem; font-weight: 500; margin-bottom: 15px; }

        /* BOTÕES */
        div.stButton > button { border-radius: 8px !important; font-weight: 600 !important; height: 38px; }
        
        .stExpander { border: 1px solid #f1f5f9 !important; border-radius: 12px !important; }
        .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------
# 🔹 Funções de Dados e PDF
# --------------------------------------------
def get_credentials(scopes):
    service_account_info = dict(st.secrets["gcp_service_account"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(service_account_info, scopes=scopes)

@st.cache_data(ttl=300)
def carregar_dados_ficha():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = get_credentials(scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        df_p = pd.DataFrame(sh.sheet1.get_all_records())
        df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        df_r = pd.DataFrame(sh.worksheet("Registros").get_all_records())
        return df_p, df_f, df_r, gc
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), None

def gerar_pdf_ficha(paciente, evolucoes, usuario_logado):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Título do PDF
    story.append(Paragraph(f"<b>FICHA CLÍNICA: {paciente.get('Nome', '').upper()}</b>", styles['Title']))
    story.append(Paragraph(f"Emitido em: {datetime.datetime.now(fuso_manaus).strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Seção Dados
    story.append(Paragraph("<b>DADOS PESSOAIS</b>", styles['Heading2']))
    for label, key in [("Nome", "Nome"), ("Idade", "Idade"), ("Sexo", "Sexo"), ("FAO", "Fao"), ("Telefone", "Telefone")]:
        story.append(Paragraph(f"<b>{label}:</b> {paciente.get(key, '-')}", styles['Normal']))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>AVALIAÇÃO CLÍNICA</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Tipo de Fissura:</b> {paciente.get('Tipo De Fissura', '-')}", styles['Normal']))
    story.append(Paragraph(f"<b>Diagnóstico:</b> {paciente.get('Diagnostico', '-')}", styles['Normal']))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>EVOLUÇÕES</b>", styles['Heading2']))
    if not evolucoes.empty:
        for _, row in evolucoes.sort_values("DATA_REGISTRO", ascending=False).iterrows():
            data_str = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if hasattr(row["DATA_REGISTRO"], "strftime") else str(row["DATA_REGISTRO"])
            story.append(Paragraph(f"<b>{data_str}:</b> {row.get('EVOLUCAO', '-')}", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------
# 🔹 Inicialização
# --------------------------------------------
df_pacientes, df_fila, df_registros, gc = carregar_dados_ficha()
if not df_pacientes.empty:
    df_pacientes.columns = df_pacientes.columns.str.strip().str.title()

# Sidebar
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.date.today()
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_h = df_fila[df_fila["DATA"] == hoje]
        for _, r in fila_h.iterrows():
            p_nome = df_pacientes[df_pacientes["Id"].astype(str).str.strip() == str(r["PACIENTE_ID"]).strip()]["Nome"].values
            st.info(f"👤 {p_nome[0] if len(p_nome)>0 else 'ID:'+str(r['PACIENTE_ID'])}")

# Cabeçalho
st.markdown('<div class="main-header"><h1>🗂️ Prontuário do Paciente</h1></div>', unsafe_allow_html=True)

id_paciente = st.query_params.get("idpaciente", "")
if isinstance(id_paciente, list): id_paciente = id_paciente[0]

paciente_df = df_pacientes[df_pacientes["Id"].astype(str) == str(id_paciente).strip()]

if paciente_df.empty:
    st.warning("Paciente não selecionado.")
    if st.button("⬅️ Voltar para Lista"): st.switch_page("pages/2_🧑🏻_lista_paciente.py")
    st.stop()

paciente = paciente_df.iloc[0]
evolucoes = df_registros[df_registros["PACIENTE_ID"].astype(str) == str(id_paciente).strip()] if not df_registros.empty else pd.DataFrame()

# Nome do Paciente (Design Profissional)
st.markdown(f'<div class="patient-name-title">{paciente.get("Nome", "").upper()}</div>', unsafe_allow_html=True)

# Ações
c1, c2, _ = st.columns([1, 1, 2.5])
with c1:
    if st.button("⬅️ Voltar", use_container_width=True):
        st.query_params.clear()
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")

with c2:
    # PDF Funcional
    pdf_data = gerar_pdf_ficha(paciente, evolucoes, "Usuário Logado")
    st.download_button(
        label="🖨️ Exportar Ficha",
        data=pdf_data,
        file_name=f"Ficha_{paciente.get('Nome','paciente')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.markdown("---")

# --------------------------------------------
# 🔹 Corpo da Ficha
# --------------------------------------------
t1, t2 = st.tabs(["📋 Dados e Diagnóstico", "📜 Histórico de Evolução"])

with t1:
    with st.expander("🧾 Dados Cadastrais", expanded=True):
        col1, col2 = st.columns(2)
        campos = [
            (col1, "Prontuário FAO", paciente.get('Fao')),
            (col1, "Idade", f"{paciente.get('Idade')} anos"),
            (col1, "Sexo", paciente.get('Sexo')),
            (col2, "Telefone", paciente.get('Telefone')),
            (col2, "Nascimento", paciente.get('Data')),
            (col2, "Endereço", paciente.get('Endereco'))
        ]
        for col, lab, val in campos:
            col.markdown(f'<p class="record-label">{lab}</p><p class="record-value">{val or "-"}</p>', unsafe_allow_html=True)

    with st.expander("🩺 Avaliação Clínica", expanded=True):
        st.info(f"**TIPO DE FISSURA:** {paciente.get('Tipo De Fissura', 'Não informado')}")
        c_c1, c_c2 = st.columns(2)
        clin = [
            (c_c1, "Diagnóstico", "Diagnostico"),
            (c_c1, "Plano de Tratamento", "Plano_Tratamento"),
            (c_c2, "História do Tratamento", "Historia_Tratamento"),
            (c_c2, "Necessidades Ortodônticas", "Neces_Orto")
        ]
        for col, lab, key in clin:
            col.markdown(f'<p class="record-label">{lab}</p><p class="record-value">{paciente.get(key) or "Sem registros"}</p>', unsafe_allow_html=True)

with t2:
    if not evolucoes.empty:
        evolucoes["DATA_REGISTRO"] = pd.to_datetime(evolucoes["DATA_REGISTRO"], dayfirst=True, errors='coerce')
        for _, row in evolucoes.sort_values("DATA_REGISTRO", ascending=False).iterrows():
            d_str = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else "S/D"
            st.markdown(f"""
                <div style="background-color:#f8fafc; padding:12px; border-radius:10px; border-left:5px solid #004a99; margin-bottom:12px;">
                    <small style="font-weight:700; color:#004a99;">📅 {d_str} | 👤 {row.get('USUARIO','-')}</small>
                    <div style="margin-top:5px; color:#1e293b;">{row.get('EVOLUCAO', '-')}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma evolução registrada.")