import streamlit as st
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed
from datetime import date

st.set_page_config(layout="wide", page_title="Lista de Pacientes")

# ==========================
# Função para adicionar páginas dinamicamente
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

# ==========================
# Função para carregar dados da planilha
# ==========================
def conectar_planilha():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    service_account_info = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }

    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc

def carregar_dados():
    gc = conectar_planilha()
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"

    # Pacientes
    sheet_pacientes = gc.open_by_key(SPREADSHEET_ID).worksheet("Pacientes")
    dados_pacientes = sheet_pacientes.get_all_records()
    df_pacientes = pd.DataFrame(dados_pacientes)

    # Fila
    sheet_fila = gc.open_by_key(SPREADSHEET_ID).worksheet("Fila")
    dados_fila = sheet_fila.get_all_records()
    df_fila = pd.DataFrame(dados_fila)

    return df_pacientes, df_fila, gc

# ==========================
# CSS para cards
# ==========================
st.markdown("""
<style>
.card {
    border-radius: 6px;
    border-width: thin;
    border-style: outset;
    padding: 0.8rem 1rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}
.card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
button.stButton>button {
    font-size: 13px;
    padding: 0.25rem 0.5rem;
}
.badge {
    font-size: 11px;
    font-weight: 600;
    text-align: center;
    border-radius: 6px;
    padding: 2px 6px;
    display: inline-block;
    min-width: 70px;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# Carregar dados
# ==========================
df_pacientes, df_fila, gc = carregar_dados()
df_pacientes.columns = df_pacientes.columns.str.strip().str.title()
df_fila.columns = df_fila.columns.str.strip().str.upper()

# ==========================
# Sidebar - Fila de Atendimento
# ==========================
st.sidebar.markdown("### 📅 Fila de Atendimento - Hoje")
hoje = date.today()
df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
fila_hoje = df_fila[df_fila["DATA"] == hoje]

if not fila_hoje.empty:
    st.sidebar.markdown(
        "<div style='display:flex; font-weight:bold; padding:4px 6px; font-size:13px'>"
        "<div style='flex:2'>NOME</div>"
        "<div style='flex:1; text-align:center'>STATUS</div>"
        "<div style='flex:1; text-align:center'>FICHA</div>"
        "<div style='flex:1; text-align:center'>EVOLUÇÃO</div>"
        "</div>",
        unsafe_allow_html=True
    )

    for _, row in fila_hoje.iterrows():
        paciente_id = str(row["PACIENTE_ID"]).strip()
        paciente = df_pacientes[df_pacientes["Id"].astype(str).str.strip() == paciente_id]
        if paciente.empty:
            continue
        nome_paciente = paciente.iloc[0]["Nome"]
        status = row["STATUS"].upper()

        if status == "AGENDADO":
            cor_status = "#FFD700"
        elif status == "ATENDIDO":
            cor_status = "#4CAF50"
        elif status == "CANCELADO":
            cor_status = "#F44336"
        else:
            cor_status = "#6c757d"

        c1, c2, c3, c4 = st.sidebar.columns([2, 1, 1, 1])
        c1.markdown(f"<div style='font-size:13px'>{nome_paciente}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='badge' style='background-color:{cor_status}; color:white'>{status}</div>", unsafe_allow_html=True)

        with c3:
            if st.button("📄", key=f"ficha_{paciente_id}", help="Ficha Clínica"):
                st.query_params = {"idpaciente": paciente_id}
                add_page("1_🏠_home", "ficha_clinica")
                st.switch_page("pages/ficha_clinica.py")
        with c4:
            if st.button("🦷", key=f"evolucao_{paciente_id}", help="Evolução Tratamento"):
                st.query_params = {"idpaciente": paciente_id}
                add_page("1_🏠_home", "evolucao_tratamento")
                st.switch_page("pages/evolucao_tratamento.py")
else:
    st.sidebar.info("⚠️ Nenhum paciente na fila hoje.")

# ==========================
# Funções auxiliares
# ==========================
def badge_status_fila(paciente_id):
    hoje = date.today()
    registros = df_fila[
        (df_fila["PACIENTE_ID"].astype(str).str.strip() == str(paciente_id)) &
        (df_fila["DATA"] == hoje)
    ]
    if registros.empty:
        return "<div class='badge' style='background-color:#6c757d; color:white'>SEM AGEND.</div>"

    status = registros.iloc[-1]["STATUS"].upper()
    if status == "AGENDADO":
        cor = "#FFD700"; txt = "black"
    elif status == "ATENDIDO":
        cor = "#28a745"; txt = "white"
    elif status == "CANCELADO":
        cor = "#dc3545"; txt = "white"
    else:
        cor = "#6c757d"; txt = "white"

    return f"<div class='badge' style='background-color:{cor}; color:{txt}'>{status}</div>"

def formatar_genero(genero, nome):
    if genero.lower() == "masculino":
        return f"<span style='color:blue;'>♂️ {nome}</span>"
    elif genero.lower() == "feminino":
        return f"<span style='color:deeppink;'>♀️ {nome}</span>"
    return nome

# ==========================
# Lista de Pacientes
# ==========================
st.markdown("## 📋 Lista de Pacientes")
busca = st.text_input("🔎 Buscar por nome, idade, FAO, etc:", placeholder="Digite aqui...")
if busca:
    busca_lower = busca.lower()
    df_pacientes = df_pacientes[df_pacientes.apply(lambda row: row.astype(str).str.lower().str.contains(busca_lower).any(), axis=1)]

st.markdown("---")

colunas = st.columns(4)

for idx, row in df_pacientes.iterrows():
    col = colunas[idx % 4]
    with col:
        with st.container():
            genero_formatado = formatar_genero(row.get("Sexo", "-"), row.get("Nome", "-"))
            badge_fila = badge_status_fila(row.get("Id", ""))

            st.markdown(f"""
            <div class="card">
                <b>{genero_formatado}</b><br>
                🎂 <b>Idade:</b> {row.get("Idade", "-")} anos<br>
                🧭 <b>FAO:</b> {row.get("Fao", "-")}<br>
                💉 <b>Tipo de Fissura:</b> {row.get("Tipo_Fissura", "-")}<br>
                📌 <b>Fila Hoje:</b> {badge_fila}
            </div>
            """, unsafe_allow_html=True)

            with st.form(key=f"form_{idx}"):
                bcol1, bcol2 = st.columns(2)
                bcol3, bcol4 = st.columns(2)

                with bcol1:
                    ver = st.form_submit_button("📄 Ficha Clínica", use_container_width=True)
                with bcol2:
                    editar = st.form_submit_button("✏️ Editar Dados", use_container_width=True)
                with bcol3:
                    exames = st.form_submit_button("🧾 Docs & Exames", use_container_width=True)
                with bcol4:
                    evoluir = st.form_submit_button("🦷 Evolução", use_container_width=True)

                agendar = st.form_submit_button("📅 Agendar Hoje", use_container_width=True)

                id_str = str(row.get("Id", "")).strip()

                if ver:
                    st.query_params = {"idpaciente": id_str}
                    add_page("1_🏠_home", "ficha_clinica")
                    st.switch_page("pages/ficha_clinica.py")
                elif editar:
                    st.query_params = {"idpaciente": id_str}
                    add_page("1_🏠_home", "alterar_paciente")
                    st.switch_page("pages/alterar_paciente.py")
                elif exames:
                    st.query_params = {"idpaciente": id_str}
                    add_page("1_🏠_home", "inserir_exames_e_diagnosticos")
                    st.switch_page("pages/inserir_exames_e_diagnosticos.py")
                elif evoluir:
                    st.query_params = {"idpaciente": id_str}
                    add_page("1_🏠_home", "evolucao_tratamento")
                    st.switch_page("pages/evolucao_tratamento.py")
                elif agendar:
                    sheet_fila = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs").worksheet("Fila")
                    registros_fila = sheet_fila.get_all_records()
                    df_fila_existente = pd.DataFrame(registros_fila)

                    df_fila_existente["DATA"] = pd.to_datetime(df_fila_existente["DATA"], dayfirst=True, errors="coerce").dt.date
                    ja_agendado = not df_fila_existente[
                        (df_fila_existente["PACIENTE_ID"].astype(str) == id_str) &
                        (df_fila_existente["DATA"] == date.today())
                    ].empty

                    if ja_agendado:
                        st.warning(f"⚠️ Paciente **{row.get('Nome')}** já está agendado para hoje.")
                    else:
                        nova_linha = [id_str, date.today().strftime("%d/%m/%Y"), "AGENDADO"]
                        sheet_fila.append_row(nova_linha)
                        st.success(f"✅ Paciente **{row.get('Nome')}** agendado para hoje.")
                        st.experimental_rerun()

st.markdown("---")
st.caption(f"👥 Total de pacientes: **{len(df_pacientes)}**")
