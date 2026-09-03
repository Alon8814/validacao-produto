import streamlit as st
from streamlit_back_camera_input import back_camera_input

st.set_page_config(
    page_title="Validação de Produto",
    page_icon="✅",
    layout="centered"
)

st.title("VALIDAÇÃO DE PRODUTO")
st.write("Sistema de comparação entre OP e plaqueta do produto.")

st.subheader("1. Ordem de Produção")
st.write("Fotografe a OP usando a câmera traseira.")

foto_op = back_camera_input()

if foto_op is not None:
    st.success("Foto da OP capturada.")
    st.image(foto_op)

st.subheader("2. Plaqueta do Produto")
st.write("Fotografe a plaqueta usando a câmera traseira.")

foto_plaqueta = back_camera_input()

if foto_plaqueta is not None:
    st.success("Foto da plaqueta capturada.")
    st.image(foto_plaqueta)

st.subheader("3. Resultado")

if foto_op is not None and foto_plaqueta is not None:
    st.info("As duas fotos foram capturadas. Próxima etapa: leitura automática dos códigos.")
else:
    st.warning("Tire as duas fotos para continuar.")
