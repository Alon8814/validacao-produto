import streamlit as st
from streamlit_back_camera_input import back_camera_input
import easyocr
import numpy as np
from PIL import Image
import io
import re

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

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
# FUNÇÕES BÁSICAS
# ============================================================

def foto_para_bytes(foto):
    if foto is None:
        return None

    if hasattr(foto, "getvalue"):
        return foto.getvalue()

    return foto


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

    if len(texto) < 8:
        return False

    # precisa ter pelo menos uma letra
    if not re.search(r"[A-Z]", texto):
        return False

    # precisa ter pelo menos um número
    if not re.search(r"[0-9]", texto):
        return False

    # só aceita letras, números e hífen
    if not re.fullmatch(r"[A-Z0-9\-]+", texto):
        return False

    # rejeita texto totalmente numérico
    if texto.replace("-", "").isdigit():
        return False

    palavras_proibidas = [
        "EMISSAO",
        "EMISSÃO",
        "PRODUTO",
        "PEDIDO",
        "CLIENTE",
        "QUANTIDADE",
        "ORDEM",
        "DATA",
        "CODIGO",
        "CÓDIGO"
    ]

    if texto in palavras_proibidas:
        return False

    return True

# ============================================================
# RECORTE DA OP
# ============================================================

def recortar_op(foto_bytes):
    imagem = Image.open(io.BytesIO(foto_bytes)).convert("RGB")

    largura, altura = imagem.size

    # Região onde normalmente ficam Emissão e Código do produto
    esquerda = int(largura * 0.10)
    direita = int(largura * 0.98)
    topo = int(altura * 0.10)
    base = int(altura * 0.60)

    recorte = imagem.crop(
        (esquerda, topo, direita, base)
    )

    return np.array(recorte)

# ============================================================
# RECORTE DA PLAQUETA
# ============================================================

def recortar_plaqueta(foto_bytes):
    imagem = Image.open(io.BytesIO(foto_bytes)).convert("RGB")

    largura, altura = imagem.size

    # Usa somente a parte superior da plaqueta
    esquerda = int(largura * 0.03)
    direita = int(largura * 0.97)
    topo = int(altura * 0.03)
    base = int(altura * 0.45)

    recorte = imagem.crop(
        (esquerda, topo, direita, base)
    )

    return np.array(recorte)

# ============================================================
# OCR DA OP
# ============================================================

def ler_op(foto_bytes):
    imagem = recortar_op(foto_bytes)

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

    return sorted(
        itens,
        key=lambda item: (item["y"], item["x"])
    )

# ============================================================
# OCR DA PLAQUETA
# ============================================================

def ler_plaqueta(foto_bytes):
    imagem = recortar_plaqueta(foto_bytes)

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

    return sorted(
        itens,
        key=lambda item: (item["y"], item["x"])
    )

# ============================================================
# AGRUPAR TEXTOS EM LINHAS
# ============================================================

def agrupar_em_linhas(itens, tolerancia=35):
    linhas = []

    for item in sorted(itens, key=lambda x: x["y"]):
        colocado = False

        for linha in linhas:
            if abs(linha["y"] - item["y"]) < tolerancia:
                linha["itens"].append(item)
                colocado = True
                break

        if not colocado:
            linhas.append({
                "y": item["y"],
                "itens": [item]
            })

    for linha in linhas:
        linha["itens"] = sorted(
            linha["itens"],
            key=lambda x: x["x"]
        )

    return sorted(
        linhas,
        key=lambda x: x["y"]
    )

# ============================================================
# LOCALIZAR CÓDIGO DA OP
# ============================================================

def localizar_codigo_op(itens):
    linhas = agrupar_em_linhas(itens)

    # Primeiro procura "Emissão"
    indice_emissao = None

    for i, linha in enumerate(linhas):
        texto_linha = " ".join(
            item["texto"] for item in linha["itens"]
        ).upper()

        if "EMISS" in texto_linha:
            indice_emissao = i
            break

    # Regra principal:
    # segunda linha abaixo de Emissão
    if indice_emissao is not None:
        indice_codigo = indice_emissao + 2

        if indice_codigo < len(linhas):
            linha_codigo = linhas[indice_codigo]

            candidatos = []

            for item in linha_codigo["itens"]:
                candidato = normalizar(item["texto"])

                if codigo_valido(candidato):
                    candidatos.append(candidato)

            if candidatos:
                # dá preferência para código com hífen
                candidatos = sorted(
                    candidatos,
                    key=lambda x: ("-" in x, len(x)),
                    reverse=True
                )

                return candidatos[0]

    # Segunda regra:
    # procura campo Produto / Código do produto
    for i, linha in enumerate(linhas):
        texto_linha = " ".join(
            item["texto"] for item in linha["itens"]
        ).upper()

        if "PRODUTO" in texto_linha:

            # mesma linha
            for item in linha["itens"]:
                candidato = normalizar(item["texto"])

                if codigo_valido(candidato):
                    return candidato

            # linha logo abaixo
            if i + 1 < len(linhas):
                for item in linhas[i + 1]["itens"]:
                    candidato = normalizar(item["texto"])

                    if codigo_valido(candidato):
                        return candidato

    return None

# ============================================================
# LOCALIZAR CÓDIGO DA PLAQUETA
# ============================================================

def localizar_codigo_plaqueta(itens):
    linhas = agrupar_em_linhas(itens, tolerancia=30)

    # Primeira linha válida da plaqueta
    for linha in linhas:

        candidatos = []

        for item in linha["itens"]:
            candidato = normalizar(item["texto"])

            if codigo_valido(candidato):
                candidatos.append({
                    "codigo": candidato,
                    "confianca": item["confianca"]
                })

        if candidatos:

            candidatos = sorted(
                candidatos,
                key=lambda x: (
                    "-" in x["codigo"],
                    x["confianca"],
                    len(x["codigo"])
                ),
                reverse=True
            )

            return candidatos[0]["codigo"]

    return None

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
# CABEÇALHO
# ============================================================

st.title("VALIDAÇÃO DE PRODUTO")

st.write(
    "Comparação automática entre o código da OP "
    "e o código da plaqueta."
)

st.divider()

# ============================================================
# ETAPA 1 - OP
# ============================================================

if st.session_state.etapa == 1:

    st.header("1️⃣ ORDEM DE PRODUÇÃO")

    st.info(
        "Fotografe a OP inteira, mantendo o documento "
        "reto e com boa iluminação."
    )

    foto = back_camera_input(
        key="camera_op"
    )

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
# ETAPA 2 - PLAQUETA
# ============================================================

elif st.session_state.etapa == 2:

    st.success("✅ Foto da OP salva")

    st.header("2️⃣ PLAQUETA DO PRODUTO")

    st.info(
        "Fotografe a plaqueta de frente, "
        "com a primeira linha bem nítida."
    )

    foto = back_camera_input(
        key="camera_plaqueta"
    )

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
# ETAPA 3 - OCR + COMPARAÇÃO
# ============================================================

elif st.session_state.etapa == 3:

    st.header("3️⃣ RESULTADO")

    with st.spinner(
        "Lendo os códigos... Aguarde."
    ):

        itens_op = ler_op(
            st.session_state.foto_op
        )

        itens_plaqueta = ler_plaqueta(
            st.session_state.foto_plaqueta
        )

        codigo_op = localizar_codigo_op(
            itens_op
        )

        codigo_plaqueta = localizar_codigo_plaqueta(
            itens_plaqueta
        )

    # --------------------------------------------------------
    # CÓDIGOS IDENTIFICADOS
    # --------------------------------------------------------

    st.subheader("ORDEM DE PRODUÇÃO")

    if codigo_op:
        st.write("Código identificado:")
        st.markdown(
            f"## `{codigo_op}`"
        )
    else:
        st.error(
            "Código do produto não identificado na OP."
        )

    st.subheader("PLAQUETA")

    if codigo_plaqueta:
        st.write("Código identificado:")
        st.markdown(
            f"## `{codigo_plaqueta}`"
        )
    else:
        st.error(
            "Código não identificado na plaqueta."
        )

    st.divider()

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if codigo_op is None or codigo_plaqueta is None:

        st.warning(
            "## 🟡 ERRO DE LEITURA"
        )

        st.warning(
            "Não liberar o produto. "
            "Faça uma nova fotografia."
        )

    elif normalizar(codigo_op) == normalizar(codigo_plaqueta):

        st.success(
            "## 🟢 OK"
        )

        st.success(
            "### PRODUTO CORRETO"
        )

        st.write("Código OP:")
        st.code(codigo_op)

        st.write("Código Plaqueta:")
        st.code(codigo_plaqueta)

    else:

        st.error(
            "## 🔴 NOK"
        )

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
        "🔎 DIAGNÓSTICO DO OCR"
    ):

        st.write(
            "### Região analisada da OP"
        )

        st.image(
            recortar_op(
                st.session_state.foto_op
            )
        )

        st.write(
            "### Texto encontrado na OP"
        )

        if itens_op:
            for item in itens_op:
                st.write(
                    f'{item["texto"]} '
                    f'— confiança: '
                    f'{item["confianca"]:.0%}'
                )
        else:
            st.write(
                "Nenhum texto encontrado."
            )

        st.divider()

        st.write(
            "### Região analisada da plaqueta"
        )

        st.image(
            recortar_plaqueta(
                st.session_state.foto_plaqueta
            )
        )

        st.write(
            "### Texto encontrado na plaqueta"
        )

        if itens_plaqueta:
            for item in itens_plaqueta:
                st.write(
                    f'{item["texto"]} '
                    f'— confiança: '
                    f'{item["confianca"]:.0%}'
                )
        else:
            st.write(
                "Nenhum texto encontrado."
            )

# ============================================================
# NOVA VERIFICAÇÃO
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
