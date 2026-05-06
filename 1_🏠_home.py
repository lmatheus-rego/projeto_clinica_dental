import streamlit as st
import datetime
import pandas as pd
import time
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from pathlib import Path
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed

# ==========================
# Configuração da Página
# ==========================
st.set_page_config(
    page_title="Céu da Boca - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores Padrão
COR_PRIMARIA = "#004a99"  # Azul Institucional
COR_ALERTA = "#E57373"    # Vermelho Suave para "Não Especificado"
COR_MASCULINO = "#AED6F1"
COR_FEMININO = "#F5B7B1"

# CSS Profissional e Customizado
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * {{ font-family: 'Inter', sans-serif; }}

        /* Estilização do Título Profissional */
        .main-header {{
            background: linear-gradient(90deg, {COR_PRIMARIA} 0%, #007bff 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .main-header h1 {{ 
            margin: 0; 
            font-weight: 800; 
            font-size: 2.2rem; 
            color: white !important; 
        }}
        .main-header p {{ 
            margin: 5px 0 0 0; 
            opacity: 0.9; 
            font-size: 1rem; 
            color: white !important; 
        }}

        /* Cards de Métricas */
        .metric-card {{
            background-color: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-top: 4px solid {COR_PRIMARIA};
            text-align: center;
        }}
        .metric-label {{ color: #64748b; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; }}
        .metric-value {{ color: #1e293b; font-size: 2rem; font-weight: 700; margin-top: 5px; }}

        /* Ajustes de Tabs */
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            padding-top: 10px;
            font-weight: 600;
            font-size: 1rem;
        }}
    </style>
""", unsafe_allow_html=True)

# ==========================
# Funções de Dados
# ==========================
@st.cache_data(ttl=300)
def carregar_dados():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        
        df_p = pd.DataFrame(sh.worksheet("Pacientes").get_all_records())
        df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        df_r = pd.DataFrame(sh.worksheet("Registros").get_all_records())
        
        return df_p, df_f, df_r
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_pacientes, df_fila, df_registros = carregar_dados()

# Limpeza e Padronização
if not df_pacientes.empty:
    df_pacientes.columns = df_pacientes.columns.str.strip().str.upper()
    fiss_col = "TIPO_FISSURA"
    df_pacientes[fiss_col] = df_pacientes[fiss_col].astype(str).str.strip().replace(["", "nan", "None"], "Não Especificado")

# ==========================
# Cabeçalho Institucional
# ==========================
st.markdown("""
    <div class="main-header">
        <h1>Céu da Boca — FAO/UFAM</h1>
        <p>Faculdade de Odontologia | Universidade Federal do Amazonas</p>
    </div>
""", unsafe_allow_html=True)

# ==========================
# Métricas Principais
# ==========================
total_p = len(df_pacientes)
total_e = len(df_registros)
nao_esp = (df_pacientes["TIPO_FISSURA"] == "Não Especificado").sum()

m1, m2, m3 = st.columns(3)
with m1: st.markdown(f'<div class="metric-card"><div class="metric-label">👥 Total Pacientes</div><div class="metric-value">{total_p}</div></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-card"><div class="metric-label">🦷 Evoluções</div><div class="metric-value">{total_e}</div></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="metric-card"><div class="metric-label">⚠️ Pacientes sem Fissura Definida</div><div class="metric-value">{nao_esp}</div></div>', unsafe_allow_html=True)

st.write("")

# ==========================
# Área de Gráficos
# ==========================
tab_clinico, tab_demo, tab_hist = st.tabs(["📋 Perfil Clínico", "👥 Demografia", "📈 Histórico"])

with tab_clinico:
    st.subheader("Distribuição por Tipo de Fissura")
    df_fiss = df_pacientes["TIPO_FISSURA"].value_counts().reset_index()
    df_fiss.columns = ["Tipo", "Qtd"]
    
    df_normal = df_fiss[df_fiss["Tipo"] != "Não Especificado"].sort_values("Qtd", ascending=False)
    df_extra = df_fiss[df_fiss["Tipo"] == "Não Especificado"]
    df_final_fiss = pd.concat([df_normal, df_extra])
    
    cores_map = {tipo: COR_PRIMARIA for tipo in df_final_fiss["Tipo"]}
    cores_map["Não Especificado"] = COR_ALERTA
    
    fig_fiss = px.bar(
        df_final_fiss, x="Tipo", y="Qtd", 
        color="Tipo", color_discrete_map=cores_map,
        text="Qtd", template="plotly_white"
    )
    fig_fiss.update_layout(showlegend=False, height=500, xaxis_title="", yaxis_title="Nº de Pacientes")
    st.plotly_chart(fig_fiss, use_container_width=True)

with tab_demo:
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.subheader("Gênero")
        sexo_col = "SEXO" if "SEXO" in df_pacientes.columns else df_pacientes.columns[1]
        df_sexo = df_pacientes[sexo_col].value_counts().reset_index()
        df_sexo.columns = ["Sexo", "Qtd"]
        
        fig_sexo = px.pie(
            df_sexo, names="Sexo", values="Qtd",
            color="Sexo",
            color_discrete_map={"Masculino": COR_MASCULINO, "Feminino": COR_FEMININO},
            hole=0.4, template="plotly_white"
        )
        st.plotly_chart(fig_sexo, use_container_width=True)
        
    with col_d2:
        st.subheader("Faixa Etária")
        if "DATA" in df_pacientes.columns:
            df_pacientes["DATA_DT"] = pd.to_datetime(df_pacientes["DATA"], errors='coerce', dayfirst=True)
            hoje_dt = pd.Timestamp.now()
            df_pacientes["IDADE"] = (hoje_dt - df_pacientes["DATA_DT"]).dt.days // 365
            
            bins = [0, 12, 18, 30, 60, 120]
            labels = ["Infantil (0-12)", "Adolescente (13-18)", "Jovem Adulto (19-30)", "Adulto (31-60)", "Idoso (60+)"]
            df_pacientes["FAIXA"] = pd.cut(df_pacientes["IDADE"], bins=bins, labels=labels)
            
            df_idade = df_pacientes["FAIXA"].value_counts().reindex(labels).reset_index()
            df_idade.columns = ["Faixa", "Qtd"]
            
            fig_idade = px.bar(
                df_idade, x="Faixa", y="Qtd", 
                text="Qtd", color_discrete_sequence=[COR_PRIMARIA],
                template="plotly_white"
            )
            fig_idade.update_layout(yaxis_title="Nº de Pacientes", xaxis_title="")
            st.plotly_chart(fig_idade, use_container_width=True)

with tab_hist:
    st.subheader("Evolução de Atendimentos")
    if not df_registros.empty and "DATA_REGISTRO" in df_registros.columns:
        df_registros["DATA_DT"] = pd.to_datetime(df_registros["DATA_REGISTRO"], errors='coerce', dayfirst=True)
        df_registros["Mês"] = df_registros["DATA_DT"].dt.to_period("M").astype(str)
        df_hist = df_registros.groupby("Mês").size().reset_index(name="Atendimentos")
        
        fig_hist = px.line(
            df_hist, x="Mês", y="Atendimentos", 
            markers=True, line_shape="spline",
            template="plotly_white", color_discrete_sequence=[COR_PRIMARIA]
        )
        fig_hist.update_layout(yaxis_title="Registros", xaxis_title="Mês de Referência")
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Aguardando mais registros de evolução para gerar o histórico.")

# ==========================
# Sidebar: Fila do Dia
# ==========================
with st.sidebar:
    st.markdown("### 🏛️ Institucional")
    st.caption("Universidade Federal do Amazonas\nFaculdade de Odontologia")
    st.markdown("---")
    st.markdown("### 📅 Fila de Atendimento")
    hoje = datetime.date.today()
    
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA"] == hoje]
        
        if not fila_hoje.empty:
            for _, r in fila_hoje.iterrows():
                p_id = str(r["PACIENTE_ID"]).strip()
                p_nome = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == p_id]["NOME"].values
                nome_display = p_nome[0] if len(p_nome) > 0 else f"ID: {p_id}"
                st.success(f"👤 **{nome_display}**\n\nStatus: {r.get('STATUS', 'Agendado')}")
        else:
            st.write("Sem atendimentos hoje.")
    
    st.markdown("---")
    if st.button("🔄 Atualizar Informações"):
        st.cache_data.clear()
        st.rerun()

# Rodapé
st.markdown("---")
st.caption(f"Céu da Boca Dashboard | FAO-UFAM | Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")