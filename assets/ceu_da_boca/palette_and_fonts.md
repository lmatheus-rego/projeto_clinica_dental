# Paleta de cores e tipografia sugerida

**Cores (aproximações extraídas da arte):**
- Azul claro (fundo antigo): #bfe1f8
- Azul accent: #7fb6e6
- Azul escuro (texto): #071a2a
- Cinza médio: #223344

**Tipografias sugeridas:**
- Título com script/cursiva: *Great Vibes* (Google Fonts) — para reproduzir a sensação da caligrafia.
- Texto e menus: *Montserrat* (Google Fonts) — fonte sans-serif limpa e legível.

**Como importar no Streamlit** (exemplo):
```python
st.markdown("""<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">""", unsafe_allow_html=True)
```

Arquivos gerados:
- /mnt/data/logo_transparent.png  (PNG com fundo transparente)
- /mnt/data/logo_embedded.svg    (SVG que embute o PNG — útil como fallback vetorial)
- /mnt/data/header_footer.py     (pequeno componente para Streamlit: render_header(), render_footer())
- /mnt/data/style.css
- /mnt/data/palette_and_fonts.md
