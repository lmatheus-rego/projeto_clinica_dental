import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import io
import datetime
import pytz
from pathlib import Path

# --------------------------------------------
# 🔹 Configuração da Página e UI Profissional
# --------------------------------------------
st.set_page_config(page_title="Ficha do Paciente - Céu da Boca", page_icon="🦷", layout="wide")

# Fuso horário de Manaus
fuso_manaus = pytz.timezone("America/Manaus")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }
        
        /* CABEÇALHO PROPORCIONAL (Padrão Dashboard) */
        .main-header {
            background: linear-gradient(90deg, #004a99 0%, #007bff 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .main-header h1 { 
            margin: 0 !important; 
            font-weight: 700 !important; 
            font-size: 1.8rem !important; 
            color: #FFFFFF !important;
            letter-spacing: -0.5px;
        }

        /* Botões Padrão Profissional */
        div.stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            height: 38px;
            transition: all 0.3s ease;
        }

        /* Labels de Prontuário */
        .record-label {
            color: #64748b;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 2px;
        }
        .record-value {
            color: #1e293b;
            font-size: 1.05rem;
            font-weight: 500;
            margin-bottom: 15px;
        }

        /* Estilo dos Expanders */
        .stExpander {
            border: 1px solid #f1f5f9 !important;
            border-radius: 12px !important;
            background-color: white !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }

        .block-container {
            padding-top: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------
# 🔹 Funções de Dados e Credenciais
# --------------------------------------------
def get_credentials(scopes):
    service_account_info = dict(st.secrets["gcp_service_account"])
    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(service_account_info, scopes=scopes)

@st.cache_data(ttl=300)
def carregar_dados_completos():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = get_credentials(scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1H3sOlQ1cDTj8z4uMSrM0oP-45TF0hR5gYwXjCJN97cs")
        
        df_p = pd.DataFrame(sh.sheet1.get_all_records())
        df_f = pd.DataFrame(sh.worksheet("Fila").get_all_records())
        df_r = pd.DataFrame(sh.worksheet("Registros").get_all_records())
        
        return df_p, df_f, df_r, gc
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), None

# Inicializar dados
df_pacientes, df_fila, df_registros, gc_global = carregar_dados_completos()
if not df_pacientes.empty:
    df_pacientes.columns = df_pacientes.columns.str.strip().str.title()

# --------------------------------------------
# 🔹 Menu Lateral Profissional
# --------------------------------------------
with st.sidebar:
    st.markdown("### 🏛️ Institucional\n**FAO/UFAM**")
    st.caption("Projeto Céu da Boca")
    st.markdown("---")
    
    st.markdown("### 📅 Fila de Hoje")
    hoje = datetime.date.today()
    if not df_fila.empty:
        df_fila["DATA"] = pd.to_datetime(df_fila["DATA"], dayfirst=True, errors="coerce").dt.date
        fila_hoje = df_fila[df_fila["DATA"] == hoje]
        if not fila_hoje.empty:
            for _, r in fila_hoje.iterrows():
                p_id = str(r["PACIENTE_ID"]).strip()
                p_nome = df_pacientes[df_pacientes["Id"].astype(str).str.strip() == p_id]["Nome"].values
                st.info(f"👤 **{p_nome[0] if len(p_nome)>0 else p_id}**")
        else:
            st.write("Sem agendamentos.")
    
    st.markdown("---")
    if st.button("🔄 Sincronizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --------------------------------------------
# 🔹 Cabeçalho da Página
# --------------------------------------------
st.markdown("""
    <div class="main-header">
        <h1>🗂️ Ficha Clínica do Paciente</h1>
    </div>
""", unsafe_allow_html=True)

# Captura de ID dos Query Params
id_paciente_str = st.query_params.get("idpaciente", "")
if isinstance(id_paciente_str, list): id_paciente_str = id_paciente_str[0]
id_paciente_str = id_paciente_str.strip()

# Validar Paciente
paciente_df = df_pacientes[df_pacientes["Id"].astype(str) == id_paciente_str] if not df_pacientes.empty else pd.DataFrame()

if paciente_df.empty:
    st.warning("Selecione um paciente na lista para visualizar a ficha.")
    if st.button("Ir para Lista de Pacientes"):
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")
    st.stop()

paciente = paciente_df.iloc[0]

# --------------------------------------------
# 🔹 Ações de Topo
# --------------------------------------------
c_nav1, c_nav2, _ = st.columns([1, 1, 2.5])

with c_nav1:
    if st.button("⬅️ Voltar para Lista", use_container_width=True):
        st.query_params.clear()
        st.switch_page("pages/2_🧑🏻_lista_paciente.py")

with c_nav2:
    # Botão de PDF (Simplificado para o exemplo)
    if st.button("🖨️ Exportar PDF", use_container_width=True):
        st.toast("Gerando documento...", icon="⏳")

st.markdown(f"## **{paciente.get('Nome', '-').upper()}**")
st.markdown("---")

# --------------------------------------------
# 🔹 Corpo da Ficha (Aspecto Profissional)
# --------------------------------------------

with st.expander("🧾 Dados Cadastrais", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    fields = [
        (col1, "Nome Completo", paciente.get('Nome')),
        (col1, "Idade", f"{paciente.get('Idade')} anos"),
        (col1, "Sexo", paciente.get('Sexo')),
        (col2, "FAO (Prontuário)", paciente.get('Fao')),
        (col2, "Telefone", paciente.get('Telefone')),
        (col2, "Data de Nascimento", paciente.get('Data')),
        (col3, "Endereço", paciente.get('Endereco')),
        (col3, "Filiação", paciente.get('Filiacao'))
    ]
    
    for col, label, value in fields:
        col.markdown(f'<p class="record-label">{label}</p><p class="record-value">{value or "-"}</p>', unsafe_allow_html=True)

with st.expander("🩺 Avaliação e Diagnóstico", expanded=True):
    c_clin1, c_clin2 = st.columns(2)
    
    # Campo de destaque para o Tipo de Fissura
    st.info(f"**TIPO DE FISSURA:** {paciente.get('Tipo De Fissura', 'Não especificado')}")
    
    clin_fields = [
        (c_clin1, "História do Tratamento", "Historia_Tratamento"),
        (c_clin1, "Características Oclusais", "Carac_Oclusais"),
        (c_clin1, "Necessidades Ortodônticas", "Neces_Orto"),
        (c_clin2, "Necessidades Cirúrgicas", "Neces_Cirur"),
        (c_clin2, "Diagnóstico", "Diagnostico"),
        (c_clin2, "Plano de Tratamento", "Plano_Tratamento")
    ]
    
    for col, label, key in clin_fields:
        col.markdown(f'<p class="record-label">{label}</p><p class="record-value">{paciente.get(key) or "Sem registros"}</p>', unsafe_allow_html=True)

with st.expander("📜 Histórico de Evoluções", expanded=True):
    evolucoes = df_registros[df_registros["PACIENTE_ID"].astype(str) == id_paciente_str] if not df_registros.empty else pd.DataFrame()
    
    if not evolucoes.empty:
        evolucoes["DATA_REGISTRO"] = pd.to_datetime(evolucoes["DATA_REGISTRO"], dayfirst=True, errors='coerce')
        for _, row in evolucoes.sort_values("DATA_REGISTRO", ascending=False).iterrows():
            data_f = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if pd.notna(row["DATA_REGISTRO"]) else "S/D"
            st.markdown(f"""
                <div style="background-color:#f8fafc; padding:12px; border-radius:10px; border-left:5px solid #004a99; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                        <span style="font-weight:700; color:#004a99;">📅 {data_f}</span>
                        <span style="font-size:0.8rem; color:#64748b;">👤 {row.get('USUARIO','-')}</span>
                    </div>
                    <div style="color:#1e293b; line-height:1.5;">{row.get('EVOLUCAO', '-')}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma evolução clínica registrada para este paciente.")

with st.expander("📎 Documentos Digitais", expanded=False):
    # Aqui entraria a função de listar PDFs do Drive que você já tem
    st.write("Consulte os arquivos anexados no Google Drive vinculados ao ID deste paciente.")

# Rodapé
st.markdown("---")
st.caption(f"Ficha atualizada em: {datetime.datetime.now(fuso_manaus).strftime('%d/%m/%Y %H:%M')}")