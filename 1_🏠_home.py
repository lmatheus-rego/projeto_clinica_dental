import streamlit as st
import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import get_pages, _on_pages_changed

# ==========================
# Função para deletar páginas do menu lateral
# ==========================
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# ==========================
# Configuração inicial da página
# ==========================
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
)
st.sidebar.title("Fila de Atendimento")
st.title("Projeto Céu da Boca")

# Remover páginas temporárias
delete_page("1_🏠_home", "ficha_clinica")
delete_page("1_🏠_home", "alterar_paciente")
delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
delete_page("1_🏠_home", "evolucao_tratamento")

# ==========================
# Função para carregar dados de planilha privada usando secrets
# ==========================
def carregar_aba(nome_aba):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    gc = gspread.authorize(credentials)

    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(nome_aba)

    dados = sheet.get_all_records()
    return pd.DataFrame(dados)

# ==========================
# Carregar pacientes e fila
# ==========================
df_pacientes = carregar_aba("Pacientes")
df_fila = carregar_aba("Fila")

# ==============================
# 📋 Fila de Atendimento
# ==============================
st.sidebar.markdown("### 📅 Fila de Atendimento - Hoje")

# Data de hoje
hoje = datetime.date.today()

# Normalizar colunas
df_fila["Status"] = df_fila["Status"].astype(str).str.strip().str.lower()
df_fila["Data"] = pd.to_datetime(df_fila["Data"], dayfirst=True, errors="coerce").dt.date

# Logs de debug
st.sidebar.write("DEBUG - Valores únicos de Status:", df_fila["Status"].unique().tolist())
st.sidebar.write("DEBUG - Datas convertidas (5 primeiras):", df_fila["Data"].head())
st.sidebar.write("DEBUG - Hoje:", hoje)

# Filtrar pacientes agendados para hoje
fila_hoje = df_fila[(df_fila["Data"] == hoje) & (df_fila["Status"] == "agendado")]

st.sidebar.write("DEBUG - Fila de Hoje:", fila_hoje)

# Mostrar pacientes agendados com emojis clicáveis
if not fila_hoje.empty:
    for _, row in fila_hoje.iterrows():
        paciente_id = row["Paciente_ID"]

        # Filtrar paciente no df_pacientes correto
        paciente = df_pacientes[df_pacientes["ID"] == paciente_id]

        if not paciente.empty:
            nome_paciente = paciente.iloc[0]["Nome"]
            ficha_url = f"/ficha_clinica?idpaciente={paciente_id}"
            evolucao_url = f"/evolucao_tratamento?idpaciente={paciente_id}"

            st.sidebar.markdown(
                f"- {nome_paciente} "
                f"[📄]({ficha_url}) [🦷]({evolucao_url})",
                unsafe_allow_html=True
            )
else:
    st.sidebar.info("⚠️ Nenhum paciente encontrado para hoje com status 'Agendado'.")

# ===================== RESUMO GERAL =====================
def pacientes_do_mes(df):
    if "Data de Atendimento" not in df.columns:
        return 0
    df["Data de Atendimento"] = pd.to_datetime(df["Data de Atendimento"], errors='coerce')
    hoje = datetime.datetime.now()
    return df[
        (df["Data de Atendimento"].dt.month == hoje.month) &
        (df["Data de Atendimento"].dt.year == hoje.year)
    ].shape[0]

total_pacientes = len(df_pacientes)
atendidos_mes = pacientes_do_mes(df_pacientes)
fissuras = (
    df_pacientes["Tipo de Fissura"].value_counts().to_dict()
    if "Tipo de Fissura" in df_pacientes.columns
    else {}
)

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
