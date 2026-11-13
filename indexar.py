import fitz
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Configurar el modelo multilingüe (Entiende Español e Inglés)
ef_multilingue = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# 2. Configuración de ChromaDB
cliente = chromadb.PersistentClient(path="./bd_vectorial")

# Reiniciar colección para evitar duplicados o mezclas
try:
    cliente.delete_collection("reglas_bjj")
    print("Colección anterior eliminada.")
except Exception:
    pass

# Crear la colección inyectando el modelo multilingüe
coleccion = cliente.create_collection(
    name="reglas_bjj", 
    embedding_function=ef_multilingue
)

# 3. Configuración del solapamiento
splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=180,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# 4. Lectura del PDF página a página con extracción de metadatos
ruta_pdf = "documentos/reglas.pdf" 
doc = fitz.open(ruta_pdf)

documentos = []
metadatos = []
ids = []
contador = 0

print(f"Indexando '{ruta_pdf}' con cerebro multilingüe... (esto tardará un poco más)")

for num_pagina, pagina in enumerate(doc, start=1):
    texto = pagina.get_text()
    if not texto or not texto.strip():
        continue
    
    # Cortar el texto de la página aplicando solapamiento
    bloques = splitter.split_text(texto)
    
    for bloque in bloques:
        documentos.append(bloque)
        metadatos.append({
            "pagina": num_pagina,
            "origen": "Libro de Reglas Oficial IBJJF"
        })
        ids.append(f"frag_{contador}")
        contador += 1

# 5. Guardar en la base de datos
coleccion.add(
    documents=documentos,
    metadatas=metadatos,
    ids=ids
)

print(f"Indexación completada: {len(documentos)} fragmentos guardados exitosamente.")