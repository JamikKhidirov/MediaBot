from aiogram.fsm.state import State, StatesGroup


class EditMetadata(StatesGroup):
    waiting_for_title = State()
    waiting_for_artist = State()
    waiting_for_cover = State()


class BatchProcess(StatesGroup):
    collecting = State()
    waiting_for_title = State()
    waiting_for_artist = State()
