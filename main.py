import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

# Loyiha modullarini import qilish
from database.db_manager import DatabaseManager
from handlers import start_handler, barcode_handler

# Logging (jurnal yuritish) sozlamasi
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")


async def main():
    """
    Botni ishga tushirish uchun asosiy asinxron funksiya.
    """
    # .env faylini yuklash
    load_dotenv()
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN .env faylida topilmadi. Iltimos, tekshiring.")
        return

    # 1. Ma'lumotlar bazasi (PostgreSQL) ulanishini o'rnatish
    db_manager = DatabaseManager()
    try:
        await db_manager.create_pool()
        logging.info("✅ PostgreSQL ga ulanish muvaffaqiyatli o'rnatildi.")
    except Exception as e:
        logging.error(f"❌ PostgreSQL ga ulanishda xato: {e}")
        return # Xato bo'lsa, botni ishga tushirmaymiz

    # 2. Bot va Dispatcher obyektlarini yaratish
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    # FSMContext ma'lumotlarini xotirada saqlaymiz (MemoryStorage)
    dp = Dispatcher(storage=MemoryStorage())
    
    # 3. Handlerlarni ro'yxatdan o'tkazish
    dp.include_router(start_handler.router)
    dp.include_router(barcode_handler.router)

    # 4. Middleware/Dependency Injection orqali DBManager ni handlerlarga kiritish
    # Bu orqali har bir handler funksiyasi avtomatik ravishda db_manager obyektini oladi.
    dp["db_manager"] = db_manager 

    # 5. Botni ishga tushirish (Botni avvalgi o'qilmagan xabarlarni o'tkazib yuborish orqali)
    logging.info("🚀 SanoqBot ishga tushmoqda...")
    await dp.start_polling(bot)

    # 6. Bot to'xtatilganda ulanish pulini yopish
    await db_manager.close()


if __name__ == "__main__":
    # Python 3.7+ uchun asyncio ishga tushirish
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.warning("🛑 Bot to'xtatildi!")