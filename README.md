# 🚀 AI SQL Agent — Akıllı Veri Analiz ve Raporlama Platformu

Doğal dil sorgularını, yerel bir LLM (**Ollama / Llama 3**) ve **RAG** (Retrieval-Augmented Generation) mimarisiyle doğrudan çalıştırılabilir, optimize edilmiş SQLite sorgularına dönüştüren kurumsal seviyede bir asistan.

![Status](https://img.shields.io/badge/Status-Active-success)
![Version](https://img.shields.io/badge/Version-3.1.0-blue)
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
14. [Sürüm Geçmişi](#-sürüm-geçmişi)
15. [Lisans](#-lisans)

---

## 🎯 Proje Özeti

AI SQL Agent, teknik olmayan kullanıcıların bile bir veritabanına Türkçe soru sorarak anında grafiksel ve tablo bazlı raporlar alabilmesini sağlayan uçtan uca bir yapay zeka asistanıdır.

```
"Geçen ay en çok satan 5 ürün hangileri?"
        ↓
  [RAG: İlgili tablolar filtrelenir]
        ↓
  [Llama3 (async): SELECT sorgusu üretilir]
        ↓
  [SQLite: Sorgu çalıştırılır]
        ↓
  [Akıllı Doğrulama: Risk analizi → gerekirse LLM hakem devreye girer]
        ↓
  [SQLite: Geçmişe kaydedilir]
        ↓
  [Frontend: Bar / Pie / Line grafiği + sayfalı tablo]
```

Tüm işlem **yerel bilgisayarınızda** gerçekleşir — hiçbir veri dışarı çıkmaz.

---

## 🏛️ Mimari Genel Bakış

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              KULLANICI ARAYÜZÜ                                │
│       (Vanilla JS + Chart.js + CSS — Model Seçici, Durum Göstergesi)          │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │ HTTP (REST)
┌─────────────────────────────────▼────────────────────────────────────────────┐
│                              FastAPI Backend                                   │
│                                                                                │
│  /api/generate_sql   /api/run_sql     /api/schema    /api/upload_db           │
│  /api/health         /api/models      /api/history   /api/export_csv          │
└────────┬──────────────────────────┬─────────────────────────┬─────────────────┘
         │                          │                         │
┌────────▼──────┐   ┌───────────────▼──────────┐   ┌─────────▼──────────────┐
│   agent.py    │   │      database.py          │   │     rag_schema.py       │
│               │   │                           │   │                         │
│ • Async LLM   │   │ • SQLAlchemy Engine       │   │ • Schema Extraction     │
│ • Self-Corr.  │   │ • execute_query()         │   │ • ChromaDB Embed        │
│ • Validator   │   │ • Schema Reflect          │   │ • Similarity Search     │
│ • Chat Fall.  │   │ • Mock DB Setup           │   │ • OllamaEmbeddings      │
│ • Chat Hist.  │   │ • Query History (SQLite)  │   │ • Eski klasör temizliği │
└────────┬──────┘   └───────────────┬──────────┘   └─────────┬──────────────┘
         │                          │                         │
         └──────────────────────────┴─────────────────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   Ollama (Llama3+)   │
                         │  localhost:11434     │
                         └─────────────────────┘
```

### Veri Akışı (Adım Adım)

| Adım | Bileşen | İşlem |
|------|---------|-------|
| 1 | `rag_schema.py` | Veritabanı şeması + örnek veriler çekilir, tablolar ayrıştırılır |
| 2 | `ChromaDB` | Her tablo metni OllamaEmbeddings ile vektöre çevrilir |
| 3 | `rag_schema.py` | Kullanıcı sorusuna göre en yakın `k` tablo similarity search ile bulunur |
| 4 | `agent.py` | Filtrelenmiş şema + konuşma geçmişi + soru → seçili modele **async** gönderilir |
| 5 | `Ollama` | JSON formatında `{ reasoning, sql, chart_type }` döndürür |
| 6 | `database.py` | SQL çalıştırılır; hata varsa Self-Correction döngüsü başlar (max 5 deneme) |
| 7 | `agent.py` | `_needs_validation()` ile sonuç risk analizi yapılır; riskli ise LLM hakem devreye girer |
| 8 | `database.py` | Başarılı sorgu `query_history.sqlite` tablosuna otomatik kaydedilir |
| 9 | Frontend | Sayfalı veri tablosu + Chart.js grafiği render edilir |

---

## 🌟 Öne Çıkan Özellikler

| Özellik | Açıklama |
|---------|---------|
| 🔒 **Zero-Data-Leak** | Tüm AI işlemleri Ollama üzerinden yerel makinede çalışır |
| ⚡ **Async LLM** | `run_in_executor` ile LLM çağrısı thread pool'a taşındı; FastAPI event loop bloke olmaz |
| 📊 **Şema Ölçeklenebilirliği** | RAG sayesinde yüzlerce tablolu veritabanlarında düşük token tüketimi |
| 🔄 **Self-Correction** | SQL hatası alınırsa hata mesajı + önceki düşünce LLM'e geri bildirilir; otonom düzeltme |
| 🗄️ **Dinamik DB Yükleme** | Arayüzden `.sqlite` yükleyerek anında veritabanı ve RAG güncellenir |
| 💬 **Sohbet Geçmişi (Oturum)** | Son 10 mesaj konuşma bağlamı olarak korunur; "bunu", "öncekini" gibi atıflar desteklenir |
| 🗃️ **Kalıcı Sorgu Geçmişi** | Başarılı her sorgu `query_history.sqlite`'a kaydedilir; tarayıcı yenilenince kaybolmaz |
| 🤖 **Chat Fallback** | DB ile ilgisiz sorularda SQL üretmek yerine kullanıcıyla doğal dil sohbeti |
| 📈 **Görsel Zeka** | Bar, Pie, Line grafik tiplerinden en uygununu LLM seçer |
| 🌲 **Şema Kaşifi** | Ağaç hiyerarşisinde sidebar; yüklü DB yapısını interaktif görüntüleme |
| ✏️ **Düzenlenebilir SQL** | Üretilen sorgu editable alan üzerinden manuel değiştirip yeniden çalıştırılabilir |
| 📑 **Sonuç Sayfalama** | 50 satır/sayfa; Önceki/Sonraki butonları + "X–Y / N satır" bilgisi |
| 🎛️ **Model Seçimi** | Header'daki dropdown ile Ollama'da yüklü tüm modeller arasından seçim yapılabilir |
| 🟢 **Sistem Durum Göstergesi** | Header'daki yeşil/kırmızı nokta; hover'da RAG + Ollama + model listesi detayı |
| 📤 **Backend CSV Export** | UTF-8 BOM kodlamalı CSV; Excel'de Türkçe karakter sorunu olmaz |
| 🎨 **Animasyonlu UI** | Glassmorphism tasarım; Header, Sidebar, Chat staggered giriş animasyonları |
| 🔍 **Akıllı Sonuç Doğrulama** | `_needs_validation()` ile kural tabanlı risk analizi; şüpheli sonuçlarda LLM hakem (`_validate_result()`) devreye girer — gereksiz ek LLM çağrısı yapılmaz |
| 🛡️ **Gelişmiş SQL Güvenliği** | `sqlparse` ile tam AST analizi; `SELECT 1; DROP TABLE` tarzı multi-statement saldırılar engellenir |
| 🧹 **ChromaDB Temizliği** | Her RAG güncellemesinde eski timestamp'li klasörler otomatik silinir; disk dolmaz |

---

## 📂 Proje Yapısı

```
deneme/
├── main.py                  # FastAPI uygulama girişi; tüm endpoint'ler
├── agent.py                 # Async LLM çağrısı, self-correction döngüsü, chat fallback
├── database.py              # SQLAlchemy engine, schema reflection, execute_query, sorgu geçmişi
├── rag_schema.py            # ChromaDB embedding, similarity search, eski klasör temizliği
├── prompts.py               # Alternatif/ek system prompt şablonları (A-B test için rezerve)
├── demo.py                  # Web arayüzü olmadan CLI test modu
├── test_e2e.py              # Uçtan uca otomasyon testleri
├── requirements.txt         # Python bağımlılıkları
├── ecommerce.sqlite         # Demo e-ticaret veritabanı (otomatik oluşturulur)
├── query_history.sqlite     # Kalıcı sorgu geçmişi (otomatik oluşturulur)
├── databases/               # Upload edilen kullanıcı veritabanları
├── static/
│   └── index.html           # Frontend (Vanilla JS + Chart.js)
└── chroma_schema_db_*/      # ChromaDB vektör deposu (en güncel 1 adet tutulur)
```

---

## 🛠️ Teknoloji Yığını

### Backend

| Kütüphane | Sürüm | Kullanım |
|-----------|-------|---------|
| FastAPI | latest | REST API, dosya yükleme, StreamingResponse, HTML sunumu |
| Uvicorn | latest | ASGI sunucusu |
| Pydantic | v2+ | Request/Response model validasyonu |
| python-multipart | latest | Dosya upload desteği |
| httpx | latest | Ollama sağlık ve model listesi sorguları (async HTTP) |
| sqlparse | latest | SQL AST analizi; multi-statement güvenlik doğrulaması |

### AI / LLM

| Kütüphane | Sürüm | Kullanım |
|-----------|-------|---------|
| LangChain | latest | LLM orkestrasyon katmanı |
| langchain-community | latest | Ollama ve Chroma entegrasyonları |
| Ollama | - | Yerel LLM; JSON format modu, async thread pool üzerinden çağrılır |
| ChromaDB | latest | Vektör veritabanı (embedding deposu) |

### Veritabanı / Veri

| Kütüphane | Sürüm | Kullanım |
|-----------|-------|---------|
| SQLAlchemy | latest | ORM, schema reflection |
| Pandas | latest | SQL sonucu DataFrame → dict/CSV |
| SQLite (builtin) | - | Ana veritabanı motoru + kalıcı sorgu geçmişi |

### Frontend

- **Vanilla JS** — Sıfır bağımlılık, DOM manipülasyonu
- **Chart.js** — Bar, Line, Pie dinamik grafik
- **Glassmorphism CSS** — Modern backdrop-filter tasarım
- **Google Fonts (Outfit + Fira Code)** — Tipografi

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
- `query_history.sqlite` sorgu geçmişi veritabanını oluşturur
- `rag_schema.py` üzerinden şemayı vektörize ederek ChromaDB'ye yükler
- Ollama bağlanamasa bile sunucu çalışır; yalnızca `/api/generate_sql` 503 döner

### 5. Tarayıcıdan Erişin

```
http://127.0.0.1:8000
```

---

## 🔌 API Referansı

### `GET /`

Ana arayüz HTML sayfasını döndürür.

---

### `GET /api/health`

Ollama bağlantısını, RAG durumunu ve yüklü modelleri kontrol eder.

**Response:**
```json
{
  "rag": true,
  "ollama": true,
  "models": ["llama3", "mistral", "codellama"]
}
```

| Alan | Tür | Açıklama |
|------|-----|---------|
| `rag` | bool | ChromaDB vectorstore başlatılmış mı |
| `ollama` | bool | `localhost:11434` erişilebilir mi |
| `models` | list | Ollama'da pull edilmiş modeller |

---

### `GET /api/models`

Ollama'dan kullanılabilir model listesini çeker.

**Response (başarılı):**
```json
{ "success": true, "models": ["llama3", "mistral"] }
```

**Response (Ollama erişilemez):**
```json
{ "success": false, "models": ["llama3"], "error": "Connection refused" }
```

---

### `GET /api/schema`

Yüklü veritabanının şemasını ağaç (JSON) formatında döndürür.

**Response:**
```json
{
  "schema_json": {
    "products": ["id [INTEGER] (PK)", "product_name [TEXT]", "price [FLOAT]"],
    "sales": ["id [INTEGER] (PK)", "p_id [INTEGER] (FK -> personnel.id)", "product_id [INTEGER] (FK -> products.id)", "qty [INTEGER]", "amount [FLOAT]", "date [TEXT]"]
  }
}
```

---

### `GET /api/history`

Kalıcı sorgu geçmişini döndürür (en yeni en üstte, son 20 kayıt).

**Response:**
```json
{
  "history": [
    {
      "id": 42,
      "query": "En çok satan 5 ürün hangileri?",
      "sql": "SELECT product_name, SUM(amount) AS Toplam FROM sales JOIN products...",
      "chart_type": "bar",
      "time": "2026-04-24 14:32:01"
    }
  ]
}
```

---

### `POST /api/generate_sql`

Doğal dil sorusunu SQL'e çevirir, çalıştırır, geçmişe kaydeder ve grafik verisiyle döndürür.

**Request:**
```json
{
  "query": "Geçen ayın toplam satışını getir",
  "model_name": "llama3",
  "chat_history": [
    { "role": "user", "content": "Satış tablosu nedir?" },
    { "role": "assistant", "content": "Satış tablosu..." }
  ]
}
```

| Alan | Tür | Varsayılan | Açıklama |
|------|-----|-----------|---------|
| `query` | string | zorunlu | Kullanıcının doğal dil sorusu |
| `model_name` | string | `"llama3"` | Kullanılacak Ollama modeli |
| `chat_history` | list | `[]` | Önceki konuşma mesajları (bağlam için) |

**Response (başarılı SQL):**
```json
{
  "success": true,
  "sql": "SELECT strftime('%Y-%m', date) AS Ay, SUM(amount) AS Toplam FROM sales GROUP BY Ay",
  "reasoning": "Kullanıcı aylık toplam satış istiyor...",
  "chart_type": "bar",
  "data": [{ "Ay": "2026-03", "Toplam": 125000 }],
  "columns": ["Ay", "Toplam"],
  "attempts": 1
}
```

**Response (sohbet fallback — DB dışı soru):**
```json
{
  "success": true,
  "is_chat": true,
  "message": "Hangi tablo hakkında soru sormak istersiniz?"
}
```

**Response (hata — max_retries aşıldı):**
```json
{
  "success": false,
  "error": "5 denemede de doğru sonuç üretilemedi.\nSon SQL: SELECT ...\nSon sorun: ..."
}
```

---

### `POST /api/run_sql`

Kullanıcının doğrudan yazdığı / düzenlediği SQL'i çalıştırır. `sqlparse` ile tam AST doğrulaması yapılır; yalnızca SELECT kabul edilir.

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

**Reddedilen örnekler:**
```json
{ "success": false, "error": "Güvenlik ihlali: 'DROP' ifadesi reddedildi." }
{ "success": false, "error": "Güvenlik ihlali: Tek seferde birden fazla SQL ifadesi çalıştırılamaz." }
```

---

### `POST /api/upload_db`

Yeni bir `.sqlite` dosyası yükler, aktif veritabanını değiştirir ve RAG sistemini yeniden başlatır.

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

### `POST /api/export_csv`

Tablo verisini UTF-8 BOM kodlamalı CSV dosyası olarak döndürür (Excel Türkçe karakter desteği dahil).

**Request:**
```json
{
  "columns": ["Ürün", "Toplam Satış"],
  "data": [{ "Ürün": "Laptop", "Toplam Satış": 45000 }],
  "filename": "aylik_rapor"
}
```

**Response:** `Content-Type: text/csv` ikili dosya akışı (`aylik_rapor.csv`)

---

## 📦 Modül Açıklamaları

### `main.py` — FastAPI Giriş Noktası

Startup sırası:
1. `setup_mock_database()` — demo DB oluşturulur (yoksa)
2. `init_history_db()` — `query_history.sqlite` + `history` tablosu oluşturulur (yoksa)
3. `initialize_schema_rag()` — ChromaDB vektörleştirilir; Ollama erişilemezse sunucu yine de çalışır

Güvenlik yardımcısı `_validate_select_only(sql)`:
- `sqlparse.parse()` ile tüm statement'ları tip kontrolünden geçirir
- Multi-statement saldırılarını (`SELECT ...; DROP TABLE ...`) `meaningful > 1` kuralıyla reddeder

---

### `agent.py` — Async LLM Orkestrasyon Motoru

Ana fonksiyon: `async generate_sql_and_chart(query, vectorstore, llm_model, max_retries, chat_history)`

```
1. RAG → ilgili tablo şemalarını getir (k=5)
2. Konuşma geçmişini (son 10 mesaj) okunabilir metne çevir
3. AGENT_SYSTEM_PROMPT'u doldur (sütun doğruluğu kuralı dahil)
4. asyncio.get_running_loop().run_in_executor() ile Ollama'ya async gönder (temperature=0, format=json)
5. SQL boşsa → is_chat:True döndür (fallback)
6. SQL doluysa → execute_query() çalıştır
7. Hata varsa → hata + önceki reasoning + SQLite hatası ile yeniden dene (max_retries=5)
8. SQL başarılıysa → _needs_validation() ile risk kontrolü
   • Riskli (LIMIT uyuşmazlığı, boş sonuç, sayı uyuşmazlığı) → _validate_result() LLM hakemi çağır
   • Düşük riskli → doğrudan kabul et (ekstra LLM çağrısı yapma)
9. Hakem reddi → hata + mantık açıklamasıyla yeniden dene; hakem onayı → sonucu döndür
```

**Async Mimarisi:**

`llm.invoke()` senkron bir çağrıdır. FastAPI'nin async event loop'unu bloke etmemek için `asyncio.get_running_loop().run_in_executor(None, llm.invoke, prompt)` ile thread pool'a taşınmıştır. Böylece LLM işlemi sırasında diğer API istekleri yanıtlanmaya devam eder.

**Self-Correction Döngüsü:**
```
Hatalı SQL
  → hata mesajı + önceki reasoning + SQLite özel uyarıları
    → LLM'e geri bildirim
      → yeni, düzeltilmiş SQL (max 5 deneme)
```

**Akıllı Doğrulama (Validator):**

`_needs_validation(sql, data, question)` → kural tabanlı ön kontrol (ucuz):
- `LIMIT N` istenmiş ama `N`'den az satır döndüyse → riskli
- Sorgu hiç sonuç döndürmediyse → riskli
- Kullanıcı belirli bir sayı belirttiyse ama o kadar satır gelmemişse → riskli

`_validate_result(question, sql, data, llm, loop)` → LLM hakem (yalnızca riskli durumlarda):
- `VALIDATOR_PROMPT` ile 5 satır örnek veriyi LLM'e gönderir
- `{ "valid": true/false, "issue": "..." }` döner
- Hakem kendisi hata verirse sonuç kabul edilir (fail-open).

---

### `database.py` — Veritabanı Katmanı

**Ana DB işlemleri:**

| Fonksiyon | Açıklama |
|-----------|---------|
| `setup_mock_database()` | `ecommerce.sqlite` oluşturur: `products`, `personnel`, `sales` (200 satır) |
| `set_current_db_path(path)` | Global aktif DB yolunu günceller |
| `get_database_schema()` | SQLAlchemy reflection + her tablodan 3 satır örnek veri (RAG için) |
| `get_clean_schema_json()` | Arayüz sidebar için sade JSON şema ağacı |
| `execute_query(sql)` | Pandas `read_sql_query` ile SELECT çalıştırır, dict/columns döndürür |

**Sorgu Geçmişi işlemleri (`query_history.sqlite`):**

| Fonksiyon | Açıklama |
|-----------|---------|
| `init_history_db()` | `history` tablosunu oluşturur (idempotent — varsa atlar) |
| `save_to_history(query, sql, chart_type)` | Başarılı sorguyu tarihçeye ekler |
| `get_history(limit=20)` | En yeni `limit` kaydı döndürür |

**`history` Tablo Şeması:**
```sql
CREATE TABLE history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    query      TEXT NOT NULL,
    sql        TEXT,
    chart_type TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
)
```

**Demo Veritabanı (`ecommerce.sqlite`) Şeması:**
```sql
products  (id PK, product_name, stock_quantity, price)
personnel (id PK, name, department)
sales     (id PK, p_id FK→personnel.id, product_id FK→products.id, qty, amount, date)
```

---

### `rag_schema.py` — RAG Katmanı

| Fonksiyon | Açıklama |
|-----------|---------|
| `initialize_schema_rag(model_name)` | Şemayı okur, tablolara böler, ChromaDB'ye embed eder |
| `get_relevant_schema(query, vectorstore, k)` | Similarity search ile en yakın `k` tabloyu döndürür |
| `_cleanup_old_chroma_dirs(keep_latest)` | Eski `chroma_schema_db_*` klasörlerini siler, sadece en yeniyi korur |

**ChromaDB Klasör Stratejisi:**

Windows'ta `WinError 32` (dosya kilitleme) sorununu önlemek için her `initialize_schema_rag()` çağrısında `chroma_schema_db_<unix_timestamp>/` formatında yeni bir klasör oluşturulur. Yeni vektörleştirme tamamlandıktan sonra `_cleanup_old_chroma_dirs(keep_latest=1)` çağrılarak sadece en güncel klasör bırakılır, eskiler silinir.

---

### `prompts.py` — Ek Prompt Şablonu

`SQL_AGENT_SYSTEM_PROMPT` — `{database_schema}` placeholder'lı alternatif prompt. `agent.py`'deki `AGENT_SYSTEM_PROMPT` aktif olarak kullanılır; bu dosya genişleme / A-B test için rezerve edilmiştir.

---

### `demo.py` — CLI Test Modu

Web arayüzü olmadan terminal üzerinden AI SQL agent yeteneklerini test etmek için:

```bash
# 3 hazır test sorgusunu sırayla çalıştırır
python3 demo.py

# Kendi sorgunuzu tek argüman olarak geçin
python3 demo.py "En çok satış yapan personel kim?"
```

Çıktı örneği:
```
❓ Sorgu   : En çok satış yapan personel kim?
🤖 Model   : llama3
⏳ İşleniyor...

✅ Başarılı  (1 deneme)
📝 SQL      :
   SELECT p.name, SUM(s.amount) AS Toplam FROM sales s JOIN personnel p ON s.p_id = p.id GROUP BY p.id ORDER BY Toplam DESC LIMIT 1
📊 Grafik   : bar
📋 Sütunlar : ['name', 'Toplam']
📦 Sonuç    : 1 satır
    1. {'name': 'Ahmet Yılmaz', 'Toplam': 485000}
```

---

### `test_e2e.py` — Uçtan Uca Testler

Sistemi otomatik test eden senaryo betiği:

```bash
python test_e2e.py
```

---

## 🔗 Entegrasyon Rehberi

### 🅰️ Python Kütüphanesi Olarak

`generate_sql_and_chart` artık `async` olduğu için `asyncio.run()` ile çağrılmalıdır:

```python
import asyncio
from agent import generate_sql_and_chart
from rag_schema import initialize_schema_rag
from database import set_current_db_path

# İsteğe bağlı: farklı DB yükle
set_current_db_path("my_database.sqlite")

# RAG'ı başlat (bir kez yeterli)
vectorstore = initialize_schema_rag(model_name="llama3")

# Sorgu çalıştır
result = asyncio.run(generate_sql_and_chart(
    query="En yüksek satış yapan personel kim?",
    vectorstore=vectorstore,
    llm_model="llama3",
    max_retries=5,
    chat_history=[]
))

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
# Model seçerek sorgu
curl -X POST http://localhost:8000/api/generate_sql \
  -H "Content-Type: application/json" \
  -d '{"query": "En pahalı 5 ürünü listele", "model_name": "mistral", "chat_history": []}'

# Sistem durumu kontrolü
curl http://localhost:8000/api/health

# Sorgu geçmişi
curl http://localhost:8000/api/history

# CSV export
curl -X POST http://localhost:8000/api/export_csv \
  -H "Content-Type: application/json" \
  -d '{"columns":["Ürün","Fiyat"],"data":[{"Ürün":"Laptop","Fiyat":15000}],"filename":"rapor"}' \
  --output rapor.csv

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
| `max_retries` | `agent.py` | `5` | Self-correction döngüsü maksimum deneme sayısı |
| `k` (RAG k-value) | `agent.py → get_relevant_schema()` | `5` | LLM bağlamına dahil edilecek maksimum tablo sayısı |
| `temperature` | `agent.py → Ollama(temperature=0)` | `0` | LLM yaratıcılık seviyesi (SQL için 0 şiddetle önerilir) |
| `chat_history` limit | `agent.py` (son 10 mesaj) | `10` | Konuşma bağlamı için tutulan maksimum mesaj sayısı |
| `PAGE_SIZE` | `static/index.html` | `50` | Tablo sayfalama: sayfa başına satır sayısı |
| `keep_latest` | `rag_schema.py → _cleanup_old_chroma_dirs()` | `1` | Saklanacak ChromaDB klasör sayısı |
| `DEFAULT_DB_NAME` | `database.py` | `ecommerce.sqlite` | Başlangıç veritabanı dosyası |
| `HISTORY_DB_PATH` | `database.py` | `query_history.sqlite` | Sorgu geçmişi veritabanı dosyası |
| `OLLAMA_BASE_URL` | `main.py` | `http://localhost:11434` | Ollama servis adresi |
| `model_name` (varsayılan) | `main.py → QueryRequest` | `"llama3"` | API'ye gönderilmediğinde kullanılan model |

---

## 🛡️ Güvenlik Katmanı

Sistem **"Security by Prompting" + "Backend AST Validation"** çift katmanlı yaklaşımı uygular:

### 1. Prompt Seviyesi (`agent.py`)

```
KURALLAR:
1. SADECE "SELECT" sorgusu üret.
   INSERT, UPDATE, DELETE veya DROP kesinlikle yasaktır.
```

LLM'e sistem promptunda birden fazla noktada tekrarlanan kısıtlama.

### 2. Backend AST Validasyonu (`main.py → _validate_select_only`)

Basit `startswith("SELECT")` kontrolü yerine `sqlparse` ile tam sözdizimi ağacı analizi yapılır:

```python
# Eski (zayıf) yöntem — atlanabilir
if not sql.upper().startswith("SELECT"):
    return error

# Yeni (güçlü) yöntem — AST tabanlı
statements = sqlparse.parse(sql)
for stmt in statements:
    if stmt.get_type() != "SELECT":
        return error          # SELECT dışı her tip reddedilir
if len(meaningful_stmts) > 1:
    return error              # Multi-statement saldırıları engellenir
```

**Engellenen saldırı örnekleri:**
| Girdi | Eski Kontrol | Yeni Kontrol |
|-------|-------------|-------------|
| `DROP TABLE users` | ✅ Engellendi | ✅ Engellendi |
| `SELECT 1; DROP TABLE users` | ❌ **Geçti** | ✅ Engellendi |
| `SELECT * FROM products; DELETE FROM sales` | ❌ **Geçti** | ✅ Engellendi |

### 3. Veritabanı Kullanıcı Yetkisi (Entegrasyon)

Prodüksiyon ortamında veritabanı bağlantısında **yalnızca READ-ONLY** yetkili kullanıcı tanımlanmalıdır:

```sql
-- PostgreSQL örneği
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_agent_user;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM ai_agent_user;
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
| LLM çalışırken paralel API isteği yanıtlanması (async) | ✅ |
| Multi-statement SQL saldırısı engelleme | ✅ |
| Sorgu geçmişi → tarayıcı yenilemesi sonrası korunma | ✅ |
| 50+ satır sonuç → sayfalama butonları görünür | ✅ |
| Farklı Ollama modeli seçip sorgu gönderme | ✅ |
| CSV export → Excel'de Türkçe karakter doğruluğu | ✅ |
| Birden fazla DB yükleme → eski ChromaDB klasörleri silinir | ✅ |
| "Top 5 ürün" sorgusu → `product_id` / `qty` içeren doğru `sales` şeması | ✅ |
| Validator tetiklendi (LIMIT uyuşmazlığı) → hakem LLM'e gönderildi | ✅ |
| Validator atlandı (düşük riskli sorgu) → ekstra LLM çağrısı yapılmadı | ✅ |
| `demo.py` CLI argümanıyla özel sorgu çalıştırma | ✅ |

---

## 🗺️ Yol Haritası (Roadmap)

- [x] **Async LLM** — FastAPI event loop bloke edilmeden LLM çağrısı
- [x] **Gelişmiş SQL Güvenliği** — `sqlparse` ile AST tabanlı multi-statement koruması
- [x] **ChromaDB Otomatik Temizliği** — Eski timestamp'li klasörlerin silinmesi
- [x] **Sistem Durum Göstergesi** — Header'da gerçek zamanlı Ollama + RAG sağlık bilgisi
- [x] **Kalıcı Sorgu Geçmişi** — SQLite'a yazılan, tarayıcı yenilemesinde korunan tarihçe
- [x] **Model Seçimi** — Arayüzden farklı Ollama modeli seçebilme
- [x] **Sonuç Sayfalama** — Büyük veri setleri için Önceki/Sonraki navigasyonu
- [x] **Backend CSV Export** — UTF-8 BOM ile Excel uyumlu sunucu taraflı dışa aktarım
- [x] **Akıllı Sonuç Doğrulama** — `_needs_validation()` risk analizi + koşullu LLM hakem; performanssız ekstra çağrı yok
- [x] **demo.py Async Yeniden Yazımı** — `asyncio.run()` + CLI argüman desteği (`python3 demo.py "sorgu"`)
- [x] **Sales Şeması Düzeltmesi** — `product_id` ve `qty` kolonları eklenerek ürün bazlı analizler çalışır hale getirildi
- [ ] **Multi-Database** — Aynı anda birden fazla DB sorgulama ve join yapabilme
- [ ] **Excel / PDF Export** — Alternatif dışa aktarım formatları
- [ ] **Speech-to-SQL** — Sesli komut desteği
- [ ] **Kullanıcı Rolleri** — Tablo bazlı erişim kısıtlamaları
- [ ] **Otomatik Şema Güncellemesi** — Veritabanı değişince RAG'ın periyodik olarak yenilenmesi
- [ ] **Sorgu Favorileri** — Sık kullanılan sorguları kaydetme ve hızlı erişim

---

## 📜 Sürüm Geçmişi

### v3.1.0 — Akıllı Doğrulama ve Kararlılık Güncellemesi

- **Akıllı Validator:** `_needs_validation()` kural motoru + `_validate_result()` LLM hakemi; yalnızca şüpheli sonuçlarda tetiklenir (LIMIT uyuşmazlığı, boş sonuç, sayı uyuşmazlığı)
- **max_retries artırıldı:** Self-correction döngüsü 3 → 5 denemeye çıkarıldı; karmaşık JOIN sorguları için daha fazla iterasyon hakkı
- **`asyncio.get_running_loop()`:** `get_event_loop()` deprecation uyarısı giderildi; Python 3.10+ uyumlu
- **Sütun Doğruluğu Kuralı:** AGENT_SYSTEM_PROMPT'a "KRİTİK KURAL — SÜTUN DOĞRULUĞU" eklendi; LLM artık şemada olmayan sütun üretemiyor
- **Sales şeması düzeltmesi:** `sales` tablosuna `product_id FK→products.id` ve `qty` kolonları eklendi; ürün bazlı analizler (`JOIN products`) artık doğru çalışıyor
- **`demo.py` tam yeniden yazımı:** `asyncio.run(main())` + CLI argüman desteği; `python3 demo.py "sorum"` ile tek sorgu, argümansız çalıştırınca 3 hazır test sorgusu

### v3.0.0 — Güvenlik ve UX Güncellemesi
- **Async LLM:** `llm.invoke()` → `loop.run_in_executor()` ile thread pool'a taşındı
- **Güvenlik:** `sqlparse` AST analizi ile multi-statement SQL saldırılarına karşı tam koruma
- **ChromaDB temizliği:** `_cleanup_old_chroma_dirs()` ile disk taşması önlendi
- **Sistem durum göstergesi:** Header'da yeşil/kırmızı dot; hover'da detay
- **Kalıcı sorgu geçmişi:** `query_history.sqlite` ile tarayıcı yenileme sonrası korunan tarihçe
- **Model seçimi:** Header dropdown; Ollama'daki tüm modeller `/api/models` ile otomatik listelenir
- **Sonuç sayfalama:** 50 satır/sayfa, Önceki/Sonraki butonları
- **Backend CSV:** UTF-8 BOM kodlamalı `StreamingResponse`; Excel Türkçe karakter desteği
- **Yeni endpoint'ler:** `/api/health`, `/api/models`, `/api/history`, `/api/export_csv`

### v2.0.0 — RAG Mimarisi
- ChromaDB ile per-tablo vektörel şema filtrelemesi
- Dinamik `.sqlite` yükleme
- Self-correction döngüsü (max 3 deneme)
- Konuşma geçmişi bağlamı (session bazlı)
- Chat fallback modu
- Düzenlenebilir SQL alanı
- Syntax highlighting

### v1.0.0 — İlk Sürüm
- Temel FastAPI + Ollama + SQLite entegrasyonu
- Vanilla JS frontend

---

<div align="center">

**⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!**

Made with ❤️ using FastAPI + LangChain + Ollama

</div>
