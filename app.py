import streamlit as st
from streamlit_back_camera_input import back_camera_input

st.set_page_config(
    page_title="Validação de Produto",
    page_icon="✅",
    layout="centered"
)

# Inicialização
if "etapa" not in st.session_state:
    st.session_state.etapa = 1

if "foto_op" not in st.session_state:
    st.session_state.foto_op = None

if "foto_plaqueta" not in st.session_state:
    st.session_state.foto_plaqueta = None


def converter_foto(foto):
    if foto is None:
        return None

    if hasattr(foto, "getvalue"):
        return foto.getvalue()

    return foto


st.title("VALIDAÇÃO DE PRODUTO")

st.write("Validação entre código da OP e código da plaqueta.")

st.divider()


# ==============================
# ETAPA 1 - OP
# ==============================

if st.session_state.etapa == 1:

    st.header("1. Ordem de Produção")

    st.info("Fotografe a OP, mostrando claramente o campo Código do produto.")

    foto = back_camera_input(
        key="camera_op"
    )

    if foto is not None:

        foto_bytes = converter_foto(foto)

        st.image(
            foto_bytes,
            caption="Foto da Ordem de Produção"
        )

        if st.button(
            "✅ CONFIRMAR FOTO DA OP",
            use_container_width=True
        ):

            st.session_state.foto_op = foto_bytes
            st.session_state.etapa = 2

            st.rerun()


# ==============================
# ETAPA 2 - PLAQUETA
# ==============================

elif st.session_state.etapa == 2:

    st.success("✅ Foto da OP salva")

    st.image(
        st.session_state.foto_op,
        caption="Ordem de Produção",
        width=300
    )

    st.divider()

    st.header("2. Plaqueta do Produto")

    st.info("Fotografe a plaqueta mostrando claramente a primeira linha.")

    foto = back_camera_input(
        key="camera_plaqueta"
    )

    if foto is not None:

        foto_bytes = converter_foto(foto)

        st.image(
            foto_bytes,
            caption="Foto da plaqueta"
        )

        if st.button(
            "✅ CONFIRMAR FOTO DA PLAQUETA",
            use_container_width=True
        ):

            st.session_state.foto_plaqueta = foto_bytes
            st.session_state.etapa = 3

            st.rerun()


# ==============================
# ETAPA 3 - FINAL
# ==============================

elif st.session_state.etapa == 3:

    st.success("✅ Fotos capturadas com sucesso")

    st.subheader("Ordem de Produção")

    st.image(
        st.session_state.foto_op,
        width=300
    )

    st.subheader("Plaqueta")

    st.image(
        st.session_state.foto_plaqueta,
        width=300
    )

    st.divider()

    st.info(
        "Próxima etapa: fazer a leitura automática dos códigos e realizar a comparação."
    )


# ==============================
# REINICIAR
# ==============================

st.divider()

if st.button(
    "🔄 INICIAR NOVA VERIFICAÇÃO",
    use_container_width=True
):

    st.session_state.etapa = 1
    st.session_state.foto_op = None
    st.session_state.foto_plaqueta = None

    st.rerun()
