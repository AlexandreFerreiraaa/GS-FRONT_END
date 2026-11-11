"""Estado centralizado da aplicação (st.session_state)."""
import streamlit as st


def init_state():
    st.session_state.setdefault("historico", [])   # relatos confirmados (alimenta o painel)
    st.session_state.setdefault("pendente", None)  # resultado da IA aguardando revisão humana


def adicionar_historico(item: dict):
    st.session_state.historico.append(item)
