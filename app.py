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

# ============================================================
# OCR
# ============================================================

@st.cache_resource
def carregar_ocr():
    return easyocr.Reader(["pt", "en"], gpu=False)

reader = carregar_ocr()


# ============================================================
# FUNÇÕES
# ============================================================

def foto_para_bytes(foto):
    if foto is None:
        return None

    if hasattr(foto, "getvalue"):
        return foto.getvalue()

    return foto


def ler_imagem(foto_bytes):
    imagem = Image.open(io.BytesIO(foto_bytes)).convert("RGB")
    imagem = np.array(imagem)

    resultados = reader.readtext(
        imagem,
        detail=1,
        paragraph=False
    )

    itens = []

    for caixa, texto, confianca in resultados:
        x = min(p[0] for p in caixa)
        y = min(p[1] for p in caixa)

        itens.append({
            "texto": texto.strip(),
            "confianca": confianca,
            "x": x,
            "y": y
        })

    itens = sorted(itens, key=lambda item: (item["y"], item["x"]))

    return itens


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

    if len(texto) < 7:
        return False

    if not re.search(r"[A-Z]", texto):
        return False

    if not re.search(r"[0-9]", texto):
        return False

    if not re.fullmatch(r"[A-Z0-9\-]+", texto):
        return False

    return True


# ============================================================
# REGRA DA OP
# ============================================================

def localizar_codigo_op(itens):

    # Procura especificamente pelo campo:
    # Código do produto

    for i, item in enumerate(itens):

        texto = item["texto"].upper()

        if "PRODUTO" in texto:

            y_referencia = item["y"]

            candidatos = []

            # Procura textos próximos ao campo
            for outro in itens:

                if outro == item:
                    continue

                distancia_y = abs(outro["y"] - y_referencia)

                if distancia_y < 120:

                    candidato = normalizar(outro["texto"])

                    if codigo_valido(candidato):

                        candidatos.append({
                            "codigo": candidato,
                            "x": outro["x"],
                            "y": outro["y"]
                        })

            if candidatos:

                # Prioriza quem está mais à direita
                candidatos = sorted(
                    candidatos,
                    key=lambda c: c["x"],
                    reverse=True
                )

                return candidatos[0]["codigo"]

    return None


# ============================================================
# REGRA DA PLAQUETA
# ============================================================

def localizar_codigo_plaqueta(itens):

    candidatos = []

    for item in itens:

        candidato = normalizar(item["texto"])

        if codigo_valido(candidato):

            candidatos.append({
                "codigo": candidato,
                "y": item["y"]
            })

    if not candidatos:
        return None

    # A regra da plaqueta é:
    # primeira linha válida = código do produto

    candidatos = sorted(
        candidatos,
        key=lambda c: c["y"]
    )

    return candidatos[0]["codigo"]


# ============================================================
# SESSÃO
# ============================================================

if "etapa" not in st.session_state:
    st.session_state.etapa = 1

if "foto_op" not in st.session_state:
    st.session_state.foto_op = None

if "foto_plaqueta" not in st.session_state:
    st.session_state.foto_plaqueta = None


# ============================================================
# TELA
# ============================================================

st.title("VALIDAÇÃO DE PRODUTO")

st.write(
    "Comparação automática entre o código da OP "
    "e o código da plaqueta."
)

st.divider()


# ============================================================
# ETAPA 1 - FOTO DA OP
# ============================================================

if st.session_state.etapa == 1:

    st.header("1️⃣ ORDEM DE PRODUÇÃO")

    st.info(
        "Fotografe a OP mostrando claramente "
        "o campo 'Código do produto'."
    )

    foto = back_camera_input(key="camera_op")

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


# ============================================================
# ETAPA 2 - FOTO DA PLAQUETA
# ============================================================

elif st.session_state.etapa == 2:

    st.success("✅ Foto da OP salva")

    st.header("2️⃣ PLAQUETA DO PRODUTO")

    st.info(
        "Fotografe a plaqueta mostrando claramente "
        "a primeira linha."
    )

    foto = back_camera_input(key="camera_plaqueta")

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


# ============================================================
# ETAPA 3 - OCR + RESULTADO
# ============================================================

elif st.session_state.etapa == 3:

    st.header("3️⃣ RESULTADO")

    with st.spinner("Lendo OP e plaqueta..."):

        itens_op = ler_imagem(
            st.session_state.foto_op
        )

        itens_plaqueta = ler_imagem(
            st.session_state.foto_plaqueta
        )

        codigo_op = localizar_codigo_op(
            itens_op
        )

        codigo_plaqueta = localizar_codigo_plaqueta(
            itens_plaqueta
        )

    # --------------------------------------------------------
    # MOSTRA O QUE FOI LIDO
    # --------------------------------------------------------

    st.subheader("OP")

    if codigo_op:
        st.write("Código identificado:")
        st.markdown(f"## `{codigo_op}`")
    else:
        st.error(
            "Não consegui identificar o campo Código do produto."
        )

    st.subheader("PLAQUETA")

    if codigo_plaqueta:
        st.write("Código identificado:")
        st.markdown(f"## `{codigo_plaqueta}`")
    else:
        st.error(
            "Não consegui identificar a primeira linha da plaqueta."
        )

    st.divider()

    # --------------------------------------------------------
    # RESULTADO FINAL
    # --------------------------------------------------------

    if codigo_op is None or codigo_plaqueta is None:

        st.warning("## 🟡 ERRO DE LEITURA")

        st.warning(
            "Não realizar a liberação. "
            "Faça uma nova fotografia."
        )

    elif codigo_op == codigo_plaqueta:

        st.success("## 🟢 OK")

        st.success(
            "### PRODUTO CORRETO"
        )

        st.write("Código OP:")
        st.code(codigo_op)

        st.write("Código Plaqueta:")
        st.code(codigo_plaqueta)

    else:

        st.error("## 🔴 NOK")

        st.error(
            "### DIVERGÊNCIA DE IDENTIFICAÇÃO"
        )

        st.write("Código OP:")
        st.code(codigo_op)

        st.write("Código Plaqueta:")
        st.code(codigo_plaqueta)

        st.error(
            "⛔ NÃO LIBERAR O PRODUTO"
        )

    # --------------------------------------------------------
    # DIAGNÓSTICO
    # --------------------------------------------------------

    with st.expander(
        "🔎 VER EXATAMENTE O QUE O OCR LEU"
    ):

        st.write("### OP")

        if itens_op:
            for item in itens_op:
                st.write(
                    f'{item["texto"]} '
                    f'({item["confianca"]:.0%})'
                )
        else:
            st.write("Nenhum texto encontrado.")

        st.divider()

        st.write("### PLAQUETA")

        if itens_plaqueta:
            for item in itens_plaqueta:
                st.write(
                    f'{item["texto"]} '
                    f'({item["confianca"]:.0%})'
                )
        else:
            st.write("Nenhum texto encontrado.")


# ============================================================
# NOVA INSPEÇÃO
# ============================================================

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
