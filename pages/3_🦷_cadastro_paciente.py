import streamlit as st
import datetime
import controllers.PacienteController as PacienteController
import models.Paciente as paciente

st.set_page_config(
    page_title="Cadastro de Pacientes",
)

st.title("Cadastro de Paciente")

col1, col2 = st.columns(2)

with st.form(key="include_paciente"):
    with col1:
        input_name = st.text_input(label="Nome")
        input_fao = st.text_input(label="FAO", placeholder="xxxxx/xx")
        input_idade = st.number_input(label="Idade", format="%d",step=1)
        input_data = st.date_input("Data de Nascimento", format="DD/MM/YYYY")
        input_sexo = st.selectbox("Sexo", ["Masculino", "Feminino"], placeholder = "Selecione")

    with col2:
        
     
        input_filiacao = st.text_input(label="Filiação")
        input_endereco = st.text_input(label="Endereço")
        input_telefone = st.text_input(label="Telefone", placeholder="(92)XXXXX-XXXX")
        input_tipo_fissura = st.text_input(label="Tipo de Fissura")
        input_historia_tratamento = st.text_area(label="Historia do Tratamento")

    input_button_submit = st.form_submit_button("Enviar")


if input_button_submit:
    paciente.id = 0
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
    PacienteController.incluir(paciente)
    st.success("Paciente cadastrado com sucesso!")
