import streamlit as st
import datetime
import pandas as pd
import time
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed

# ==========================
# Configuração da Página
# ==========================
st.set_page_config(
    page_title="Gestão Céu da Boca - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profissional de Alta Densidade (UI/UX)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Padrão Profissional */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; letter-spacing: -0.5px; }
        .main-header p { margin: 0; opacity: 0.8; font-size: 0.85rem; }

        /* Estilização da Tabela */
        .table-header {
            background-color: #f1f5f9;
            padding: 8px 15px;
            border-radius: 8px;
            font-weight: 700;
            color: #475569;
            font-size: 0.8rem;
            margin-bottom: 5px;
            display: flex;
            text-transform: uppercase;
        }

        /* Linha de Paciente Ultra Estreita */
        .patient-row-container {
            border-bottom: 1px solid #f1f5f9;
            padding: 4px 0;
            transition: background 0.2s;
        }
        .patient-row-container:hover { background-color: #f8fafc; }

        /* Botões de Ação Mini */
        div[data-testid="column"] button {
            font-size: 10px !important;
            padding: 0px 4px !important;
            height: 24px !important;
            min-height: 24px !important;
            border-radius: 4px !important;
            width: 100%;
        }

        /* Badges */
        .badge {
            padding: 1px 6px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 700;
        }
        .badge-m { background-color: #e0f2fe; color: #0369a1; }
        .badge-f { background-color: #fdf2f8; color: #be185d; }
    </style>
""", unsafe_allow_html=True)

# ==========================
# Funções de Páginas e Dados
# ==========================
def add_page(main_script_path_str, page_name):
    pages = get_pages(main_script_path_str)
    main_script_path = Path(main_script_path_str)
    pages_dir = main_script_path.parent / "pages"
    try:
        script_path = [f for f in list(pages_dir.glob("*.py")) + list(main_script_path.parent.glob("*.py"))
                       if f.name.find(page_name) != -1][0]
        script_path_str = str(script_path.resolve())
        pi, pn = page_icon_and_name(script_path)
        psh = calc_md5(script_path_str)
        pages[psh] = {"page_script_hash": psh, "page_name": pn, "icon": pi, "script_path": script_path_str}
        _on_pages_changed.send()
    except IndexError:
        st.error(f"Página '{page_name}' não encontrada no diretório.")

def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        return pd.DataFrame(sh.worksheet("Pacientes").get_all_records()), pd.DataFrame(sh.worksheet("Fila").get_all_records()), gc
    except:
        return pd.DataFrame(), pd.DataFrame(), None

# Limpar menu lateral no carregamento
MAIN_SCRIPT = "1_🏠_home.py" # Ajuste conforme o nome do seu arquivo principal
for p in ["ficha_clinica", "alterar_paciente", "inserir_exames_e_diagnosticos", "evolucao_tratamento"]:
    delete_page(MAIN_SCRIPT, p)

df_pacientes, df_fila, gc = carregar_dados()

# Padronização
if not df_pacientes.empty:
    df_pacientes.columns = df_pacientes.columns.str.strip().str.upper()

# ==========================
# Sidebar e Cabeçalho
# ==========================
with st.sidebar:
    st.markdown("### 🏛️ Institucional\nFAO/UFAM")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.date.today()
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA"] == hoje]
        for _, r in fila_hoje.iterrows():
            p_id = str(r["PACIENTE_ID"]).strip()
            p_nome = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == p_id]["NOME"].values
            st.info(f"👤 **{p_nome[0] if len(p_nome)>0 else p_id}**")
    
    st.markdown("---")
    if st.button("🔄 Sincronizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("""
    <div class="main-header">
        <h1>Céu da Boca — Gestão de Pacientes</h1>
        <p>Sistema de Prontuários | Faculdade de Odontologia da UFAM</p>
    </div>
""", unsafe_allow_html=True)

# Busca Profissional
c_search, _ = st.columns([1.5, 2])
busca = c_search.text_input("🔍 Localizar paciente:", placeholder="Digite nome, FAO ou status...")

if busca:
    df_pacientes = df_pacientes[df_pacientes.apply(lambda r: r.astype(str).str.lower().str.contains(busca.lower()).any(), axis=1)]

# ==========================
# Lista de Pacientes
# ==========================
st.markdown("""
    <div class="table-header">
        <div style="flex: 2.2;">PACIENTE / FAO</div>
        <div style="flex: 0.5;">IDADE</div>
        <div style="flex: 0.4;">GEN</div>
        <div style="flex: 1.4;">FISSURA</div>
        <div style="flex: 1.0;">STATUS</div>
        <div style="flex: 4.5; text-align: center;">AÇÕES</div>
    </div>
""", unsafe_allow_html=True)

for idx, row in df_pacientes.iterrows():
    p_id = str(row.get("ID", "")).strip()
    nome = str(row.get("NOME", "-")).strip().upper()
    fao = row.get("FAO", "-")
    sexo = str(row.get("SEXO", "-")).upper()[:1]
    
    with st.container():
        # Linha principal
        c1, c2, c3, c4, c5, c_btns = st.columns([2.2, 0.5, 0.4, 1.4, 1.0, 4.5])
        
        c1.markdown(f"**{nome}**<br><small style='color:#64748b'>FAO: {fao}</small>", unsafe_allow_html=True)
        c2.markdown(f"<div style='padding-top:6px'>{row.get('IDADE', '-')}a</div>", unsafe_allow_html=True)
        
        g_style = "badge-m" if sexo == "M" else "badge-f"
        c3.markdown(f"<div style='padding-top:6px'><span class='badge {g_style}'>{sexo}</span></div>", unsafe_allow_html=True)
        
        c4.markdown(f"<div style='padding-top:6px; font-size:11px'>{row.get('TIPO_FISSURA', '-')}</div>", unsafe_allow_html=True)
        
        status_color = "#10b981" if "ATIVO" in str(row.get("STATUS")).upper() else "#94a3b8"
        c5.markdown(f"<div style='padding-top:6px; font-size:10px; color:{status_color}; font-weight:700'>{row.get('STATUS', '-')}</div>", unsafe_allow_html=True)

        with c_btns:
            st.write("") # Spacer
            # Agrupamento de 5 botões em mini colunas
            b1, b2, b3, b4, b5 = st.columns(5)
            
            if b1.button("📄 Ficha", key=f"f_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page(MAIN_SCRIPT, "ficha_clinica")
                st.switch_page("pages/ficha_clinica.py")
            
            if b2.button("✏️ Edit", key=f"e_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page(MAIN_SCRIPT, "alterar_paciente")
                st.switch_page("pages/alterar_paciente.py")

            if b3.button("🧾 Exam", key=f"x_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page(MAIN_SCRIPT, "inserir_exames_e_diagnosticos")
                st.switch_page("pages/inserir_exames_e_diagnosticos.py")
                
            if b4.button("🦷 Evol", key=f"v_{p_id}_{idx}"):
                st.query_params = {"idpaciente": p_id}
                add_page(MAIN_SCRIPT, "evolucao_tratamento")
                st.switch_page("pages/evolucao_tratamento.py")
                
            if b5.button("📅 Agnd", key=f"a_{p_id}_{idx}"):
                try:
                    sheet_f = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    sheet_f.append_row([p_id, hoje.strftime("%d/%m/%Y"), "AGENDADO"])
                    st.toast(f"✅ {nome} na fila!", icon="📅")
                    time.sleep(0.5)
                    st.rerun()
                except: st.error("Erro")

    st.markdown("<div style='margin-bottom:2px'></div>", unsafe_allow_html=True)

st.markdown("---")
st.caption(f"Total: {len(df_pacientes)} registros.")