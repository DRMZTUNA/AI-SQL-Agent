"""
CLI demo — web arayüzü olmadan agent'ı terminalden test eder.
Kullanım: python demo.py
Opsiyonel: python demo.py "sorunuzu buraya yazın"
"""
import asyncio
import sys
import json
from database import setup_mock_database, set_current_db_path
from rag_schema import initialize_schema_rag
from agent import generate_sql_and_chart

DEFAULT_MODEL = "llama3"

TEST_QUERIES = [
    "En çok satış yapan 5 ürün hangileri?",
    "Departman bazında toplam satış miktarı nedir?",
    "Geçen ay kaç satış yapıldı?",
]


def print_separator():
    print("\n" + "─" * 60 + "\n")


async def run_query(query: str, vectorstore, model: str):
    print(f"❓ Sorgu   : {query}")
    print(f"🤖 Model   : {model}")
    print("⏳ İşleniyor...\n")

    result = await generate_sql_and_chart(
        query=query,
        vectorstore=vectorstore,
        llm_model=model,
        max_retries=5,
        chat_history=[],
    )

    if not result.get("success"):
        print(f"❌ Hata    : {result.get('error')}")
        return

    if result.get("is_chat"):
        print(f"💬 Yanıt   : {result.get('message')}")
        return

    print(f"✅ Başarılı  ({result.get('attempts', 1)} deneme)")
    print(f"📝 SQL      :\n   {result['sql']}\n")
    print(f"📊 Grafik   : {result.get('chart_type', 'table')}")
    print(f"📋 Sütunlar : {result['columns']}")
    print(f"📦 Sonuç    : {len(result['data'])} satır")

    for i, row in enumerate(result["data"][:10]):
        print(f"   {i+1:>2}. {row}")
    if len(result["data"]) > 10:
        print(f"   ... ve {len(result['data']) - 10} satır daha")


async def main():
    print_separator()
    print("🚀 AI SQL Agent — CLI Demo")
    print_separator()

    print("📂 Veritabanı hazırlanıyor...")
    setup_mock_database()
    set_current_db_path("ecommerce.sqlite")

    print("🔗 RAG ve Ollama bağlantısı kuruluyor...")
    try:
        vectorstore = initialize_schema_rag(model_name=DEFAULT_MODEL)
        print("✅ RAG hazır.\n")
    except Exception as e:
        print(f"❌ Ollama bağlantısı kurulamadı: {e}")
        print("   Çözüm: 'ollama serve' komutunu çalıştırın.")
        sys.exit(1)

    # Komut satırından sorgu verilmişse onu çalıştır
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print_separator()
        await run_query(query, vectorstore, DEFAULT_MODEL)
        print_separator()
        return

    # Yoksa hazır test sorgularını sırayla çalıştır
    for query in TEST_QUERIES:
        print_separator()
        await run_query(query, vectorstore, DEFAULT_MODEL)

    print_separator()
    print("✅ Demo tamamlandı.")
    print_separator()


if __name__ == "__main__":
    asyncio.run(main())
