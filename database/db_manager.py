import asyncpg
import datetime
from typing import List, Tuple, Optional
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))

# PostgreSQL ulanish sozlamalari
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

TABLE_NAME = 'scan_log'


class DatabaseManager:
    def __init__(self):
        self.pool = None
        
    async def create_pool(self):
        """Asinxron ulanishlar pulini (pool) yaratish."""
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            database=DB_NAME
        )
        await self.create_table()
        
    async def create_table(self):
        """SCAN_LOG jadvalini yaratish. UNIQUE cheklovini kiritamiz."""
        query = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id SERIAL PRIMARY KEY,
            barcode TEXT NOT NULL UNIQUE, 
            user_id BIGINT NOT NULL,
            scanned_at TIMESTAMP WITH TIME ZONE NOT NULL,
            session_id TEXT NOT NULL
        )
        """
        # Ulanish havzasidan (pool) ulanish olib, jadval yaratamiz
        async with self.pool.acquire() as conn:
            await conn.execute(query)
            
    async def add_barcode(self, barcode: str, user_id: int, session_id: str) -> bool:
        """Yangi shtrix kodni yozuvlariga qo'shish."""
        scanned_at = datetime.datetime.now(datetime.timezone.utc)
        
        query = f"""
        INSERT INTO {TABLE_NAME} (barcode, user_id, scanned_at, session_id)
        VALUES ($1, $2, $3, $4)
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, barcode, user_id, scanned_at, session_id)
                return True # Muvaffaqiyatli qo'shildi
            except asyncpg.exceptions.UniqueViolationError:
                return False # Takroriy barcode
            except Exception as e:
                print(f"PostgreSQL xatosi: {e}")
                return False
    
    async def get_scanned_count(self, session_id: str) -> int:
        """Joriy sessiyada skanerlangan shtrix kodlar sonini olish."""
        query = f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE session_id = $1"
        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query, session_id)
            return count
        
    
    async def get_session_data(self, session_id: str) -> List[Tuple]:
        """Sessiya uchun barcha skanerlangan ma'lumotlarni olish."""
        query = f"SELECT barcode, scanned_at FROM {TABLE_NAME} WHERE session_id = $1 ORDER BY scanned_at"
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, session_id)
            # Natijalarni Tuple formatiga o'tkazish
            return [(r['barcode'], r['scanned_at']) for r in records]
        
    
    async def close(self):
        if self.pool:
            await self.pool.close()