from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
import io
import datetime
import pytz
from pathlib import Path

fuso_manaus = pytz.timezone("America/Manaus")

def gerar_pdf_ficha(paciente, evolucoes, arquivos, usuario_logado):
    buffer = io.BytesIO()
    nome_paciente = paciente.get('Nome', 'Paciente')

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"Ficha de {nome_paciente}",
        author=usuario_logado,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    story = []

    # Caminho da logo
    logo_path = Path("assets/ceu_da_boca/logo_embedded.png")
    if logo_path.exists():
        logo = Image(str(logo_path))
        logo.drawHeight = 3*cm  # altura proporcional
        logo.drawWidth = 3*cm   # largura proporcional
    else:
        logo = Paragraph(" ", styles["Normal"])

    # Texto da coluna da esquerda
    texto_linha1 = Paragraph(f"<b>Ficha de Paciente - {nome_paciente}</b>", styles["Title"])
    texto_linha2 = Paragraph(
        f"Gerado em {datetime.datetime.now(fuso_manaus).strftime('%d/%m/%Y %H:%M')} por {usuario_logado}",
        styles["Normal"]
    )

    # Monta tabela 2 colunas x 2 linhas
    data = [
        [texto_linha1, logo],
        [texto_linha2, '']  # vazio na segunda linha da coluna da direita, pois logo vai ocupar as duas linhas
    ]

    tabela_header = Table(data, colWidths=[11*cm, 5*cm])
    tabela_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,1), 'CENTER'),
        ('SPAN', (1,0), (1,1)),  # logo ocupa duas linhas
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))

    story.append(tabela_header)
    story.append(Spacer(1, 18))

    def add_title(text):
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>{text}</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))

    # 🧾 Dados do Paciente
    add_title("🧾 Dados do Paciente")
    for campo in ["Nome", "Idade", "Sexo", "Data", "Endereco", "Filiacao", "Telefone", "Fao"]:
        story.append(Paragraph(f"<b>{campo}:</b> {paciente.get(campo, '-')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # 🩺 Dados Clínicos
    add_title("🩺 Dados Clínicos")
    for campo in ["Tipo De Fissura", "Historia_Tratamento", "Carac_Oclusais", "Neces_Orto", "Neces_Cirur", "Neces_Odonto", "Outros"]:
        story.append(Paragraph(f"<b>{campo.replace('_',' ')}:</b> {paciente.get(campo,'-')}", styles["Normal"]))
    story.append(Spacer(1,12))

    # 📜 Evoluções
    add_title("📜 Evoluções do Paciente")
    if not evolucoes.empty:
        evolucoes_sorted = evolucoes.sort_values(by="DATA_REGISTRO", ascending=False)
        for _, row in evolucoes_sorted.iterrows():
            data_str = row["DATA_REGISTRO"].strftime("%d/%m/%Y") if row["DATA_REGISTRO"] is not pd.NaT else ""
            story.append(Paragraph(f"<b>Data:</b> {data_str}", styles["Normal"]))
            story.append(Paragraph(f"<b>Descrição:</b> {row.get('EVOLUCAO','')}", styles["Normal"]))
            story.append(Paragraph(f"<i>Registrado por:</i> {row.get('USUARIO','')}", styles["Italic"]))
            story.append(Spacer(1,8))
    else:
        story.append(Paragraph("Nenhuma evolução registrada.", styles["Normal"]))
    story.append(Spacer(1,12))

    # 📎 Documentos
    add_title("📎 Documentos Anexados")
    if arquivos:
        for arq in arquivos:
            nome = arq["name"]
            link = arq.get("webContentLink", "")
            story.append(Paragraph(f"{nome} - <a href='{link}' color='blue'>{link}</a>", styles["Normal"]))
    else:
        story.append(Paragraph("Nenhum documento encontrado.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer
