# 🚀 AI SQL Agent: Akıllı Veri Analiz ve Raporlama Platformu

AI SQL Agent, doğal dil sorgularını doğrudan çalıştırılabilir ve optimize edilmiş SQL sorgularına dönüştüren, yerel bir LLM (**Ollama**) ve **RAG** (Retrieval-Augmented Generation) mimarisi üzerine kurulu kurumsal seviyede bir asistan çözümüdür.

![Status](https://img.shields.io/badge/Status-Active-success)
![Version](https://img.shields.io/badge/Version-2.0.0-blue)
![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-orange)
![LLM](https://img.shields.io/badge/LLM-Ollama%20(Llama3)-red)

---

## 🏛️ Mimari Genel Bakış

Sistem, büyük veritabanı şemalarını (yüzlerce tablo) akıllıca yönetmek ve LLM'in bağlam (context) penceresini optimize etmek için tasarlanmıştır.

1.  **Vektör Veritabanı (ChromaDB)**: Tüm veritabanı şeması tablo bazlı vektörize edilir.
2.  **RAG Katmanı**: Kullanıcı sorusuna göre sadece *ilgili* tablo şemaları seçilir.
3.  **Prompt Katmanı**: Şema + Kurallar + Kullanıcı Sorusu birleştirilir.
4.  **Self-Correction**: SQL hatası alınırsa, hata mesajı ile birlikte LLM'e geri bildirim gönderilir ve sorgu otomatik düzeltilir.

---

## 🌟 Öne Çıkan Özellikler

-   ✅ **Zero-Data-Leak**: Tüm işlemler yerel sunucunuzda (Ollama) gerçekleşir.
-   ✅ **Şema Ölçeklenebilirliği**: RAG sayesinde devasa şemalarda bile düşük token tüketimi ve yüksek doğruluk.
-   ✅ **Hata Toleransı**: SQL sözdizimi hatalarını algılayıp kendi kendine düzeltebilen otonom yapı.
-   ✅ **Dinamik Veritabanı Yükleme**: Arayüzden `.sqlite` dosyası yükleyerek anında bağlam ve sistem değiştirme kabiliyeti.
-   ✅ **Kalıcı Sohbet Akışı (Feed)**: Sunucuyu yormadan, tarayıcı DOM manipülasyonu ile üretilen geçmiş mesajların tutulduğu yenilikçi UI.
-   ✅ **Otonom Sohbet Fallback**: Veritabanı ile ilgisiz veya eksik bilgi içeren sorularda SQL üretmeye zorlamak yerine, kullanıcıyla akıcı bir şekilde sohbet edebilme.
-   ✅ **Görsel Zeka**: Veriyi sadece tablo olarak değil, en uygun grafik tipiyle (Bar, Pie, Line) sunma.
-   ✅ **Şema Kaşifi & Dinamik Menü**: Yüklü veritabanının yapısını ağaç hiyerarşisinde gösterebilme ve animasyonlu gizlenebilir yan menü (Sidebar) ile tam ekran deneyimi.
-   ✅ **Akıcı Açılış Animasyonları**: UI bileşenlerinin (Header, Sidebar, Chat) akıcı ve gecikmeli (staggered) giriş animasyonları ile modern görünüm.
-   ✅ **Güvenlik Odaklı**: Sadece `SELECT` (Salt-Okunur) izni ile çalışan, DDL/DML komutlarını engelleyen katı filtreleme.
---

## 🔍 Gerçek Zamanlı Sistem Testi ve Dinamik Mimari Doğrulamaları

Uygulamanın mimarisi, statik kurallardan arındırılmış ve dinamik tak-çalıştır bir yaklaşımla dizayn edilmiştir. Sistemin bütünlüğü ve otonom davranış testleri başarıyla doğrulanmıştır:

1. **Dinamik Veritabanı Algılama (RAG Adaptasyonu):**
   - Uygulamaya (`database.py` veya SQLite URL üzerinden) yepyeni bir veritabanı verdiğiniz anda, RAG sistemi (`rag_schema.py`) arka planda otonom olarak çalışır. Yeni yapıyı, sütunları, yabancı anahtarları (ilişkileri) ve en önemlisi **örnek verileri analiz edip** yeni bir Chroma vektör hafızası oluşturur. Sistemi baştan kodlamanıza gerek kalmaz.
2. **Bağlam Filtreleme ve Anlama (Similarity Search):**
   - Senaryo dışı veya yeni yapıya özel bir soru sorulduğunda, sistem tüm veritabanını taramak yerine cümlenin niyetini analiz eder, hafızasındaki (ChromaDB) tablolardan yalnızca söz konusu spesifik soruyla eşleşenleri süzer.
3. **Anlık Prompt Adaptasyonu (Ollama Llama3 Entegrasyonu):**
   - Filtrelenmiş spesifik tablolar ve yapılar, Ollama'ya (yapay zeka modeline) anlık olarak "sadece bu tablolara dikkat et" direktifi ile aktarılır (`agent.py`). Model, daha önce hiç görmediği veri yapısını anında yorumlar ve soruya %100 uygun, hatasız bir SQL'i JSON formatında (grafik türüyle birlikte) geri döndürür. Eğer yazdığı SQL çalışmazsa, bunu kendi kendine analiz edip düzeltme (Self-Correction) otonomisine sahiptir.
4. **Kesintisiz Uçtan Uca Akış & UI:**
   - Üretilen SQL, backend üzerinde Pandas ile pürüzsüzce işlenir ve ön yüze dinamik veri nesnesi olarak gönderilir. Frontend (JavaScript), bu yapıları otomatik analiz edip bar, çizgi, veya pasta grafikleri haline (Chart.js) dönüştürür. Uçtan uca testlerde hiçbir senkronizasyon, RAG veya syntax hatasına rastlanmamıştır.

---

## 🛠️ Teknoloji Yığını

-   **Backend**: FastAPI, Python 3.10+
-   **AI Framework**: LangChain, Ollama
-   **Vector DB**: ChromaDB
-   **ORM/DB**: SQLAlchemy, Pandas, SQLite
-   **Frontend**: Vanilla JS, Chart.js, Glassmorphism CSS

---

## 📥 Kurulum ve Çalıştırma Rehberi (Adım Adım)

Sistemi ilk kez kuruyorsanız aşağıdaki adımları sırasıyla takip edin:

### 1. Python Sanal Ortamı Oluşturun (Önerilir)
Proje bağımlılıklarının sisteminizle çakışmaması için bir sanal ortam oluşturun:
```bash
python -m venv venv
# Windows için aktif etme:
.\venv\Scripts\activate
# Mac/Linux için aktif etme:
source venv/bin/activate
```

### 2. Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Yapay Zeka Modelini Hazırlayın (Ollama)
Sistemin beyni olan Ollama'yı kurmanız ve modeli indirmeniz gerekir:
1. [ollama.com](https://ollama.com) adresinden Ollama'yı indirin ve kurun.
2. Terminalden Ollama servisini başlatın: `ollama serve` (Zaten arka planda çalışıyorsa bu adımı geçin).
3. Llama 3 modelini bilgisayarınıza indirin:
```bash
ollama pull llama3
```

### 4. Uygulamayı Başlatın
Tüm hazırlıklar tamamlandığında backend sunucusunu ayağa kaldırın:
```bash
uvicorn main:app --reload
```
Uygulama başladığında otomatik olarak `ecommerce.sqlite` veritabanını oluşturacak ve şemayı vektör veritabanına (ChromaDB) gömecektir.

### 5. Arayüze Erişin
Tarayıcınızı açın ve şu adrese gidin:
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧪 Hızlı Test: Demo Modu
Eğer web arayüzüne girmeden sadece yapay zekanın SQL üretme kabiliyetini test etmek isterseniz:
```bash
python demo.py
```

---

## 🔌 ENTEGRASYON REHBERİ (Başka Projelere Dahil Etme)

Bu sistem modüler tasarımı sayesinde 3 farklı yöntemle mevcut projelerinize entegre edilebilir:

### 🅰️ Python Kütüphanesi Olarak Kullanım
Eğer mevcut bir Python projeniz varsa, agent yeteneklerini doğrudan import edebilirsiniz:

```python
from agent import generate_sql_and_chart
from rag_schema import initialize_schema_rag

# 1. Şemayı bir kez initialize edin
vectorstore = initialize_schema_rag(model_name="llama3")

# 2. Sorguyu çalıştırın
result = generate_sql_and_chart(
    query="Geçen ayın toplam satış grafiğini getir",
    vectorstore=vectorstore,
    llm_model="llama3"
)

if result["success"]:
    print(f"SQL: {result['sql']}")
    print(f"Veriler: {result['data']}")
```

### 🅱️ REST API Üzerinden Entegrasyon (Mikroservis)
Herhangi bir dildeki (Node.js, Go, PHP, Java) uygulamanızdan bu sistemi bir mikroservis gibi çağırabilirsiniz:

**Endpoint 1:** `POST /api/generate_sql` (Sorgu Üretme)
**Payload:**
```json
{
  "query": "En pahalı 5 ürünü listele"
}
```

**Endpoint 2:** `GET /api/schema` (Güncel Şemayı Çekme)
**Response:**
```json
{
  "schema_text": "Tablo: personnel\n - id(int)..."
}
```

**Endpoint 3:** `POST /api/upload_db` (Dinamik Veritabanı Yükleme ve RAG Eğitim Tetikleyicisi)
**Payload:** `multipart/form-data` (file: .sqlite dosyası)

### 🅱️ Farklı Veritabanlarına Bağlanma
Sistemi SQLite yerine kurumsal bir veritabanına bağlamak için `database.py` dosyasındaki connection string'i güncellemeniz yeterlidir:

```python
# PostgreSQL Örneği
DB_URL = "postgresql://user:password@localhost:5432/my_database"
engine = create_engine(DB_URL)
```

> [!TIP]
> **Schema Reflection**: Sistem otomatik olarak SQLAlchemy'nin `MetaData.reflect()` özelliğini kullanır. Yani veritabanı bağlantı dizesini değiştirdiğinizde, şema dökümantasyonu otomatik olarak güncellenir ve RAG sistemine dahil edilir.

---

## ⚙️ Gelişmiş Konfigürasyon

| Parametre | Dosya | Açıklama |
| :--- | :--- | :--- |
| `max_retries` | `agent.py` | Self-correction döngüsünün kaç kez deneyeceği (Default: 3) |
| `k-value` | `rag_schema.py` | LLM'e gönderilecek maksimum tablo sayısı (Default: 3) |
| `temperature` | `agent.py` | LLM'in yaratıcılık seviyesi (SQL için 0 önerilir) |
| `LIMIT 100` | `prompts.py` | Veritabanı güvenliği için varsayılan sonuç limiti |

---

## 🛡️ Güvenlik Katmanı

Bu sistem **"Security by Prompting"** ve **"Backend Validation"** prensiplerini birleştirir:
1.  **Prompt Seviyesi**: Sistem promptunda sadece SELECT sorgusu yapabileceği 5 farklı noktada vurgulanır.
2.  **Validation**: `execute_query` fonksiyonu öncesinde sorgu metni içinde yasaklı kelimeler (DROP, DELETE, TRUNCATE) taranabilir.
3.  **DB User**: Entegrasyon sırasında veritabanı kullanıcısının sadece **Read-Only** yetkisine sahip olması kritik önem taşır.

---

## 🗺️ Yol Haritası (Roadmap)

- [ ] Multi-Database (Aynı anda birden fazla DB sorgulama)
- [ ] Excel/CSV olarak rapor indirme özelliği
- [ ] Sesli komut (Speech-to-SQL) desteği
- [ ] Kullanıcı rol tabanlı tablo erişim kısıtlamaları

---

## 📄 Lisans
Bu proje MIT lisansı altındadır. İstediğiniz projede ticari veya kişisel amaçla kullanabilir, geliştirebilirsiniz.
