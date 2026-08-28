import streamlit as st

st.set_page_config(
    page_title="Validação de Produto",
    page_icon="✅",
    layout="centered"
)

st.title("VALIDAÇÃO DE PRODUTO")

st.write("Sistema de comparação entre OP e plaqueta do produto.")

st.subheader("1. Ordem de Produção")
foto_op = st.camera_input("Tire uma foto da OP")

st.subheader("2. Plaqueta do Produto")
foto_plaqueta = st.camera_input("Tire uma foto da plaqueta")

st.subheader("3. Resultado")

if foto_op is not None and foto_plaqueta is not None:
    st.info("Fotos capturadas com sucesso. Em breve faremos a leitura automática dos códigos.")
else:
    st.warning("Tire as duas fotos para continuar.")