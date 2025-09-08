import streamlit as st
from datetime import datetime, date
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# --- Funções utilitárias ---
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

# --- Carregamento dos dados ---
def carregar_dados():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = {
        k: v.replace('\\n', '\n') if k == "private_key" else v
        for k, v in st.secrets["gcp_service_account"].items()
    }

    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sh = gc.open_by_key(SPREADSHEET_ID)
    sheet = sh.sheet1
    df = pd.DataFrame(sheet.get_all_records())
    return df, sh, gc, SPREADSHEET_ID

# --- Botão voltar ---
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "alterar_paciente")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# --- Carregar planilha ---
df, sh, gc, SPREADSHEET_ID = carregar_dados()
df.columns = df.columns.str.strip().str.upper()

# --- Captura do ID via URL ---
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list):
    id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

try:
    id_paciente = int(id_paciente_str)
except:
    st.error("ID do paciente inválido.")
    st.stop()

paciente_df = df[df["ID"].astype(str) == id_paciente_str]
if paciente_df.empty:
    st.error("Paciente não encontrado.")
    st.stop()

paciente_info = paciente_df.iloc[0]

# --- Evolução do Tratamento ---
st.markdown("<h3 style='text-align:center;'>📈 Evolução do Tratamento</h3><hr>", unsafe_allow_html=True)

descricao_evolucao = st.text_area("📝 **Descrição da Evolução**", height=100)
data_evolucao = st.date_input("📅 **Data da Evolução**", format="DD/MM/YYYY")

if st.button("💾 Salvar Evolução"):
    if descricao_evolucao.strip() == "":
        st.warning("⚠️ A descrição da evolução não pode estar vazia.")
    else:
        try:
            # --- Criar ou abrir aba Registros ---
            try:
                aba_registros = sh.worksheet("Registros")
            except gspread.exceptions.WorksheetNotFound:
                aba_registros = sh.add_worksheet(title="Registros", rows="1000", cols="10")
                aba_registros.append_row(["PACIENTE_ID", "DATA_REGISTRO", "EVOLUCAO", "USUARIO"])

            # --- Inserir evolução ---
            nova_linha = [
                id_paciente_str,
                data_evolucao.strftime("%d/%m/%Y"),
                descricao_evolucao.strip(),
                "usuario_a_definir"
            ]
            aba_registros.append_row(nova_linha)

            # --- Atualizar status na aba Fila, se existir ---
            try:
                aba_fila = sh.worksheet("Fila")
                registros_fila = aba_fila.get_all_records()
                if registros_fila:
                    for idx, row in enumerate(registros_fila, start=2):  # start=2 -> linha na planilha
                        paciente_id_fila = str(row["PACIENTE_ID"]).strip()
                        data_fila = datetime.strptime(row["DATA"], "%d/%m/%Y").date() if row["DATA"] else None
                        if paciente_id_fila == id_paciente_str and data_fila == data_evolucao:
                            col_status = list(aba_fila.row_values(1)).index("STATUS") + 1
                            aba_fila.update_cell(idx, col_status, "ATENDIDO")
                            break
            except gspread.exceptions.WorksheetNotFound:
                st.warning("⚠️ Aba 'Fila' não encontrada, status não atualizado.")

            st.success("✅ Evolução registrada com sucesso!")
            
            # --- Redirecionar para página Home ---
            st.query_params.clear()
            delete_page("1_🏠_home", "evolucao_tratamento")
            st.switch_page("pages/1_🏠_home.py")

        except Exception as e:
            st.error(f"Erro ao salvar evolução: {e}")

# --- Histórico das Evoluções ---
try:
    aba_registros = sh.worksheet("Registros")
    registros = aba_registros.get_all_records()
    df_registros = pd.DataFrame(registros)

    if "PACIENTE_ID" in df_registros.columns:
        df_paciente = df_registros[df_registros["PACIENTE_ID"].astype(str) == id_paciente_str]

        df_paciente["DATA_REGISTRO"] = pd.to_datetime(df_paciente["DATA_REGISTRO"], format="%d/%m/%Y", errors="coerce")
        df_paciente = df_paciente.dropna(subset=["DATA_REGISTRO"])
        df_paciente = df_paciente.sort_values(by="DATA_REGISTRO", ascending=False).reset_index(drop=True)

        if not df_paciente.empty:
            st.markdown("<h4>📜 Histórico de Evoluções</h4><hr>", unsafe_allow_html=True)
            for i, row in df_paciente.iterrows():
                num = len(df_paciente) - i
                data = row["DATA_REGISTRO"].strftime("%d/%m/%Y")
                descricao = row.get("EVOLUCAO", "").strip()
                usuario = row.get("USUARIO", "").strip()
                st.markdown(f"""
                    <div style='padding: 6px 12px; background-color:#f8f9fa; margin-bottom:6px; border-left: 4px solid #0d6efd; border-radius: 4px;'>
                        <p style='font-size: 0.85rem; margin: 0;'>
                            <b>📄</b> - No dia <b>{data}</b> foi registrada a seguinte evolução:<br>
                            <i>"{descricao}"</i><br>
                            <span style='color:gray;'>Registrado por: <b>{usuario}</b></span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma evolução registrada para este paciente.")
    else:
        st.warning("A aba 'Registros' não contém a coluna 'PACIENTE_ID'.")
except Exception as e:
    st.error(f"Erro ao carregar evoluções: {e}")

# --- Dados Pessoais ---
st.markdown("<h3 style='text-align:center;'>📋 Dados do Paciente</h3><hr>", unsafe_allow_html=True)

status = paciente_info.get('STATUS', '').strip().lower()
status_emoji = {"ativo": "✅", "inativo": "⛔", "ausente": "🕓"}.get(status, "❔")
status_color = {"ativo": "#28a745", "inativo": "#6c757d", "ausente": "#ffc107"}.get(status, "#000")

espaco, col1, col2, col3, col4, espaco2 = st.columns([1, 2, 2, 2, 2, 1])
with col1:
    st.markdown(f"<h5 style='text-align:center;'>👤<br>{paciente_info['NOME']}</h5>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h5 style='text-align:center;'>🧭<br>FAO: {paciente_info['FAO']}</h5>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h5 style='text-align:center;'>🎂<br>{paciente_info['IDADE']} anos</h5>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<h5 style='text-align:center; color:{status_color};'>{status_emoji}<br>Status: {paciente_info['STATUS']}</h5>", unsafe_allow_html=True)
