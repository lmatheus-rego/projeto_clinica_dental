import streamlit as st
import datetime
import pandas as pd
import time
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5, 
    get_pages, 
    _on_pages_changed
)

# ==========================
# 🎨 CONFIGURAÇÃO E DESIGN FAO/UFAM
# ==========================
st.set_page_config(
    page_title="Gestão Céu da Boca - FAO/UFAM", 
    page_icon="🦷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS de Alta Fidelidade (Inter Font + Blue Gradient)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif !important; }

        /* Cabeçalho Gradient - Texto Branco */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%) !important;
            padding: 1.5rem 2rem !important;
            border-radius: 15px !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 4px 15px rgba(0,74,153,0.2) !important;
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .main-header h1 { 
            margin: 0 !important; 
            font-weight: 700 !important; 
            font-size: 1.8rem !important; 
            color: #FFFFFF !important; 
            border: none !important;
        }
        .main-header p { 
            margin: 5px 0 0 0 !important; 
            opacity: 0.9 !important; 
            font-size: 0.9rem !important; 
            color: #FFFFFF !important; 
        }

        /* Estilização da Tabela de Pacientes */
        .table-header {
            background-color: #f1f5f9;
            padding: 12px 15px;
            border-radius: 10px;
            font-weight: 700;
            color: #475569;
            font-size: 0.8rem;
            margin-bottom: 10px;
            display: flex;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .patient-row {
            padding: 10px 0;
            border-bottom: 1px solid #f1f5f9;
            transition: background 0.2s;
        }
        .patient-row:hover { background-color: #f8fafc; }

        /* Badges e Status */
        .badge {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
        }
        .badge-m { background-color: #e0f2fe; color: #0369a1; }
        .badge-f { background-color: #fdf2f8; color: #be185d; }
        .badge-evol { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }

        /* Botões de Ação Customizados */
        div[data-testid="column"] button {
            font-size: 11px !important;
            font-weight: 600 !important;
            height: 32px !important;
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            transition: all 0.3s !important;
        }
        div[data-testid="column"] button:hover {
            border-color: #004a99 !important;
            color: #004a99 !important;
            transform: translateY(-1px);
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- Funções de Sistema -----------------

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
    except: pass

def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# Removido @st.cache_data para garantir atualização em tempo real conforme solicitado
def carregar_dados():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        svc_account = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(svc_account, scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        
        # Carregamento de Tabelas
        df_p = pd.DataFrame(sh.worksheet("Pacientes").get_all_records())
        df_p.columns = df_p.columns.str.strip().str.upper()
        
        df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        df_f.columns = df_f.columns.str.strip().str.upper()
        
        df_r = pd.DataFrame(sh.worksheet("Registros").get_all_records())
        df_r.columns = df_r.columns.str.strip().str.upper()
        
        # Contagem de Evoluções
        if not df_r.empty and 'PACIENTE_ID' in df_r.columns:
            evol_counts = df_r['PACIENTE_ID'].astype(str).value_counts().reset_index()
            evol_counts.columns = ['ID_EVOL', 'QTD_EVOL']
            df_p['ID'] = df_p['ID'].astype(str)
            evol_counts['ID_EVOL'] = evol_counts['ID_EVOL'].astype(str)
            df_p = df_p.merge(evol_counts, left_on='ID', right_on='ID_EVOL', how='left').fillna({'QTD_EVOL': 0})
        else:
            df_p['QTD_EVOL'] = 0
            
        df_p['IDADE'] = pd.to_numeric(df_p['IDADE'], errors='coerce').fillna(0).astype(int)
        df_p['QTD_EVOL'] = df_p['QTD_EVOL'].astype(int)
            
        return df_p, df_f, gc
    except Exception as e:
        st.error(f"Erro na conexão com Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame(), None

# Limpeza de páginas dinâmicas ao carregar a Home
MAIN_SCRIPT = "1_🏠_home.py" 
for p in ["ficha_clinica", "alterar_paciente", "inserir_exames_e_diagnosticos", "evolucao_tratamento"]:
    delete_page(MAIN_SCRIPT, p)

# Carga de dados (Sempre atualizado)
df_pacientes, df_fila, gc = carregar_dados()

# ----------------- Sidebar -----------------
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.date.today()
    if not df_fila.empty:
        df_fila["DATA_DT"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA_DT"] == hoje]
        if fila_hoje.empty:
            st.caption("Nenhum paciente na fila.")
        for _, r in fila_hoje.iterrows():
            pid = str(r["PACIENTE_ID"]).strip()
            nome_p = df_pacientes[df_pacientes["ID"].astype(str).str.strip() == pid]["NOME"].values
            st.info(f"👤 **{nome_p[0] if len(nome_p)>0 else pid}**")
    
    st.markdown("<br>"*5, unsafe_allow_html=True)
    if st.button("🔄 Forçar Atualização", use_container_width=True):
        st.rerun()

# ----------------- Header Principal -----------------
st.markdown(f"""
    <div class="main-header">
        <span style="font-size: 2.5rem;">🦷</span>
        <div>
            <h1>Gestão de Pacientes — Céu da Boca</h1>
            <p>Faculdade de Odontologia - UFAM | {hoje.strftime('%d/%m/%Y')}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Filtros e Busca
c_search, c_sort = st.columns([2, 1])
busca = c_search.text_input("🔍 Localizar paciente:", placeholder="Digite nome, FAO ou status...")

with c_sort:
    opcoes_ordem = {
        "Nome (A-Z)": ("NOME", True),
        "Mais Evoluções": ("QTD_EVOL", False),
        "Idade (Crescente)": ("IDADE", True),
        "Status": ("STATUS", True)
    }
    ordem_sel = st.selectbox("⇅ Ordenar por:", list(opcoes_ordem.keys()))

# Lógica de Filtro e Ordem
if busca:
    df_pacientes = df_pacientes[df_pacientes.apply(lambda r: r.astype(str).str.lower().str.contains(busca.lower()).any(), axis=1)]

col_sort, asc_flag = opcoes_ordem[ordem_sel]
df_pacientes = df_pacientes.sort_values(by=col_sort, ascending=asc_flag)

# ----------------- Tabela de Resultados -----------------
st.markdown("""
    <div class="table-header">
        <div style="flex: 2.1;">PACIENTE / FAO</div>
        <div style="flex: 0.5;">IDADE</div>
        <div style="flex: 0.3;">GEN</div>
        <div style="flex: 1.5;">TIPO DE FISSURA</div>
        <div style="flex: 1.0;">STATUS</div>
        <div style="flex: 0.6; text-align: center;">EVOL.</div>
        <div style="flex: 3.5; text-align: center;">AÇÕES</div>
    </div>
""", unsafe_allow_html=True)

if df_pacientes.empty:
    st.warning("Nenhum paciente encontrado.")

for idx, row in df_pacientes.iterrows():
    p_id = str(row.get("ID", "")).strip()
    nome = str(row.get("NOME", "-")).strip().upper()
    fao = row.get("FAO", "-")
    sexo = str(row.get("SEXO", "-")).upper()[:1]
    fissura = row.get("TIPO_FISSURA", "-")
    status = row.get("STATUS", "-")
    qtd_evol = int(row.get("QTD_EVOL", 0))
    
    with st.container():
        c1, c2, c3, c4, c5, c6, c_btns = st.columns([2.1, 0.5, 0.3, 1.5, 1.0, 0.6, 3.5])
        
        c1.markdown(f"**{nome}**<br><small style='color:#64748b'>FAO: {fao}</small>", unsafe_allow_html=True)
        c2.markdown(f"<div style='padding-top:10px'>{row.get('IDADE')}a</div>", unsafe_allow_html=True)
        
        badge_sexo = "badge-m" if sexo == "M" else "badge-f"
        c3.markdown(f"<div style='padding-top:8px'><span class='badge {badge_sexo}'>{sexo}</span></div>", unsafe_allow_html=True)
        
        c4.markdown(f"<div style='padding-top:8px; font-size:12px; color:#475569'>{fissura}</div>", unsafe_allow_html=True)
        
        st_color = "#10b981" if "ATIVO" in str(status).upper() else "#94a3b8"
        c5.markdown(f"<div style='padding-top:8px; font-size:12px; font-weight:700; color:{st_color}'>{status}</div>", unsafe_allow_html=True)

        c6.markdown(f"<div style='padding-top:8px; text-align:center;'><span class='badge badge-evol'>{qtd_evol}</span></div>", unsafe_allow_html=True)

        with c_btns:
            st.write("") 
            b_cols = st.columns(5)
            
            # Navegação Dinâmica com Passagem de ID
            paginas_acao = [
                ("📄 Ficha", "ficha_clinica", "f"),
                ("✏️ Edit", "alterar_paciente", "e"),
                ("🧾 Exam", "inserir_exames_e_diagnosticos", "x"),
                ("🦷 Evol", "evolucao_tratamento", "v")
            ]
            
            for i, (label, pg, prefix) in enumerate(paginas_acao):
                if b_cols[i].button(label, key=f"{prefix}_{p_id}_{idx}"):
                    st.query_params["idpaciente"] = p_id
                    add_page(MAIN_SCRIPT, pg)
                    st.switch_page(f"pages/{pg}.py")
            
            # Ação de Agendamento Rápido
            if b_cols[4].button("📅 Agnd", key=f"a_{p_id}_{idx}"):
                try:
                    sheet_f = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    sheet_f.append_row([p_id, hoje.strftime("%d/%m/%Y"), "AGENDADO"])
                    st.toast(f"✅ {nome} adicionado à fila!", icon="📅")
                    time.sleep(0.5)
                    st.rerun()
                except: st.error("Erro ao agendar.")

    st.markdown("<hr style='margin:2px 0; opacity:0.05'>", unsafe_allow_html=True)