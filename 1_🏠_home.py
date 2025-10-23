import streamlit as st
import datetime
import pandas as pd
import time
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import plotly.express as px
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed

# ==========================
# Funções de páginas dinâmicas
# ==========================
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

def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# ==========================
# Configuração inicial
# ==========================
st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")
st.sidebar.title("📅 Fila de Atendimentos de Hoje")
st.title("Projeto Céu da Boca")

# Remover páginas temporárias
delete_page("1_🏠_home", "ficha_clinica")
delete_page("1_🏠_home", "alterar_paciente")
delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
delete_page("1_🏠_home", "evolucao_tratamento")

# ==========================
# Função para carregar dados do Google Sheets
# ==========================
def carregar_aba(nome_aba, tentativas=3, delay=3):
    for i in range(tentativas):
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )
            gc = gspread.authorize(credentials)
            sheet = gc.open_by_key(
                "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
            ).worksheet(nome_aba)
            dados = sheet.get_all_records()
            return pd.DataFrame(dados)
        except Exception as e:
            if i < tentativas - 1:
                st.warning(f"⚠️ Erro ao carregar '{nome_aba}', tentando novamente ({i+1}/{tentativas})...")
                time.sleep(delay)
            else:
                st.error(f"❌ Falha ao carregar '{nome_aba}': {e}")
                return pd.DataFrame()

# ==========================
# Carregar dados
# ==========================
df_pacientes = carregar_aba("Pacientes")
df_fila = carregar_aba("Fila")
df_registros = carregar_aba("Registros")

# ==========================
# 📋 Fila de Atendimento - Hoje
# ==========================
hoje = datetime.date.today()
if "STATUS" in df_fila.columns and "DATA" in df_fila.columns:
    df_fila["STATUS"] = df_fila["STATUS"].astype(str).str.strip().str.upper()
    df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
    fila_hoje = df_fila[df_fila["DATA"] == hoje]
else:
    fila_hoje = pd.DataFrame()

if not fila_hoje.empty:
    st.sidebar.markdown(
        "<div style='display:flex; font-weight:bold; padding:4px 8px; font-size:12px;'>"
        "<div style='flex:2'>NOME</div>"
        "<div style='flex:1; text-align:center'>STATUS</div>"
        "<div style='flex:1; text-align:center'>FICHA</div>"
        "<div style='flex:1; text-align:center'>EVOLUÇÃO</div>"
        "</div>", unsafe_allow_html=True)

    for _, row in fila_hoje.iterrows():
        paciente_id = str(row.get("PACIENTE_ID", "")).strip()
        paciente = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == paciente_id]

        if not paciente.empty:
            nome_paciente = paciente.iloc[0]["NOME"]
            status = row["STATUS"].capitalize()

            cor_status = {
                "AGENDADO": ("#FFD700", "black"),
                "ATENDIDO": ("#28a745", "white"),
                "CANCELADO": ("#dc3545", "white"),
            }.get(status.upper(), ("#6c757d", "white"))

            cols = st.sidebar.columns([2, 1, 1, 1])
            cols[0].markdown(
                f"<span style='font-size:13px; font-weight:500'>{nome_paciente}</span>",
                unsafe_allow_html=True
            )
            cols[1].markdown(
                f"<div style='background-color:{cor_status[0]}; color:{cor_status[1]}; font-size:11px;"
                f"font-weight:600; text-align:center; border-radius:8px; padding:2px 6px; width:90%'>{status}</div>",
                unsafe_allow_html=True
            )

            if cols[2].button("📄", key=f"ficha_{paciente_id}", help="Ver ficha clínica"):
                st.query_params = {"idpaciente": paciente_id}
                add_page("1_🏠_home", "ficha_clinica")
                st.switch_page("pages/ficha_clinica.py")

            if cols[3].button("🦷", key=f"evolucao_{paciente_id}", help="Evolução"):
                st.query_params = {"idpaciente": paciente_id}
                add_page("1_🏠_home", "evolucao_tratamento")
                st.switch_page("pages/evolucao_tratamento.py")
else:
    st.sidebar.info("⚠️ Nenhum paciente encontrado para hoje.")

# ==========================
# 📊 Resumo Geral
# ==========================
total_pacientes = len(df_pacientes)
atendidos_mes = len(df_registros)  # simplificado
fissuras = df_pacientes["TIPO DE FISSURA"].value_counts().to_dict() if "TIPO DE FISSURA" in df_pacientes.columns else {}

st.markdown("## 📊 Resumo Geral")
col1, col2, col3 = st.columns(3)
col1.metric("👥 Total de Pacientes", value=total_pacientes)
col2.metric("📆 Total de Registros", value=atendidos_mes)
col3.metric("💉 Tipos de Fissura", value=len(fissuras))

# ==========================
# Gráficos Históricos
# ==========================
st.markdown("## 📈 Gráficos Históricos")

# --- Gráfico 1: Tipo de Fissura ---
st.markdown("### 🦷 Pacientes por Tipo de Fissura")
if "TIPO DE FISSURA" in df_pacientes.columns:
    df_fissura = df_pacientes["TIPO DE FISSURA"].value_counts().reset_index()
    df_fissura.columns = ["Tipo de Fissura", "Quantidade"]
    fig_fissura = px.bar(df_fissura, x="Tipo de Fissura", y="Quantidade", text="Quantidade",
                         title="Pacientes por Tipo de Fissura")
    fig_fissura.update_traces(textposition="outside")
    st.plotly_chart(fig_fissura, use_container_width=True)

# --- Gráfico 2: Sexo (Pizza) ---
st.markdown("### 👩‍🦰 Pacientes por Sexo")
if "SEXO" in df_pacientes.columns:
    df_sexo = df_pacientes["SEXO"].value_counts().reset_index()
    df_sexo.columns = ["Sexo", "Quantidade"]
    fig_sexo = px.pie(df_sexo, names="Sexo", values="Quantidade", title="Distribuição de Pacientes por Sexo")
    st.plotly_chart(fig_sexo, use_container_width=True)

# --- Gráfico 3: Linha Temporal de Atendimentos ---
st.markdown("### 📈 Atendimentos ao Longo do Tempo")
if not df_registros.empty and "DATA_REGISTRO" in df_registros.columns:
    df_registros["DATA_REGISTRO"] = pd.to_datetime(df_registros["DATA_REGISTRO"], errors="coerce", dayfirst=True)
    df_tempo = df_registros.dropna(subset=["DATA_REGISTRO"]).copy()
    df_tempo["AnoMes"] = df_tempo["DATA_REGISTRO"].dt.to_period("M").astype(str)
    df_tempo_contagem = df_tempo.groupby("AnoMes")["PACIENTE_ID"].nunique().reset_index()
    df_tempo_contagem.columns = ["Ano-Mês", "Pacientes Atendidos"]
    fig_tempo = px.line(df_tempo_contagem, x="Ano-Mês", y="Pacientes Atendidos",
                        markers=True, title="Pacientes Atendidos por Mês")
    fig_tempo.update_yaxes(range=[0, df_tempo_contagem["Pacientes Atendidos"].max() + 1])
    st.plotly_chart(fig_tempo, use_container_width=True)
