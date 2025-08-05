import streamlit as st
import gspread
from datetime import datetime
import models.Paciente as Paciente
from datetime import date
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# Função para deletar páginas do menu lateral
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

st.set_page_config(page_title="Alterar Paciente", page_icon="📝")
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()  # Remove parâmetros da URL

    # Deleta a página atual (Ficha Clínica) do menu lateral
    delete_page("1_🏠_home", "alterar_paciente")

    # Redireciona para a lista de pacientes
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")
st.title("📝 Alterar Cadastro do Paciente")

def calcular_idade(data_nascimento: date) -> int:
    hoje = date.today()
    idade = hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )
    return idade

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
    if str(row["ID"]) == str(id_paciente):
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
        nome = st.text_input("NOME", value=paciente_encontrado["NOME"])
        fao = st.text_input("FAO", value=paciente_encontrado["FAO"])
        data_nasc = st.date_input("DATA", value=datetime.strptime(paciente_encontrado["DATA"], "%d/%m/%Y"))
        sexo = st.selectbox("SEXO", options=sexo_opcoes, index=sexo_opcoes.index(paciente_encontrado["SEXO"]))

    with col2:
        filiacao = st.text_input("Filiação", value=paciente_encontrado["FILIACAO"])
        endereco = st.text_input("Endereço", value=paciente_encontrado["ENDERECO"])
        telefone = st.text_input("Telefone", value=paciente_encontrado["TELEFONE"], placeholder="(92) 00000-0000")
        tipo_fissura = st.text_input("Tipo de Fissura", value=paciente_encontrado["TIPO_FISSURA"])
        historia_tratamento = st.text_area("História do Tratamento", value=paciente_encontrado["HISTORIA_TRATAMENTO"])

    st.markdown("---")
    submitted = st.form_submit_button("💾 Confirmar Alteração")

# Salvar alterações na planilha
if submitted:
    idade = calcular_idade(data_nasc)
    nova_linha = [
        id_paciente,
        nome,
        idade,
        data_nasc.strftime("%d/%m/%Y"),
        sexo,
        filiacao,
        endereco,
        telefone,
        fao,
        tipo_fissura,
        historia_tratamento
    ]

    # Encontrar índice da linha na planilha (considerando cabeçalho na linha 1)
    index_linha = None
    for i, row in enumerate(dados):
        if str(row["ID"]) == str(id_paciente):
            index_linha = i + 2  # +2 pois gspread é 1-based e linha 1 é cabeçalho
            break

    if index_linha:
        worksheet.update(f"A{index_linha}:K{index_linha}", [nova_linha])
        st.success("✅ Dados do paciente atualizados com sucesso!")
        st.rerun()
    else:
        st.error("Erro ao localizar a linha do paciente na planilha.")
