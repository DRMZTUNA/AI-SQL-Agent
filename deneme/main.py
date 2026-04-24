from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import shutil
import csv
import io
import httpx
import sqlparse

from database import (
    setup_mock_database, set_current_db_path, get_clean_schema_json,
    execute_query, init_history_db, save_to_history, get_history
)
from rag_schema import initialize_schema_rag
from agent import generate_sql_and_chart

if not os.path.exists("static"):
    os.makedirs("static")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

vectorstore = None
OLLAMA_BASE_URL = "http://localhost:11434"


@app.on_event("startup")
async def startup_event():
    global vectorstore
    print("Sistem başlatılıyor. Veritabanı hazırlanıyor...")
    setup_mock_database()
    init_history_db()
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
    model_name: str = "llama3"


class SqlRunRequest(BaseModel):
    sql: str


class CsvExportRequest(BaseModel):
    columns: List[str]
    data: List[Dict[str, Any]]
    filename: str = "sorgu"


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
async def health_check():
    ollama_ok = False
    models = []
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                ollama_ok = True
                models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return {
        "rag": vectorstore is not None,
        "ollama": ollama_ok,
        "models": models,
    }


@app.get("/api/models")
async def get_models():
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                return {"success": True, "models": models}
    except Exception as e:
        return {"success": False, "models": ["llama3"], "error": str(e)}


@app.get("/api/schema")
async def api_get_schema():
    return {"schema_json": get_clean_schema_json()}


@app.get("/api/history")
async def api_get_history():
    return {"history": get_history(limit=20)}


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
        result = await generate_sql_and_chart(
            request.query,
            vectorstore,
            llm_model=request.model_name,
            max_retries=5,
            chat_history=request.chat_history or []
        )
        if result.get("success") and not result.get("is_chat") and result.get("sql"):
            save_to_history(request.query, result["sql"], result.get("chart_type", "table"))
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _validate_select_only(sql: str) -> Optional[str]:
    statements = sqlparse.parse(sql.strip())
    if not statements:
        return "Geçerli bir SQL ifadesi bulunamadı."

    for stmt in statements:
        if not stmt.get_type():
            continue
        if stmt.get_type() != "SELECT":
            return (
                f"Güvenlik ihlali: Yalnızca SELECT sorguları çalıştırılabilir. "
                f"'{stmt.get_type()}' ifadesi reddedildi."
            )

    meaningful = [s for s in statements if s.get_type()]
    if len(meaningful) > 1:
        return "Güvenlik ihlali: Tek seferde birden fazla SQL ifadesi çalıştırılamaz."

    return None


@app.post("/api/run_sql")
async def run_sql(request: SqlRunRequest):
    sql = request.sql.strip()
    error_msg = _validate_select_only(sql)
    if error_msg:
        return {"success": False, "error": error_msg}
    try:
        result = execute_query(sql)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/export_csv")
async def export_csv(request: CsvExportRequest):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(request.columns)
    for row in request.data:
        writer.writerow([row.get(c, "") for c in request.columns])
    output.seek(0)
    filename = request.filename.replace(" ", "_") + ".csv"
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),  # utf-8-sig = Excel BOM desteği
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
