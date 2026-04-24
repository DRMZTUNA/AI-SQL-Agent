import sqlite3
import pandas as pd
from sqlalchemy import create_engine, MetaData
from datetime import datetime, timedelta
import random

DEFAULT_DB_NAME = "ecommerce.sqlite"
CURRENT_DB_PATH = DEFAULT_DB_NAME
HISTORY_DB_PATH = "query_history.sqlite"


def init_history_db():
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            sql TEXT,
            chart_type TEXT,
            created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


def save_to_history(query: str, sql: str, chart_type: str = "table"):
    conn = sqlite3.connect(HISTORY_DB_PATH)
    conn.execute(
        "INSERT INTO history (query, sql, chart_type) VALUES (?, ?, ?)",
        (query, sql, chart_type)
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 20) -> list:
    conn = sqlite3.connect(HISTORY_DB_PATH)
    rows = conn.execute(
        "SELECT id, query, sql, chart_type, created_at FROM history ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"id": r[0], "query": r[1], "sql": r[2], "chart_type": r[3], "time": r[4]} for r in rows]

def get_current_db_url():
    return f"sqlite:///{CURRENT_DB_PATH}"

def set_current_db_path(path: str):
    global CURRENT_DB_PATH
    CURRENT_DB_PATH = path

def setup_mock_database():
    import os
    if os.path.exists(DEFAULT_DB_NAME):
        # Already setup
        return
        
    engine = create_engine(f"sqlite:///{DEFAULT_DB_NAME}")
    
    # Products
    products = pd.DataFrame({
        'id': range(1, 11),
        'product_name': ['Laptop', 'Mouse', 'Klavye', 'Monitör', 'Kulaklık', 'Kamera', 'Yazıcı', 'Tablet', 'Telefon', 'Şarj Aleti'],
        'stock_quantity': [5, 50, 45, 12, 8, 3, 20, 15, 25, 100],
        'price': [15000, 300, 500, 4000, 800, 2500, 1200, 6000, 20000, 150]
    })
    products.to_sql('products', engine, index=False, if_exists='replace')

    # Personnel
    personnel = pd.DataFrame({
        'id': range(1, 6),
        'name': ['Ahmet Yılmaz', 'Ayşe Demir', 'Mehmet Kaya', 'Fatma Şahin', 'Ali Can'],
        'department': ['Satış', 'Satış', 'IT', 'Satış', 'Pazarlama']
    })
    personnel.to_sql('personnel', engine, index=False, if_exists='replace')

    # Sales
    # Toplam 200 sahte satış verisi oluşturalım (Son 2 ay içerisinde)
    sales_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    for i in range(1, 201):
        random_days = random.randint(0, 60)
        sale_date = start_date + timedelta(days=random_days)
        p_id = random.choice([1, 2, 4]) # Sadece satış personeli satsın
        product_id = random.randint(1, 10)
        product_price = products.loc[products['id'] == product_id, 'price'].values[0]
        qty = random.randint(1, 3)
        amount = product_price * qty
        
        sales_data.append({
            'id': i,
            'p_id': p_id,
            'product_id': product_id,
            'qty': qty,
            'amount': amount,
            'date': sale_date.strftime('%Y-%m-%d')
        })
        
    sales = pd.DataFrame(sales_data)
    sales.to_sql('sales', engine, index=False, if_exists='replace')
    print("Mock Veritabanı (ecommerce.sqlite) oluşturuldu ve dolduruldu.")

def get_database_schema(db_url=None):
    """Extracts the DDL / Schema metadata and sample data from database."""
    if db_url is None:
        db_url = get_current_db_url()
        
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    schema_info = []
    for table_name, table in metadata.tables.items():
        columns = []
        for col in table.columns:
            pk_str = ", Primary Key" if col.primary_key else ""
            fk_str = ""
            if col.foreign_keys:
                fk_list = [f"Foreign Key -> {fk.target_fullname}" for fk in col.foreign_keys]
                fk_str = ", " + " / ".join(fk_list)
                
            columns.append(f"  - {col.name} ({col.type}{pk_str}{fk_str})")
        
        # Sample data injection
        try:
            df_sample = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", engine)
            sample_str = "  Örnek Veri:\n" + df_sample.to_string(index=False, justify='left').replace('\n', '\n    ')
        except Exception as e:
            sample_str = f"  Örnek veri alınamadı: {e}"

        table_str = f"Tablo: {table_name}\n" + "\n".join(columns) + "\n" + sample_str
        schema_info.append(table_str)
        
    return "\n\n".join(schema_info)

def get_clean_schema_json(db_url=None):
    """Arayüz (Frontend Sidebar) için sade ve temiz JSON ağaç formatında şema döndürür."""
    if db_url is None:
        db_url = get_current_db_url()
        
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    schema_dict = {}
    for table_name, table in metadata.tables.items():
        columns = []
        for col in table.columns:
            pk_str = " (PK)" if col.primary_key else ""
            fk_str = ""
            if col.foreign_keys:
                fk_list = [f"FK -> {fk.target_fullname}" for fk in col.foreign_keys]
                fk_str = f" ({' / '.join(fk_list)})"
                
            columns.append(f"{col.name} [{col.type}]{pk_str}{fk_str}")
        schema_dict[table_name] = columns
        
    return schema_dict

def execute_query(query: str, db_url=None):
    """Executes a SQL query and returns results and columns."""
    if db_url is None:
        db_url = get_current_db_url()
        
    engine = create_engine(db_url)
    # pandas üzerinden direk çalıştırmak data dönmek için en kolayıdır.
    try:
        df = pd.read_sql_query(query, engine)
        return {"success": True, "data": df.to_dict(orient="records"), "columns": list(df.columns)}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    setup_mock_database()
    print(get_database_schema())
