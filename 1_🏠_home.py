import streamlit as st
import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import (
    get_pages,
    _on_pages_changed
)

# ==========================
# Função para deletar páginas temporárias
# ==========================
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# ==========================
# Configuração inicial
# ==========================
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
)
st.sidebar.title("📅 Fila de Atendimento de Hoje")
st.title("Projeto Céu da Boca")

# Remover páginas temporárias
delete_page("1_🏠_home", "ficha_clinica")
delete_page("1_🏠_home", "alterar_paciente")
delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
delete_page("1_🏠_home", "evolucao_tratamento")

# ==========================
# Função para carregar dados da planilha
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
# Carregar dados de Pacientes e Fila
# ==========================
df_pacientes = carregar_aba("Pacientes")
df_fila = carregar_aba("Fila")
# ==============================
# 📋 Fila de Atendimento - Hoje (estilizada)
# ==============================
hoje = datetime.date.today()

# Normalizar colunas
df_fila["STATUS"] = df_fila["STATUS"].astype(str).str.strip().str.upper()
df_fila["DATA"] = pd.to_datetime(
    df_fila["DATA"], 
    dayfirst=True, 
    errors="coerce"
).dt.date

# Filtrar pacientes agendados para hoje
fila_hoje = df_fila[
    (df_fila["DATA"] == hoje) & 
    (df_fila["STATUS"] == "AGENDADO")
]

if not fila_hoje.empty:
    st.sidebar.markdown("#### 🏥 Pacientes Agendados Hoje")
    # Cabeçalho da tabela
    st.sidebar.markdown(
        "<div style='display:flex; font-weight:bold; padding:4px 8px;'>"
        "<div style='flex:2'>Nome</div>"
        "<div style='flex:1; text-align:center'>Status</div>"
        "<div style='flex:1; text-align:center'>Ficha</div>"
        "<div style='flex:1; text-align:center'>Evolução</div>"
        "</div>",
        unsafe_allow_html=True
    )

    for _, row in fila_hoje.iterrows():
        paciente_id = row["PACIENTE_ID"]

        # Garantir que os IDs sejam comparáveis
        paciente = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == str(paciente_id).strip()]

        if not paciente.empty:
            nome_paciente = paciente.iloc[0]["NOME"]
            status = row["STATUS"].capitalize()

            # Card do paciente
            st.sidebar.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:4px 8px;
                    margin-bottom:4px;
                    border-radius:6px;
                    background-color:#f9f9f9;
                    border-left: 5px solid #4caf50;
                    font-size:13px;
                ">
                    <div style='flex:2'>{nome_paciente}</div>
                    <div style='flex:1; text-align:center'>{status}</div>
                    <div style='flex:1; text-align:center'>📄</div>
                    <div style='flex:1; text-align:center'>🦷</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Botões de ação reais do Streamlit (para redirecionamento)
            col_ficha, col_evolucao = st.sidebar.columns([1,1])
            with col_ficha:
                if st.button("📄", key=f"ficha_{paciente_id}"):
                    st.query_params = {"idpaciente": str(paciente_id)}
                    from streamlit.source_util import add_page
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")
            with col_evolucao:
                if st.button("🦷", key=f"evolucao_{paciente_id}"):
                    st.query_params = {"idpaciente": str(paciente_id)}
                    add_page("1_🏠_home", "evolucao_tratamento")
                    st.switch_page("pages/evolucao_tratamento.py")
else:
    st.sidebar.info("⚠️ Nenhum paciente encontrado para hoje com status 'AGENDADO'.")
# ==========================
# RESUMO GERAL
# ==========================
def pacientes_do_mes(df):
    if "DATA DE ATENDIMENTO" not in df.columns:
        return 0
    df["DATA DE ATENDIMENTO"] = pd.to_datetime(df["DATA DE ATENDIMENTO"], errors='coerce')
    hoje = datetime.datetime.now()
    return df[
        (df["DATA DE ATENDIMENTO"].dt.month == hoje.month) &
        (df["DATA DE ATENDIMENTO"].dt.year == hoje.year)
    ].shape[0]

total_pacientes = len(df_pacientes)
atendidos_mes = pacientes_do_mes(df_pacientes)
fissuras = (
    df_pacientes["TIPO DE FISSURA"].value_counts().to_dict()
    if "TIPO DE FISSURA" in df_pacientes.columns
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
