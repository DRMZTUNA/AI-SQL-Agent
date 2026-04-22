from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import shutil

from database import setup_mock_database, set_current_db_path, get_database_schema, get_clean_schema_json, execute_query
from rag_schema import initialize_schema_rag
from agent import generate_sql_and_chart

# Eğer klasör yoksa oluşturalım
if not os.path.exists("static"):
    os.makedirs("static")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

vectorstore = None

@app.on_event("startup")
async def startup_event():
    global vectorstore
    print("Sistem başlatılıyor. Veritabanı hazırlanıyor...")
    setup_mock_database()
    try:
        print("RAG ve Ollama baglantisi kuruluyor...")
        vectorstore = initialize_schema_rag(model_name="llama3")
        print("[OK] Sistem tam olarak hazir! RAG aktif.")
    except Exception as e:
        vectorstore = None
        print(f"[UYARI] RAG baslatılamadı: {e}")
        print("   -> Ollama servisi calismiyor olabilir.")
        print("   -> Sunucu yine de calisiyor, ancak /api/generate_sql endpoint'i hata verecek.")
        print("   -> Cozum: 'ollama serve' komutunu calistirin, ardindan sunucuyu yeniden baslatın.")

class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, Any]]] = []

class SqlRunRequest(BaseModel):
    sql: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/schema")
async def api_get_schema():
    return {"schema_json": get_clean_schema_json()}

@app.post("/api/upload_db")
async def api_upload_db(file: UploadFile = File(...)):
    global vectorstore
    if not os.path.exists("databases"):
        os.makedirs("databases")
        
    file_path = f"databases/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    set_current_db_path(file_path)
    
    try:
        print(f"Yeni DB yuklendi: {file_path}, RAG guncelleniyor...")
        # Yeni veritabanına göre ChromaDB'yi ezerek baştan oluşturacak
        vectorstore = initialize_schema_rag(model_name="llama3")
        return {"success": True, "message": "Veritabani basariyla yuklendi ve RAG senkronize edildi."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/generate_sql")
async def generate_sql(request: QueryRequest):
    global vectorstore
    if not vectorstore:
        raise HTTPException(
            status_code=503,
            detail="RAG servisi baslatılamadı. Ollama calısmıyor. Lutfen 'ollama serve' komutunu calistirin ve sunucuyu yeniden baslatın."
        )
        
    try:
        result = generate_sql_and_chart(
            request.query,
            vectorstore,
            llm_model="llama3",
            max_retries=3,
            chat_history=request.chat_history or []
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/run_sql")
async def run_sql(request: SqlRunRequest):
    """Kullanıcının düzenlediği SQL'i doğrudan çalıştırır (agent atlanır)."""
    sql = request.sql.strip()
    # Güvenlik: sadece SELECT izni
    if not sql.upper().startswith("SELECT"):
        return {"success": False, "error": "Güvenlik ihlali: Yalnızca SELECT sorguları çalıştırılabilir."}
    try:
        result = execute_query(sql)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
