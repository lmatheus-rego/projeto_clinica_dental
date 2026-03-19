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

fuso_manaus = pytz.timezone("America/Manaus")

user_info = st.experimental_user
usuario_logado = user_info.get("email") if user_info else "Usuário"

# ==========================
# 🔧 FUNÇÃO PADRÃO DE CAMPO
# ==========================
def get_valor(paciente, *chaves):
    for chave in chaves:
        val = paciente.get(chave)
        if val and str(val).strip() != "":
            return val
    return "-"

# ==========================
# 🔹 Google Sheets
# ==========================
def get_credentials(scopes):
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(info, scopes=scopes)

def carregar_dados():
    gc = gspread.authorize(get_credentials(["https://www.googleapis.com/auth/spreadsheets"]))
    df = pd.DataFrame(gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").sheet1.get_all_records())
    df.columns = df.columns.str.strip().str.upper()
    return df

def carregar_evolucoes():
    gc = gspread.authorize(get_credentials(["https://www.googleapis.com/auth/spreadsheets"]))
    df = pd.DataFrame(gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Registros").get_all_records())
    df["DATA_REGISTRO"] = pd.to_datetime(df.get("DATA_REGISTRO"), errors="coerce", dayfirst=True)
    return df

# ==========================
# 🔹 PDF
# ==========================
def gerar_pdf_ficha(paciente, evolucoes, arquivos, usuario_logado):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    def bloco(label, valor):
        story.append(Paragraph(f"<b>{label}</b>", styles["Heading4"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(valor, styles["Normal"]))
        story.append(Spacer(1, 10))

    # Logo
    logo = Path("assets/ceu_da_boca/logo_embedded.png")
    if logo.exists():
        story.append(Image(str(logo), width=10*cm, height=5*cm))

    story.append(Paragraph("<b>Ficha do Paciente</b>", styles["Title"]))
    story.append(Spacer(1, 10))

    # Dados Clínicos
    story.append(Paragraph("<b>Dados Clínicos</b>", styles["Heading2"]))
    story.append(Spacer(1, 10))

    bloco("Tipo de Fissura", get_valor(paciente, "TIPO_FISSURA", "TIPO DE FISSURA"))
    bloco("Diagnóstico", get_valor(paciente, "DIAGNOSTICO"))
    bloco("Plano de Tratamento", get_valor(paciente, "PLANO_TRATAMENTO"))

    story.append(Spacer(1, 6))

    bloco("História do Tratamento", get_valor(paciente, "HISTORIA_TRATAMENTO"))
    bloco("Características Oclusais", get_valor(paciente, "CARAC_OCLUSAIS"))

    bloco("Necessidade Ortodôntica", get_valor(paciente, "NECES_ORTO"))
    bloco("Necessidade Cirúrgica", get_valor(paciente, "NECES_CIRUR"))
    bloco("Necessidade Odontológica", get_valor(paciente, "NECES_ODONTO"))

    bloco("Outros", get_valor(paciente, "OUTROS"))

    # Evoluções
    story.append(Paragraph("<b>Evoluções</b>", styles["Heading2"]))
    story.append(Spacer(1, 10))

    for _, row in evolucoes.iterrows():
        data = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else ""
        bloco(f"{data}", row.get("EVOLUCAO", ""))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================
# 🔹 UI
# ==========================
st.title("🗂️ Ficha de Paciente")

id_paciente = st.query_params.get("idpaciente", "")
if isinstance(id_paciente, list):
    id_paciente = id_paciente[0]

df = carregar_dados()
paciente_df = df[df["ID"].astype(str) == id_paciente]

if paciente_df.empty:
    st.error("Paciente não encontrado")
    st.stop()

paciente = paciente_df.iloc[0]

df_evolucao = carregar_evolucoes()
evolucoes = df_evolucao[df_evolucao["PACIENTE_ID"].astype(str) == id_paciente]

# ==========================
# 🩺 Dados Clínicos (UI)
# ==========================
with st.expander("🩺 Dados Clínicos", expanded=True):

    def campo(label, valor):
        st.markdown(f"""
        <div style='margin-bottom:15px'>
            <b>{label}</b>
            <div style='margin-top:5px;padding:10px;background:#f8f9fa;border-radius:6px'>
                {valor}
            </div>
        </div>
        """, unsafe_allow_html=True)

    campo("🦷 Tipo de Fissura", get_valor(paciente, "TIPO_FISSURA", "TIPO DE FISSURA"))

    st.markdown("---")

    campo("📋 Diagnóstico", get_valor(paciente, "DIAGNOSTICO"))

    st.markdown("---")

    campo("🧭 Plano de Tratamento", get_valor(paciente, "PLANO_TRATAMENTO"))

    st.markdown("---")

    campo("📜 História do Tratamento", get_valor(paciente, "HISTORIA_TRATAMENTO"))
    campo("🔎 Características Oclusais", get_valor(paciente, "CARAC_OCLUSAIS"))

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        campo("🦷 Necessidade Ortodôntica", get_valor(paciente, "NECES_ORTO"))
        campo("🦷 Necessidade Odontológica", get_valor(paciente, "NECES_ODONTO"))

    with col2:
        campo("🏥 Necessidade Cirúrgica", get_valor(paciente, "NECES_CIRUR"))
        campo("📌 Outros", get_valor(paciente, "OUTROS"))

# ==========================
# 📜 Evoluções
# ==========================
with st.expander("📜 Evoluções", expanded=False):
    for _, row in evolucoes.iterrows():
        data = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else ""
        st.write(f"**{data}** - {row.get('EVOLUCAO','')}")

# ==========================
# 🖨️ PDF
# ==========================
if st.button("🖨️ Gerar PDF"):
    pdf = gerar_pdf_ficha(paciente, evolucoes, [], usuario_logado)
    st.download_button("Download PDF", pdf, file_name="ficha.pdf")