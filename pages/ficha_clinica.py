import streamlit as st;
import controllers.PacienteController as PacienteController
#from  PyPDF2 import PdfFileReader
import streamlit.components.v1 as components
from streamlit_pdf_viewer import pdf_viewer
import glob

Ficha = PacienteController.Ficha_Clinica()
st.title("Ficha Clínica")
col1, col2 = st.columns(2)
with col1:
                st.write(f"**Nome:** {Ficha[0].nome}")
                st.write(f"**Idade:** {Ficha[0].idade}")
                st.write(f"**FAO:** {Ficha[0].fao}")
                st.write(f"**Endereço:** {Ficha[0].endereco}")
with col2:
                st.write(f"**Data de Nascimento:** {Ficha[0].data}")
                st.write(f"**Sexo:** {Ficha[0].sexo}")
                st.write(f"**Filiação:** {Ficha[0].filiacao}")
                st.write(f"**Telefone:** {Ficha[0].telefone}")
                
st.write(f"______________________________")
st.write(f"**Tipo de Fissura:** {Ficha[0].tipo_fissura}")
col1, col2 = st.columns(2)
with col1:
                st.write("**História do Tratamento:**") 
                st.write(f"{Ficha[0].historia_tratamento}")
                st.write("**Necessidades Odontológicas:**") 
                st.write(f"{Ficha[0].historia_tratamento}")
                st.write("**Necessidades Cirúrgicas:**") 
                st.write(f"{Ficha[0].historia_tratamento}")
                

with col2:

                st.write(f"**Características Oclusais:**")
                st.write(f"{Ficha[0].historia_tratamento}")
                st.write("**Necessidades Ortodônticas:**") 
                st.write(f"{Ficha[0].historia_tratamento}")
                st.write("**Outros:**") 
                st.write(f"{Ficha[0].historia_tratamento}")

st.write(f"______________________________")
st.write("**Registros Clínicos:**") 
st.write(f"______________________________")
st.write("**Documentos Anexados:**") 
pdffiles = []
for file in glob.glob(f"files\pacientes\{Ficha[0].id}\*.pdf"):
        pdffiles.append(file)
with st.expander("Documentos", expanded=True):
        for arquivo in pdffiles:
                st.write(f"______________________________")
                st.write(arquivo)
                #pdf_display = F'<iframe src="{arquivo}" width="800" height="800" type="application/pdf"></iframe>'
                #st.markdown(pdf_display, unsafe_allow_html=True)
                pdf_viewer(arquivo)
