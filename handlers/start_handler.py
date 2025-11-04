from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from uuid import uuid4 # Har bir sanash sessiyasi uchun noyob ID yaratish uchun

from utils.states import ScanStates # Biz yaratgan FSM holatlari
from database.db_manager import DatabaseManager # DB bilan ishlash uchun

# Handlerlarni ro'yxatdan o'tkazish uchun yangi Router yaratamiz
router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    """
    /start buyrug'ini qabul qiladi.
    Sanashni boshlash uchun karopkalar sonini so'raydi.
    """
    await message.answer(
        "👋 Xush kelibsiz, SanoqBot!\n"
        "Iltimos, ushbu sessiyada sanalishi kerak bo'lgan jami karopkalar sonini kiriting (faqat raqamda):"
    )
    # Foydalanuvchini son kiritish holatiga o'tkazish
    await state.set_state(ScanStates.waiting_for_count)
    
    
@router.message(ScanStates.waiting_for_count, F.text)
async def process_count(message: types.Message, state: FSMContext):
    """
    Foydalanuvchi kiritgan sonni tekshiradi va saqlaydi.
    """
    # 1. Kiritilgan ma'lumotning raqam ekanligini tekshirish
    try:
        target_count = int(message.text)
        if target_count <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, musbat son kiriting (masalan, 100)."
        )
        # Holatni o'zgartirmaymiz, foydalanuvchi yana son kiritishi kerak
        return

    # 2. Ma'lumotlarni FSM context ga saqlash
    # Har bir yangi sessiya uchun noyob ID yaratamiz
    session_id = str(uuid4())
    
    await state.update_data(
        target_count=target_count,
        current_session_id=session_id
    )
    
    
# 3. Foydalanuvchini shtrix kod kutish holatiga o'tkazish
    await state.set_state(ScanStates.waiting_for_barcode)
    
    await message.answer(
        f"✅ Tayyor! Siz {target_count} ta karopka sanaysiz.\n"
        f"Joriy sessiya ID: `{session_id}`\n\n"
        "Iltimos, birinchi shtrix kodni skanerlang yoki yuboring."
    )