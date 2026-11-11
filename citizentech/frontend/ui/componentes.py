"""Componentes visuais reutilizáveis."""
import html
import streamlit as st

# Cor + ícone + texto: a criticidade nunca depende só da cor.
ESTILOS = {
    "alta":  ("#B71C1C", "#FFFFFF", "🔴", "URGÊNCIA ALTA"),
    "media": ("#F9A825", "#000000", "🟠", "URGÊNCIA MÉDIA"),
    "baixa": ("#2E7D32", "#FFFFFF", "🟢", "URGÊNCIA BAIXA"),
}


def cartao_urgencia(urgencia: str, titulo: str, texto: str):
    """Usado no resultado da análise e na lista de últimos relatos do painel."""
    fundo, fonte, icone, rotulo = ESTILOS[urgencia]
    st.markdown(
        f"<div role='alert' style='background:{fundo};color:{fonte};padding:14px;"
        f"border-radius:8px;margin-bottom:8px'>"
        f"<b>{icone} {rotulo}</b><br>{html.escape(titulo)}<br>"
        f"<small>{html.escape(texto)}</small></div>",
        unsafe_allow_html=True,
    )
