import streamlit as st
import datetime
import pandas as pd
import time
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import plotly.express as px
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from assets.ceu_da_boca.header_footer import render_header, render_footer

css_path = "assets/ceu_da_boca/style.css"

with open(css_path, "r", encoding="utf-8") as f:
    css_content = f.read()

# ==========================
# Funções de páginas dinâmica
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
st.set_page_config(page_title="Projeto Céu da Boca", page_icon="🦷", layout="wide")
st.sidebar.title("📅 Fila de Atendimentos de Hoje")
st.title("Projeto Céu da Boca")

delete_page("1_🏠_home", "ficha_clinica")
delete_page("1_🏠_home", "alterar_paciente")
delete_page("1_🏠_home", "inserir_exames_e_diagnosticos")
delete_page("1_🏠_home", "evolucao_tratamento")

# ==========================
# Função para carregar dados
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

# Remove linhas completamente vazias ou com espaços
df_registros = df_registros[
    ~df_registros.astype(str)
    .apply(lambda x: x.str.strip())
    .eq("")
    .all(axis=1)
]

# ==========================
# 📊 Resumo Geral
# ==========================
st.markdown("## 📊 Resumo Geral")

total_pacientes = len(df_pacientes)
atendidos_mes = len(df_registros)

df_pacientes["TIPO_FISSURA"] = df_pacientes.get("TIPO_FISSURA", "").astype(str).str.strip()
df_pacientes["TIPO_FISSURA"] = df_pacientes["TIPO_FISSURA"].replace("", "Não Especificado").fillna("Não Especificado")

total_nao_especificado = (df_pacientes["TIPO_FISSURA"] == "Não Especificado").sum()

col1, col2, col3 = st.columns(3)
col1.metric("👥 Total de Pacientes", total_pacientes)
col2.metric("📆 Registros de Evolução", atendidos_mes)
col3.metric("❓ Fissuras Não Especificadas", total_nao_especificado)

# ==========================
# 📈 Gráficos
# ==========================
st.markdown("## 📈 Gráficos Históricos")

# --- CORES POR GRUPO ---
def cor_fissura(tipo):
    if tipo == "Não Especificado":
        return "#E57373"  # vermelho
    if tipo in ["Pré-forame Unilateral Direita", "Pré-forame Unilateral Esquerda", "Pré-forame Bilateral"]:
        return "#AED6F1"
    if tipo in ["Transforame Unilateral Direita", "Transforame Unilateral Esquerda", "Transforame Bilateral"]:
        return "#A9DFBF"
    if tipo in ["Pós-forame Completa", "Pós-forame Incompleta"]:
        return "#F9E79F"
    if tipo == "Fissura Rara da Face":
        return "#D7BDE2"
    if tipo == "Fissura Mediana":
        return "#F5CBA7"
    return "#D5DBDB"

# --- Tipo de Fissura ---
st.markdown("### 🦷 Pacientes por Tipo de Fissura")

df_fissura = df_pacientes["TIPO_FISSURA"].value_counts().reset_index()
df_fissura.columns = ["Tipo", "Qtd"]

nao = df_fissura[df_fissura["Tipo"] == "Não Especificado"]
outros = df_fissura[df_fissura["Tipo"] != "Não Especificado"].sort_values("Qtd", ascending=False)
df_fissura = pd.concat([outros, nao])

df_fissura["Cor"] = df_fissura["Tipo"].apply(cor_fissura)

fig = px.bar(df_fissura, x="Tipo", y="Qtd", text="Qtd", color="Tipo",
             color_discrete_map={t: cor_fissura(t) for t in df_fissura["Tipo"]},
             title="Distribuição por Tipo de Fissura")

st.plotly_chart(fig, use_container_width=True)

# --- Pizzas ---
colg1, colg2 = st.columns(2)

with colg1:
    st.markdown("### 🧒🏾👴🏻 Faixa Etária dos Pacientes")
    if "DATA" in df_pacientes.columns:
        df_pacientes["DATA"] = pd.to_datetime(df_pacientes["DATA"], errors="coerce", dayfirst=True)
        hoje = pd.Timestamp.today()
        df_pacientes["IDADE"] = (hoje - df_pacientes["DATA"]).dt.days // 365

        bins = [0, 9, 20, 29, 59, 200]
        labels = ["0-9", "10-20", "21-29", "30-59", "60+"]
        df_pacientes["FAIXA"] = pd.cut(df_pacientes["IDADE"], bins=bins, labels=labels)

        df_idade = df_pacientes["FAIXA"].value_counts().reset_index()
        df_idade.columns = ["Faixa", "Qtd"]

        fig = px.pie(df_idade, names="Faixa", values="Qtd",
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     title="Distribuição por Faixa Etária")
        st.plotly_chart(fig, use_container_width=True)

with colg2:
    st.markdown("### ♂️♀️ Pacientes por Sexo")

    df_sexo = df_pacientes["SEXO"].value_counts().reset_index()
    df_sexo.columns = ["Sexo", "Qtd"]

    cores = {
        "Masculino": "#AED6F1",
        "Feminino": "#F5B7B1"
    }

    fig = px.pie(df_sexo, names="Sexo", values="Qtd",
                 color="Sexo", color_discrete_map=cores,
                 title="Distribuição por Sexo")

    st.plotly_chart(fig, use_container_width=True)

# --- Linha Temporal ---
st.markdown("### 📈 Atendimentos ao Longo do Tempo")

if not df_registros.empty and "DATA_REGISTRO" in df_registros.columns:

    # Converter data
    df_registros["DATA_REGISTRO"] = pd.to_datetime(
        df_registros["DATA_REGISTRO"], errors="coerce", dayfirst=True
    )

    # NÃO remover registros — apenas criar agrupamento
    df_registros["AnoMes"] = df_registros["DATA_REGISTRO"].dt.to_period("M").astype(str)

    # Contar TODAS as linhas (sem nunique)
    df_group = df_registros.groupby("AnoMes").size().reset_index(name="Registros")

    # Ordenar corretamente
    df_group = df_group.sort_values("AnoMes")

    # Criar gráfico
    fig = px.line(
        df_group,
        x="AnoMes",
        y="Registros",
        markers=True,
        title="Total de Registros por Mês"
    )

    # Garantir eixo começando em 0
    fig.update_yaxes(range=[0, df_group["Registros"].max() + 1])

    st.plotly_chart(fig, use_container_width=True)

render_footer()