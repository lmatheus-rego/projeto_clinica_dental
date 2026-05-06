import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
import io
import datetime
import pytz
from pathlib import Path

# --------------------------------------------
# 🔹 Configuração e Estilo
# --------------------------------------------
st.set_page_config(page_title="Prontuário - Céu da Boca", page_icon="🦷", layout="wide")
fuso_manaus = pytz.timezone("America/Manaus")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; color: white; }

        .patient-header-area {
            background-color: #f8fafc;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            margin-bottom: 10px;
        }
        .patient-name-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; }
        .patient-name-value { color: #1e293b; font-size: 1.5rem; font-weight: 700; }

        .record-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-top: 10px; }
        .record-value { color: #1e293b; font-size: 1rem; font-weight: 500; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; margin-bottom: 8px; }

        div.stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
        .stExpander { border: 1px solid #f1f5f9 !important; border-radius: 12px !important; margin-bottom: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------
# 🔹 Funções de Dados e Credenciais
# --------------------------------------------
def get_credentials(scopes):
    service_account_info = dict(st.secrets["gcp_service_account"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(service_account_info, scopes=scopes)

@st.cache_data(ttl=300)
def carregar_tudo():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = get_credentials(scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        return pd.DataFrame(sh.sheet1.get_all_records()), pd.DataFrame(sh.worksheet("Fila").get_all_records()), pd.DataFrame(sh.worksheet("Registros").get_all_records()), gc
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), None

def listar_arquivos(paciente_id):
    try:
        creds = get_credentials(['https://www.googleapis.com/auth/drive.readonly'])
        service = build('drive', 'v3', credentials=creds)
        PASTA_ID = "1LFJq0950S2vf9TNyjLKHl6TO4E4YYPdn"
        query = f"'{PASTA_ID}' in parents and trashed=false"
        res = service.files().list(q=query, fields='files(id, name, webContentLink)').execute()
        prefixo = f'P{paciente_id}#'
        return [f for f in res.get('files', []) if f['name'].startswith(prefixo)]
    except: return []

# --------------------------------------------
# 🔹 Relatório PDF Profissional
# --------------------------------------------
def gerar_pdf_completo(paciente, evolucoes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    # Título Institucional
    story.append(Paragraph("<b>PROJETO CÉU DA BOCA - FAO/UFAM</b>", styles['Title']))
    story.append(Paragraph(f"PRONTUÁRIO CLÍNICO DIGITAL - {datetime.datetime.now(fuso_manaus).strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 15))

    def format_table_data(title, data_dict):
        story.append(Paragraph(f"<b>{title}</b>", styles['Heading2']))
        table_data = []
        for k, v in data_dict.items():
            val = str(v) if v and str(v).strip() != "" else "Não informado"
            table_data.append([Paragraph(f"<b>{k}:</b>", styles['Normal']), Paragraph(val, styles['Normal'])])
        
        t = Table(table_data, colWidths=[4*cm, 13*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

    # Dados Pessoais
    dados_pessoais = {
        "Nome": paciente.get('Nome'), "Idade": paciente.get('Idade'), "Sexo": paciente.get('Sexo'),
        "FAO": paciente.get('Fao'), "Telefone": paciente.get('Telefone'), "Data de Nascimento": paciente.get('Data'),
        "Endereço": paciente.get('Endereco'), "Filiação": paciente.get('Filiacao')
    }
    format_table_data("DADOS PESSOAIS", dados_pessoais)

    # Dados Clínicos
    dados_clinicos = {
        "Tipo de Fissura": paciente.get('Tipo De Fissura') or paciente.get('Tipo_Fissura'),
        "História do Tratamento": paciente.get('Historia_Tratamento'),
        "Características Oclusais": paciente.get('Carac_Oclusais'),
        "Diagnóstico": paciente.get('Diagnostico'),
        "Plano de Tratamento": paciente.get('Plano_Tratamento'),
        "Outros": paciente.get('Outros')
    }
    format_table_data("AVALIAÇÃO CLÍNICA", dados_clinicos)

    # Evoluções
    story.append(Paragraph("<b>HISTÓRICO DE EVOLUÇÕES</b>", styles['Heading2']))
    if not evolucoes.empty:
        for _, row in evolucoes.sort_values("DATA_REGISTRO", ascending=False).iterrows():
            d = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if hasattr(row["DATA_REGISTRO"], "strftime") else str(row["DATA_REGISTRO"])
            story.append(Paragraph(f"<b>{d} - {row.get('USUARIO','-')}:</b>", styles['Normal']))
            story.append(Paragraph(str(row.get('EVOLUCAO','')), styles['Normal']))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Nenhuma evolução registrada.", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------
# 🔹 Interface do Usuário
# --------------------------------------------
df_p, df_f, df_r, gc = carregar_tudo()
if not df_p.empty: df_p.columns = df_p.columns.str.strip().str.title()

with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    if not df_f.empty:
        df_f["DATA"] = pd.to_datetime(df_f["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_h = df_f[df_f["DATA"] == datetime.date.today()]
        for _, r in fila_h.iterrows():
            n = df_p[df_p["Id"].astype(str).str.strip() == str(r["PACIENTE_ID"]).strip()]["Nome"].values
            st.info(f"👤 {n[0] if len(n)>0 else r['PACIENTE_ID']}")

st.markdown('<div class="main-header"><h1>🗂️ Prontuário Clínico Digital</h1></div>', unsafe_allow_html=True)

id_p = st.query_params.get("idpaciente", "")
if isinstance(id_p, list): id_p = id_p[0]
id_p = str(id_p).strip()

paciente_df = df_p[df_p["Id"].astype(str) == id_p]
if paciente_df.empty:
    st.warning("Aguardando seleção de paciente.")
    if st.button("⬅️ Voltar para Lista"): st.switch_page("pages/2_🧑🏻_lista_paciente.py")
    st.stop()

paciente = paciente_df.iloc[0]
evolucoes = df_r[df_r["PACIENTE_ID"].astype(str) == id_p] if not df_r.empty else pd.DataFrame()

# Cabeçalho do Paciente (Nome próximo aos dados)
st.markdown(f"""
    <div class="patient-header-area">
        <div class="patient-name-label">Paciente Selecionado</div>
        <div class="patient-name-value">{str(paciente.get('Nome','')).upper()}</div>
    </div>
""", unsafe_allow_html=True)

# Ações
c1, c2, _ = st.columns([1, 1, 2.5])
with c1:
    if st.button("⬅️ Lista de Pacientes", use_container_width=True):
        st.query_params.clear()
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")
with c2:
    pdf_buffer = gerar_pdf_completo(paciente, evolucoes)
    st.download_button("🖨️ Imprimir Ficha Completa", data=pdf_buffer, file_name=f"Ficha_{paciente.get('Nome','paciente')}.pdf", mime="application/pdf", use_container_width=True)

st.markdown("---")

# --------------------------------------------
# 🔹 Corpo da Ficha (Vertical com Expanders)
# --------------------------------------------

def render_field(label, value):
    val = str(value) if value and str(value).strip() != "" else "Não informado"
    st.markdown(f'<div class="record-label">{label}</div><div class="record-value">{val}</div>', unsafe_allow_html=True)

with st.expander("🧾 Dados Cadastrais", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        render_field("Nome Completo", paciente.get("Nome"))
        render_field("Idade", paciente.get("Idade"))
        render_field("Sexo", paciente.get("Sexo"))
        render_field("Prontuário FAO", paciente.get("Fao"))
    with col_b:
        render_field("Telefone de Contato", paciente.get("Telefone"))
        render_field("Data de Nascimento", paciente.get("Data"))
        render_field("Endereço", paciente.get("Endereco"))
        render_field("Filiação", paciente.get("Filiacao"))

with st.expander("🩺 Avaliação Clínica", expanded=True):
    render_field("Tipo de Fissura", paciente.get('Tipo De Fissura') or paciente.get('Tipo_Fissura'))
    c_clin1, c_clin2 = st.columns(2)
    with c_clin1:
        render_field("História do Tratamento", paciente.get("Historia_Tratamento"))
        render_field("Características Oclusais", paciente.get("Carac_Oclusais"))
        render_field("Outros Detalhes", paciente.get("Outros"))
    with c_clin2:
        render_field("Diagnóstico Clínico", paciente.get("Diagnostico"))
        render_field("Plano de Tratamento Proposto", paciente.get("Plano_Tratamento"))

with st.expander("📜 Histórico de Evoluções", expanded=True):
    if not evolucoes.empty:
        evolucoes["DATA_REGISTRO"] = pd.to_datetime(evolucoes["DATA_REGISTRO"], dayfirst=True, errors='coerce')
        for _, row in evolucoes.sort_values("DATA_REGISTRO", ascending=False).iterrows():
            d_str = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else "S/D"
            st.markdown(f"""
                <div style="background-color:#f1f5f9; padding:12px; border-radius:8px; border-left:5px solid #004a99; margin-bottom:10px;">
                    <small style="font-weight:700; color:#004a99;">📅 {d_str} | 👤 {row.get('USUARIO','-')}</small>
                    <div style="margin-top:5px; color:#1e293b; font-size:14px;">{row.get('EVOLUCAO', '-')}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma evolução registrada.")

with st.expander("📎 Documentos Associados", expanded=False):
    arquivos = listar_arquivos(id_p)
    if arquivos:
        for f in arquivos:
            col_f1, col_f2 = st.columns([4, 1])
            col_f1.markdown(f"📄 **{f['name']}**")
            col_f2.link_button("Abrir", f["webContentLink"], use_container_width=True)
    else:
        st.caption("Nenhum arquivo encontrado no Sistema.")