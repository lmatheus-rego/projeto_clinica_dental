import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)
import base64

# ====================== FUNÇÕES AUXILIARES ======================
def delete_page(main_script_path_str, page_name):
    """Remove páginas do menu lateral do Streamlit"""
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()


def carregar_dados():
    """Carrega os dados da planilha principal"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = st.secrets["gcp_service_account"]
    service_account_info["private_key"] = service_account_info["private_key"].replace('\\n', '\n')

    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)

    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
    return df


def carregar_evolucoes():
    """Carrega os registros de evolução clínica"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    service_account_info = st.secrets["gcp_service_account"]
    service_account_info["private_key"] = service_account_info["private_key"].replace('\\n', '\n')

    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)

    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    registros_sheet = gc.open_by_key(SPREADSHEET_ID).worksheet("Registros")

    evolucoes = registros_sheet.get_all_records()
    df_evolucao = pd.DataFrame(evolucoes)
    return df_evolucao


def listar_pdfs_paciente(paciente_id_str: str):
    """Lista os arquivos PDF do paciente no Google Drive"""
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    service_account_info = st.secrets["gcp_service_account"]
    service_account_info["private_key"] = service_account_info["private_key"].replace('\\n', '\n')

    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
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
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    prefixo = f'P{id_paciente_str}#'
    arquivos_filtrados = [arq for arq in arquivos if arq['name'].startswith(prefixo)]
    return arquivos_filtrados


def gerar_pdf_download_link(html_content, filename="ficha_clinica.html"):
    """Gera link para imprimir ou baixar a ficha"""
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}" target="_blank">🖨️ Imprimir/Salvar Ficha</a>'
    return href


# ====================== INÍCIO DA PÁGINA ======================
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

try:
    id_paciente = int(id_paciente_str)
except ValueError:
    st.error("ID de paciente inválido.")
    st.stop()

df = carregar_dados()
df.columns = df.columns.str.strip().str.title()
paciente_df = df[df["Id"].astype(str) == id_paciente_str]

if paciente_df.empty:
    st.error("❌ Paciente não encontrado.")
    st.stop()

paciente = paciente_df.iloc[0]

if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "ficha_clinica")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

st.title("🗂️ Ficha Clínica do Paciente")

# ====================== DADOS DO PACIENTE ======================
with st.expander(f"⬇️ Dados do Paciente - {paciente.get('Nome', '-')} ⬇️", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Idade:** {paciente.get('Idade', '-')}")
        st.write(f"**FAO:** {paciente.get('Fao', '-')}")
        st.write(f"**Endereço:** {paciente.get('Endereco', '-')}")
        st.write(f"**Telefone:** {paciente.get('Telefone', '-')}")
    with col2:
        st.write(f"**Data de Nascimento:** {paciente.get('Data', '-')}")
        st.write(f"**Sexo:** {paciente.get('Sexo', '-')}")
        st.write(f"**Filiação:** {paciente.get('Filiacao', '-')}")

st.markdown("___")

# ====================== DADOS CLÍNICOS ======================
st.markdown("### 🩺 Dados Clínicos")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**História do Tratamento:** {paciente.get('Historia_Tratamento', '-')}")
    st.write(f"**Necessidades Odontológicas:** {paciente.get('Neces_Odonto', '-')}")
    st.write(f"**Necessidades Cirúrgicas:** {paciente.get('Neces_Cirur', '-')}")
with col2:
    st.write(f"**Tipo de Fissura:** {paciente.get('Tipo De Fissura', '-')}")
    st.write(f"**Características Oclusais:** {paciente.get('Carac_Oclusais', '-')}")
    st.write(f"**Necessidades Ortodônticas:** {paciente.get('Neces_Orto', '-')}")
    st.write(f"**Outros:** {paciente.get('Outros', '-')}")

st.write("**Registro Clínico:**")
st.write(paciente.get("Registro Clínico", "-"))

# ====================== EVOLUÇÕES ======================
st.markdown("## 🧾 Evoluções do Paciente")

try:
    df_evolucoes = carregar_evolucoes()
    evolucoes_paciente = df_evolucoes[df_evolucoes["ID_PACIENTE"].astype(str) == id_paciente_str]
    if not evolucoes_paciente.empty:
        evolucoes_paciente = evolucoes_paciente.sort_values(by="DATA", ascending=False)
        for _, evolucao in evolucoes_paciente.iterrows():
            with st.expander(f"🗓️ {evolucao['DATA']} - por {evolucao['USUARIO']}"):
                st.markdown(f"**Descrição:** {evolucao['DESCRICAO']}")
    else:
        st.info("Nenhuma evolução registrada para este paciente.")
except Exception as e:
    st.warning(f"⚠️ Erro ao carregar evoluções: {e}")

# ====================== EXAMES E DOCUMENTOS ======================
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

# ====================== IMPRESSÃO ======================
usuario_logado = st.session_state.get("usuario_nome", "Usuário não identificado")
st.markdown("### 🖨️ Impressão da Ficha Clínica")

html_content = f"""
<html>
<body>
<h2>Ficha Clínica - {paciente.get('Nome', '-')}</h2>
<hr>
<p><strong>Idade:</strong> {paciente.get('Idade', '-')}<br>
<strong>FAO:</strong> {paciente.get('Fao', '-')}<br>
<strong>Tipo de Fissura:</strong> {paciente.get('Tipo De Fissura', '-')}<br>
<strong>História do Tratamento:</strong> {paciente.get('Historia_Tratamento', '-')}</p>
<br><hr>
<footer style='text-align:center; font-size:12px; color:gray;'>
Ficha clínica impressa pelo usuário: <b>{usuario_logado}</b>
</footer>
</body>
</html>
"""

st.markdown(gerar_pdf_download_link(html_content), unsafe_allow_html=True)
