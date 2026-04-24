import os
import time
import shutil
import glob
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from database import get_database_schema

CHROMA_DIR = "./chroma_schema_db"


def _cleanup_old_chroma_dirs(keep_latest: int = 1):
    """Eski chroma_schema_db_<timestamp> klasörlerini siler, en yeni `keep_latest` adedi korur."""
    dirs = sorted(glob.glob("./chroma_schema_db_*"))
    to_delete = dirs[:-keep_latest] if len(dirs) > keep_latest else []
    for d in to_delete:
        try:
            shutil.rmtree(d)
        except Exception as e:
            pass  # Kilitli klasörü zorla silmeye çalışmıyoruz (Windows uyumu)


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
    
    vectorstore = Chroma.from_documents(docs, embedding=embeddings, persist_directory=CHROMA_DIR)

    # Yeni klasör başarıyla oluşturulduktan sonra eskileri temizle
    _cleanup_old_chroma_dirs(keep_latest=1)

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
