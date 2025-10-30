import streamlit as st
import datetime
import pandas as pd
import time
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import plotly.express as px
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from assets.ceu_da_boca.header_footer import render_header, render_footer, _svg_data_uri, _ASSET_SVG_PATH

# ==========================
# Configuração inicial
# ==========================
st.set_page_config(page_title="Projeto Céu da Boca", page_icon="🦷", layout="wide")

# ==========================
# CSS global
# ==========================
css_path = "assets/ceu_da_boca/style.css"
with open(css_path, "r", encoding="utf-8") as f:
    css_content = f.read()
st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


# ==========================
# Adicionar logotipo como marca d’água na sidebar
# ==========================
svg_data = _svg_data_uri(_ASSET_SVG_PATH) if _ASSET_SVG_PATH.exists() else ""

st.markdown(f"""
<style>
/* Marca d'água no topo da sidebar */
[data-testid="stSidebar"]::before {{
    content: "";
    position: absolute;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    width: 85%;
    height: 120px;
    background-image: url('{svg_data}');
    background-repeat: no-repeat;
    background-position: center top;
    background-size: contain;
    opacity: 0.15; /* transparência para efeito de marca d'água */
    z-index: 0;
}}
/* Garantir que os elementos da sidebar fiquem acima da imagem */
[data-testid="stSidebar"] > div:first-child {{
    position: relative;
    z-index: 1;
}}
</style>
""", unsafe_allow_html=True)

# ==========================
# Sidebar e Título
# ==========================
st.sidebar.title("📅 Fila de Atendimentos de Hoje")
st.title("Projeto Céu da Boca")

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
# Carregar dados
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

df_pacientes = carregar_aba("Pacientes")
df_fila = carregar_aba("Fila")
df_registros = carregar_aba("Registros")

# ==========================
# Fila de Atendimento
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
            cols[0].markdown(f"<span style='font-size:13px; font-weight:500'>{nome_paciente}</span>", unsafe_allow_html=True)
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
# Resumo e Gráficos
# ==========================
total_pacientes = len(df_pacientes)
atendidos_mes = len(df_registros)
st.markdown("## 📊 Resumo Geral")
col1, col2 = st.columns(2)
col1.metric("👥 Total de Pacientes Cadastrados no Projeto", value=total_pacientes)
col2.metric("📆 Total de Registros de Evolução", value=atendidos_mes)

# ==========================
# Rodapé
# ==========================
render_footer()
