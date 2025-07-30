import streamlit as st
import pandas as pd

# Obter o ID passado via query string
idpaciente = st.query_params.get("idpaciente", [None])[0]

# Verifica se o parâmetro foi passado corretamente
if idpaciente is None:
    st.error("❌ Nenhum paciente foi selecionado.")
    st.stop()

# Converte o ID para inteiro (se possível)
try:
    idpaciente = int(idpaciente)
except ValueError:
    st.error("❌ ID de paciente inválido.")
    st.stop()

# Carrega dados da planilha
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs/export?format=csv"
    return pd.read_csv(url)

df = carregar_dados()
df.columns = df.columns.str.strip().str.title()

# Verifica se o índice existe
if idpaciente >= len(df):
    st.error("❌ Paciente não encontrado.")
    st.stop()

# Obtém o paciente
paciente = df.iloc[idpaciente]

# Exibe os dados
st.title("🗂️ Ficha Clínica do Paciente")
col1, col2 = st.columns(2)

with col1:
    st.write(f"**Nome:** {paciente.get('Nome', '-')}")
    st.write(f"**Idade:** {paciente.get('Idade', '-')}")
    st.write(f"**FAO:** {paciente.get('Fao', '-')}")
    st.write(f"**Endereço:** {paciente.get('Endereço', '-')}")

with col2:
    st.write(f"**Data de Nascimento:** {paciente.get('Data De Nascimento', '-')}")
    st.write(f"**Sexo:** {paciente.get('Sexo', '-')}")
    st.write(f"**Filiação:** {paciente.get('Filiação', '-')}")
    st.write(f"**Telefone:** {paciente.get('Telefone', '-')}")

st.markdown("___")

col1, col2 = st.columns(2)
with col1:
    st.write("**História do Tratamento:**")
    st.write(paciente.get("História Do Tratamento", "-"))

with col2:
    st.write(f"**Tipo de Fissura:** {paciente.get('Tipo De Fissura', '-')}")

st.write("**Registro Clínico:**")
st.write(paciente.get("Registro Clínico", "-"))


# Ações
if st.button("Voltar"):
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Função para listar arquivos PDF do paciente no Google Drive
def listar_pdfs_paciente(paciente_id: int):
    # Autentica com service account
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json", scopes=SCOPES
    )

    service = build('drive', 'v3', credentials=creds)

    # ID da pasta onde estão os PDFs
    PASTA_ID = "1cH2C7KrcX69-GfwcPtk_IGIh3WydB-X5"  # <- Substitua se necessário

    # Define o prefixo dos arquivos
    prefixo = f"P{paciente_id}#"

    # Consulta os arquivos dentro da pasta com prefixo correspondente
    query = f"'{PASTA_ID}' in parents and name contains '{prefixo}' and mimeType='application/pdf'"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        orderBy='name'
    ).execute()

    return results.get('files', [])

# Exibir arquivos PDF do paciente
st.markdown("## 📄 Exames e Documentos")

arquivos = listar_pdfs_paciente(paciente_id=idpaciente)

if not arquivos:
    st.info("Nenhum arquivo PDF encontrado para este paciente.")
else:
    for arquivo in arquivos:
        nome = arquivo["name"]
        file_id = arquivo["id"]
        link = f"https://drive.google.com/file/d/{file_id}/preview"

        with st.expander(f"📎 {nome}"):
            st.components.v1.iframe(link, height=500)
