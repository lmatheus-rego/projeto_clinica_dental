import streamlit as st;
import controllers.PacienteController as PacienteController
from datetime import datetime
import models.Paciente as paciente
from pathlib import Path
import os

st.set_page_config(layout="centered")
st.title("Atualizar Documentos e Diagnóstico")
id = st.query_params["idpaciente"]
Ficha = PacienteController.Buscar_Paciente(id)
sexo = ["Masculino", "Feminino"]

st.write(f"______________________________")
st.write(f"**Paciente:** {Ficha[0].nome}")
st.write(f"**FAO:** {Ficha[0].fao}")
st.write(f"**Tipo de Fissura:** {Ficha[0].tipo_fissura}")
st.write("**História do Tratamento:**") 
st.write(f"{Ficha[0].historia_tratamento}")
st.write(f"______________________________")
st.write(f"Inserir Exames e Diagnósticos")
with st.form(key="diagnostico_paciente"):
    col1, col2 = st.columns(2)
    with col1:
        input_oclusais = st.text_area(label="**Características Oclusais:**", value= Ficha[0].carac_oclusais)
        input_odonto = st.text_area(label="**Necessidades Odontológicas:**", value= Ficha[0].neces_odonto)
        input_outros = st.text_area(label="**Outros:**", value= Ficha[0].outros)
        input_plano = st.text_area(label="**Plano de Tratamento:**", value= Ficha[0].plano_tratamento)
    with col2:
        input_orto = st.text_area(label="**Necessidades Ortodônticas:**", value= Ficha[0].neces_orto)
        input_cirur = st.text_area(label="**Necessidades Cirúrgicas:**", value= Ficha[0].neces_cirur)
        input_diagnostico = st.text_area(label="**Diagnostico:**", value= Ficha[0].diagnostico)
        input_docs = st.file_uploader(label="**Inserir Exames:**", type=["pdf"], accept_multiple_files=True)   
        
    input_button_submit = st.form_submit_button("Confirmar")




if input_button_submit:
    paciente.id = id
    paciente.carac_oclusais = input_oclusais
    paciente.neces_odonto = input_odonto
    paciente.neces_orto = input_orto
    paciente.neces_cirur = input_cirur
    paciente.diagnostico = input_diagnostico
    paciente.plano_tratamento = input_plano
    paciente.outros = input_outros
    if input_docs is not None:
        for exame in input_docs:
            with open(os.path.join(f"files/pacientes/{id}", exame.name), "wb") as f:
                    f.write(exame.getbuffer())
    PacienteController.Diagnostico_docs(paciente)
    st.success("Paciente atualizado com sucesso!")