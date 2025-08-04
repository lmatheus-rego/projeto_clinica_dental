import streamlit as st;
import controllers.PacienteController as PacienteController
from datetime import datetime
import models.Paciente as paciente

id_paciente = st.query_params.get("idpaciente", "")
if isinstance(id_paciente, list):
    id_paciente = id_paciente[0]
id_paciente = id_paciente.strip()

st.write("ID do paciente recebido:", id_paciente)
Ficha = PacienteController.Buscar_Paciente(id)
sexo = ["Masculino", "Feminino"]
st.write(f"Alterar dados do paciente")

with st.form(key="alterar_paciente"):
        col1, col2 = st.columns(2)
        with col1:
                input_name = st.text_input(label="**Nome:**", value= Ficha[0].nome)
                input_fao = st.text_input(label="**FAO:**", value= Ficha[0].fao)
                input_idade = st.number_input(label="Idade", format="%d",step=1, value=Ficha[0].idade)
                input_data = st.date_input("Data de Nascimento", value=datetime.strptime(Ficha[0].data, "%Y-%m-%d"), format="DD/MM/YYYY")
                input_sexo = st.selectbox("Sexo", options=sexo, index=sexo.index(Ficha[0].sexo))
                
        with col2:
                input_filiacao = st.text_input(label="**Filiação:**", value= Ficha[0].filiacao)
                input_endereco = st.text_input(label="**Endereço:**", value= Ficha[0].endereco)
                input_telefone = st.text_input(label="**Telefone:**", value= Ficha[0].telefone, placeholder="(92)XXXXX-XXXX")
                input_tipo_fissura = st.text_input(label="**Tipo de Fissura:**", value= Ficha[0].tipo_fissura)
                input_historia_tratamento = st.text_area(label="**Historia do Tratamento:**", value= Ficha[0].historia_tratamento)
        
        input_button_submit = st.form_submit_button("Confirmar Alteração")


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
    st.experimental_rerun()
