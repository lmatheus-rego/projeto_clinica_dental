import streamlit as st
from datetime import datetime
import pandas as pd
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from streamlit.source_util import (
    page_icon_and_name,
    calc_md5,
    get_pages,
    _on_pages_changed
)

# ----------------- Funções -----------------

def delete_page(main_script_path_str, page_name):
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
    _on_pages_changed.send()

def carregar_planilhas():
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    service_account_info = {k: v.replace('\\n','\n') if k=='private_key' else v 
                            for k,v in st.secrets['gcp_service_account'].items()}
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    gc = gspread.authorize(credentials)
    SPREADSHEET_ID = "1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs"
    sh = gc.open_by_key(SPREADSHEET_ID)

    # Aba Registros
    try:
        aba_registros = sh.worksheet("Registros")
    except gspread.exceptions.WorksheetNotFound:
        aba_registros = sh.add_worksheet("Registros", rows="1000", cols="10")
        aba_registros.append_row(["PACIENTE_ID","DATA_REGISTRO","EVOLUCAO","USUARIO"])

    # Aba Fila
    try:
        aba_fila = sh.worksheet("Fila")
    except gspread.exceptions.WorksheetNotFound:
        aba_fila = sh.add_worksheet("Fila", rows="1000", cols="10")
        aba_fila.append_row(["PACIENTE_ID","DATA","STATUS"])

    return sh, aba_registros, aba_fila

def carregar_paciente(id_paciente_str, sh):
    sheet_principal = sh.sheet1
    df = pd.DataFrame(sheet_principal.get_all_records())
    df.columns = df.columns.str.strip().str.upper()
    paciente_df = df[df["ID"].astype(str) == id_paciente_str]
    if paciente_df.empty:
        st.error("Paciente não encontrado.")
        st.stop()
    return paciente_df.iloc[0]

# ----------------- Botão Voltar -----------------
if st.button("🔙 Voltar para lista de pacientes"):
    st.query_params.clear()
    delete_page("1_🏠_home", "evolucao_tratamento")
    st.switch_page("pages/2_🧑🏻_lista_paciente.py")

# ----------------- Carregar Planilhas -----------------
sh, aba_registros, aba_fila = carregar_planilhas()

# ----------------- Captura ID Paciente -----------------
id_paciente_str = str(st.query_params.get("idpaciente", "")).strip()
if not id_paciente_str:
    st.error("ID do paciente não encontrado.")
    st.stop()

# ----------------- Carregar Dados do Paciente -----------------
paciente_info = carregar_paciente(id_paciente_str, sh)

# ----------------- Exibir Dados do Paciente -----------------
st.markdown("<h3 style='text-align:center;'>📋 Dados do Paciente</h3><hr>", unsafe_allow_html=True)
status = paciente_info.get('STATUS','').strip().lower()
status_emoji = {"ativo": "✅", "inativo": "⛔", "ausente": "🕓"}.get(status, "❔")
status_color = {"ativo": "#28a745", "inativo": "#6c757d", "ausente": "#ffc107"}.get(status, "#000")

espaco, col1, col2, col3, col4, espaco2 = st.columns([1,2,2,2,2,1])
with col1:
    st.markdown(f"<h5 style='text-align:center;'>👤<br>{paciente_info.get('NOME','')}</h5>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h5 style='text-align:center;'>🧭<br>FAO: {paciente_info.get('FAO','')}</h5>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h5 style='text-align:center;'>🎂<br>{paciente_info.get('IDADE','')} anos</h5>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<h5 style='text-align:center; color:{status_color};'>{status_emoji}<br>Status: {paciente_info.get('STATUS','')}</h5>", unsafe_allow_html=True)

# ----------------- Exibir Dados Clínicos -----------------
st.markdown("<h5 style='text-align:center;'>🩺 Dados Clínicos</h5><hr>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])
with col1:
    st.markdown(f"<h8 style='text-align:center;'>👤Tipo de Fissura:</h8><br>st.markdown(f"<h9 style='text-align:center;'>{paciente_info.get('TIPO_FISSURA','')}</h9>", unsafe_allow_html=True)
    st.markdown(f"<h8 style='text-align:center;'>👤Necessidades Cirúrgicas:<br> {paciente_info.get('NECES_CIRUR','')}</h8>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h8 style='text-align:center;'>🧭História do Tratamento:<br> {paciente_info.get('HISTORIA_TRATAMENTO','')}</h8>", unsafe_allow_html=True)
    st.markdown(f"<h8 style='text-align:center;'>👤Outros:<br> {paciente_info.get('OUTROS','')}</h8>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h8 style='text-align:center;'>🎂Características Oclusais:<br> {paciente_info.get('CARAC_OCLUSAIS','')}</h8>", unsafe_allow_html=True)
    st.markdown(f"<h8 style='text-align:center;'>👤Diagnóstico:<br> {paciente_info.get('DIAGNOSTICO','')}</h8>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<h8 style='text-align:center;'>👤Necessidades Odontológicas:<br> {paciente_info.get('NECES_ODONTO','')}</h8>", unsafe_allow_html=True)
    st.markdown(f"<h8 style='text-align:center;'>👤Plano de Tratamento:<br> {paciente_info.get('PLANO_TRATAMENTO','')}</h8>", unsafe_allow_html=True)
with col5:
    st.markdown(f"<h8 style='text-align:center;'>🎂Necessidades Ortodônticas:<br> {paciente_info.get('NECES_ORTO','')}</h8>", unsafe_allow_html=True)

# ----------------- Evolução do Tratamento -----------------
st.markdown("<h3 style='text-align:center;'>📈 Evolução do Tratamento</h3><hr>", unsafe_allow_html=True)
descricao_evolucao = st.text_area("📝 **Descrição da Evolução**", height=100)
data_evolucao = st.date_input("📅 **Data da Evolução**", format="DD/MM/YYYY")

if st.button("💾 Salvar Evolução"):
    if not descricao_evolucao.strip():
        st.warning("⚠️ A descrição da evolução não pode estar vazia.")
    else:
        try:
            # Inserir evolução
            aba_registros.append_row([
                id_paciente_str,
                data_evolucao.strftime("%d/%m/%Y"),
                descricao_evolucao.strip(),
                "usuario_a_definir"
            ])
            st.success("✅ Evolução registrada com sucesso!")

            # Atualizar status na Fila
            registros_fila = aba_fila.get_all_records()
            if registros_fila:
                colunas = [c.strip().upper() for c in aba_fila.row_values(1)]
                col_paciente = colunas.index("PACIENTE_ID") + 1
                col_data = colunas.index("DATA") + 1
                col_status = colunas.index("STATUS") + 1

                for idx, row in enumerate(registros_fila, start=2):
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

            st.experimental_rerun()

        except Exception as e:
            st.error(f"Erro ao salvar evolução: {e}")

# ----------------- Histórico de Evoluções -----------------
try:
    registros = aba_registros.get_all_records()
    df_registros = pd.DataFrame(registros)

    if "PACIENTE_ID" in df_registros.columns:
        df_paciente = df_registros[df_registros["PACIENTE_ID"].astype(str) == id_paciente_str].copy()
        df_paciente["DATA_REGISTRO"] = pd.to_datetime(
            df_paciente["DATA_REGISTRO"], format="%d/%m/%Y", errors="coerce"
        )
        df_paciente = df_paciente.dropna(subset=["DATA_REGISTRO"]).sort_values(
            by="DATA_REGISTRO", ascending=False
        ).reset_index(drop=True)

        if not df_paciente.empty:
            st.markdown("<h4>📜 Histórico de Evoluções</h4><hr>", unsafe_allow_html=True)
            for i, row in df_paciente.iterrows():
                data = row["DATA_REGISTRO"].strftime("%d/%m/%Y")
                descricao = row.get("EVOLUCAO","").strip()
                usuario = row.get("USUARIO","").strip()
                st.markdown(f"""
                    <div style='padding:6px 12px; background-color:#f8f9fa; margin-bottom:6px; border-left:4px solid #0d6efd; border-radius:4px;'>
                        <p style='font-size:0.85rem; margin:0;'>
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
