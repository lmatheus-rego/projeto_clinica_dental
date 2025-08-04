import streamlit as st
import datetime
import pandas as pd
import gspread
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)
from google.oauth2.service_account import Credentials

# Função para deletar páginas do menu lateral
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# Configuração inicial da página
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
)
st.sidebar.title("Menu")
st.title("Projeto Céu da Boca")

# Remoção de páginas temporárias
delete_page("1_🏠_home", "ficha_clinica")
delete_page("1_🏠_home", "alterar_paciente")
delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")

# Função para carregar dados de planilha privada usando gspread
def carregar_dados():
    # Escopos necessários para acesso à planilha
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Lê as credenciais do secrets do Streamlit
    service_account_info = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }
    
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)

    # Abra a planilha pelo ID
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # A primeira aba

    # Pega todos os dados da planilha
    dados = sheet.get_all_records()

    # Converte para DataFrame
    df = pd.DataFrame(dados)

    return df

# A partir daqui seu código original segue normalmente
def pacientes_do_mes(df):
    if "Data de Atendimento" not in df.columns:
        return 0
    df["Data de Atendimento"] = pd.to_datetime(df["Data de Atendimento"], errors='coerce')
    hoje = datetime.datetime.now()
    return df[
        (df["Data de Atendimento"].dt.month == hoje.month) &
        (df["Data de Atendimento"].dt.year == hoje.year)
    ].shape[0]

# Dados
df = carregar_dados()
total_pacientes = len(df)
atendidos_mes = pacientes_do_mes(df)
fissuras = df["Tipo de Fissura"].value_counts().to_dict() if "Tipo de Fissura" in df.columns else {}

# Resto do seu código para UI e gráficos
st.markdown("## 📊 Resumo Geral")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 👥 Total de Pacientes")
    st.metric("Cadastrados", value=total_pacientes)

with col2:
    st.markdown("### 📆 Atendidos no Mês")
    st.metric("Neste mês", value=atendidos_mes)

with col3:
    st.markdown("### 💉 Tipos de Fissura")
    if fissuras:
        for tipo, qtd in fissuras.items():
            st.markdown(f"- **{tipo}**: {qtd}")
    else:
        st.markdown("_Nenhuma informação disponível._")

with st.expander("📈 Ver gráfico por tipo de fissura"):
    if fissuras:
        import plotly.express as px
        fig = px.pie(
            names=list(fissuras.keys()),
            values=list(fissuras.values()),
            title="Distribuição por Tipo de Fissura"
        )
        st.plotly_chart(fig)
    else:
        st.info("Nenhum dado para exibir o gráfico.")
