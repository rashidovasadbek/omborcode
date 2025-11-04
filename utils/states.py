from aiogram.fsm.state import State, StatesGroup

class ScanStates(StatesGroup):
    """
    Shtrix kod skanerlash jarayonidagi foydalanuvchi holatlarini boshqarish.
    """
    
    # 1. Boshlang'ich holat: Bot karopkalar sonini kutmoqda.
    waiting_for_count = State()
    
    # 2. Sanash holati: Bot bitta shtrix kodni kutmoqda.
    waiting_for_barcode = State()