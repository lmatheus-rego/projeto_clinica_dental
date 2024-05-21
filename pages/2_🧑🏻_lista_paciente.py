import streamlit as st;
import controllers.PacienteController as PacienteController
from pathlib import Path
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5, 
    get_pages,
    _on_pages_changed
)
st.set_page_config(layout="wide")
def add_page(main_script_path_str, page_name):
    pages = get_pages(main_script_path_str)
    main_script_path = Path(main_script_path_str)
    pages_dir = main_script_path.parent / "pages"
    # st.write(list(pages_dir.glob("*.py"))+list(main_script_path.parent.glob("*.py")))
    script_path = [f for f in list(pages_dir.glob("*.py"))+list(main_script_path.parent.glob("*.py")) if f.name.find(page_name) != -1][0]
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

@st.experimental_dialog("Ficha Clínica", width ="large")

def ficha():
        col1, col2 = st.columns(2)
        with col1:
                st.write(f"**Nome:** {item.nome}")
                st.write(f"**Idade:** {item.idade}")
                st.write(f"**FAO:** {item.fao}")
                st.write(f"**Endereço:** {item.endereco}")

        with col2:
                st.write(f"**Data de Nascimento:** {item.data}")
                st.write(f"**Sexo:** {item.sexo}")
                st.write(f"**Filiação:** {item.filiacao}")
                st.write(f"**Telefone:** {item.telefone}")
                
        st.write(f"______________________________")

        col1, col2 = st.columns(2)
        with col1:
                st.write("**História do Tratamento:**") 
                st.write(f"{item.historia_tratamento}")
                

        with col2:
                st.write(f"**Tipo de Fissura:** {item.tipo_fissura}")
        st.write(f"**Registro Clínico:**")
        st.write(f"{item.nome}")
  
        if st.button("Fechar"):
                st.rerun()
        if st.button("Imprimir"):
                st.write("IMPRESSAO")

colms = st.columns((1, 2, 1, 1, 1, 1, 1, 1))
campos = ['Nº', 'Nome', 'Idade', 'FAO', 'Ficha Clínica', 'Alterar', 'Exames/Diagnosticos', 'Excluir']
for col, campo_nome in zip(colms, campos):
        col.write(campo_nome) 
for item in PacienteController.SelecionarTodos():
        col1, col2, col3, col4, col5, col6, col8, col9 = st.columns((1,2,1,1,1,1,1,1))
        col1.write(item.id)
        col2.write(item.nome)
        col3.write(item.idade)
        col4.write(item.fao)
        button_space_ficha = col5.empty()
        on_click_ver = button_space_ficha.button('Ver', 'btnFicha' + str(item.id))
        if on_click_ver:
                st.query_params["idpaciente"] = [item.id]
                add_page("1_🏠_home", "ficha_clinica")
                st.switch_page("pages/ficha_clinica.py")
        button_space_alterar = col6.empty()
        on_click_alterar = button_space_alterar.button('Alterar', 'btnAlterarDoc' + str(item.id))
        if on_click_alterar:
                st.query_params["idpaciente"] = [item.id]
                add_page("1_🏠_home", "alterar_paciente")
                st.switch_page("pages/alterar_paciente.py")
        button_space_docs = col8.empty()
        on_click_docs = button_space_docs.button('Exames e Diag.', 'btndocs' + str(item.id))
        if on_click_docs:
                st.query_params["idpaciente"] = [item.id]
                add_page("1_🏠_home", "inserir_exames_e_diagnosticos")
                st.switch_page("pages/inserir_exames_e_diagnosticos.py")
        button_space_excluir = col9.empty()
        on_click_excluir = button_space_excluir.button('Excluir', 'btnExcluir' + str(item.id))