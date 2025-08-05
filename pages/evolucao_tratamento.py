import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Autenticação e carregamento da planilha ---
def carregar_dados():
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

    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

    df = pd.DataFrame(sheet.get_all_records())
    return df, sheet, credentials, gc, SPREADSHEET_ID

df, sheet, credentials, gc, SPREADSHEET_ID = carregar_dados()
df.columns = df.columns.str.strip().str.upper()

# ID do paciente via query
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()
try:
    id_paciente = int(id_paciente_str)
except:
    st.error("ID do paciente inválido.")
    st.stop()

# Dados do paciente
paciente_df = df[df["ID"].astype(str) == id_paciente_str]
if paciente_df.empty:
    st.error("Paciente não encontrado.")
    st.stop()

paciente_info = paciente_df.iloc[0]

# --- Inputs para evolução (empilhados verticalmente) ---
st.markdown("<h3 style='text-align:center;'>📈 Inserir Evolução do Tratamento</h3>", unsafe_allow_html=True)

descricao_evolucao = st.text_area("📝 **Descrição da Evolução**", height=100)
data_evolucao = st.date_input("📅 **Data da Evolução**", format="DD/MM/YYYY")

if st.button("💾 Salvar Evolução"):
    if descricao_evolucao.strip() == "":
        st.warning("⚠️ A descrição da evolução não pode estar vazia.")
    else:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            try:
                aba = sh.worksheet("Registros")
            except gspread.exceptions.WorksheetNotFound:
                aba = sh.add_worksheet(title="Registros", rows="1000", cols="10")
                aba.append_row(["ID", "Data", "Descrição", "Usuário"])

            nova_linha = [
                id_paciente_str,  # ID do paciente
                data_evolucao.strftime("%d/%m/%Y"),
                descricao_evolucao.strip(),
                "usuario_a_definir"
            ]
            aba.append_row(nova_linha)
            st.success("✅ Evolução registrada com sucesso!")
            st.experimental_rerun()  # Atualiza para mostrar as evoluções atualizadas
        except Exception as e:
            st.error(f"Erro ao salvar evolução: {e}")

# --- Listagem das evoluções do paciente ---
try:
    sh = gc.open_by_key(SPREADSHEET_ID)
    aba = sh.worksheet("Registros")
    registros = aba.get_all_records()
    df_registros = pd.DataFrame(registros)
    # Filtra pelo paciente atual
    df_paciente = df_registros[df_registros["ID"].astype(str) == id_paciente_str]

    if not df_paciente.empty:
        st.markdown("<h4>📜 Histórico de Evoluções</h4>", unsafe_allow_html=True)
        for _, row in df_paciente.iterrows():
            texto = f'No dia "{row["Data"]}" foi realizada "{row["Descrição"]}", cadastrada pelo usuário "{row["Usuário"]}".'
            st.write(texto)
    else:
        st.info("Nenhuma evolução registrada para este paciente.")
except Exception as e:
    st.error(f"Erro ao carregar evoluções: {e}")

# --- Título e dados pessoais ---
st.markdown("<h3 style='text-align:center;'>📋 Dados E Registros do Paciente</h3><hr>", unsafe_allow_html=True)
status = paciente_info.get('STATUS', '').strip().lower()
if status == 'ativo':
    status_emoji = "✅"
    status_color = "#28a745"
elif status == 'inativo':
    status_emoji = "⛔"
    status_color = "#6c757d"
elif status == 'ausente':
    status_emoji = "🕓"
    status_color = "#ffc107"
else:
    status_emoji = "❔"
    status_color = "#000"

espaco, col1, col2, col3, col4, espaco2 = st.columns([1, 2, 2, 2, 2, 1])
with col1:
    st.markdown(f"<h5 style='text-align:center;'>👤<br>{paciente_info['NOME']}</h5>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h5 style='text-align:center;'>🧭<br>FAO: {paciente_info['FAO']}</h5>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h5 style='text-align:center;'>🎂<br>{paciente_info['IDADE']} anos</h5>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<h5 style='text-align:center; color:{status_color};'>{status_emoji}<br>Status: {paciente_info['STATUS']}</h5>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Dados clínicos ---
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"<h6 style='text-align:center;'>🧬 Tipo de Fissura</h6><p style='text-align:center;'>{paciente_info.get('TIPO_FISSURA', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📋 Plano de Tratamento</h6><p style='text-align:center;'>{paciente_info.get('PLANO_TRATAMENTO', '')}</p>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<h6 style='text-align:center;'>📝 Diagnóstico</h6><p style='text-align:center;'>{paciente_info.get('DIAGNOSTICO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>🧩 Características Oclusais</h6><p style='text-align:center;'>{paciente_info.get('CARAC_OCLUSAIS', '')}</p>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<h6 style='text-align:center;'>🪥 Necessidades Odontológicas</h6><p style='text-align:center;'>{paciente_info.get('NECES_ODONTO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📜 Histórico do Tratamento</h6><p style='text-align:center;'>{paciente_info.get('HISTORIA_TRATAMENTO', '')}</p>", unsafe_allow_html=True)

with col4:
    st.markdown(f"<h6 style='text-align:center;'>🦷 Necessidades Ortodônticas</h6><p style='text-align:center;'>{paciente_info.get('NECES_ORTO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📌 Outros</h6><p style='text-align:center;'>{paciente_info.get('OUTROS', '')}</p>", unsafe_allow_html=True)

with col5:
    st.markdown(f"<h6 style='text-align:center;'>🔪 Necessidades Cirúrgicas</h6><p style='text-align:center;'>{paciente_info.get('NECES_CIRUR', '')}</p>", unsafe_allow_html=True)
