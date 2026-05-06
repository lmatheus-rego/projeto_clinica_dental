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

# CSS Profissional de Alta Precisão
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }

        /* Cabeçalho Gradient */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; }
        .main-header p { margin: 0; opacity: 0.8; font-size: 0.85rem; }

        /* Estilização da Tabela */
        .table-header {
            background-color: #f1f5f9;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: 700;
            color: #475569;
            font-size: 0.85rem;
            margin-bottom: 5px;
            display: flex;
        }

        /* Ajuste de Fontes de Dados (Fissura e Status) */
        .data-text {
            font-size: 13.5px !important;
            font-weight: 500;
            color: #1e293b;
        }
        .status-text {
            font-size: 13px !important;
            font-weight: 700;
            text-transform: uppercase;
        }

        /* Botões de Ação Otimizados */
        div[data-testid="column"] button {
            font-size: 12px !important; /* Fonte maior para legibilidade */
            padding: 0px 2px !important;
            height: 30px !important;
            border-radius: 6px !important;
            width: 100%;
            border: 1px solid #e2e8f0 !important;
            background-color: white !important;
            color: #004a99 !important;
        }
        div[data-testid="column"] button:hover {
            background-color: #004a99 !important;
            color: white !important;
        }

        /* Badges */
        .badge {
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
        }
        .badge-m { background-color: #e0f2fe; color: #0369a1; }
        .badge-f { background-color: #fdf2f8; color: #be185d; }
    </style>
""", unsafe_allow_html=True)

# ==========================
# Funções de Redirecionamento e Dados
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
    except:
        pass

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

# Nome do arquivo principal para controle de páginas
MAIN_SCRIPT = "1_🏠_home.py" 

# Esconder páginas do menu lateral ao carregar
for p in ["ficha_clinica", "alterar_paciente", "inserir_exames_e_diagnosticos", "evolucao_tratamento"]:
    delete_page(MAIN_SCRIPT, p)

df_pacientes, df_fila, gc = carregar_dados()

if not df_pacientes.empty:
    df_pacientes.columns = df_pacientes.columns.str.strip().str.upper()

# ==========================
# Sidebar e Pesquisa
# ==========================
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM")
    st.markdown("---")
    st.markdown("### 📅 Fila do Dia")
    hoje = datetime.date.today()
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA"] == hoje]
        for _, r in fila_hoje.iterrows():
            p_id = str(r["PACIENTE_ID"]).strip()
            p_nome = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == p_id]["NOME"].values
            st.info(f"👤 **{p_nome[0] if len(p_nome)>0 else p_id}**")
    
    if st.button("🔄 Sincronizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("""
    <div class="main-header">
        <h1>Céu da Boca — Gestão de Pacientes</h1>
        <p>Faculdade de Odontologia da Universidade Federal do Amazonas</p>
    </div>
""", unsafe_allow_html=True)

c_search, _ = st.columns([1.5, 2])
busca = c_search.text_input("🔍 Buscar paciente:", placeholder="Nome, FAO ou status...")

if busca:
    df_pacientes = df_pacientes[df_pacientes.apply(lambda r: r.astype(str).str.lower().str.contains(busca.lower()).any(), axis=1)]

# ==========================
# Lista de Pacientes (Tabela Otimizada)
# ==========================
# Reajustei as proporções: Ações agora ocupa 3.5 em vez de 4.5
st.markdown("""
    <div class="table-header">
        <div style="flex: 2.2;">PACIENTE / FAO</div>
        <div style="flex: 0.5;">IDADE</div>
        <div style="flex: 0.4;">GEN</div>
        <div style="flex: 1.8;">TIPO DE FISSURA</div>
        <div style="flex: 1.2;">STATUS</div>
        <div style="flex: 3.5; text-align: center;">AÇÕES</div>
    </div>
""", unsafe_allow_html=True)

for idx, row in df_pacientes.iterrows():
    p_id = str(row.get("ID", "")).strip()
    nome = str(row.get("NOME", "-")).strip().upper()
    fao = row.get("FAO", "-")
    sexo = str(row.get("SEXO", "-")).upper()[:1]
    fissura = row.get("TIPO_FISSURA", "-")
    status = row.get("STATUS", "-")
    
    with st.container():
        # Layout da Linha
        c1, c2, c3, c4, c5, c_btns = st.columns([2.2, 0.5, 0.4, 1.8, 1.2, 3.5])
        
        c1.markdown(f"**{nome}**<br><small style='color:#64748b'>FAO: {fao}</small>", unsafe_allow_html=True)
        c2.markdown(f"<div style='padding-top:10px'>{row.get('IDADE', '-')}a</div>", unsafe_allow_html=True)
        
        g_style = "badge-m" if sexo == "M" else "badge-f"
        c3.markdown(f"<div style='padding-top:8px'><span class='badge {g_style}'>{sexo}</span></div>", unsafe_allow_html=True)
        
        # Colunas com fonte aumentada conforme solicitado
        c4.markdown(f"<div class='data-text' style='padding-top:8px'>{fissura}</div>", unsafe_allow_html=True)
        
        st_color = "#10b981" if "ATIVO" in str(status).upper() else "#94a3b8"
        c5.markdown(f"<div class='status-text' style='padding-top:8px; color:{st_color}'>{status}</div>", unsafe_allow_html=True)

        with c_btns:
            st.write("") # Alinhador vertical
            b_cols = st.columns(5)
            
            if b_cols[0].button("📄 Ficha", key=f"f_{p_id}_{idx}", help="Ver Ficha"):
                st.query_params["idpaciente"] = p_id
                add_page(MAIN_SCRIPT, "ficha_clinica")
                st.switch_page("pages/ficha_clinica.py")
            
            if b_cols[1].button("✏️ Edit", key=f"e_{p_id}_{idx}", help="Editar Dados"):
                st.query_params["idpaciente"] = p_id
                add_page(MAIN_SCRIPT, "alterar_paciente")
                st.switch_page("pages/alterar_paciente.py")

            if b_cols[2].button("🧾 Exam", key=f"x_{p_id}_{idx}", help="Exames"):
                st.query_params["idpaciente"] = p_id
                add_page(MAIN_SCRIPT, "inserir_exames_e_diagnosticos")
                st.switch_page("pages/inserir_exames_e_diagnosticos.py")
                
            if b_cols[3].button("🦷 Evol", key=f"v_{p_id}_{idx}", help="Evolução"):
                st.query_params["idpaciente"] = p_id
                add_page(MAIN_SCRIPT, "evolucao_tratamento")
                st.switch_page("pages/evolucao_tratamento.py")
                
            if b_cols[4].button("📅 Agnd", key=f"a_{p_id}_{idx}", help="Agendar Hoje"):
                try:
                    sheet_f = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    sheet_f.append_row([p_id, hoje.strftime("%d/%m/%Y"), "AGENDADO"])
                    st.toast(f"✅ {nome} agendado!", icon="📅")
                    time.sleep(0.5)
                    st.rerun()
                except: st.error("Erro")

    st.markdown("<hr style='margin:2px 0; opacity:0.1'>", unsafe_allow_html=True)