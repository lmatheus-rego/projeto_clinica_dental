import streamlit as st
import datetime
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from streamlit.source_util import (
    get_pages,
    _on_pages_changed
)

def add_page(main_script_path_str, page_name):
    pages = get_pages(main_script_path_str)
    main_script_path = Path(main_script_path_str)
    pages_dir = main_script_path.parent / "pages"
    script_path = [f for f in list(pages_dir.glob("*.py")) + list(main_script_path.parent.glob("*.py"))
                   if f.name.find(page_name) != -1][0]
    script_path_str = str(script_path.resolve())
    pi, pn = page_icon_and_name(script_path)
    psh = calc_md5(script_path_str)
    pages[psh] = {
        "page_script_hash": psh,
        "page_name": pn,
        "icon": pi,
        "script_path": script_path_str,
    }
    _on_pages_changed.send()

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
st.sidebar.title("📅 Fila de Atendimentos de Hoje")
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
# 📋 Fila de Atendimento - Hoje (compacta e estilizada)
# ==============================
hoje = datetime.date.today()

# Normalizar colunas
df_fila["STATUS"] = df_fila["STATUS"].astype(str).str.strip().str.upper()
df_fila["DATA"] = pd.to_datetime(
    df_fila["DATA"], 
    dayfirst=True, 
    errors="coerce"
).dt.date

# Filtrar pacientes do dia
fila_hoje = df_fila[df_fila["DATA"] == hoje]

if not fila_hoje.empty:
    # Cabeçalho da tabela
    st.sidebar.markdown(
        "<div style='display:flex; font-weight:bold; padding:4px 8px; font-size:12px;'>"
        "<div style='flex:2'>NOME</div>"
        "<div style='flex:1; text-align:center'>STATUS</div>"
        "<div style='flex:1; text-align:center'>FICHA</div>"
        "<div style='flex:1; text-align:center'>EVOLUÇÃO</div>"
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

            # Badge de cor para status
            if status.upper() == "AGENDADO":
                cor_fundo = "#FFD700"   # amarelo
                cor_texto = "black"
            elif status.upper() == "ATENDIDO":
                cor_fundo = "#28a745"   # verde
                cor_texto = "white"
            elif status.upper() == "CANCELADO":
                cor_fundo = "#dc3545"   # vermelho
                cor_texto = "white"
            else:
                cor_fundo = "#6c757d"   # cinza
                cor_texto = "white"

            # Card horizontal estilizado
            with st.sidebar.container():
                cols = st.columns([2,1,1,1])
                
                # Nome
                cols[0].markdown(
                    f"<span style='font-size:13px; font-weight:500'>{nome_paciente}</span>",
                    unsafe_allow_html=True
                )
                
                # Status como badge colorido
                cols[1].markdown(
                    f"""
                    <div style='background-color:{cor_fundo};
                                color:{cor_texto};
                                font-size:11px;
                                font-weight:600;
                                text-align:center;
                                border-radius:8px;
                                padding:2px 6px;
                                display:inline-block;
                                width:90%'>
                        {status}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Botões de ação
                if cols[2].button("📄", key=f"ficha_{paciente_id}", help="Ver ficha clínica"):
                    st.query_params = {"idpaciente": str(paciente_id)}
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")

                if cols[3].button("🦷", key=f"evolucao_{paciente_id}", help="Incluir evolução do tratamento"):
                    st.query_params = {"idpaciente": str(paciente_id)}
                    add_page("1_🏠_home", "evolucao_tratamento")
                    st.switch_page("pages/evolucao_tratamento.py")
else:
    st.sidebar.info("⚠️ Nenhum paciente encontrado para hoje.")

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
