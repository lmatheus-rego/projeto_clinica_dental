import streamlit as st
from datetime import datetime, date
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import get_pages, _on_pages_changed

# --- Funções ---
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

def carregar_planilhas():
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    service_account_info = {k: v.replace('\\n','\n') if k=='private_key' else v for k,v in st.secrets['gcp_service_account'].items()}
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sh = gc.open_by_key(SPREADSHEET_ID)

    # Registros
    try:
        aba_registros = sh.worksheet("Registros")
    except gspread.exceptions.WorksheetNotFound:
        aba_registros = sh.add_worksheet("Registros", rows="1000", cols="10")
        aba_registros.append_row(["PACIENTE_ID","DATA_REGISTRO","EVOLUCAO","USUARIO"])
    
    # Fila
    try:
        aba_fila = sh.worksheet("Fila")
    except gspread.exceptions.WorksheetNotFound:
        aba_fila = sh.add_worksheet("Fila", rows="1000", cols="10")
        aba_fila.append_row(["PACIENTE_ID","DATA","STATUS"])
    
    return sh, aba_registros, aba_fila

# --- Botão voltar ---
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "alterar_paciente")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# --- Carregar planilhas ---
sh, aba_registros, aba_fila = carregar_planilhas()

# --- Captura do ID via URL ---
id_paciente_str = st.query_params.get("idpaciente", [""])[0].strip()
if not id_paciente_str:
    st.error("ID do paciente não encontrado.")
    st.stop()

# --- Verificar paciente ---
df = pd.DataFrame(sh.sheet1.get_all_records())
df.columns = df.columns.str.strip().str.upper()
paciente_df = df[df["ID"].astype(str)==id_paciente_str]
if paciente_df.empty:
    st.error("Paciente não encontrado.")
    st.stop()
paciente_info = paciente_df.iloc[0]

# --- Evolução ---
st.markdown("<h3 style='text-align:center;'>📈 Evolução do Tratamento</h3><hr>", unsafe_allow_html=True)
descricao_evolucao = st.text_area("📝 **Descrição da Evolução**", height=100)
data_evolucao = st.date_input("📅 **Data da Evolução**", format="DD/MM/YYYY")

if st.button("💾 Salvar Evolução"):
    if not descricao_evolucao.strip():
        st.warning("⚠️ A descrição da evolução não pode estar vazia.")
    else:
        try:
            # --- Inserir evolução ---
            aba_registros.append_row([
                id_paciente_str,
                data_evolucao.strftime("%d/%m/%Y"),
                descricao_evolucao.strip(),
                "usuario_a_definir"
            ])
            st.success("✅ Evolução registrada com sucesso!")

            # --- Atualizar status na Fila diretamente na planilha ---
            registros_fila = aba_fila.get_all_records()
            if registros_fila:
                colunas = [c.strip().upper() for c in aba_fila.row_values(1)]
                col_paciente = colunas.index("PACIENTE_ID") + 1
                col_data = colunas.index("DATA") + 1
                col_status = colunas.index("STATUS") + 1

                for idx, row in enumerate(registros_fila, start=2):  # start=2 porque a primeira linha é o cabeçalho
                    fila_id = str(row["PACIENTE_ID"]).strip()
                    fila_data_raw = str(row["DATA"]).strip()
                    try:
                        fila_data = datetime.strptime(fila_data_raw, "%d/%m/%Y").date()
                    except:
                        continue

                    if fila_id == id_paciente_str and fila_data == data_evolucao:
                        aba_fila.update_cell(idx, col_status, "ATENDIDO")
                        st.success(f"✅ Status da fila atualizado para ATENDIDO")
                        break

            # --- Redirecionar para Home ---
            st.query_params.clear()
            delete_page("1_🏠_home","evolucao_tratamento")
            st.switch_page("pages/1_🏠_home.py")

        except Exception as e:
            st.error(f"Erro ao salvar evolução: {e}")
