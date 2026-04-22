import os
import sqlite3
import pandas as pd
from fastapi.testclient import TestClient
from main import app, startup_event
import asyncio

def run_e2e():
    print("\n[+] E2E TEST BASLIYOR...\n")
    # 1. Create a brand new mock HR database
    hr_db_path = "test_hr.sqlite"
    if os.path.exists(hr_db_path):
        os.remove(hr_db_path)

    conn = sqlite3.connect(hr_db_path)
    df_emp = pd.DataFrame({'emp_id': [1,2,3], 'fullname': ['Ali Kaan', 'Ayse Demir', 'Veli Guc'], 'salary': [5000, 7000, 4500]})
    df_emp.to_sql('employees', conn, index=False)
    conn.close()

    # 2. Run app startup
    asyncio.run(startup_event())

    # 3. Use client
    client = TestClient(app)

    print("\n--- 1. VARSAYILAN SEMA (Ecommerce) ---")
    res1 = client.get("/api/schema")
    print(str(res1.json()["schema_json"])[:150] + "...\n")

    print("--- 2. YENI DB YUKLEME (HR/Insan Kaynaklari) ---")
    with open(hr_db_path, "rb") as f:
        res2 = client.post("/api/upload_db", files={"file": ("test_hr.sqlite", f, "application/octet-stream")})
    print("Upload status:", res2.json(), "\n")

    print("--- 3. YENI SEMA (HR - RAG test) ---")
    res3 = client.get("/api/schema")
    print(str(res3.json()["schema_json"])[:150] + "...\n")

    print("--- 4. YENI DB UZERINDEN AI SQL SORGUSU ---")
    res4 = client.post("/api/generate_sql", json={"query": "Maasi 6000den az olan calisanlari ve maaslarini goster"})
    data = res4.json()
    print("AI Success Flag:", data.get("success"))
    if data.get("success"):
        print("Uretilen SQL:", data.get("sql"))
        print("Tablo Satirlari:", data.get("data"))
    else:
        print("AI ERROR:", data.get("error"))

    print("\n[+] E2E TEST TAMAMLANDI.\n")

if __name__ == "__main__":
    run_e2e()
