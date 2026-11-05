import os
import html
import time
import streamlit as st
import chromadb
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Árbitro Virtual de BJJ",
    page_icon="🥋",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estilos (Tu diseño premium de v0.app)
# ---------------------------------------------------------------------------
SEARCH_ICON = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' "
    "fill='none' stroke='%23dc2626' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/></svg>"
)

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {{
    --bg: #0a0a0a;
    --surface: #141414;
    --surface-2: #1c1c1c;
    --border: #2a2a2a;
    --text: #f5f5f5;
    --muted: #a3a3a3;
    --accent: #dc2626;
    --accent-hover: #b91c1c;
}}

html, body, [data-testid="stAppViewContainer"], .stApp {{
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(220, 38, 38, 0.18), transparent 60%),
        var(--bg) !important;
    color: var(--text);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}}

/* Ocultamos el contenido del header, pero NO el header entero:
   ahí vive el botón para volver a abrir el sidebar. */
header[data-testid="stHeader"] {{
    background: transparent !important;
    box-shadow: none !important;
}}
#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stMainMenu"],
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"] {{
    visibility: hidden;
}}

/* ---------- Botón para reabrir el panel lateral ---------- */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{
    visibility: visible !important;
    position: fixed !important;
    top: 1rem;
    left: 1rem;
    z-index: 999999;
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    padding: 0 !important;
    border-radius: 14px !important;
    background: linear-gradient(145deg, #1f1f1f, #0f0f0f) !important;
    border: 1px solid var(--border) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 0 1px rgba(220, 38, 38, 0.25), 0 12px 30px -12px rgba(220, 38, 38, 0.6);
    cursor: pointer;
    transition: border-color .2s ease, transform .2s ease, box-shadow .2s ease;
}}
[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="collapsedControl"]:hover {{
    border-color: var(--accent) !important;
    transform: translateY(-1px);
    box-shadow: 0 0 0 1px rgba(220, 38, 38, 0.5), 0 14px 36px -10px rgba(220, 38, 38, 0.75);
}}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: var(--accent) !important;
    padding: 0 !important;
    width: auto !important;
}}
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stExpandSidebarButton"] span,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {{
    color: var(--accent) !important;
    fill: currentColor;
}}

/* Botón de cerrar dentro del sidebar, siempre visible y a juego */
[data-testid="stSidebarCollapseButton"] {{
    visibility: visible !important;
    display: flex !important;
}}
[data-testid="stSidebarCollapseButton"] button {{
    width: auto !important;
    background: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--muted) !important;
    box-shadow: none !important;
    padding: .25rem !important;
}}
[data-testid="stSidebarCollapseButton"] button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: transparent !important;
}}

.block-container {{
    max-width: 760px;
    padding-top: 3.5rem;
    padding-bottom: 4rem;
}}

/* ---------- Hero ---------- */
.hero {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 1rem;
    margin-bottom: 2.5rem;
}}
.hero-icon {{
    width: 76px;
    height: 76px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.4rem;
    border-radius: 20px;
    background: linear-gradient(145deg, #1f1f1f, #0f0f0f);
    border: 1px solid var(--border);
    box-shadow: 0 0 0 1px rgba(220, 38, 38, 0.25), 0 12px 40px -12px rgba(220, 38, 38, 0.55);
}}
.hero-eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: .5rem;
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--muted);
}}
.hero-eyebrow .dot {{
    width: 6px; height: 6px; border-radius: 999px; background: var(--accent);
    box-shadow: 0 0 10px var(--accent);
}}
.hero h1 {{
    font-size: clamp(2rem, 6vw, 3.25rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.05;
    margin: 0;
    padding: 0;
    color: var(--text);
}}
.hero h1 span {{ color: var(--accent); }}
.hero p {{
    color: var(--muted);
    font-size: 1.05rem;
    max-width: 480px;
    margin: 0;
}}

/* ---------- Formulario ---------- */
[data-testid="stForm"] {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.25rem;
}}
.stTextInput label {{ display: none; }}
.stTextInput > div > div {{
    background: transparent !important;
    border: none !important;
}}
.stTextInput input {{
    background-color: var(--surface-2) !important;
    background-image: url("{SEARCH_ICON}");
    background-repeat: no-repeat;
    background-position: 18px center;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 1.05rem 1rem 1.05rem 3.1rem !important;
    font-size: 1rem !important;
    transition: border-color .2s ease, box-shadow .2s ease;
}}
.stTextInput input::placeholder {{ color: #737373; }}
.stTextInput input:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.2) !important;
}}

[data-testid="stFormSubmitButton"] button,
.stButton button {{
    width: 100%;
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 14px !important;
    padding: .9rem 1rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: .01em;
    transition: background .2s ease, transform .2s ease, box-shadow .2s ease;
    box-shadow: 0 10px 30px -10px rgba(220, 38, 38, 0.7);
}}
[data-testid="stFormSubmitButton"] button:hover,
.stButton button:hover {{
    background: var(--accent-hover) !important;
    transform: translateY(-1px);
}}

/* ---------- Sugerencias ---------- */
.suggest-title {{
    font-size: .75rem; color: var(--muted); text-transform: uppercase;
    letter-spacing: .14em; margin: 1.5rem 0 .6rem; font-weight: 600;
}}
div[data-testid="stHorizontalBlock"] .stButton button {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
    box-shadow: none;
    font-weight: 500 !important;
    font-size: .85rem !important;
    padding: .55rem .75rem !important;
}}
div[data-testid="stHorizontalBlock"] .stButton button:hover {{
    border-color: var(--accent) !important;
    color: var(--text) !important;
    background: var(--surface-2) !important;
}}

/* ---------- Carga ---------- */
.loading {{
    display: flex; align-items: center; justify-content: center; gap: .85rem;
    margin-top: 2rem; padding: 1.25rem;
    border: 1px dashed var(--border); border-radius: 16px;
    color: var(--muted);
    animation: pulse 1.6s ease-in-out infinite;
}}
.spinner {{
    width: 20px; height: 20px; border-radius: 999px;
    border: 2px solid rgba(220, 38, 38, .25); border-top-color: var(--accent);
    animation: spin .8s linear infinite;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
@keyframes pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .55; }} }}

/* ---------- Tarjeta de resultado ---------- */
.result {{
    position: relative;
    margin-top: 2rem;
    padding: 1.75rem;
    border-radius: 20px;
    background: linear-gradient(180deg, #161616, #101010);
    border: 1px solid rgba(220, 38, 38, 0.35);
    box-shadow: 0 0 0 1px rgba(220, 38, 38, 0.08), 0 30px 80px -30px rgba(220, 38, 38, 0.45);
    overflow: hidden;
}}
.result::before {{
    content: ""; position: absolute; inset: 0 0 auto 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}}
.result-head {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; flex-wrap: wrap; margin-bottom: 1.1rem;
}}
.badge {{
    display: inline-flex; align-items: center; gap: .45rem;
    background: rgba(220, 38, 38, 0.12); color: #fca5a5;
    border: 1px solid rgba(220, 38, 38, 0.35);
    padding: .3rem .7rem; border-radius: 999px;
    font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
}}
.badge .dot {{ width: 6px; height: 6px; border-radius: 999px; background: var(--accent); }}
.meta {{ font-size: .8rem; color: #737373; }}
.question {{
    color: var(--muted); font-size: .92rem; font-style: italic;
    border-left: 2px solid var(--border); padding-left: .8rem; margin-bottom: 1.1rem;
}}
.result h3 {{
    font-size: 1.35rem; font-weight: 700; color: var(--text);
    margin: 0 0 .75rem; padding: 0; letter-spacing: -0.01em;
}}
.result p, .result li {{ color: #d4d4d4; line-height: 1.65; font-size: .98rem; }}
.result strong {{ color: #fff; }}
.result ul {{ padding-left: 1.1rem; margin: .5rem 0 1rem; }}
.result li {{ margin-bottom: .4rem; }}
.source {{
    margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);
    font-size: .8rem; color: #737373;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Conexión Backend REAL (ChromaDB + Gemini)
# ---------------------------------------------------------------------------
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
cliente_chroma = chromadb.PersistentClient(path="./bd_vectorial")
coleccion = cliente_chroma.get_collection(name="reglas_bjj")

# ---------------------------------------------------------------------------
# Interfaz Visual Principal
# ---------------------------------------------------------------------------
st.markdown(
    """
    <section class="hero">
        <div class="hero-icon" aria-hidden="true">🥋</div>
        <span class="hero-eyebrow"><span class="dot"></span>IA · Reglamento IBJJF</span>
        <h1>Árbitro Virtual <span>de BJJ</span></h1>
        <p>Resolución de dudas sobre el reglamento oficial impulsada por IA</p>
    </section>
    """,
    unsafe_allow_html=True,
)

if "query" not in st.session_state:
    st.session_state.query = ""

# Formulario principal
with st.form("search", clear_on_submit=False, border=False):
    question = st.text_input(
        "Consulta",
        value=st.session_state.query,
        placeholder="Ej: ¿Cuántos puntos otorga pasar la guardia y estabilizar 3 segundos?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Consultar al Árbitro", use_container_width=True)

# ---------------------------------------------------------------------------
# Consultas Frecuentes (Botones de sugerencia)
# ---------------------------------------------------------------------------
SUGGESTIONS = [
    "¿Cuántos puntos da la montada?",
    "¿Qué vale un raspado?",
    "¿Cuándo se da una ventaja?",
]

st.markdown('<div class="suggest-title">Consultas frecuentes</div>', unsafe_allow_html=True)
cols = st.columns(len(SUGGESTIONS))
suggested_question = None

# Crear los botones en línea
for col, text in zip(cols, SUGGESTIONS):
    if col.button(text, use_container_width=True, key=f"sug-{text}"):
        suggested_question = text

# Definir la pregunta final (ya sea escrita o clickeada)
pregunta_final = suggested_question if suggested_question else (question.strip() if submitted else "")

# ---------------------------------------------------------------------------
# Inicialización de Groq y Panel Lateral de Hiperparámetros (Sidebar)
# ---------------------------------------------------------------------------
cliente_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

with st.sidebar:
    st.markdown("## ⚙️ Panel de Control RAG")
    st.caption("Configuración en tiempo real del pipeline de arbitraje")
    
    modelo_seleccionado = st.selectbox(
        "Motor LLM (Inferencia)",
        options=["Google Gemini Flash", "Groq (Llama 3.3 70B Versatile)"],
        index=0,
        help="Permite comparar latencia, estilo de respuesta y razonamiento entre diferentes arquitecturas."
    )
    
    top_k = st.slider(
        "Fragmentos a recuperar (Top-K)",
        min_value=1,
        max_value=6,
        value=3,
        step=1,
        help="Número de fragmentos semánticamente más cercanos que ChromaDB inyectará al prompt."
    )
    
    modo_arbitro = st.radio(
        "Modo del Veredicto",
        options=[
            "Oficial de Mesa (Estricto)", 
            "Formador Arbitral (Explicativo)",
            "Resolución de Escenario (Paso a paso)"
        ],
        index=0,
        help="Estricto: directo al grano. Formador: pedagógico. Escenario: analiza jugadas complejas y calcula el marcador Atleta A vs B."
    )
    # --- Filtro Reglamentario por Contexto ---
    st.markdown("### 🥋 Contexto del Combate")
    
    modalidad = st.selectbox(
        "Modalidad",
        ["Gi (Con Kimono)", "No-Gi (Sin Kimono)"]
    )
    
    cinturon = st.selectbox(
        "Rango del Atleta",
        ["Blanco", "Azul", "Morado", "Marrón", "Negro"]
    )
    
    edad = st.selectbox(
        "Categoría",
        ["Adulto / Máster", "Infantil (Menor de 15)", "Juvenil (16-17 años)"]
    )

    idioma = st.selectbox(
        "🌐 Idioma / Language", 
        ["Español", "English", "Português"]
    )
    
    st.markdown("---")
    st.markdown("### 📋 Ficha Técnica Activa")
    motor_nombre = "Gemini Flash" if "Gemini" in modelo_seleccionado else "Llama 3.3 70B (Groq)"
    st.markdown(f"""
    * **LLM en uso:** `{motor_nombre}`
    * **Top-K Chunks:** `{top_k}`
    * **Vector Store:** ChromaDB (Persistente)
    * **Modelo Embeddings:** `all-MiniLM-L6-v2`
    * **Reglamento:** IBJJF Oficial v6.1
    """)
    
    if st.button("🔄 Reiniciar Consulta", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------------
# Lógica de Ejecución RAG
# ---------------------------------------------------------------------------
if pregunta_final:
    placeholder = st.empty()
    
    placeholder.markdown(
        '<div class="loading"><div class="spinner"></div>'
        "<span>Auditando el reglamento oficial con IA...</span></div>",
        unsafe_allow_html=True,
    )
    
    # 1. Búsqueda vectorial
    t0_busqueda = time.time()
    resultados = coleccion.query(
        query_texts=[pregunta_final], 
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    t_busqueda_ms = (time.time() - t0_busqueda) * 1000
    
    contexto_extraido = "\n\n".join(resultados["documents"][0])
    
    paginas_numeros = sorted(list({
        int(meta["pagina"]) for meta in resultados["metadatas"][0] if meta and "pagina" in meta
    }))
    texto_paginas = f"Pág. {', '.join(str(p) for p in paginas_numeros)}" if paginas_numeros else "Reglamento General"
    
    # 2. Configuración del prompt
    if "Estricto" in modo_arbitro:
        instruccion_estilo = (
            "Sé extremadamente directo, conciso y normativo. Dictamina puntos, ventajas, descalificaciones "
            "o requisitos sin preámbulos. Máximo 3 o 4 viñetas técnicas."
        )
        badge_titulo = "Veredicto Oficial"
    elif "Escenario" in modo_arbitro:
        instruccion_estilo = (
            "Actúa como juez de mesa evaluando una secuencia de combate. Analiza cronológicamente la jugada, "
            "evalúa los tiempos de estabilización (3 segundos) y calcula el marcador final para 'Atleta A' y 'Atleta B'. "
            "Desglosa los puntos, ventajas o penalizaciones de cada uno paso a paso basándote en la narrativa."
        )
        badge_titulo = "Análisis de Jugada"
    else:
        instruccion_estilo = (
            "Adopta un enfoque didáctico y pedagógico. Explica con claridad la decisión reglamentaria, "
            "el criterio de seguridad detrás de la norma y las posibles excepciones o situaciones límite."
        )
        badge_titulo = "Criterio Formativo"
    
    prompt = f"""
    Eres un árbitro experto de Jiu-Jitsu Brasileño de la IBJJF.
    DEBES REDACTAR TU RESPUESTA OBLIGATORIAMENTE EN ESTE IDIOMA: {idioma}. 
    Responde a la pregunta basándote ÚNICAMENTE en el reglamento proporcionado. 
    {instruccion_estilo}
    
    CONTEXTO DEL COMBATE:
    Evalúa la legalidad de la acción o la regla aplicando las restricciones específicas para:
    - Modalidad: {modalidad}
    - Rango/Cinturón: {cinturon}
    - Categoría de Edad: {edad}
    
    Usa listas HTML (<ul><li>) o etiquetas de negrita (<strong>) para estructurar tu respuesta de forma muy limpia. No uses markdown con asteriscos (*).
    
    REGLAMENTO:
    {contexto_extraido}
    
    PREGUNTA: {pregunta_final}
    """
    
    # 3. Inferencia
    texto_respuesta = ""
    t_llm_s = 0.0
    exito = False
    mensaje_error = ""
    
    try:
        t0_llm = time.time()
        
        if "Gemini" in modelo_seleccionado:
            ultimo_error = ""
            for intento in range(3):
                try:
                    res = client.models.generate_content(
                        model='gemini-flash-latest', # Restaurado a tu versión original
                        contents=prompt
                    )
                    texto_respuesta = res.text
                    exito = True
                    break
                except Exception as err_gemini:
                    ultimo_error = str(err_gemini)
                    time.sleep(1.5)
            
            # Si falla las 3 veces, forzamos a que muestre el error real
            if not exito:
                raise Exception(f"Fallo en Gemini: {ultimo_error}")

        else:
            # Llamada a Groq con el modelo universal estable
            res = cliente_groq.chat.completions.create(
                model="qwen/qwen3.8-27b", 
                messages=[
                    {"role": "system", "content": "Eres un árbitro oficial de Jiu-Jitsu Brasileño de la IBJJF."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            texto_respuesta = res.choices[0].message.content
            exito = True
            
        t_llm_s = time.time() - t0_llm

    except Exception as e:
        exito = False
        mensaje_error = str(e)

    # 4. Renderizado
    if exito:
        safe_q = html.escape(pregunta_final)
        resultado_html = f"""
        <div class="result">
            <div class="result-head">
                <span class="badge"><span class="dot"></span>{badge_titulo}</span>
                <span class="meta">{modelo_seleccionado.split()[0]} · {texto_paginas}</span>
            </div>
            <div class="question">“{safe_q}”</div>
            <div class="respuesta-ia">
                {texto_respuesta}
            </div>
            <div class="source">Fuente: Libro de Reglas Oficial IBJJF ({texto_paginas}). Decisión orientativa.</div>
        </div>
        """
        placeholder.markdown(resultado_html, unsafe_allow_html=True)
        
        # 5. Panel de Transparencia RAG
        with st.expander("🔍 Auditoría Técnica RAG (Explainability & Telemetría)"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Búsqueda ChromaDB", f"{t_busqueda_ms:.1f} ms")
            c2.metric("Inferencia LLM", f"{t_llm_s:.2f} s")
            c3.metric("Top-K Fragmentos", f"{top_k}")
            c4.metric("Motor Inferencia", modelo_seleccionado.split()[0])
            
            st.markdown("#### Fragmentos originales recuperados de la Base Vectorial:")
            
            docs = resultados["documents"][0]
            metas = resultados["metadatas"][0]
            distancias = resultados["distances"][0] if "distances" in resultados and resultados["distances"] else [None] * len(docs)
            
            for i, (doc, meta, dist) in enumerate(zip(docs, metas, distancias), start=1):
                pag = meta.get("pagina", "N/A") if meta else "N/A"
                info_dist = f" | Distancia semántica: `{dist:.4f}`" if dist is not None else ""
                st.markdown(f"**Fragmento #{i}** — **Página {pag}**{info_dist}")
                st.info(doc)
    else:
        error_html = f"""
        <div class="result" style="border-color: #ef4444;">
            <div class="result-head">
                <span class="badge" style="background: #ef4444; color: white;">❌ Error de Inferencia</span>
            </div>
            <div class="respuesta-ia" style="color: #fca5a5; font-size: 0.95rem;">
                No fue posible conectar con el motor seleccionado.<br><br>
                <strong>Detalle técnico:</strong> <code>{html.escape(mensaje_error)}</code>
            </div>
        </div>
        """
        placeholder.markdown(error_html, unsafe_allow_html=True)
