from datetime import datetime
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Inputs para evolução do tratamento
st.markdown("<h4 style='text-align:center;'>📈 Inserir Evolução do Tratamento</h4>", unsafe_allow_html=True)
espaco, col1, col2, espaco2 = st.columns([1, 3, 3, 1])

with col1:
    data_evolucao = st.date_input("📅 Data da Evolução", format="DD/MM/YYYY")
with col2:
    descricao_evolucao = st.text_area("📝 Descrição da Evolução", height=100)

# Botão de salvar evolução
salvar = st.button("💾 Salvar Evolução")
if salvar:
    if descricao_evolucao.strip() == "":
        st.warning("⚠️ A descrição da evolução não pode estar vazia.")
    else:
        try:
            # Autenticando com o Google
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
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
            sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")

            try:
                worksheet = sh.worksheet("Registros")
            except gspread.exceptions.WorksheetNotFound:
                worksheet = sh.add_worksheet(title="Registros", rows="1000", cols="10")
                worksheet.append_row(["ID", "Data", "Descrição", "Usuário"])

            nova_linha = [
                id_paciente_str,
                data_evolucao.strftime("%d/%m/%Y"),
                descricao_evolucao.strip(),
                "usuario_a_definir"
            ]
            worksheet.append_row(nova_linha)
            st.success("✅ Evolução registrada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar evolução: {e}")


# ------------------ TÍTULO E INFORMAÇÕES DO PACIENTE ------------------

st.markdown("<h2 style='text-align:center;'>📋 Dados E Registros do Paciente</h2><hr>", unsafe_allow_html=True)

espaco, col1, col2, col3, col4, espaco2 = st.columns([1, 2, 2, 2, 2, 1])

with col1:
    st.markdown(f"<h5 style='text-align:center;'>👤<br>{paciente_info['NOME']}</h5>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h5 style='text-align:center;'>🧭<br>FAO: {paciente_info['FAO']}</h5>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h5 style='text-align:center;'>🎂<br>{paciente_info['IDADE']} anos</h5>", unsafe_allow_html=True)
with col4:
    status = paciente_info['STATUS'].strip().lower()
    if status == "ativo":
        cor = "green"
        icone = "✅"
    elif status == "inativo":
        cor = "gray"
        icone = "⛔"
    elif status == "ausente":
        cor = "orange"
        icone = "🟠"
    else:
        cor = "black"
        icone = "❓"

    st.markdown(
        f"<h5 style='text-align:center; color:{cor};'>{icone}<br>Status: {paciente_info['STATUS']}</h5>",
        unsafe_allow_html=True
    )

st.markdown("<hr>", unsafe_allow_html=True)
