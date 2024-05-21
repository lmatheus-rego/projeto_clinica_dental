import streamlit as st;
import controllers.PacienteController as PacienteController
from datetime import datetime
import models.Paciente as paciente

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
        input_orto = st.text_area(label="**Necessidades Cirúrgicas:**", value= Ficha[0].neces_cirur)
        input_diagnostico = st.text_area(label="**Diagnostico:**", value= Ficha[0].diagnostico)
        input_docs = st.file_uploader(label="**Inserir Exames:**")   
        
    input_button_submit = st.form_submit_button("Confirmar")




if input_button_submit:
    paciente.id = id
    paciente.nome = input_name
    paciente.fao = input_fao
    paciente.idade = input_idade
    paciente.data = input_data
    paciente.sexo = input_sexo
    paciente.filiacao = input_filiacao
    paciente.endereco = input_endereco
    paciente.telefone = input_telefone
    paciente.tipo_fissura = input_tipo_fissura
    paciente.historia_tratamento = input_historia_tratamento
    PacienteController.Alterar(paciente)
    st.success("Paciente atualizado com sucesso!")