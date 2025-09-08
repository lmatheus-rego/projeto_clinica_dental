import streamlit as st
from datetime import datetime, date
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import page_icon_and_name, calc_md5, get_pages, _on_pages_changed

# --- Funções utilitárias ---
def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

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
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    return df, sheet, credentials, gc, SPREADSHEET_ID

# --- Botão voltar ---
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "alterar_paciente")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# --- Carregamento dos dados ---
df, sheet, credentials, gc, SPREADSHEET_ID = carregar_dados()
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
data_evolucao = st.date_input("📅 **Data da Evolução**", value=date.today(), format="DD/MM/YYYY")

if st.button("💾 Salvar Evolução"):
    if descricao_evolucao.strip() == "":
        st.warning("⚠️ A descrição da evolução não pode estar vazia.")
    else:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)

            # --- Aba Registros ---
            try:
                aba_reg = sh.worksheet("Registros")
            except gspread.exceptions.WorksheetNotFound:
                aba_reg = sh.add_worksheet(title="Registros", rows="1000", cols="10")
                aba_reg.append_row(["PACIENTE_ID", "DATA_REGISTRO", "EVOLUCAO", "USUARIO"])

            nova_linha = [
                id_paciente_str,
                data_evolucao.strftime("%d/%m/%Y"),
                descricao_evolucao.strip(),
                "usuario_a_definir"
            ]
            aba_reg.append_row(nova_linha)

            # --- Aba Fila: atualizar status se existir ---
            try:
                aba_fila = sh.worksheet("Fila")
                registros_fila = aba_fila.get_all_records()
                df_fila = pd.DataFrame(registros_fila)

                if not df_fila.empty:
                    df_fila["DATA"] = pd.to_datetime(
                        df_fila["DATA"], dayfirst=True, errors="coerce"
                    ).dt.date

                    mask = (
                        (df_fila["PACIENTE_ID"].astype(str).str.strip() == id_paciente_str) &
                        (df_fila["DATA"] == data_evolucao)
                    )

                    if mask.any():
                        idx = df_fila[mask].index[0]  # primeira ocorrência
                        col_status = list(df_fila.columns).index("STATUS") + 1
                        aba_fila.update_cell(idx + 2, col_status, "ATENDIDO")
                        st.info("📌 Status do paciente atualizado para ATENDIDO na fila de hoje.")
            except gspread.exceptions.WorksheetNotFound:
                st.warning("⚠️ Aba 'Fila' não encontrada, nenhum status foi atualizado.")

            st.success("✅ Evolução registrada com sucesso!")
            st.switch_page("1_🏠_home.py")

        except Exception as e:
            st.error(f"Erro ao salvar evolução: {e}")

# --- Histórico das Evoluções ---
try:
    aba = gc.open_by_key(SPREADSHEET_ID).worksheet("Registros")
    registros = aba.get_all_records()
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
                texto = f"""
                <div style='padding: 6px 12px; background-color:#f8f9fa; margin-bottom:6px; border-left: 4px solid #0d6efd; border-radius: 4px;'>
                    <p style='font-size: 0.85rem; margin: 0;'>
                        <b>📄</b> - No dia <b>{data}</b> foi registrada a seguinte evolução:<br>
                        <i>"{descricao}"</i><br>
                        <span style='color:gray;'>Registrado por: <b>{usuario}</b></span>
                    </p>
                </div>
                """
                st.markdown(texto, unsafe_allow_html=True)
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

st.markdown("<hr>", unsafe_allow_html=True)

# --- Dados Clínicos ---
st.markdown("<h4>🧪 Informações Clínicas</h4>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"<h6 style='text-align:center;'>🧬 Tipo de Fissura</h6><p style='text-align:center;'>{paciente_info.get('TIPO_FISSURA', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📋 Plano de Tratamento</h6><p style='text-align:center;'>{paciente_info.get('PLANO_TRATAMENTO', '')}</p>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h6 style='text-align:center;'>📝 Diagnóstico</h6><p style='text-align:center;'>{paciente_info.get('DIAGNOSTICO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>🧩 Características Oclusais</h6><p style='text-align:center;'>{paciente_info.get('CARAC_OCLUSAIS', '')}</p>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h6 style='text-align:center;'>🪥 Necessidades Odontológicas</h6><p style='text-align:center;'>{paciente_info.get('NECES_ODONTO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📜 Histórico do Tratamento</h6><p style='text-align:center;'>{paciente_info.get('HISTORIA_TRATAMENTO', '')}</p>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<h6 style='text-align:center;'>🦷 Necessidades Ortodônticas</h6><p style='text-align:center;'>{paciente_info.get('NECES_ORTO', '')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align:center;'>📌 Outros</h6><p style='text-align:center;'>{paciente_info.get('OUTROS', '')}</p>", unsafe_allow_html=True)
with col5:
    st.markdown(f"<h6 style='text-align:center;'>🔪 Necessidades Cirúrgicas</h6><p style='text-align:center;'>{paciente_info.get('NECES_CIRUR', '')}</p>", unsafe_allow_html=True)
