import streamlit as st
import gspread
from datetime import datetime
import models.Paciente as Paciente

st.set_page_config(page_title="Alterar Paciente", page_icon="📝")
st.title("📝 Alterar Cadastro do Paciente")

# Obter o ID do paciente via query params
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()
try:
    id_paciente = int(id_paciente_str)
except ValueError:
    st.error("ID do paciente inválido.")
    st.stop()

# Conectar à planilha via gspread
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
worksheet = sh.worksheet("Pacientes")
dados = worksheet.get_all_records()

# Buscar paciente na planilha
paciente_encontrado = None
for row in dados:
    if str(row["id"]) == str(id_paciente):
        paciente_encontrado = row
        break

if not paciente_encontrado:
    st.error("Paciente não encontrado.")
    st.stop()

sexo_opcoes = ["Masculino", "Feminino"]

# Formulário para edição
with st.form(key="form_alterar_paciente"):
    st.subheader("🧾 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome", value=paciente_encontrado["nome"])
        fao = st.text_input("FAO", value=paciente_encontrado["fao"])
        idade = st.number_input("Idade", min_value=0, max_value=130, step=1, value=int(paciente_encontrado["idade"]))
        data_nasc = st.date_input("Data de Nascimento", value=datetime.strptime(paciente_encontrado["data"], "%Y-%m-%d"))
        sexo = st.selectbox("Sexo", options=sexo_opcoes, index=sexo_opcoes.index(paciente_encontrado["sexo"]))

    with col2:
        filiacao = st.text_input("Filiação", value=paciente_encontrado["filiacao"])
        endereco = st.text_input("Endereço", value=paciente_encontrado["endereco"])
        telefone = st.text_input("Telefone", value=paciente_encontrado["telefone"], placeholder="(92) 00000-0000")
        tipo_fissura = st.text_input("Tipo de Fissura", value=paciente_encontrado["tipo_fissura"])
        historia_tratamento = st.text_area("História do Tratamento", value=paciente_encontrado["historia_tratamento"])

    st.markdown("---")
    submitted = st.form_submit_button("💾 Confirmar Alteração")

# Salvar alterações na planilha
if submitted:
    nova_linha = [
        id_paciente,
        nome,
        fao,
        idade,
        data_nasc.strftime("%Y-%m-%d"),
        sexo,
        filiacao,
        endereco,
        telefone,
        tipo_fissura,
        historia_tratamento
    ]

    # Encontrar índice da linha na planilha (considerando cabeçalho na linha 1)
    index_linha = None
    for i, row in enumerate(dados):
        if str(row["id"]) == str(id_paciente):
            index_linha = i + 2  # +2 pois gspread é 1-based e linha 1 é cabeçalho
            break

    if index_linha:
        worksheet.update(f"A{index_linha}:K{index_linha}", [nova_linha])
        st.success("✅ Dados do paciente atualizados com sucesso!")
        st.experimental_rerun()
    else:
        st.error("Erro ao localizar a linha do paciente na planilha.")
