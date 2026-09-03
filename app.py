import streamlit as st
from streamlit_back_camera_input import back_camera_input
import easyocr
import numpy as np
from PIL import Image
import io
import re

st.set_page_config(
    page_title="Validação de Produto",
    page_icon="✅",
    layout="centered"
)

# ==========================================
# OCR
# ==========================================

@st.cache_resource
def carregar_ocr():
    return easyocr.Reader(["pt", "en"], gpu=False)

reader = carregar_ocr()


# ==========================================
# FUNÇÕES
# ==========================================

def foto_para_bytes(foto):
    if foto is None:
        return None

    if hasattr(foto, "getvalue"):
        return foto.getvalue()

    return foto


def ler_imagem(foto_bytes):
    imagem = Image.open(io.BytesIO(foto_bytes)).convert("RGB")
    imagem = np.array(imagem)

    resultado = reader.readtext(
        imagem,
        detail=0,
        paragraph=False
    )

    return resultado


def normalizar(texto):
    if texto is None:
        return None

    texto = texto.upper().strip()
    texto = re.sub(r"\s+", "", texto)

    return texto


def codigo_valido(texto):
    texto = normalizar(texto)

    if not texto:
        return False

    # Tem letra e número
    if not re.search(r"[A-Z]", texto):
        return False

    if not re.search(r"[0-9]", texto):
        return False

    # Somente letras, números e hífen
    if not re.fullmatch(r"[A-Z0-9\-]+", texto):
        return False

    # Evita números curtos, datas etc.
    if len(texto) < 7:
        return False

    return True


# ==========================================
# PROCURAR CÓDIGO NA OP
# ==========================================

def localizar_codigo_op(textos):

    textos_normalizados = [normalizar(x) for x in textos]

    # Primeiro tenta localizar a palavra PRODUTO
    for i, texto in enumerate(textos):

        if "PRODUTO" in texto.upper():

            # Procura nos elementos seguintes
            for candidato in textos[i + 1:i + 6]:

                candidato = normalizar(candidato)

                if codigo_valido(candidato):
                    return candidato

    # Segunda tentativa:
    # preferência para códigos com hífen
    for texto in textos_normalizados:

        if texto and "-" in texto and codigo_valido(texto):
            return texto

    # Última tentativa
    for texto in textos_normalizados:

        if codigo_valido(texto):
            return texto

    return None


# ==========================================
# PROCURAR CÓDIGO NA PLAQUETA
# ==========================================

def localizar_codigo_plaqueta(textos):

    # Na sua regra:
    # primeira linha válida = código do produto

    for texto in textos:

        candidato = normalizar(texto)

        if codigo_valido(candidato):
            return candidato

    return None


# ==========================================
# MEMÓRIA
# ==========================================

if "etapa" not in st.session_state:
    st.session_state.etapa = 1

if "foto_op" not in st.session_state:
    st.session_state.foto_op = None

if "foto_plaqueta" not in st.session_state:
    st.session_state.foto_plaqueta = None


# ==========================================
# TELA
# ==========================================

st.title("VALIDAÇÃO DE PRODUTO")

st.write(
    "Comparação entre código da Ordem de Produção "
    "e código da plaqueta."
)

st.divider()


# ==========================================
# FOTO DA OP
# ==========================================

if st.session_state.etapa == 1:

    st.header("1️⃣ ORDEM DE PRODUÇÃO")

    st.info(
        "Fotografe a OP mostrando claramente "
        "o campo Código do produto."
    )

    foto = back_camera_input(key="op")

    if foto is not None:

        foto_bytes = foto_para_bytes(foto)

        st.image(
            foto_bytes,
            caption="Foto da OP"
        )

        if st.button(
            "✅ CONFIRMAR FOTO DA OP",
            use_container_width=True,
            type="primary"
        ):

            st.session_state.foto_op = foto_bytes
            st.session_state.etapa = 2

            st.rerun()


# ==========================================
# FOTO DA PLAQUETA
# ==========================================

elif st.session_state.etapa == 2:

    st.success("✅ Foto da OP salva")

    st.header("2️⃣ PLAQUETA")

    st.info(
        "Fotografe a plaqueta mostrando "
        "claramente a primeira linha."
    )

    foto = back_camera_input(key="plaqueta")

    if foto is not None:

        foto_bytes = foto_para_bytes(foto)

        st.image(
            foto_bytes,
            caption="Foto da plaqueta"
        )

        if st.button(
            "✅ CONFIRMAR E COMPARAR",
            use_container_width=True,
            type="primary"
        ):

            st.session_state.foto_plaqueta = foto_bytes
            st.session_state.etapa = 3

            st.rerun()


# ==========================================
# OCR + COMPARAÇÃO
# ==========================================

elif st.session_state.etapa == 3:

    st.header("3️⃣ RESULTADO")

    with st.spinner("Lendo os códigos... Aguarde."):

        texto_op = ler_imagem(
            st.session_state.foto_op
        )

        texto_plaqueta = ler_imagem(
            st.session_state.foto_plaqueta
        )

        codigo_op = localizar_codigo_op(texto_op)

        codigo_plaqueta = localizar_codigo_plaqueta(
            texto_plaqueta
        )

    st.subheader("Código identificado na OP")

    if codigo_op:
        st.markdown(f"## `{codigo_op}`")
    else:
        st.error("Código não identificado")

    st.subheader("Código identificado na plaqueta")

    if codigo_plaqueta:
        st.markdown(f"## `{codigo_plaqueta}`")
    else:
        st.error("Código não identificado")

    st.divider()

    # =========================
    # RESULTADO FINAL
    # =========================

    if codigo_op is None or codigo_plaqueta is None:

        st.warning("## 🟡 ERRO DE LEITURA")

        st.warning(
            "Não foi possível identificar um dos códigos. "
            "Faça uma nova fotografia."
        )

    elif codigo_op == codigo_plaqueta:

        st.success("## 🟢 OK")

        st.success("### PRODUTO CORRETO")

    else:

        st.error("## 🔴 NOK")

        st.error("### DIVERGÊNCIA DE IDENTIFICAÇÃO")

        st.write("Código OP:")

        st.code(codigo_op)

        st.write("Código Plaqueta:")

        st.code(codigo_plaqueta)

        st.error("NÃO LIBERAR O PRODUTO")

    # ======================================
    # DIAGNÓSTICO OCR
    # ======================================

    with st.expander("🔎 Ver o que a câmera conseguiu ler"):

        st.write("### Texto encontrado na OP")

        st.write(texto_op)

        st.write("### Texto encontrado na plaqueta")

        st.write(texto_plaqueta)


# ==========================================
# NOVA VERIFICAÇÃO
# ==========================================

if st.session_state.etapa > 1:

    st.divider()

    if st.button(
        "🔄 NOVA VERIFICAÇÃO",
        use_container_width=True
    ):

        st.session_state.etapa = 1
        st.session_state.foto_op = None
        st.session_state.foto_plaqueta = None

        st.rerun()
