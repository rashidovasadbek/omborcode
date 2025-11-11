import datetime
from aiogram import Router, types, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.storage.base import StorageKey
from aiogram.enums.content_type import ContentType
from utils.states import ScanStates
from utils.report_generator import generate_excel_report
from database.db_manager import DatabaseManager 
from pyzbar.pyzbar import decode 
from PIL import Image
from io import BytesIO

import logging

router = Router()

import logging # <<<< ALO HIDA QATORGA QO'SHILADI

@router.message(ScanStates.waiting_for_barcode, F.text)
async def process_barcode(message: types.Message, state: FSMContext, db_manager: DatabaseManager):
    """
    Foydalanuvchidan shtrix kodni qabul qiladi va Yakunlash/Davom etishni tekshiradi.
    """
    barcode = message.text.strip()
    user_id = message.from_user.id
    
    # 1. FSM context dan sessiya ma'lumotlarini olish
    data = await state.get_data()
    target_count = data.get('target_count')
    session_id = data.get('current_session_id')

    if not target_count or not session_id:
        logging.error(f"FATAL: Target yoki Session ID topilmadi. User: {user_id}") # <<<< YANGI LOG
        await message.answer("❌ Xato! Sessiya ma'lumotlari topilmadi. Iltimos, /start buyrug'i orqali qayta boshlang.")
        await state.clear()
        return
        
    # 2. Shtrix kodni ma'lumotlar bazasiga qo'shish (UNIQUE cheklovini tekshirish)
    is_added = await db_manager.add_barcode(
        barcode=barcode,
        user_id=user_id,
        session_id=session_id
    )

    if not is_added:
        # Xato: Takroriy shtrix kod!
        await message.answer(
            f"❌ Xato: **{barcode}** shtrix kodi **allaqachon sanalgan!** Iltimos, boshqasini skanerlang.",
            parse_mode="Markdown"
        )
        return

    # 3. Muvaffaqiyatli qo'shildi. Joriy progressni hisoblash.
    current_count = await db_manager.get_scanned_count(session_id)
    
    # 4. Yakunlash Cheklovi
    if current_count == target_count:
        logging.info(f"YAKUNLASH: Sessiya ({session_id[:8]}...) tugadi. Soni: {target_count}") # <<<< LOG QO'SHILDI
        
        # Tugmani yaratishda session_id ni callback_data ichiga joylashtirish (MUHIM!)
        report_data = f"generate_report:{session_id}" 
        
        dynamic_report_button = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Hisobotni Yuborish", callback_data=report_data)],
                [InlineKeyboardButton(text="❌ Sessiyani To'xtatish", callback_data="stop_session")]
            ]
        )

        await message.answer(
            f"🎉 Tabriklaymiz! Barcha **{target_count}** ta karopka muvaffaqiyatli sanaldi.\n"
            "Hisobotni olish uchun tugmani bosing.",
            reply_markup=dynamic_report_button,
            parse_mode="Markdown"
        )
        
        # Sanash tugagani uchun FSM holatini tozalaymiz.
        await state.clear() 
    else:
        logging.info(f"DAVOM ETISH: Sessiya ({session_id[:8]}...) davom etmoqda. Joriy soni: {current_count}/{target_count}") # <<<< LOG QO'SHILDI
        # Sanash davom etmoqda
        remaining = target_count - current_count
        await message.answer(
            f"✅ Qabul qilindi. Sanalgan: **{current_count} / {target_count}**.\n"
            f"Yana **{remaining}** ta karopka qoldi. Keyingisini skanerlang.",
            parse_mode="Markdown"
        )

@router.message(ScanStates.waiting_for_barcode, F.photo | F.document)
async def process_barcode_from_image(message: types.Message, state: FSMContext, bot: Bot, db_manager: DatabaseManager):
    """
    Rasm yoki Fayl (document) ichidagi bar-kodni skanerlaydi.
    """
    await message.answer("Rasm qabul qilindi, bar-kod skanerlanmoqda...")
    
    try:
        # 1. Fayl ID ni olish
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document and message.document.mime_type.startswith('image'):
            file_id = message.document.file_id
        else:
            await message.answer("Rasm fayl turi qo'llab-quvvatlanmaydi. Faqat rasm yuboring.")
            return

        # 2. Faylni yuklab olish
        file = await bot.get_file(file_id)
        file_content = await bot.download_file(file.file_path) # BytesIO obyekti
        
        # 3. Bar-kodni o'qish (pyzbar va PIL)
        img = Image.open(file_content)
        decoded_objects = decode(img)
        
        if not decoded_objects:
            await message.answer("❌ Uzr, rasmda hech qanday bar-kod topilmadi. Yoki sifati past.")
            return

        # 4. Bar-kod matnini olish
        # Birinchi topilgan bar-kodni olamiz
        barcode = decoded_objects[0].data.decode('utf-8')
        
        # 5. Asosiy matn handler funksiyasini chaqirish
        # Bu yerda siz yuqoridagi 'process_barcode' funksiyasining mantiqini takrorlashingiz kerak bo'ladi.
        # yoki yaxshisi:
        
        # message.text ni so'zma-so'z o'zgartirish o'rniga, mantiqni alohida yordamchi funksiyaga ajratish yaxshiroq.
        # Lekin tez hal qilish uchun:
        
        # Matn handleriga o'tish uchun message.text ni o'rnatish mumkin emas, 
        # shuning uchun logikani shu yerda takrorlash yoki yordamchi funksiyadan foydalanish kerak.

        # ... process_barcode funksiyasining barcha mantiqini (2-banddan 5-bandgacha) shu yerga ko'chiring
        # Matn handleridagi "barcode = message.text.strip()" qatorini bu yerda
        # "barcode = decoded_objects[0].data.decode('utf-8')" qatoriga almashtirasiz.

        # Agar bu juda murakkab bo'lsa, avval bu handler uchun **`pyzbar`** ni o'rnatishingiz kerak.
        
    except Exception as e:
        await message.answer(f"❌ Rasmni qayta ishlashda kutilmagan xato: {e}")
        # Loglarga xatoni yozing
        logging.error(f"BARCODE_IMAGE_ERROR: {e}")
# =================================================================
# CALLBACK HANDLERS (Tugmalarga javob)
# =================================================================

@router.callback_query(F.data.startswith("generate_report:"))
async def send_report_callback(callback: types.CallbackQuery, db_manager: DatabaseManager):
    """
    Hisobot tugmasi bosilganda ishlaydi. Excel faylini yaratadi va yuboradi.
    """
    await callback.answer("Hisobot tayyorlanmoqda...", show_alert=False)
    
    # 1. Xabarni yangilash va Loading holatini ko'rsatish
    await callback.message.edit_text("⏳ Hisobot ma'lumotlari bazadan yuklanmoqda...")
    
    # 2. Callback Data dan Session ID ni olish
    try:
        session_id = callback.data.split(":")[1]
    except IndexError:
        await callback.message.edit_text("❌ Xato: Sessiya ID topilmadi. Iltimos, /start buyrug'idan boshlang.")
        return
        
    # 3. Ma'lumotlarni bazadan olish
    session_data = await db_manager.get_session_data(session_id)
    
    if not session_data:
        await callback.message.edit_text(f"❌ Xato: Sessiya ({session_id[:8]}...) uchun ma'lumot topilmadi.")
        return
        
    target_count = len(session_data)
    
    # 4. Excel faylini yaratish (report_generator.py dan foydalanamiz)
    excel_buffer = generate_excel_report(session_data, target_count) 
    
    # 5. Faylni Telegramga yuborish
    report_filename = f"Hisobot_{session_id[:8]}_{datetime.date.today().isoformat()}.xlsx"
    
    await callback.bot.send_document(
        chat_id=callback.message.chat.id,
        document=BufferedInputFile(excel_buffer.getvalue(), filename=report_filename),
        caption=f"✅ **Hisobot tayyor!**\nSessiya ID: `{session_id[:8]}...`\nSanalgan karopkalar: {target_count} ta.",
        parse_mode="Markdown"
    )
    
    # 6. Tugmani o'chirish va yakuniy xabarni ko'rsatish
    await callback.message.edit_text(
        f"✅ Ma'lumotlar Excel fayli shaklida yuborildi.\n"
        "Yangi sessiyani boshlash uchun /start buyrug'ini ishlating."
    )


@router.callback_query(F.data == "stop_session")
async def stop_session_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Joriy sanash sessiyasini to'xtatish va holatni tozalash.
    """
    # Holatni tozalaymiz
    await state.clear()
    
    # Xabarni tahrirlaymiz
    await callback.message.edit_text(
        "❌ Sessiya bekor qilindi. Barcha kirishlar to'xtatildi.\n"
        "Yangi sessiyani boshlash uchun /start buyrug'ini ishlating."
    )
    await callback.answer("Sessiya to'xtatildi.")