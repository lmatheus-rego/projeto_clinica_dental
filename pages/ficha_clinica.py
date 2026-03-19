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
# 🔹 Definir fuso horário de Manaus
# --------------------------------------------
fuso_manaus = pytz.timezone("America/Manaus")

# --------------------------------------------
# 🔹 Capturar o usuário logado
# --------------------------------------------
user_info = st.experimental_user
if user_info:
    usuario_logado = user_info.get("email") or user_info.get("name")
else:
    usuario_logado = "Usuário não logado"

# --------------------------------------------
# 🔹 Funções auxiliares
# --------------------------------------------
def get_credentials(scopes):
    """Cria credenciais Google sem alterar st.secrets"""
    service_account_info = dict(st.secrets["gcp_service_account"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(service_account_info, scopes=scopes)

def carregar_dados():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = get_credentials(scopes)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").sheet1
    df = pd.DataFrame(sheet.get_all_records())
    return df

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
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, webContentLink)',
            orderBy='name',
            pageToken=page_token
        ).execute()
        arquivos.extend(response.get('files', []))
        page_token = response.get('nextPageToken')
        if not page_token:
            break

    prefixo = f'P{paciente_id_str}#'
    return [arq for arq in arquivos if arq['name'].startswith(prefixo)]

# --------------------------------------------
# 🔹 Geração do PDF com logo
# --------------------------------------------
def gerar_pdf_ficha(paciente, evolucoes, arquivos, usuario_logado):
    buffer = io.BytesIO()

    nome_paciente = paciente.get('Nome', 'Paciente')
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"Ficha de {nome_paciente}",
        author=usuario_logado,
        topMargin=0*cm,
        bottomMargin=0*cm
    )

    styles = getSampleStyleSheet()
    story = []

    # Caminho do logo
    logo_path = Path("assets/ceu_da_boca/logo_embedded.png")
    if logo_path.exists():
        # Ajuste da largura (12cm = largura total do PDF ~ A4)
        story.append(Image(str(logo_path), width=10*cm, height=6*cm))
        story.append(Spacer(1, 6))

    # Cabeçalho
    story.append(Paragraph(f"<b>Ficha de Paciente - {nome_paciente}</b>", styles["Title"]))
    story.append(Paragraph(
        f"Gerado em: {datetime.datetime.now(fuso_manaus).strftime('%d/%m/%Y %H:%M')} por {usuario_logado}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    def add_title(text):
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>{text}</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))

    # 🧾 Dados do Paciente
    add_title("🧾 Dados do Paciente")
    for campo in ["Nome", "Idade", "Sexo", "Data", "Endereco", "Filiacao", "Telefone", "Fao"]:
        story.append(Paragraph(f"<b>{campo}:</b> {paciente.get(campo, '-')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # 🩺 Dados Clínicos
    add_title("🩺 Dados Clínicos")
    for campo in [
        "Tipo De Fissura", "Historia_Tratamento", "Carac_Oclusais",
        "Neces_Orto", "Neces_Cirur", "Neces_Odonto", "Outros"
    ]:
        story.append(Paragraph(f"<b>{campo.replace('_', ' ')}:</b> {paciente.get(campo, '-')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # 📜 Evoluções
    add_title("📜 Evoluções do Paciente")
    if not evolucoes.empty:
        evolucoes_sorted = evolucoes.sort_values(by="DATA_REGISTRO", ascending=False)
        for _, row in evolucoes_sorted.iterrows():
            data_str = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else ""
            story.append(Paragraph(f"<b>Data:</b> {data_str}", styles["Normal"]))
            story.append(Paragraph(f"<b>Descrição:</b> {row.get('EVOLUCAO','')}", styles["Normal"]))
            story.append(Paragraph(f"<i>Registrado por:</i> {row.get('USUARIO','')}", styles["Italic"]))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Nenhuma evolução registrada.", styles["Normal"]))
    story.append(Spacer(1, 12))

    # 📎 Documentos
    add_title("📎 Documentos Anexados")
    if arquivos:
        for arq in arquivos:
            nome = arq["name"]
            link = arq.get("webContentLink", "")
            story.append(Paragraph(f"{nome} - <a href='{link}' color='blue'>{link}</a>", styles["Normal"]))
    else:
        story.append(Paragraph("Nenhum documento encontrado.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------
# 🔹 Página principal
# --------------------------------------------
st.title("🗂️ Ficha de Paciente")

id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🔙 Voltar para Lista de Pacientes"):
        st.query_params.clear()
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# Carrega dados
df = carregar_dados()
df.columns = df.columns.str.strip().str.title()
paciente_df = df[df["Id"].astype(str) == id_paciente_str]

if paciente_df.empty:
    st.error("❌ Paciente não encontrado.")
    st.stop()

paciente = paciente_df.iloc[0]

# Carregar evoluções e anexos
df_evolucao = carregar_evolucoes()
arquivos = listar_pdfs_paciente(id_paciente_str)
evolucoes_paciente = pd.DataFrame()
if "PACIENTE_ID" in df_evolucao.columns:
    evolucoes_paciente = df_evolucao[df_evolucao["PACIENTE_ID"].astype(str) == id_paciente_str]

with col_btn2:
    if st.button("🖨️ Imprimir Ficha Clínica"):
        pdf = gerar_pdf_ficha(paciente, evolucoes_paciente, arquivos, usuario_logado)
        st.download_button(
            label="⬇️ Baixar Ficha de Paciente (PDF)",
            data=pdf,
            file_name=f"Ficha_{paciente.get('Nome','sem_nome')}.pdf",
            mime="application/pdf"
        )

# --------------------------------------------
# 🔹 Expansores (colapsáveis)
# --------------------------------------------
with st.expander("🧾 Dados do Paciente", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Nome:** {paciente.get('Nome', '-')}") 
        st.write(f"**Idade:** {paciente.get('Idade', '-')}") 
        st.write(f"**Sexo:** {paciente.get('Sexo', '-')}") 
        st.write(f"**Data de Nascimento:** {paciente.get('Data', '-')}") 
    with col2:
        st.write(f"**Endereço:** {paciente.get('Endereco', '-')}") 
        st.write(f"**Filiação:** {paciente.get('Filiacao', '-')}") 
        st.write(f"**Telefone:** {paciente.get('Telefone', '-')}") 
        st.write(f"**FAO:** {paciente.get('Fao', '-')}")

with st.expander("🩺 Dados Clínicos", expanded=False):

    def get_valor_multi(paciente, *chaves):
        for chave in chaves:
            if chave in paciente and str(paciente.get(chave)).strip():
                return paciente.get(chave)
        return "-"

    def campo(label, valor):
        st.markdown(f"**{label}**")
        st.write(valor)

    campo("🦷 Tipo de Fissura", get_valor_multi(
        paciente, "Tipo De Fissura", "Tipo de Fissura", "TIPO_FISSURA"
    ))

    campo("📜 História do Tratamento", get_valor_multi(
        paciente, "Historia_Tratamento"
    ))

    campo("🔎 Características Oclusais", get_valor_multi(
        paciente, "Carac_Oclusais"
    ))

    campo("🦷 Necessidades Ortodônticas", get_valor_multi(
        paciente, "Neces_Orto"
    ))

    campo("🏥 Necessidades Cirúrgicas", get_valor_multi(
        paciente, "Neces_Cirur"
    ))

    campo("🦷 Necessidades Odontológicas", get_valor_multi(
        paciente, "Neces_Odonto"
    ))

    campo("📌 Outros", get_valor_multi(
        paciente, "Outros"
    ))
    campo("📋 Diagnóstico", get_valor_multi(
        paciente, "Diagnostico", "DIAGNOSTICO"
    ))

    campo("🧭 Plano de Tratamento", get_valor_multi(
        paciente, "Plano_Tratamento", "PLANO_TRATAMENTO"
    ))

with st.expander("📜 Evoluções do Paciente", expanded=False):
    if not evolucoes_paciente.empty:
        evolucoes_paciente = evolucoes_paciente.sort_values(by="DATA_REGISTRO", ascending=False)
        for _, row in evolucoes_paciente.iterrows():
            data_str = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else ""
            st.markdown(f"""
            <div style='padding:10px; background-color:#f9f9f9; border-left:4px solid #0d6efd; margin-bottom:8px; border-radius:5px;'>
                <b>📅 {data_str}</b><br>
                <i>{row.get("EVOLUCAO","")}</i><br>
                <span style='color:gray;'>👤 {row.get("USUARIO","")}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma evolução registrada para este paciente.")

with st.expander("📎 Documentos Anexados", expanded=False):
    if not arquivos:
        st.info("Nenhum arquivo PDF encontrado para este paciente.")
    else:
        for arquivo in arquivos:
            nome = arquivo["name"]
            file_id = arquivo["id"]
            link = f"https://drive.google.com/file/d/{file_id}/preview"
            with st.expander(f"📄 {nome}"):
                st.components.v1.iframe(link, height=500)
