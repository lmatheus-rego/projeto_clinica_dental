import streamlit as st
from pathlib import Path
import base64

_ASSET_SVG_PATH = Path(__file__).parent / "logo_embedded.svg"

def _svg_data_uri(path: Path) -> str:
    svg = path.read_text(encoding="utf-8")
    # compacta para data-uri (escapa '<' '>' etc)
    b = svg.encode("utf-8")
    return "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(b).decode("ascii")

def render_header(show_menu=True):
    svg_data = _svg_data_uri(_ASSET_SVG_PATH) if _ASSET_SVG_PATH.exists() else ""
    st.markdown(f"""
    <style>
    .cdb-header{{display:flex;align-items:center;gap:16px;padding:12px 0}}
    .cdb-logo{{height:72px}}
    .cdb-title{{font-family: 'Great Vibes', cursive; font-size:34px; margin:0; color:#071a2a}}
    .cdb-sub{{font-family: 'Montserrat', sans-serif; font-size:12px; color:#223344; margin:0}}
    </style>
    <div class="cdb-header">
      <img class="cdb-logo" src="{svg_data}" alt="Céu da Boca logo" />
      <div>
        <h1 class="cdb-title">Céu da Boca</h1>
        <div class="cdb-sub">UFAM</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("""
    <style>
    .cdb-footer{padding:18px 0;margin-top:36px;border-top:1px solid rgba(0,0,0,0.06);display:flex;align-items:center;justify-content:space-between;font-family:'Montserrat',sans-serif}
    .cdb-footer .left{font-size:14px;color:#223344}
    .cdb-footer .right{font-size:13px;color:#223344;opacity:0.8}
    </style>
    <div class="cdb-footer">
      <div class="left">© Céu da Boca - UFAM</div>
      <div class="right">Desenvolvido por • <a href="mailto:luciomatheus.frego@gmail.com">contato</a></div>
    </div>
    """, unsafe_allow_html=True)
