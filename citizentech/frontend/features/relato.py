from datetime import datetime
import streamlit as st
from providers.api import enviar_relato, classificar_foto, ErroApi
from state.store import adicionar_historico
from ui.componentes import cartao_urgencia

CATEGORIAS = ["buraco", "fissura", "calcada", "iluminacao", "outro"]
URGENCIAS = ["baixa", "media", "alta"]


@st.cache_data(show_spinner=False, ttl=600)
def _analisar(descricao: str, local: str) -> dict:
    # Cache: o mesmo relato não chama o LLM de novo a cada rerun.
    return enviar_relato(descricao, local)


@st.cache_data(show_spinner=False, ttl=600)
def _analisar_foto(nome: str, conteudo: bytes, tipo: str) -> dict:
    return classificar_foto(nome, conteudo, tipo)


def render():
    st.subheader("Relatar um problema na sua cidade")
    with st.form("form_relato"):
        descricao = st.text_area("Descreva o problema", max_chars=1000,
                                 placeholder="Ex.: Buraco grande na rua, perto da escola.")
        local = st.text_input("Bairro ou endereço", max_chars=120)
        foto = st.file_uploader("Foto do local (opcional)", type=["jpg", "jpeg", "png"])
        enviado = st.form_submit_button("Analisar relato")

    if enviado:
        if len(descricao.strip()) < 10 or len(local.strip()) < 3:
            st.warning("Preencha a descrição (mínimo 10 caracteres) e o local.")
        else:
            _processar(descricao.strip(), local.strip(), foto)

    if st.session_state.pendente:
        _revisar(st.session_state.pendente)


def _processar(descricao, local, foto):
    st.session_state.pendente = None
    try:
        with st.spinner("Analisando seu relato..."):
            resp = _analisar(descricao, local)
    except ErroApi as e:
        st.error(str(e))
        return

    visao = None
    if foto is not None:
        try:
            with st.spinner("Analisando a foto..."):
                visao = _analisar_foto(foto.name, foto.getvalue(), foto.type)
        except ErroApi as e:
            st.info(str(e))   # a foto é opcional: segue só com o texto

    st.session_state.pendente = {"resp": resp, "local": local, "visao": visao}


def _revisar(pend: dict):
    a = pend["resp"]["analise"]
    st.markdown("### Resultado da análise")
    cartao_urgencia(a["urgencia"], a["resumo"], a["orientacao"])
    st.write(f"**Encaminhamento sugerido:** {a['encaminhamento']}")

    v = pend.get("visao")
    if v:
        achado = "possível fissura" if v["possivel_fissura"] else "nenhuma fissura aparente"
        st.write(f"**Análise da foto:** {achado} (confiança {v['confianca']:.0%})")
        st.caption(v["aviso"])

    st.caption("A IA pode errar. Confira e corrija antes de registrar.")
    c1, c2 = st.columns(2)
    categoria = c1.selectbox("Categoria", CATEGORIAS, index=CATEGORIAS.index(a["categoria"]))
    urgencia = c2.selectbox("Urgência", URGENCIAS, index=URGENCIAS.index(a["urgencia"]))

    if st.button("Confirmar e registrar"):
        adicionar_historico({
            "protocolo": pend["resp"]["protocolo"],
            "data": datetime.now(),
            "local": pend["local"],
            "categoria": categoria,
            "urgencia": urgencia,
            "resumo": a["resumo"],
            "corrigido": categoria != a["categoria"] or urgencia != a["urgencia"],
        })
        st.session_state.pendente = None
        st.success(f"Relato registrado. Protocolo: {pend['resp']['protocolo']}")
