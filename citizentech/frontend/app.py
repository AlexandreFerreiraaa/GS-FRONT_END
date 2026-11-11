import streamlit as st
from state.store import init_state
from features import relato, painel

st.set_page_config(page_title="CitizenTech – Manutenção Urbana", page_icon="🏙️", layout="wide")
init_state()

with st.sidebar:
    st.title("🏙️ CitizenTech")
    st.write("Relate buracos, fissuras e outros danos na sua cidade. "
             "A IA ajuda a organizar e priorizar o atendimento.")
    st.caption("Este sistema apoia a triagem e não avalia a segurança estrutural de construções.")

tab1, tab2 = st.tabs(["📝 Relatar problema", "📊 Painel"])
with tab1:
    relato.render()
with tab2:
    painel.render()
