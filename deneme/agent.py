import json
import logging
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
3. Örnek Verileri (Sample Data) analiz ederek tarih formatlarına (YYYY-MM-DD gibi) ve departman/ürün isimlerine tam uyum sağla. Şemada var olmayan HİÇBİR SÜTUN veya TABLO UYDURMA.
4. Tablo birleştirirken (JOIN) şemada belirtilen Foreign Key (Yabancı Anahtar) ilişkilerini kullan.
5. Çıktın KESİNLİKLE VE SADECE geçerli bir JSON objesi olmalıdır. Markdown veya ek metin ekleme.
6. Eğer soruyu cevaplamak için gereken tablolar yukarıdaki şemada yoksa, uydurma!
7. SOHBET KURALI: Detaysız veya veritabanı dışı sorularda sql alanını BOŞ bırak. Sadece "reasoning" alanına ona kibarca ne istediğini soran bir yanıt yaz.
8. BAĞLAM KURALI: Aşağıdaki konuşma geçmişini dikkate alarak kullanıcının ne demek istediğini anla. "bunu", "onu", "öncekini" gibi ifadeler önceki konuşmaya atıfta bulunuyor olabilir.

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

def generate_sql_and_chart(query: str, vectorstore, llm_model="llama3", max_retries=3, chat_history: list = []):
    from rag_schema import get_relevant_schema
    # Ollama'yı JSON formatına zorluyoruz, böylece ayrıştırması çok kolay oluyor.
    llm = Ollama(model=llm_model, format="json", temperature=0) 
    
    # Soruyla alakalı tabloları getir (k=5 yaparak tüm küçük şemayı kapsıyoruz)
    filtered_schema = get_relevant_schema(query, vectorstore, k=5)
    current_query = query

    # Konuşma geçmişini okunabilir metne çevir
    history_text = "(Henüz geçmiş yok)"
    if chat_history:
        lines = []
        for msg in chat_history[-10:]:  # Son 10 mesajı al, token tasarrufu
            role = "Kullanıcı" if msg.get("role") == "user" else "Asistan"
            lines.append(f"{role}: {msg.get('content', '')}")
        history_text = "\n".join(lines)
        
    for attempt in range(max_retries):
        prompt = AGENT_SYSTEM_PROMPT.format(
            filtered_schema=filtered_schema,
            question=current_query,
            chat_history=history_text
        )
        logger.info(f"LLM'e sorgu gönderiliyor (Deneme {attempt+1}/{max_retries})")
        
        try:
            response = llm.invoke(prompt)
            data = json.loads(response)
            
            reasoning = data.get("reasoning", "Belirtilmemiş.")
            sql = data.get("sql", "")
            chart_type = data.get("chart_type", "table")
            
            if not sql or sql.strip() == "":
                logger.info(f"Yapay Zeka Sohbet Yanıtı: {reasoning}")
                # SQL üretmemiş, muhtemelen sohbet ediyor veya eksik bilgi var.
                return {
                    "success": True,
                    "is_chat": True,
                    "message": reasoning
                }
            
            logger.info(f"AI Düşüncesi: {reasoning}")
            logger.info(f"Üretilen SQL: {sql}")
            
            # Üretilen SQL'i veritabanında çalıştırıyoruz
            result = execute_query(sql)
            
            if result["success"]:
                logger.info("SQL başarıyla çalıştı ve veriler çekildi.")
                return {
                    "sql": sql,
                    "reasoning": reasoning,
                    "chart_type": chart_type,
                    "data": result["data"],
                    "columns": result["columns"],
                    "success": True,
                    "attempts": attempt + 1
                }
            else:
                db_error = result["error"]
                logger.warning(f"SQL Çalıştırma Hatası: {db_error}")
                # Hata Düzeltme Döngüsü (Self-Correction)
                current_query = f"{query}\n\nÖnceki denemende şu mantığı yürüttün: '{reasoning}'\nAncak ürettiğin SQL: {sql}\nBu SQL çalışmadı ve veritabanı (SQLite) şu hatayı verdi: '{db_error}'. Lütfen hatanı fark et (özellikle SQLite standartlarına uyup uymadığını kontrol et) ve yeni, tamamen doğru bir JSON üret."
                
        except json.JSONDecodeError as e:
            logger.warning(f"LLM geçerli JSON dönmedi: {e}")
            current_query = f"{query}\n\nLütfen SADECE geçerli bir JSON objesi döndür, markdown veya ek metin kullanma."
        except Exception as e:
            logger.error(f"Beklenmeyen Hata: {str(e)}")
            return {"success": False, "error": str(e)}
            
    return {
        "success": False, 
        "error": "Yapay zeka maksimum deneme sayısına ulaştı ancak geçerli bir SQL sorgusu üretemedi."
    }
