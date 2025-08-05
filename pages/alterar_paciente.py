import streamlit as st
import controllers.PacienteController as PacienteController
from datetime import datetime
import models.Paciente as Paciente

st.set_page_config(page_title="Alterar Paciente", page_icon="📝")
st.title("📝 Alterar Cadastro do Paciente")

# Obtém ID do paciente da URL
id_paciente = st.query_params.get("idpaciente", "")
if isinstance(id_paciente, list):
    id_paciente = id_paciente[0]
id_paciente = id_paciente.strip()

# Carrega dados do paciente
paciente = PacienteController.Buscar_Paciente(id_paciente)
if not paciente:
    st.error("Paciente não encontrado.")
    st.stop()

p = paciente[0]  # objeto retornado da lista
sexo_opcoes = ["Masculino", "Feminino"]

with st.form(key="form_alterar_paciente"):
    st.subheader("🧾 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome", value=p.nome)
        fao = st.text_input("FAO", value=p.fao)
        idade = st.number_input("Idade", min_value=0, max_value=130, step=1, value=int(p.idade))
        data_nasc = st.date_input("Data de Nascimento", value=datetime.strptime(p.data, "%Y-%m-%d"))
        sexo = st.selectbox("Sexo", options=sexo_opcoes, index=sexo_opcoes.index(p.sexo))

    with col2:
        filiacao = st.text_input("Filiação", value=p.filiacao)
        endereco = st.text_input("Endereço", value=p.endereco)
        telefone = st.text_input("Telefone", value=p.telefone, placeholder="(92) 00000-0000")
        tipo_fissura = st.text_input("Tipo de Fissura", value=p.tipo_fissura)
        historia_tratamento = st.text_area("História do Tratamento", value=p.historia_tratamento)

    st.markdown("---")
    submitted = st.form_submit_button("💾 Confirmar Alteração")

if submitted:
    paciente_atualizado = Paciente.Paciente(
        id=id_paciente,
        nome=nome,
        fao=fao,
        idade=int(idade),
        data=data_nasc.strftime("%Y-%m-%d"),
        sexo=sexo,
        filiacao=filiacao,
        endereco=endereco,
        telefone=telefone,
        tipo_fissura=tipo_fissura,
        historia_tratamento=historia_tratamento
    )

    PacienteController.Alterar(paciente_atualizado)
    st.success("✅ Dados do paciente atualizados com sucesso!")
    st.experimental_rerun()
