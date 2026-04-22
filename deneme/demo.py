from prompts import SQL_AGENT_SYSTEM_PROMPT

# Örnek bir veritabanı şeması (Örneğin bir e-ticaret veya depo sistemi olabilir)
DB_SCHEMA_MOCK = """
Tablo: personnel (Personel)
- id (INT, Primary Key)
- name (VARCHAR)
- department (VARCHAR)

Tablo: sales (Satışlar)
- id (INT, Primary Key)
- p_id (INT, Foreign Key -> personnel.id)
- amount (DECIMAL)
- date (DATE)

Tablo: products (Ürünler)
- id (INT, Primary Key)
- product_name (VARCHAR)
- stock_quantity (INT)
- price (DECIMAL)
"""

def generate_agent_prompt(schema_str: str) -> str:
    # Sisteme gönderilecek olan nihai promptu şema ile birleştirir.
    return SQL_AGENT_SYSTEM_PROMPT.format(database_schema=schema_str)

if __name__ == "__main__":
    print("-" * 50)
    print("[SYSTEM] SQL AGENT SYSTEM PROMPT OLUSTURULUYOR...")
    print("-" * 50)
    
    # 1. Aşama: Şema enjekte edilmiş System Prompt'u oluştur
    final_system_prompt = generate_agent_prompt(DB_SCHEMA_MOCK)
    print("Enjekte Edilmis System Prompt:\n")
    print(final_system_prompt)
    print("-" * 50)
    
    # 2. Aşama: Kullanıcı Senaryosu
    kullanici_sorusu = "Geçen ay en çok satış yapan 5 personeli getir."
    print(f"[USER] Kullanici Sorusu: {kullanici_sorusu}\n")
    
    # Simülasyon: Normalde bu noktada bir LLM'e final_system_prompt ve kullanici_sorusu gönderilir
    # İşte LLM'in (bizim agent'ın) döneceği varsayılan çıktı:
    agent_yaniti = "SELECT p.name AS Personel_Adi, SUM(s.amount) AS Toplam_Satis FROM sales s JOIN personnel p ON s.p_id = p.id WHERE s.date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND s.date < DATE_TRUNC('month', CURRENT_DATE) GROUP BY p.name ORDER BY Toplam_Satis DESC LIMIT 5;"
    
    print(f"[AGENT] SQL Agent Yaniti (Sadece SQL):\n{agent_yaniti}")
    print("-" * 50)
