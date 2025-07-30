import streamlit as st
import pandas as pd
from pathlib import Path
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

st.set_page_config(layout="wide")

# ============ Função para adicionar páginas dinamicamente ============
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

# ============ Carrega os dados da planilha ============
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs/export?format=csv"
    return pd.read_csv(url)

df = carregar_dados()
df.columns = df.columns.str.strip().str.title()  # Normaliza nomes de colunas

# ============ Título ============
st.title("📋 Lista de Pacientes")

# ============ Cabeçalho ============
colms = st.columns((0.5, 2, 1, 1, 1.2, 1, 1.5, 1))
campos = ['Nº', 'Nome', 'Idade', 'Fao', 'Ficha Clínica', 'Alterar', 'Exames/Diag.', 'Excluir']
for col, campo_nome in zip(colms, campos):
    col.markdown(f"**{campo_nome}**")

# ============ Listagem ============
for idx, row in df.iterrows():
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns((0.5, 2, 1, 1, 1.2, 1, 1.5, 1))
    col1.write(idx + 1)
    col2.write(row.get("Nome", "-"))
    col3.write(row.get("Idade", "-"))
    col4.write(row.get("Fao", "-"))

    # 🔄 BOTÃO "VER" (restaurado como antes)
    if col5.button("Ver", key=f"ver{idx}"):
        st.query_params["idpaciente"] = [str(idx)]
        add_page("1_🏠_home", "ficha_clinica")
        st.switch_page("pages/ficha_clinica.py")

    if col6.button("Alterar", key=f"alterar{idx}"):
        st.query_params["idpaciente"] = [str(idx)]
        add_page("1_🏠_home", "alterar_paciente")
        st.switch_page("pages/alterar_paciente.py")

    if col7.button("Exames e Diag.", key=f"exames{idx}"):
        st.query_params["idpaciente"] = [str(idx)]
        add_page("1_🏠_home", "inserir_exames_e_diagnosticos")
        st.switch_page("pages/inserir_exames_e_diagnosticos.py")

    if col8.button("Excluir", key=f"excluir{idx}"):
        st.warning("⚠️ A exclusão pela planilha ainda não está implementada diretamente.")
