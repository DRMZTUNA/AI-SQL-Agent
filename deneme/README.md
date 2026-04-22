# 🚀 AI SQL Agent — Akıllı Veri Analiz ve Raporlama Platformu

Doğal dil sorgularını, yerel bir LLM (**Ollama / Llama 3**) ve **RAG** (Retrieval-Augmented Generation) mimarisiyle doğrudan çalıştırılabilir, optimize edilmiş SQLite sorgularına dönüştüren kurumsal seviyede bir asistan.

![Status](https://img.shields.io/badge/Status-Active-success)
![Version](https://img.shields.io/badge/Version-2.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-orange)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%28Llama3%29-red)
![Framework](https://img.shields.io/badge/Backend-FastAPI-teal)

---

## 📋 İçindekiler

1. [Proje Özeti](#-proje-özeti)
2. [Mimari Genel Bakış](#-mimari-genel-bakış)
3. [Öne Çıkan Özellikler](#-öne-çıkan-özellikler)
4. [Proje Yapısı](#-proje-yapısı)
5. [Teknoloji Yığını](#️-teknoloji-yığını)
6. [Kurulum ve Çalıştırma](#-kurulum-ve-çalıştırma)
7. [API Referansı](#-api-referansı)
8. [Modül Açıklamaları](#-modül-açıklamaları)
9. [Entegrasyon Rehberi](#-entegrasyon-rehberi)
10. [Gelişmiş Konfigürasyon](#️-gelişmiş-konfigürasyon)
11. [Güvenlik Katmanı](#️-güvenlik-katmanı)
12. [Test ve Doğrulama](#-test-ve-doğrulama)
13. [Yol Haritası](#️-yol-haritası-roadmap)
14. [Lisans](#-lisans)

---

## 🎯 Proje Özeti

AI SQL Agent, teknik olmayan kullanıcıların bile bir veritabanına Türkçe soru sorarak anında grafiksel ve tablo bazlı raporlar alabilmesini sağlayan uçtan uca bir yapay zeka asistanıdır.

```
"Geçen ay en çok satan 5 ürün hangileri?"
        ↓
  [RAG: İlgili tablolar filtrelenir]
        ↓
  [Llama3: SELECT sorgusu üretilir]
        ↓
  [SQLite: Sorgu çalıştırılır]
        ↓
  [Frontend: Bar / Pie / Line grafiği]
```

Tüm işlem **yerel bilgisayarınızda** gerçekleşir — hiçbir veri dışarı çıkmaz.

---

## 🏛️ Mimari Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────┐
│                          KULLANICI ARAYÜZÜ                           │
│                  (Vanilla JS + Chart.js + CSS)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP (REST)
┌──────────────────────────────▼──────────────────────────────────────┐
│                          FastAPI Backend                              │
│   /api/generate_sql  │  /api/run_sql  │  /api/schema  │  /api/upload_db │
└──────┬───────────────────────┬────────────────────────┬─────────────┘
       │                       │                        │
┌──────▼──────┐   ┌────────────▼─────────┐   ┌────────▼────────────┐
│  agent.py   │   │    database.py        │   │   rag_schema.py      │
│             │   │                       │   │                      │
│ • LLM Sorgu │   │ • SQLAlchemy Engine   │   │ • Schema Extraction  │
│ • Self-Corr │   │ • execute_query()     │   │ • ChromaDB Embed     │
│ • Chat Fall │   │ • Schema Reflect      │   │ • Similarity Search  │
│ • History   │   │ • Mock DB Setup       │   │ • OllamaEmbeddings   │
└──────┬──────┘   └────────────┬──────────┘   └────────┬────────────┘
       │                       │                        │
       └───────────────────────┴────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Ollama (Llama3)    │
                    │  localhost:11434     │
                    └─────────────────────┘
```

### Veri Akışı (Adım Adım)

| Adım | Bileşen | İşlem |
|------|---------|-------|
| 1 | `rag_schema.py` | Veritabanı şeması + örnek veriler çekilir, tablolar ayrıştırılır |
| 2 | `ChromaDB` | Her tablo metni OllamaEmbeddings ile vektöre çevrilir |
| 3 | `rag_schema.py` | Kullanıcı sorusuna göre en yakın `k` tablo similarity search ile bulunur |
| 4 | `agent.py` | Filtrelenmiş şema + konuşma geçmişi + soru → Llama3'e gönderilir |
| 5 | `Llama3` | JSON formatında `{ reasoning, sql, chart_type }` döndürür |
| 6 | `database.py` | SQL çalıştırılır, hata varsa Self-Correction döngüsü başlar |
| 7 | Frontend | Veri tablosu + Chart.js grafiği render edilir |

---

## 🌟 Öne Çıkan Özellikler

| Özellik | Açıklama |
|---------|---------|
| 🔒 **Zero-Data-Leak** | Tüm AI işlemleri Ollama üzerinden yerel makinede çalışır |
| 📊 **Şema Ölçeklenebilirliği** | RAG sayesinde yüzlerce tablolu veritabanlarında düşük token tüketimi |
| 🔄 **Self-Correction** | SQL hatası alınırsa hata mesajı + önceki düşünce LLM'e geri bildirilir; otonom düzeltme |
| 🗄️ **Dinamik DB Yükleme** | Arayüzden `.sqlite` yükleyerek anında veritabanı ve RAG güncellenir |
| 💬 **Sohbet Geçmişi** | Son 10 mesaj konuşma bağlamı olarak korunur; "bunu", "öncekini" gibi atıflar desteklenir |
| 🤖 **Chat Fallback** | DB ile ilgisiz sorularda SQL üretmek yerine kullanıcıyla doğal dil sohbeti |
| 📈 **Görsel Zeka** | Bar, Pie, Line grafik tiplerinden en uygununu LLM seçer |
| 🌲 **Şema Kaşifi** | Ağaç hiyerarşisinde sidebar; yüklü DB yapısını interaktif görüntüleme |
| ✏️ **Düzenlenebilir SQL** | Üretilen sorgu editable alan üzerinden manuel değiştirip yeniden çalıştırılabilir |
| 📤 **CSV Dışa Aktarım** | Tablo sonuçlarını tek tıkla CSV olarak indir |
| 🎨 **Animasyonlu UI** | Glassmorphism tasarım; Header, Sidebar, Chat staggered giriş animasyonları |
| 🛡️ **Güvenlik Odaklı** | Sadece SELECT; DDL/DML prompt + backend katmanında çift engel |

---

## 📂 Proje Yapısı

```
deneme/
├── main.py              # FastAPI uygulama girişi; tüm endpoint'ler
├── agent.py             # LLM çağrısı, self-correction döngüsü, chat fallback
├── database.py          # SQLAlchemy engine, schema reflection, execute_query
├── rag_schema.py        # ChromaDB embedding, similarity search
├── prompts.py           # Alternatif/ek system prompt şablonları
├── demo.py              # Web arayüzü olmadan CLI test modu
├── test_e2e.py          # Uçtan uca otomasyon testleri
├── requirements.txt     # Python bağımlılıkları
├── ecommerce.sqlite     # Demo e-ticaret veritabanı (otomatik oluşturulur)
├── databases/           # Upload edilen kullanıcı veritabanları
├── static/
│   └── index.html       # Frontend (Vanilla JS + Chart.js)
└── chroma_schema_db_*/  # ChromaDB vektör depoları (her yüklemede yeni klasör)
```

---

## 🛠️ Teknoloji Yığını

### Backend
| Kütüphane | Sürüm | Kullanım |
|-----------|-------|---------|
| FastAPI | latest | REST API, dosya yükleme, HTML sunumu |
| Uvicorn | latest | ASGI sunucusu |
| Pydantic | v2+ | Request/Response model validasyonu |
| python-multipart | latest | Dosya upload desteği |

### AI / LLM
| Kütüphane | Sürüm | Kullanım |
|-----------|-------|---------|
| LangChain | latest | LLM orkestrasyon katmanı |
| langchain-community | latest | Ollama ve Chroma entegrasyonları |
| Ollama (Llama 3) | - | Yerel LLM; JSON format modu |
| ChromaDB | latest | Vektör veritabanı (embedding depo) |

### Veritabanı / Veri
| Kütüphane | Sürüm | Kullanım |
|-----------|-------|---------|
| SQLAlchemy | latest | ORM, schema reflection |
| Pandas | latest | SQL sonucu DataFrame → dict/CSV |
| SQLite | builtin | Varsayılan veritabanı motoru |

### Frontend
- **Vanilla JS** — Sıfır bağımlılık, DOM manipülasyonu
- **Chart.js** — Bar, Line, Pie dinamik grafik
- **Glassmorphism CSS** — Modern backdrop-filter tasarım
- **Google Fonts (Inter)** — Tipografi

---

## 📥 Kurulum ve Çalıştırma

### Ön Koşullar
- Python 3.10 veya üzeri
- [Ollama](https://ollama.com) yüklü ve çalışıyor olmalı

### 1. Sanal Ortam Oluşturun (Önerilir)

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 3. Ollama ve Llama 3 Modelini Hazırlayın

```bash
# Ollama'yı başlatın (arka planda çalışmıyorsa)
ollama serve

# Llama 3 modelini indirin (~4.7 GB, tek seferlik)
ollama pull llama3
```

> [!NOTE]
> Ollama varsayılan olarak `http://localhost:11434` adresinde çalışır.
> Model indirme işlemi internet bağlantı hızına göre birkaç dakika sürebilir.

### 4. Uygulamayı Başlatın

```bash
cd deneme
uvicorn main:app --reload
```

Uygulama ilk açılışta otomatik olarak:
- `ecommerce.sqlite` demo veritabanını oluşturur (ürünler, personel, satışlar)
- `rag_schema.py` üzerinden şemayı vektörize ederek ChromaDB'ye yükler

### 5. Tarayıcıdan Erişin

```
http://127.0.0.1:8000
```

---

## 🔌 API Referansı

### `GET /`
Ana arayüz HTML sayfasını döndürür.

---

### `GET /api/schema`
Yüklü veritabanının şemasını ağaç (JSON) formatında döndürür.

**Response:**
```json
{
  "schema_json": {
    "products": ["id [INTEGER] (PK)", "product_name [TEXT]", "price [FLOAT]"],
    "sales": ["id [INTEGER] (PK)", "p_id [INTEGER] (FK -> personnel.id)", "amount [FLOAT]", "date [TEXT]"]
  }
}
```

---

### `POST /api/generate_sql`
Doğal dil sorusunu SQL'e çevirir, çalıştırır ve grafik verisiyle döndürür.

**Request:**
```json
{
  "query": "Geçen ayın toplam satışını getir",
  "chat_history": [
    { "role": "user", "content": "Satış tablosu nedir?" },
    { "role": "assistant", "content": "Satış tablosu..." }
  ]
}
```

**Response (başarılı SQL):**
```json
{
  "success": true,
  "sql": "SELECT strftime('%Y-%m', date) AS Ay, SUM(amount) AS Toplam FROM sales GROUP BY Ay",
  "reasoning": "Kullanıcı aylık toplam satış istiyor. sales tablosundan...",
  "chart_type": "bar",
  "data": [{ "Ay": "2026-03", "Toplam": 125000 }],
  "columns": ["Ay", "Toplam"],
  "attempts": 1
}
```

**Response (sohbet fallback):**
```json
{
  "success": true,
  "is_chat": true,
  "message": "Bu konuda yardımcı olmak isterim. Hangi tabloyla ilgili soru sormak istersiniz?"
}
```

**Response (hata):**
```json
{
  "success": false,
  "error": "Yapay zeka maksimum deneme sayısına ulaştı..."
}
```

---

### `POST /api/run_sql`
Kullanıcının doğrudan yazdığı / düzenlediği SQL'i çalıştırır. Sadece SELECT sorguları kabul edilir.

**Request:**
```json
{
  "sql": "SELECT product_name, price FROM products ORDER BY price DESC LIMIT 5"
}
```

**Response:**
```json
{
  "success": true,
  "data": [{ "product_name": "Telefon", "price": 20000 }],
  "columns": ["product_name", "price"]
}
```

---

### `POST /api/upload_db`
Yeni bir `.sqlite` dosyası yükler ve RAG sistemini yeni şemayla yeniden başlatır.

**Content-Type:** `multipart/form-data`
**Field:** `file` → `.sqlite` dosyası

**Response:**
```json
{
  "success": true,
  "message": "Veritabani basariyla yuklendi ve RAG senkronize edildi."
}
```

---

## 📦 Modül Açıklamaları

### `main.py` — FastAPI Giriş Noktası

- Uygulama başlangıcında (`startup_event`) demo veritabanını kurar ve RAG'ı başlatır
- Ollama bağlanamasa bile sunucu ayağa kalkar; yalnızca `/api/generate_sql` endpoint'i 503 döner
- `/static` klasörünü `StaticFiles` ile serve eder

### `agent.py` — LLM Orkestrasyon Motoru

Ana fonksiyon: `generate_sql_and_chart(query, vectorstore, llm_model, max_retries, chat_history)`

```
1. RAG → ilgili tablo şemalarını getir (k=5)
2. Konuşma geçmişini (son 10 mesaj) okunabilir metne çevir
3. AGENT_SYSTEM_PROMPT'u doldur
4. Ollama'ya JSON formatında gönder (temperature=0)
5. SQL boşsa → is_chat:True döndür (fallback)
6. SQL doluysa → execute_query() çalıştır
7. Hata varsa → hata + önceki reasoning ile yeniden dene (max_retries)
```

**Self-Correction Döngüsü:**
```
Hatalı SQL → hata mesajı + önceki reasoning → LLM'e geri bildirim → yeni SQL
```

### `database.py` — Veritabanı Katmanı

| Fonksiyon | Açıklama |
|-----------|---------|
| `setup_mock_database()` | `ecommerce.sqlite` oluşturur: `products`, `personnel`, `sales` (200 satır) |
| `set_current_db_path(path)` | Global aktif DB yolunu günceller |
| `get_database_schema()` | SQLAlchemy reflection + her tablodan 3 satır örnek veri |
| `get_clean_schema_json()` | Arayüz sidebar için sade JSON şema ağacı |
| `execute_query(sql)` | Pandas `read_sql_query` ile SELECT çalıştır, dict/columns döndür |

**Demo Veritabanı (`ecommerce.sqlite`) Şeması:**
```sql
products  (id PK, product_name, stock_quantity, price)
personnel (id PK, name, department)
sales     (id PK, p_id FK→personnel.id, amount, date)
```

### `rag_schema.py` — RAG Katmanı

| Fonksiyon | Açıklama |
|-----------|---------|
| `initialize_schema_rag(model_name)` | Şemayı okur, tablolara böler, ChromaDB'ye embed eder |
| `get_relevant_schema(query, vectorstore, k)` | Similarity search ile en yakın `k` tabloyu döndürür |

> [!NOTE]
> Windows'ta ChromaDB dosya kilitleme hatası (`WinError 32`) önlemek için her `initialize_schema_rag()` çağrısında timestamp'li yeni klasör oluşturulur: `chroma_schema_db_<unix_timestamp>/`

### `prompts.py` — Ek Prompt Şablonu

`SQL_AGENT_SYSTEM_PROMPT` — `{database_schema}` placeholder'lı alternatif prompt. `agent.py`'deki `AGENT_SYSTEM_PROMPT` aktif olarak kullanılır; bu dosya genişleme / A-B test için rezerve edilmiştir.

### `demo.py` — CLI Test Modu

Web arayüzü olmadan terminal üzerinden AI SQL agent yeteneklerini test etmek için:

```bash
python demo.py
```

### `test_e2e.py` — Uçtan Uca Testler

Sistemi otomatik test eden senaryo betiği:

```bash
python test_e2e.py
```

---

## 🔗 Entegrasyon Rehberi

### 🅰️ Python Kütüphanesi Olarak

```python
from agent import generate_sql_and_chart
from rag_schema import initialize_schema_rag
from database import set_current_db_path

# İsteğe bağlı: farklı DB yükle
set_current_db_path("my_database.sqlite")

# RAG'ı başlat (bir kez yeterli)
vectorstore = initialize_schema_rag(model_name="llama3")

# Sorgu çalıştır
result = generate_sql_and_chart(
    query="En yüksek satış yapan personel kim?",
    vectorstore=vectorstore,
    llm_model="llama3",
    max_retries=3,
    chat_history=[]
)

if result["success"] and not result.get("is_chat"):
    print(f"SQL   : {result['sql']}")
    print(f"Grafik: {result['chart_type']}")
    print(f"Veri  : {result['data']}")
elif result.get("is_chat"):
    print(f"Bot   : {result['message']}")
```

### 🅱️ REST API / Mikroservis Olarak

Herhangi bir dilden (Node.js, Go, PHP, Java) çağrılabilir:

```bash
# Örnek: cURL ile sorgu
curl -X POST http://localhost:8000/api/generate_sql \
  -H "Content-Type: application/json" \
  -d '{"query": "En pahalı 5 ürünü listele", "chat_history": []}'
```

```bash
# Veritabanı yükleme
curl -X POST http://localhost:8000/api/upload_db \
  -F "file=@my_company.sqlite"
```

### 🅲️ Farklı Veritabanına Bağlanma

`database.py` içindeki connection string'i değiştirin:

```python
# PostgreSQL
CURRENT_DB_PATH = "postgresql://user:password@localhost:5432/mydb"

# MySQL
CURRENT_DB_PATH = "mysql+pymysql://user:password@localhost/mydb"
```

> [!TIP]
> SQLAlchemy'nin `MetaData.reflect()` özelliği sayesinde bağlantı dizesini değiştirdiğinizde şema otomatik okunur ve RAG yeniden oluşturulur.

> [!WARNING]
> PostgreSQL veya MySQL kullanırken `langchain_community` Ollama embeddings servisinin **yalnızca Llama 3 embedding** modeliyle test edildiğini unutmayın. Farklı Ollama modeli denemeleri gerekebilir.

---

## ⚙️ Gelişmiş Konfigürasyon

| Parametre | Dosya | Varsayılan | Açıklama |
|-----------|-------|-----------|---------|
| `max_retries` | `agent.py → generate_sql_and_chart()` | `3` | Self-correction döngüsü maksimum deneme sayısı |
| `k` (RAG k-value) | `agent.py → get_relevant_schema()` | `5` | LLM bağlamına dahil edilecek maksimum tablo sayısı |
| `temperature` | `agent.py → Ollama(temperature=0)` | `0` | LLM yaratıcılık seviyesi (SQL için 0 şiddetle önerilir) |
| `chat_history` limit | `agent.py` (son 10 mesaj) | `10` | Konuşma bağlamı için tutulan maksimum mesaj sayısı |
| `LIMIT 100` | `prompts.py` | `100` | Varsayılan sorgu sonuç sınırı |
| `DEFAULT_DB_NAME` | `database.py` | `ecommerce.sqlite` | Başlangıç veritabanı dosyası |
| `model_name` | `main.py → initialize_schema_rag()` | `"llama3"` | Hem LLM hem embedding için kullanılan Ollama modeli |

---

## 🛡️ Güvenlik Katmanı

Sistem **"Security by Prompting" + "Backend Validation"** çift katmanlı yaklaşımı uygular:

### 1. Prompt Seviyesi (agent.py)
```
KURALLAR:
1. SADECE "SELECT" sorgusu üret.
   INSERT, UPDATE, DELETE veya DROP kesinlikle yasaktır.
```
LLM'e sistem promptunda birden fazla noktada tekrarlanan kısıtlama.

### 2. Backend Validasyonu (main.py → /api/run_sql)
```python
if not sql.upper().startswith("SELECT"):
    return {"success": False, "error": "Güvenlik ihlali: Yalnızca SELECT sorguları çalıştırılabilir."}
```
Kullanıcının düzenlediği SQL doğrudan çalıştırılmadan önce backend'de de kontrol edilir.

### 3. Veritabanı Kullanıcı Yetkisi (Entegrasyon)
Prodüksiyon ortamında veritabanı bağlantısında **yalnızca READ-ONLY** yetkili kullanıcı tanımlanmalıdır:
```sql
-- PostgreSQL örneği
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_agent_user;
```

---

## 🧪 Test ve Doğrulama

### CLI Demo Testi
```bash
python demo.py
```

### Uçtan Uca Otomasyon Testi
```bash
python test_e2e.py
```

### Manuel API Testi (Swagger UI)
```
http://127.0.0.1:8000/docs
```

FastAPI'nin otomatik Swagger arayüzünden tüm endpoint'leri interaktif olarak test edebilirsiniz.

### Doğrulanan Senaryolar

| Senaryo | Sonuç |
|---------|-------|
| Yeni `.sqlite` yükleme → RAG adaptasyonu | ✅ |
| Soru → ilgili tablo seçimi (similarity search) | ✅ |
| SQL üretimi → başarılı çalışma | ✅ |
| Hatalı SQL → self-correction → düzelme | ✅ |
| DB dışı soru → sohbet fallback | ✅ |
| Bar/Pie/Line grafik seçimi | ✅ |
| Konuşma geçmişi bağlamı ("öncekini" atfı) | ✅ |

---

## 🗺️ Yol Haritası (Roadmap)

- [ ] **Multi-Database** — Aynı anda birden fazla DB sorgulama ve join yapabilme
- [ ] **Excel/PDF Export** — Raporu tek tıkla dışa aktarma (zaten CSV mevcut)
- [ ] **Speech-to-SQL** — Sesli komut desteği
- [ ] **Kullanıcı Rolleri** — Tablo bazlı erişim kısıtlamaları
- [ ] **Model Seçimi** — Arayüzden farklı Ollama modelini seçebilme (llama3, mistral, codellama...)
- [ ] **Sorgu Geçmişi Persistans** — Tarayıcı yenilenmesinde de korunan sorgu tarihi
- [ ] **Otomatik Şema Güncellemesi** — Veritabanı değişince RAG'ın periyodik olarak yenilenmesi

---

## 📄 Lisans

Bu proje **MIT Lisansı** altındadır. Ticari veya kişisel projelerinizde serbestçe kullanabilir, değiştirebilir ve dağıtabilirsiniz.

---

<div align="center">

**⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!**

Made with ❤️ using FastAPI + LangChain + Ollama

</div>
