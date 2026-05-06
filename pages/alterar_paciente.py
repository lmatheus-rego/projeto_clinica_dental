import streamlit as st
import gspread
from datetime import datetime, date
import models.Paciente as Paciente
import time
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# ==========================
# 🎨 CONFIGURAÇÃO E DESIGN FAO/UFAM
# ==========================
st.set_page_config(page_title="Alterar Paciente - FAO/UFAM", page_icon="📝", layout="wide")

# CSS de Alta Fidelidade
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"], .stMarkdown { font-family: 'Inter', sans-serif !important; }

        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            color: white !important;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .main-header h1 { margin: 0; font-weight: 700; font-size: 1.6rem; color: white !important; border: none; }

        .form-section-title {
            font-size: 1rem;
            font-weight: 700;
            color: #004a99;
            margin-bottom: 15px;
            margin-top: 10px;
            border-left: 4px solid #004a99;
            padding-left: 10px;
            text-transform: uppercase;
        }

        .stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s;
        }
        
        [data-testid="stForm"] {
            background-color: #f8fafc;
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- Funções de Sistema (Lógica Original) -----------------
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in list(current_pages.items()):
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

def calcular_idade(data_nascimento: date) -> int:
    hoje = date.today()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

# ----------------- Sidebar Institucional -----------------
with st.sidebar:
    st.markdown("### 🏛️ FAO/UFAM\n**Céu da Boca**")
    st.markdown("---")
    st.caption("Sistema de Gestão de Prontuários")

# ----------------- Navegação (Lógica Mantida) -----------------
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    if "id_alterar_persistente" in st.session_state: 
        del st.session_state.id_alterar_persistente
    delete_page("1_🏠_home", "alterar_paciente")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# ----------------- Gestão de Dados -----------------
# Captura de ID com persistência para evitar erros no rerun
query_id = st.query_params.get("idpaciente", "")
if isinstance(query_id, list): query_id = query_id[0]

if query_id:
    st.session_state.id_alterar_persistente = str(query_id).strip()

if "id_alterar_persistente" in st.session_state:
    id_paciente = st.session_state.id_alterar_persistente
else:
    st.error("⚠️ ID do paciente não localizado.")
    st.stop()

# Conexão gspread
try:
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
    worksheet = sh.worksheet("Pacientes")
    dados = worksheet.get_all_records()
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

# Busca do Paciente
paciente_encontrado = next((row for row in dados if str(row["ID"]) == str(id_paciente)), None)

if not paciente_encontrado:
    st.error("❌ Paciente não encontrado no banco de dados.")
    st.stop()

# ----------------- UI Principal -----------------
st.markdown(f"""
    <div class="main-header">
        <h1>📝 Alterar Cadastro do Paciente</h1>
    </div>
""", unsafe_allow_html=True)

sexo_opcoes = ["Masculino", "Feminino"]

# Formulário de Edição
with st.form(key="form_alterar_paciente"):
    st.markdown('<p class="form-section-title">👤 Dados Pessoais e Identificação</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("NOME COMPLETO", value=paciente_encontrado["NOME"])
        fao = st.text_input("FAO (Nº PRONTUÁRIO)", value=paciente_encontrado["FAO"])
        
        # Tratamento da data original
        try:
            data_origem = datetime.strptime(paciente_encontrado["DATA"], "%d/%m/%Y")
        except:
            data_origem = date.today()
            
        data_nasc = st.date_input(
            "DATA DE NASCIMENTO",
            value=data_origem,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY"
        )

    with col2:
        sexo = st.selectbox("SEXO", options=sexo_opcoes, index=sexo_opcoes.index(paciente_encontrado["SEXO"]) if paciente_encontrado["SEXO"] in sexo_opcoes else 0)
        filiacao = st.text_input("FILIAÇÃO (NOME DA MÃE/PAI)", value=paciente_encontrado["FILIACAO"])
        
    st.markdown('<p class="form-section-title">📍 Localização e Contato</p>', unsafe_allow_html=True)
    c_end, c_tel = st.columns([2, 1])
    endereco = c_end.text_input("ENDEREÇO COMPLETO", value=paciente_encontrado["ENDERECO"])
    telefone = c_tel.text_input("TELEFONE", value=paciente_encontrado["TELEFONE"], placeholder="(92) 00000-0000")

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("💾 SALVAR ALTERAÇÕES")

# ----------------- Lógica de Salvamento -----------------
if submitted:
    if not nome.strip():
        st.error("O nome do paciente é obrigatório.")
    else:
        with st.spinner("Atualizando dados..."):
            idade = calcular_idade(data_nasc)
            
            # Montagem da linha seguindo a ordem da planilha
            # ID, NOME, IDADE, DATA, SEXO, FILIACAO, ENDERECO, TELEFONE, FAO, STATUS, TIPO_FISSURA...
            nova_linha = [
                id_paciente,
                nome,
                idade,
                data_nasc.strftime("%d/%m/%Y"),
                sexo,
                filiacao,
                endereco,
                telefone,
                fao
            ]

            # Localiza o índice da linha
            index_linha = next((i + 2 for i, row in enumerate(dados) if str(row["ID"]) == str(id_paciente)), None)

            if index_linha:
                try:
                    # Atualiza apenas as colunas de A até I (onde estão os dados pessoais)
                    worksheet.update(f"A{index_linha}:I{index_linha}", [nova_linha])
                    st.toast("✅ Dados atualizados com sucesso!", icon="🎉")
                    time.sleep(1.2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")
            else:
                st.error("Erro ao localizar a linha do paciente.")