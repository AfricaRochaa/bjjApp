import chromadb
import fitz
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Conectar a tu base de datos existente
cliente_chroma = chromadb.PersistentClient(path="./bd_vectorial")

# Configurar el modelo multilingüe para que coincida con la BD
ef_multilingue = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

coleccion = cliente_chroma.get_collection(
    name="reglas_bjj",
    embedding_function=ef_multilingue
)

# 2. Ruta de tu documento
ruta_pdf = "./documentos/uniform.pdf"

print("Abriendo el documento de Reglas de Uniforme con PyMuPDF...")

# Configurar el mismo cortador que en el indexador principal
splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=180,
    separators=["\n\n", "\n", ". ", " ", ""]
)

documentos = []
metadatos = []
ids = []

# 3. Extraer el texto y CORTARLO antes de guardarlo
try:
    doc = fitz.open(ruta_pdf)
    for i, pagina in enumerate(doc):
        texto = pagina.get_text() 
        if texto and texto.strip():
            # Cortamos el texto de la página en trozos manejables
            bloques = splitter.split_text(texto)
            for bloque in bloques:
                documentos.append(bloque)
                metadatos.append({"pagina": i + 1, "fuente": "Reglas de Uniforme IBJJF"})
                ids.append(f"uniform_frag_{contador}")
                contador += 1
            
    # 4. Inyectar todo en ChromaDB
    if documentos:
        print(f"Inyectando {len(documentos)} fragmentos en la base vectorial...")
        coleccion.add(
            documents=documentos,
            metadatas=metadatos,
            ids=ids
        )
        print("✅ ¡Éxito! Las Reglas de Uniforme se han fusionado correctamente.")
    else:
        print("❌ Error: Sigue sin haber texto. El PDF está hecho 100% de imágenes escaneadas.")
except Exception as e:
    print(f"Error al abrir el archivo: {e}")