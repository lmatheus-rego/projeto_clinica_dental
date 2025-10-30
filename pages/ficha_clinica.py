import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from streamlit.source_util import get_pages, _on_pages_changed
from streamlit_pdf_viewer import pdf_viewer

# --------------------------------------------
# 🔹 Funções auxiliares
# --------------------------------------------

def delete_page(main_script_path_str, page_name):
    """Remove páginas do menu lateral"""
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value["page_name"] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# --------------------------------------------
# 🔹 Conexão segura com Google Sheets/Drive
# --------------------------------------------
def get_credentials(scopes):
    """Cria credenciais Google sem alterar st.secrets"""
    service_account_info = dict(st.secrets["gcp_service_account"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(service_account_info, scopes=scopes)

# --------------------------------------------
# 🔹 Carregar dados do paciente
# --------------------------------------------
def carregar_dados():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = get_credentials(scopes)
    gc = gspread.authorize(credentials)
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    return df

# --------------------------------------------
# 🔹 Carregar evoluções
# --------------------------------------------
def carregar_evolucoes():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = get_credentials(scopes)
    gc = gspread.authorize(credentials)

    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    registros_sheet = gc.open_by_key(SPREADSHEET_ID).worksheet("Registros")

    df = pd.DataFrame(registros_sheet.get_all_records())
    return df

# --------------------------------------------
# 🔹 Listar PDFs do paciente no Drive
# --------------------------------------------
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
    arquivos_filtrados = [arq for arq in arquivos if arq['name'].startswith(prefixo)]
    return arquivos_filtrados

# --------------------------------------------
# 🔹 Página principal
# --------------------------------------------
st.title("🗂️ Ficha Clínica do Paciente")

# Captura do ID
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

# Botão voltar
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "ficha_clinica")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# Carrega dados
df = carregar_dados()
df.columns = df.columns.str.strip().str.title()
paciente_df = df[df["Id"].astype(str) == id_paciente_str]

if paciente_df.empty:
    st.error("❌ Paciente não encontrado.")
    st.stop()

paciente = paciente_df.iloc[0]

# --------------------------------------------
# 🔹 Dados principais
# --------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.write(f"**Nome:** {paciente.get('Nome', '-')}")
    st.write(f"**Idade:** {paciente.get('Idade', '-')}")
    st.write(f"**Fao:** {paciente.get('Fao', '-')}")
    st.write(f"**Endereço:** {paciente.get('Endereco', '-')}")

with col2:
    st.write(f"**Data De Nascimento:** {paciente.get('Data', '-')}")
    st.write(f"**Sexo:** {paciente.get('Sexo', '-')}")
    st.write(f"**Filiação:** {paciente.get('Filiacao', '-')}")
    st.write(f"**Telefone:** {paciente.get('Telefone', '-')}")

st.markdown("---")

# --------------------------------------------
# 🔹 Dados clínicos
# --------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.write("**História Do Tratamento:**")
    st.write(paciente.get("Historia_Tratamento", "-"))
    st.write(f"**Necessidades Odontológicas:** {paciente.get('Neces_Odonto', '-')}")
    st.write(f"**Necessidades Cirúrgicas:** {paciente.get('Neces_Cirur', '-')}")

with col2:
    st.write(f"**Tipo De Fissura:** {paciente.get('Tipo De Fissura', '-')}")
    st.write(f"**Características Oclusais:** {paciente.get('Carac_Oclusais', '-')}")
    st.write(f"**Necessidades Ortodônticas:** {paciente.get('Neces_Orto', '-')}")
    st.write(f"**Outros:** {paciente.get('Outros', '-')}")

st.write("**Registro Clínico:**")
st.write(paciente.get("Registro Clínico", "-"))

# --------------------------------------------
# 🔹 Evoluções do paciente
# --------------------------------------------
st.markdown("## 📜 Histórico de Evoluções")
df_evolucao = carregar_evolucoes()

if "PACIENTE_ID" in df_evolucao.columns:
    evolucoes_paciente = df_evolucao[df_evolucao["PACIENTE_ID"].astype(str) == id_paciente_str]

    if not evolucoes_paciente.empty:
        evolucoes_paciente = evolucoes_paciente.sort_values(
            by="DATA_REGISTRO", ascending=False
        ).reset_index(drop=True)

        for _, row in evolucoes_paciente.iterrows():
            data = row.get("DATA_REGISTRO", "")
            descricao = row.get("EVOLUCAO", "")
            usuario = row.get("USUARIO", "")
            st.markdown(f"""
            <div style='padding:8px 12px; background-color:#f9f9f9; border-left:4px solid #0d6efd; margin-bottom:8px; border-radius:4px;'>
                <b>📅 {data}</b><br>
                <i>{descricao}</i><br>
                <span style='color:gray;'>👤 Registrado por: {usuario}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma evolução registrada para este paciente.")
else:
    st.warning("A aba 'Registros' não contém a coluna 'PACIENTE_ID'.")

# --------------------------------------------
# 🔹 Exames e Documentos
# --------------------------------------------
st.markdown("## 📄 Exames e Documentos")
arquivos = listar_pdfs_paciente(id_paciente_str)

if not arquivos:
    st.info("Nenhum arquivo PDF encontrado para este paciente.")
else:
    for arquivo in arquivos:
        nome = arquivo["name"]
        file_id = arquivo["id"]
        link = f"https://drive.google.com/file/d/{file_id}/preview"
        with st.expander(f"📎 {nome}"):
            st.components.v1.iframe(link, height=500)

# --------------------------------------------
# 🔹 Impressão da ficha clínica
# --------------------------------------------
usuario_logado = st.session_state.get("user_email", "Usuário não identificado")

if st.button("🖨️ Imprimir Ficha Clínica"):
    html_content = f"""
    <html>
    <head>
        <title>Ficha Clínica</title>
        <style>
            body {{ font-family: Arial; margin: 40px; }}
            h1 {{ text-align: center; }}
            hr {{ margin: 20px 0; }}
            footer {{ text-align: center; margin-top: 50px; color: gray; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <h1>Ficha Clínica de {paciente.get('Nome','')}</h1>
        <hr>
        <p><b>Idade:</b> {paciente.get('Idade','-')}</p>
        <p><b>FAO:</b> {paciente.get('Fao','-')}</p>
        <p><b>Tipo de Fissura:</b> {paciente.get('Tipo De Fissura','-')}</p>
        <p><b>História do Tratamento:</b> {paciente.get('Historia_Tratamento','-')}</p>
        <footer>
            Ficha clínica impressa pelo usuário: <b>{usuario_logado}</b>
        </footer>
    </body>
    </html>
    """

    st.download_button(
        label="⬇️ Baixar Ficha Clínica (HTML)",
        data=html_content,
        file_name=f"Ficha_{paciente.get('Nome','sem_nome')}.html",
        mime="text/html"
    )
