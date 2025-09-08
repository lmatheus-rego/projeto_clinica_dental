import streamlit as st
import pandas as pd
import datetime
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from urllib.parse import urlencode

st.set_page_config(layout="wide", page_title="Lista de Pacientes")

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
# Carregar dados da planilha
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
# Estilo dos cards
# ==========================
st.markdown("""
<style>
.card {
    border-radius: 6px;
    border-width: thin;
    border-style: outset;
    padding: 1rem 1.2rem;
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}
.card:hover {
    box-shadow: 0 4px 18px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ==========================
# Carregar pacientes e fila
# ==========================
df = carregar_aba("Pacientes")
df_fila = carregar_aba("Fila")

df.columns = df.columns.str.strip().str.upper()
df_fila.columns = df_fila.columns.str.strip().str.upper()

# ==========================
# Filtros de busca
# ==========================
st.markdown("## 📋 Lista de Pacientes")
busca = st.text_input("🔎 Buscar por nome, idade, FAO, etc:", placeholder="Digite aqui...")
if busca:
    busca_lower = busca.lower()
    df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(busca_lower).any(), axis=1)]

st.markdown("---")

colunas = st.columns(4)

# ==========================
# Funções auxiliares
# ==========================
def badge_status(status: str) -> str:
    status = str(status).strip().upper()
    if status == "AGENDADO":
        cor_fundo, cor_texto = "#FFD700", "black"
    elif status == "ATENDIDO":
        cor_fundo, cor_texto = "#28a745", "white"
    elif status == "CANCELADO":
        cor_fundo, cor_texto = "#dc3545", "white"
    elif status == "ATIVO":
        cor_fundo, cor_texto = "#28a745", "white"
    elif status == "AUSENTE":
        cor_fundo, cor_texto = "#FFA500", "black"
    elif status == "INATIVO":
        cor_fundo, cor_texto = "#dc3545", "white"
    else:
        cor_fundo, cor_texto = "#6c757d", "white"

    return f"""
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
    """

def formatar_genero(genero, nome):
    if str(genero).strip().lower() == "masculino":
        return f"<span style='color:blue;'>♂️ {nome}</span>"
    elif str(genero).strip().lower() == "feminino":
        return f"<span style='color:deeppink;'>♀️ {nome}</span>"
    return nome

# ==========================
# Renderização dos cards
# ==========================
for idx, row in df.iterrows():
    col = colunas[idx % 4]

    with col:
        with st.container():
            genero_formatado = formatar_genero(row.get("SEXO", "-"), row.get("NOME", "-"))
            status_badge = badge_status(row.get("STATUS", "-"))

            st.markdown(f"""
            <div class="card">
                {genero_formatado}<br>
                🎂 <b>Idade:</b> {row.get("IDADE", "-")} anos<br>
                🧭 <b>FAO:</b> {row.get("FAO", "-")}<br>
                💉 <b>Tipo de Fissura:</b> {row.get("TIPO DE FISSURA", "-")}<br>
                📌 <b>Status:</b> {status_badge}
            </div>
            """, unsafe_allow_html=True)

            with st.form(key=f"form_{idx}"):
                bcol1, bcol2 = st.columns(2)
                bcol3, bcol4 = st.columns(2)
                bcol5 = st.columns(1)[0]

                with bcol1:
                    ver = st.form_submit_button("📄 Ficha Clínica", use_container_width=True)
                with bcol2:
                    editar = st.form_submit_button("✏️ Editar Dados Pessoais", use_container_width=True)
                with bcol3:
                    exames = st.form_submit_button("🧾 Inserir Docs e Exames", use_container_width=True)
                with bcol4:
                    evolucao = st.form_submit_button("🦷 Evoluir Tratamento", use_container_width=True)
                with bcol5:
                    agendar = st.form_submit_button("📅 Agendar Hoje", use_container_width=True)

                # Ações
                if ver:
                    st.query_params = {"idpaciente": str(row.get("ID", "")).strip()}
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")

                elif editar:
                    st.query_params = {"idpaciente": str(row.get("ID", "")).strip()}
                    add_page("1_🏠_home", "alterar_paciente")
                    st.switch_page("pages/alterar_paciente.py")

                elif exames:
                    st.query_params = {"idpaciente": str(row.get("ID", "")).strip()}
                    add_page("1_🏠_home", "inserir_exames_e_diagnosticos")
                    st.switch_page("pages/inserir_exames_e_diagnosticos.py")

                elif evolucao:
                    st.query_params = {"idpaciente": str(row.get("ID", "")).strip()}
                    add_page("1_🏠_home", "evolucao_tratamento")
                    st.switch_page("pages/evolucao_tratamento.py")

                elif agendar:
                    paciente_id = str(row.get("ID", "")).strip()
                    hoje = datetime.date.today()

                    # Verificar se já existe
                    ja_existe = (
                        (df_fila["PACIENTE_ID"].astype(str).str.strip() == paciente_id) &
                        (df_fila["DATA"] == str(hoje))
                    ).any()

                    if ja_existe:
                        st.warning(f"⚠️ O paciente {row.get('NOME', '-')} já está agendado para hoje.")
                    else:
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
                        sheet = gc.open_by_key(SPREADSHEET_ID).worksheet("Fila")

                        sheet.append_row([paciente_id, str(hoje), "AGENDADO"])
                        st.success(f"✅ Paciente {row.get('NOME', '-')} agendado para hoje!")
                        st.rerun()

st.markdown("---")
st.caption(f"👥 Total de pacientes: **{len(df)}**")
