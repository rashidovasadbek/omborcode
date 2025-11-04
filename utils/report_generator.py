import pandas as pd
import io
import datetime
from typing import List, Tuple

def generate_excel_report(session_data: List[Tuple], target_count: int) -> io.BytesIO:
    """
    Skanerlangan ma'lumotlar ro'yxatidan Excel faylini (io.BytesIO obyekti) yaratadi.

    :param session_data: DB dan olingan ma'lumotlar [(barcode, scanned_at), ...]
    :param target_count: Sanalishi kerak bo'lgan umumiy son.
    :return: BytesIO obyekti, u Telegramga fayl sifatida yuboriladi.
    """
    
    # 1. Ma'lumotlarni DataFrame ga o'tkazish
    data = []
    current_count = len(session_data)
    
    for i, (barcode, scanned_at) in enumerate(session_data):
        # Vaqtni O'zbekistonga mos formatga keltirish (agar kerak bo'lsa)
        # PostgreSQL TIMESTAMP WITH TIME ZONE ni qaytaradi, uni to'g'ridan-to'g'ri ishlatamiz.
        data.append({
            '№': i + 1,
            'Shtrix Kod': barcode,
            'Sanalgan vaqt': scanned_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], # millisekundgacha
        })

    df = pd.DataFrame(data)

    # 2. Excel fayliga yozish uchun BytesIO buferini yaratish
    output = io.BytesIO()
    
    # Excel faylini yaratish
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        
        # 3. Hisobot sarlavhasi (Summary)
        summary_df = pd.DataFrame({
            'Parametr': ['Belgilangan son', 'Sanalgan son', 'Farq'],
            'Qiymat': [target_count, current_count, target_count - current_count]
        })
        summary_df.to_excel(writer, sheet_name='Hisobot', startrow=0, startcol=0, index=False)
        
        # 4. Asosiy ma'lumotlar jadvali
        df.to_excel(writer, sheet_name='Hisobot', startrow=5, startcol=0, index=False)
        
        # Formatlash (Ixtiyoriy: Ustun kengligini sozlash)
        worksheet = writer.sheets['Hisobot']
        worksheet.set_column('B:B', 50) # Shtrix kod ustunini kengaytirish
        worksheet.set_column('C:C', 50) # Vaqt ustunini kengaytirish
        
    output.seek(0) # Kursorni fayl boshiga qaytarish
    return output