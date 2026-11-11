import pandas as pd
import plotly.express as px
import streamlit as st
from ui.componentes import cartao_urgencia

CORES = {"alta": "#B71C1C", "media": "#F9A825", "baixa": "#2E7D32"}


def render():
    st.subheader("Painel de ocorrências")
    historico = st.session_state.historico
    if not historico:
        st.info("Nenhum relato registrado ainda. Envie um na aba 'Relatar problema'.")
        return

    df = pd.DataFrame(historico)
    todas_cats = sorted(df.categoria.unique())
    c1, c2 = st.columns(2)
    cats = c1.multiselect("Categoria", todas_cats, default=todas_cats)
    urgs = c2.multiselect("Urgência", ["alta", "media", "baixa"], default=["alta", "media", "baixa"])

    f = df[df.categoria.isin(cats) & df.urgencia.isin(urgs)]
    if f.empty:
        st.warning("Nenhum relato com esses filtros.")
        return

    m1, m2 = st.columns(2)
    m1.metric("Relatos exibidos", len(f))
    m2.metric("Corrigidos pelo cidadão", f"{f.corrigido.mean():.0%}")

    contagem = f.groupby(["categoria", "urgencia"]).size().reset_index(name="quantidade")
    st.plotly_chart(px.bar(contagem, x="categoria", y="quantidade", color="urgencia",
                           color_discrete_map=CORES, title="Relatos por categoria e urgência"),
                    use_container_width=True)
    st.plotly_chart(px.scatter(f, x="data", y="categoria", color="urgencia",
                               color_discrete_map=CORES, hover_data=["local", "resumo"],
                               title="Linha do tempo dos relatos"),
                    use_container_width=True)

    st.markdown("#### Últimos relatos")
    for _, linha in f.tail(3).iterrows():
        cartao_urgencia(linha.urgencia, f"{linha.local}: {linha.resumo}", f"Protocolo {linha.protocolo}")
