import streamlit as st
import datetime
import pandas as pd
import time
import gspread
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
from pathlib import Path
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed

# ==========================
# Configuração da Página & CSS Profissional
# ==========================
st.set_page_config(
    page_title="Projeto Céu da Boca | Dashboard", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS para um visual mais limpo e moderno
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Estilização dos Cards de Métricas */
        .metric-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #007bff;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-title {
            color: #64748b;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .metric-value {
            color: #1e293b;
            font-size: 28px;
            font-weight: 700;
        }

        /* Ajustes de espaçamento */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Sidebar customizada */
        section[data-testid="stSidebar"] {
            background-color: #f8fafc;
            border-right: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================
# Funções de Gerenciamento de Páginas
# ==========================
def delete_page(page_name):
    try:
        pages = get_pages("1_🏠_home.py")
        for key, value in list(pages.items()):
            if value['page_name'] == page_name:
                del pages[key]
        _on_pages_changed.send()
    except:
        pass

# Limpeza de páginas de navegação interna (se necessário)
for p in ["ficha_clinica", "alterar_paciente", "inserir_exames_e_diagnosticos", "evolucao_tratamento"]:
    delete_page(p)

# ==========================
# Conexão e Dados
# ==========================
@st.cache_data(ttl=600) # Cache de 10 minutos para performance
def carregar_dados_gsheets():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        
        df_p = pd.DataFrame(sh.worksheet("Pacientes").get_all_records())
        df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        df_r = pd.DataFrame(sh.worksheet("Registros").get_all_records())
        
        # Limpeza básica
        df_r = df_r[~df_r.astype(str).apply(lambda x: x.str.strip()).eq("").all(axis=1)]
        return df_p, df_f, df_r
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_pacientes, df_fila, df_registros = carregar_dados_gsheets()

# ==========================
# Sidebar: Fila de Atendimento
# ==========================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3467/3467739.png", width=80) # Ícone Odonto
    st.markdown("### 📋 Fila de Hoje")
    hoje = datetime.date.today()
    
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA"] == hoje]
        
        if not fila_hoje.empty:
            for _, row in fila_hoje.iterrows():
                p_id = str(row["PACIENTE_ID"]).strip()
                p_info = df_pacientes[df_pacientes["Id"].astype(str).str.strip() == p_id]
                nome = p_info.iloc[0]["Nome"] if not p_info.empty else f"ID: {p_id}"
                st.info(f"👤 **{nome}**\n\nStatus: {row.get('STATUS', 'Aguardando')}")
        else:
            st.write("✨ Ninguém na fila no momento.")
    st.markdown("---")

# ==========================
# Cabeçalho Principal
# ==========================
c_title1, c_title2 = st.columns([4, 1])
with c_title1:
    st.title("🦷 Dashboard Projeto Céu da Boca")
    st.markdown("_Análise de indicadores e acompanhamento clínico_")
with c_title2:
    st.write("")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ==========================
# 📊 Seção de Métricas (Cards Customizados)
# ==========================
total_pacientes = len(df_pacientes)
total_evolucao = len(df_registros)
fissura_col = "TIPO_FISSURA" if "TIPO_FISSURA" in df_pacientes.columns else "Tipo_Fissura"
df_pacientes[fissura_col] = df_pacientes[fissura_col].astype(str).replace(["", "nan"], "Não Especificado")
nao_especificado = (df_pacientes[fissura_col] == "Não Especificado").sum()

m1, m2, m3 = st.columns(3)

def render_metric(col, title, value, icon):
    col.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{icon} {title}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

render_metric(m1, "Total de Pacientes", total_pacientes, "👥")
render_metric(m2, "Registros Clínicos", total_evolucao, "📄")
render_metric(m3, "Fissuras s/ Dados", nao_especificado, "⚠️")

st.write("")
st.write("")

# ==========================
# 📈 Área de Gráficos Históricos
# ==========================
tab1, tab2 = st.tabs(["📊 Distribuição Clínica", "📈 Evolução Temporal"])

with tab1:
    col_f1, col_f2 = st.columns([2, 1])
    
    with col_f1:
        st.markdown("#### Distribuição por Tipo de Fissura")
        df_fiss = df_pacientes[fissura_col].value_counts().reset_index()
        df_fiss.columns = ["Tipo", "Qtd"]
        
        fig_bar = px.bar(
            df_fiss, x="Qtd", y="Tipo", orientation='h',
            text="Qtd", color="Tipo",
            color_discrete_sequence=px.colors.qualitative.Safe,
            template="plotly_white"
        )
        fig_bar.update_layout(showlegend=False, height=450, margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_f2:
        st.markdown("#### Perfil Demográfico")
        sexo_col = "SEXO" if "SEXO" in df_pacientes.columns else "Sexo"
        df_sexo = df_pacientes[sexo_col].value_counts().reset_index()
        df_sexo.columns = ["Sexo", "Qtd"]
        
        fig_pie = px.pie(
            df_sexo, names="Sexo", values="Qtd",
            hole=0.5,
            color_discrete_sequence=["#AED6F1", "#F5B7B1"],
            template="plotly_white"
        )
        fig_pie.update_layout(margin=dict(l=0, r=0, t=10, b=10), height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.markdown("#### Atendimentos ao Longo do Tempo")
    if not df_registros.empty and "DATA_REGISTRO" in df_registros.columns:
        df_registros["DATA_DT"] = pd.to_datetime(df_registros["DATA_REGISTRO"], errors="coerce", dayfirst=True)
        df_registros["Mês/Ano"] = df_registros["DATA_DT"].dt.to_period("M").astype(str)
        df_evol = df_registros.groupby("Mês/Ano").size().reset_index(name="Atendimentos")
        
        fig_line = px.area(
            df_evol, x="Mês/Ano", y="Atendimentos",
            markers=True,
            color_discrete_sequence=["#007bff"],
            template="plotly_white"
        )
        fig_line.update_layout(height=400)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Dados de evolução insuficientes para gerar gráfico temporal.")

# ==========================
# Rodapé
# ==========================
st.markdown("---")
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.caption(f"Sistema Gerencial - Projeto Céu da Boca v2.0 | Último acesso: {datetime.datetime.now().strftime('%H:%M:%S')}")
with col_f2:
    st.markdown("<div style='text-align: right'>🔍 <i>Dados protegidos conforme LGPD</i></div>", unsafe_allow_html=True)