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
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# --------------------------------------------
# 🔹 Configuração e Estilo UI/UX
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
# 🔹 Funções de Dados
# --------------------------------------------

# ----------------- Funções Originais -----------------

def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

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
        return (pd.DataFrame(sh.sheet1.get_all_records()), 
                pd.DataFrame(sh.worksheet("Fila").get_all_records()), 
                pd.DataFrame(sh.worksheet("Registros").get_all_records()), 
                gc)
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
# 🔹 Mapeamento de Campos (Tratamento de Nomes)
# --------------------------------------------
MAPA_CAMPOS = {
    "NOME": "Nome Completo",
    "IDADE": "Idade",
    "DATA": "Data de Nascimento",
    "SEXO": "Gênero/Sexo",
    "FILIACAO": "Filiação",
    "ENDERECO": "Endereço Residencial",
    "TELEFONE": "Telefone de Contato",
    "FAO": "FAO",
    "STATUS": "Status do Paciente",
    "TIPO_FISSURA": "Tipo de Fissura",
    "HISTORIA_TRATAMENTO": "História do Tratamento",
    "CARAC_OCLUSAIS": "Características Oclusais",
    "NECES_ODONTO": "Necessidades Odontológicas",
    "NECES_ORTO": "Necessidades Ortodônticas",
    "NECES_CIRUR": "Necessidades Cirúrgicas",
    "OUTROS": "Outras Informações/Observações",
    "DIAGNOSTICO": "Diagnóstico Clínico",
    "PLANO_TRATAMENTO": "Plano de Tratamento Proposto"
}

# --------------------------------------------
# 🔹 Geração do Relatório PDF
# --------------------------------------------
def gerar_pdf_completo(paciente, evolucoes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>PRONTUÁRIO CLÍNICO</b>", styles['Title']))
    story.append(Paragraph(f"Documento gerado em - {datetime.datetime.now(fuso_manaus).strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 15))

    def add_section(titulo, campos_chaves):
        story.append(Paragraph(f"<b>{titulo}</b>", styles['Heading2']))
        data = []
        for chave in campos_chaves:
            label = MAPA_CAMPOS.get(chave, chave)
            valor = str(paciente.get(chave, "Não informado")).strip()
            if valor == "" or valor == "nan": valor = "Não informado"
            data.append([Paragraph(f"<b>{label}:</b>", styles['Normal']), Paragraph(valor, styles['Normal'])])
        
        t = Table(data, colWidths=[5*cm, 12*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    add_section("1. DADOS IDENTIFICADORES", ["NOME", "IDADE", "DATA", "SEXO", "FILIACAO", "ENDERECO", "TELEFONE", "FAO", "STATUS"])
    add_section("2. AVALIAÇÃO CLÍNICA", ["TIPO_FISSURA", "HISTORIA_TRATAMENTO", "CARAC_OCLUSAIS", "DIAGNOSTICO"])
    add_section("3. NECESSIDADES E PLANEJAMENTO", ["NECES_ODONTO", "NECES_ORTO", "NECES_CIRUR", "PLANO_TRATAMENTO", "OUTROS"])

    story.append(Paragraph("<b>4. HISTÓRICO DE EVOLUÇÕES</b>", styles['Heading2']))
    if not evolucoes.empty:
        for _, row in evolucoes.sort_values("DATA_REGISTRO", ascending=False).iterrows():
            d = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if hasattr(row["DATA_REGISTRO"], "strftime") else str(row["DATA_REGISTRO"])
            story.append(Paragraph(f"<b>{d} - {row.get('USUARIO','-')}:</b> {row.get('EVOLUCAO','')}", styles['Normal']))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Nenhuma evolução registrada.", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------
# 🔹 Interface do Usuário
# --------------------------------------------
df_p, df_f, df_r, gc = carregar_tudo()
if not df_p.empty: df_p.columns = df_p.columns.str.strip().str.upper()

with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    if not df_f.empty:
        df_f["DATA"] = pd.to_datetime(df_f["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_h = df_f[df_f["DATA"] == datetime.date.today()]
        for _, r in fila_h.iterrows():
            n = df_p[df_p["ID"].astype(str).str.strip() == str(r["PACIENTE_ID"]).strip()]["NOME"].values
            st.info(f"👤 {n[0] if len(n)>0 else r['PACIENTE_ID']}")

st.markdown('<div class="main-header"><h1>🗂️ Prontuário Clínico Digital</h1></div>', unsafe_allow_html=True)

id_p = st.query_params.get("idpaciente", "")
if isinstance(id_p, list): id_p = id_p[0]
id_p = str(id_p).strip()

paciente_df = df_p[df_p["ID"].astype(str) == id_p]
if paciente_df.empty:
    st.warning("⚠️ Selecione um paciente na lista para visualizar os detalhes.")
    if st.button("⬅️ Voltar para Lista"): st.switch_page("pages/2_🧑🏻_lista_paciente.py")
    st.stop()

paciente = paciente_df.iloc[0]
evolucoes = df_r[df_r["PACIENTE_ID"].astype(str) == id_p] if not df_r.empty else pd.DataFrame()



# Ações
c1, c2, _ = st.columns([1, 1, 2.5])
with c1:
    if st.button("🔙 Voltar para lista de pacientes"):
        st.query_params.clear()
        if "id_persistente" in st.session_state: del st.session_state.id_persistente
        delete_page("1_🏠_home", "ficha_clinica")
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")
with c2:
    pdf_buffer = gerar_pdf_completo(paciente, evolucoes)
    st.download_button("🖨️ Exportar Ficha Clínica", data=pdf_buffer, file_name=f"Ficha_{paciente.get('NOME','paciente')}.pdf", mime="application/pdf", use_container_width=True)

# Cabeçalho Destaque
st.markdown(f"""
    <div class="patient-header-area">
        <div class="patient-name-label">Prontuário do Paciente</div>
        <div class="patient-name-value">{str(paciente.get('NOME','')).upper()}</div>
    </div>
""", unsafe_allow_html=True)
# --------------------------------------------
# 🔹 Renderização dos Campos na Tela
# --------------------------------------------
def render_campo(chave):
    label = MAPA_CAMPOS.get(chave, chave)
    valor = str(paciente.get(chave, "Não informado")).strip()
    if valor == "" or valor == "nan": valor = "Não informado"
    st.markdown(f'<div class="record-label">{label}</div><div class="record-value">{valor}</div>', unsafe_allow_html=True)

# 1. Dados Pessoais
with st.expander("👤 1. Dados Pessoais e Identificação", expanded=True):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        for k in ["FAO", "IDADE", "DATA", "SEXO"]: render_campo(k)
    with col_p2:
        for k in ["FILIACAO", "TELEFONE", "ENDERECO", "STATUS"]: render_campo(k)

# 2. Avaliação Clínica
with st.expander("🩺 2. Avaliação Clínica e Diagnóstico", expanded=True):
    render_campo("TIPO_FISSURA")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        for k in ["HISTORIA_TRATAMENTO", "CARAC_OCLUSAIS"]: render_campo(k)
    with col_c2:
        for k in ["DIAGNOSTICO", "PLANO_TRATAMENTO"]: render_campo(k)

# 3. Necessidades Específicas
with st.expander("🦷 3. Planejamento e Necessidades Específicas", expanded=True):
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        for k in ["NECES_ODONTO", "NECES_ORTO"]: render_campo(k)
    with col_n2:
        for k in ["NECES_CIRUR", "OUTROS"]: render_campo(k)

# 4. Evoluções
with st.expander("📜 4. Histórico de Evoluções", expanded=True):
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

# 5. Documentos
with st.expander("📎 5. Documentos Associados (Drive)", expanded=False):
    arquivos = listar_arquivos(id_p)
    if arquivos:
        for f in arquivos:
            col_f1, col_f2 = st.columns([4, 1])
            col_f1.markdown(f"📄 **{f['name']}**")
            col_f2.link_button("Abrir", f["webContentLink"], use_container_width=True)
    else:
        st.caption("Nenhum arquivo encontrado.")