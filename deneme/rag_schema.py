import os
import time
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from database import get_database_schema

CHROMA_DIR = "./chroma_schema_db"

def initialize_schema_rag(model_name="llama3"):
    """
    Veritabanı şemasını çeker, tablo tablo ayırır ve ChromaDB'ye vektör olarak gömer.
    Çok tablolu büyük veritabanlarında RAG yapmak için bu yöntem en iyisidir.
    """
    
    # Windows'ta Chroma dosya kilitlenmelerini (WinError 32) önlemek için her yüklemede yeni klasör
    CHROMA_DIR = f"./chroma_schema_db_{int(time.time())}"
        
    schema_str = get_database_schema()
    tables = schema_str.split("Tablo: ")
    
    docs = []
    for table_text in tables:
        if not table_text.strip():
            continue
        # Tablo ismini ve içeriğini geri birleştiriyoruz
        full_table_text = "Tablo: " + table_text.strip()
        docs.append(Document(page_content=full_table_text))
        
    embeddings = OllamaEmbeddings(model=model_name)
    
    # Yeni temiz bir vectorstore oluşturuyoruz
    vectorstore = Chroma.from_documents(docs, embedding=embeddings, persist_directory=CHROMA_DIR)
    
    return vectorstore

def get_relevant_schema(query: str, vectorstore, k=2):
    """
    Kullanıcının sorusuna en yakın (ilgili) k adet tablo şemasını döndürür.
    """
    docs = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])

if __name__ == "__main__":
    print("Schema RAG başlatılıyor, Embeddings oluşturuluyor...")
    vs = initialize_schema_rag()
    print("Oluşturuldu. Test araması: 'satışlar nasıl'")
    print(get_relevant_schema("satışlar nasıl", vs))
