import json
import logging
import asyncio
from langchain_community.llms import Ollama
from database import execute_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """
Sen uzman bir SQL ve Veri Analizi asistanısın. AYNI ZAMANDA BİR SQLITE UZMANISIN.
Aşağıdaki tabloları (veritabanı şemasını) ve her tablodan sunulan ÖRNEK VERİLERİ (Sample Data) kullanarak kullanıcının sorduğu soruya uygun, ÇALIŞABİLİR ve GÜVENLİ bir SQLite sorgusu (SELECT) üretmelisin.

Alakalı Veritabanı Şeması ve Veri İçeriği:
{filtered_schema}

KURALLAR:
1. SADECE "SELECT" sorgusu üret. INSERT, UPDATE, DELETE veya DROP kesinlikle yasaktır.
2. DİKKAT: Veritabanımız SQLITE'dır. Asla PostgreSQL, SQL Server veya MySQL fonksiyonları kullanma! (Örneğin DATE_TRUNC, YEAR(), MONTH() gibi fonksiyonlar YASAKTIR. Tarih işlemleri için her zaman SQLite'ın strftime('%Y-%m', date) fonksiyonunu kullan).
3. KRİTİK KURAL — SÜTUN DOĞRULUĞU: Yukarıdaki şemada hangi sütunun hangi tabloda olduğunu çok dikkatli oku. Bir tablodan sütun kullanmadan önce o sütunun o tabloda VAR OLDUĞUNU şemadan doğrula. Şemada görünmeyen HİÇBİR sütunu kesinlikle kullanma.
4. Örnek Verileri (Sample Data) analiz ederek tarih formatlarına (YYYY-MM-DD gibi) ve departman/ürün isimlerine tam uyum sağla.
5. Tablo birleştirirken (JOIN) şemada belirtilen Foreign Key (Yabancı Anahtar) ilişkilerini kullan.
6. Çıktın KESİNLİKLE VE SADECE geçerli bir JSON objesi olmalıdır. Markdown veya ek metin ekleme.
7. Eğer soruyu cevaplamak için gereken tablolar yukarıdaki şemada yoksa, uydurma!
8. SOHBET KURALI: Detaysız veya veritabanı dışı sorularda sql alanını BOŞ bırak. Sadece "reasoning" alanına ona kibarca ne istediğini soran bir yanıt yaz.
9. BAĞLAM KURALI: Aşağıdaki konuşma geçmişini dikkate alarak kullanıcının ne demek istediğini anla. "bunu", "onu", "öncekini" gibi ifadeler önceki konuşmaya atıfta bulunuyor olabilir.

Konuşma Geçmişi (en yeni en altta):
{chat_history}

Gereken JSON Şablonu:
{{
  "reasoning": "Kullanıcının isteğini yerine getirmek için hangi tabloları ve hangi sütunları nasıl kullanacağımı burada adım adım açıklıyorum...",
  "sql": "SELECT ...",
  "chart_type": "bar"
}}

Kullanıcı Sorusu: {question}
"""

VALIDATOR_PROMPT = """
Sen bir SQL sonucu denetçisisin. Kullanıcının sorusuna, çalıştırılan SQL'e ve dönen sonuca bakarak sonucun mantıksal olarak doğru olup olmadığını değerlendir.

Kullanıcı Sorusu: {question}

Çalıştırılan SQL:
{sql}

Dönen Sonuç ({row_count} satır):
{sample_rows}

KONTROL LİSTESİ:
- Kullanıcı N adet sonuç istediyse (örn. "top 5", "en çok 3"), tam o kadar satır geldi mi?
- Sonuçtaki sütun isimleri soruyla mantıklı eşleşiyor mu?
- Boş sonuç döndüyse ve veri olması gerekiyorsa bu bir hata mı?
- JOIN koşulları doğru tablolar arası mı kurulmuş?

Sadece aşağıdaki JSON formatında yanıt ver:
{{
  "valid": true,
  "issue": null
}}
veya
{{
  "valid": false,
  "issue": "Sorunun kısa açıklaması. Kullanıcı 5 ürün istedi ama 3 satır döndü gibi."
}}
"""


async def _validate_result(question: str, sql: str, data: list, llm, loop) -> tuple:
    """
    LLM'e sonucu denetletir. (is_valid: bool, issue: str) döner.
    Validator kendisi hata verirse sonucu geçerli kabul ederiz (fail-open).
    """
    sample_rows = json.dumps(data[:5], ensure_ascii=False, indent=2)
    prompt = VALIDATOR_PROMPT.format(
        question=question,
        sql=sql,
        row_count=len(data),
        sample_rows=sample_rows,
    )
    try:
        response = await loop.run_in_executor(None, llm.invoke, prompt)
        verdict = json.loads(response)
        is_valid = verdict.get("valid", True)
        issue = verdict.get("issue") or ""
        logger.info(f"Validator kararı: valid={is_valid} | issue={issue or '-'}")
        return is_valid, issue
    except Exception as e:
        logger.warning(f"Validator çalışamadı, sonuç kabul edildi: {e}")
        return True, ""


async def generate_sql_and_chart(query: str, vectorstore, llm_model="llama3", max_retries=5, chat_history: list = []):
    from rag_schema import get_relevant_schema
    llm = Ollama(model=llm_model, format="json", temperature=0)

    filtered_schema = get_relevant_schema(query, vectorstore, k=5)
    current_query = query

    history_text = "(Henüz geçmiş yok)"
    if chat_history:
        lines = []
        for msg in chat_history[-10:]:
            role = "Kullanıcı" if msg.get("role") == "user" else "Asistan"
            lines.append(f"{role}: {msg.get('content', '')}")
        history_text = "\n".join(lines)

    loop = asyncio.get_running_loop()
    last_error = "Bilinmeyen hata."
    last_sql = ""

    for attempt in range(max_retries):
        prompt = AGENT_SYSTEM_PROMPT.format(
            filtered_schema=filtered_schema,
            question=current_query,
            chat_history=history_text,
        )
        logger.info(f"LLM'e sorgu gönderiliyor (Deneme {attempt+1}/{max_retries})")

        try:
            response = await loop.run_in_executor(None, llm.invoke, prompt)
            data = json.loads(response)

            reasoning = data.get("reasoning", "Belirtilmemiş.")
            sql = data.get("sql", "")
            chart_type = data.get("chart_type", "table")

            if not sql or sql.strip() == "":
                logger.info(f"Yapay Zeka Sohbet Yanıtı: {reasoning}")
                return {"success": True, "is_chat": True, "message": reasoning}

            last_sql = sql
            logger.info(f"AI Düşüncesi: {reasoning}")
            logger.info(f"Üretilen SQL: {sql}")

            result = execute_query(sql)

            if not result["success"]:
                last_error = result["error"]
                logger.warning(f"SQL Çalıştırma Hatası (Deneme {attempt+1}): {last_error}")
                current_query = (
                    f"{query}\n\n"
                    f"Önceki denemende şu mantığı yürüttün: '{reasoning}'\n"
                    f"Ancak ürettiğin SQL:\n{sql}\n"
                    f"Bu SQL çalışmadı. SQLite hatası: '{last_error}'.\n"
                    f"Lütfen SQLite standartlarına tam uygun, çalışabilir yeni bir JSON üret."
                )
                continue

            # SQL çalıştı — şimdi sonucu denetle
            is_valid, issue = await _validate_result(query, sql, result["data"], llm, loop)

            if not is_valid:
                last_error = f"Sonuç doğrulama başarısız: {issue}"
                logger.warning(f"Validator reddi (Deneme {attempt+1}): {issue}")
                current_query = (
                    f"{query}\n\n"
                    f"Önceki denemende şu SQL'i ürettin:\n{sql}\n"
                    f"SQL hatasız çalıştı ancak sonuç yanlış: '{issue}'.\n"
                    f"Lütfen bu mantık hatasını düzelterek yeni bir JSON üret."
                )
                continue

            logger.info("SQL ve sonuç doğrulama geçti. Veri döndürülüyor.")
            return {
                "sql": sql,
                "reasoning": reasoning,
                "chart_type": chart_type,
                "data": result["data"],
                "columns": result["columns"],
                "success": True,
                "attempts": attempt + 1,
            }

        except json.JSONDecodeError as e:
            last_error = f"LLM geçersiz JSON döndürdü: {e}"
            logger.warning(last_error)
            current_query = f"{query}\n\nLütfen SADECE geçerli bir JSON objesi döndür, markdown veya ek metin kullanma."
        except Exception as e:
            logger.error(f"Beklenmeyen Hata: {str(e)}")
            return {"success": False, "error": str(e)}

    return {
        "success": False,
        "error": (
            f"{max_retries} denemede de doğru sonuç üretilemedi.\n"
            f"Son SQL: {last_sql}\n"
            f"Son sorun: {last_error}"
        ),
    }
