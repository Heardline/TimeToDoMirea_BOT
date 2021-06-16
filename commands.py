
import config
from aiogram import types, Dispatcher
from sqlalchemy import select
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
import utils.task_manager as task_manager

#Переключение пользователя

class Group(StatesGroup):  
    group_select = State()  # Статус - выбор группы
    sub = State() #Уведомление
    complete = State()  #Проверка авторизации
class TaskCreate(StatesGroup):  
    name_select = State()  # Название задачи
    lesson = State() #Уведомление
    time = State()  #Проверка авторизации


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if pdb.check_user(message.chat.id) is False:
        await Group.group_select.set()
        with open(config.FileLocation.cmd_welcome, 'r', encoding='utf-8') as file:
            await message.reply(file.read(), parse_mode='HTML', disable_web_page_preview=True)
    else:
        await message.answer(message.chat.id, "<b> Привет, рад тебя видеть снова </b>", parse_mode='HTML', disable_web_page_preview=True)
        await Group.complete.set()
        await menu(message)

# Внесение группы  
@dp.message_handler(state=Group.group_select)
async def select_group(message: types.Message,state: FSMContext):
    if pdb.check_group(message.text) == True:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Да", "Нет")
        with open(config.FileLocation.cmd_group,'r', encoding='utf-8') as file:
            await message.reply(file.read(), parse_mode='HTML', disable_web_page_preview=True, reply_markup=markup)
        await Group.next()
        pdb.add_user(message.text,message.chat.id)
    else:
        await message.reply("Что-то пошло не так, проверь, чтобы группа была формата ГИБО-05-19. Если не получается, значит база данных не доступна либо ваша группа не загружена.", parse_mode='HTML', disable_web_page_preview=True)

# Настройка Уведомление за 20 минут
@dp.message_handler(state=Group.sub)
async def select_sub(message: types.Message,state: FSMContext):
    if message.text == "Да":
        pdb.setup_notify(True,message.chat.id)
    else:
        pdb.setup_notify(False,message.chat.id)
    markup = types.ReplyKeyboardRemove()
    await Group.complete.set()
    await menu(message)
    # Конец регистрации

# Главное меню
@dp.message_handler(commands=['menu'])
async def menu(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Сегодня ⏲", "Завтра 📆", "Неделя 📅","Мои задачи 📋","Настройки 🛠")
    with open(config.FileLocation.cmd_menu,'r', encoding='utf-8') as file:
            await message.reply(file.read(), parse_mode='HTML', disable_web_page_preview=True, reply_markup=markup)
# Для тестов           
@dp.message_handler(commands=['test'])
async def test(message: types.Message):
    await notif_every_lesson()

# Пары на сегодня
@dp.message_handler(commands=['day','Пары на сегодня'])
async def scheduler_today(message: types.Message):
    Lessons = f"<b> Пары на {time_lesson.TodayToEmoji(0)} | {time_lesson.NumberOfMonth()} неделя. </b> \n" 
    group = pdb.get_group(message.chat.id)
    check_lesson = False
    for i in range(1,7):
        if time_lesson.NumberOfMonth() % 2 == 0: # Четная/ не четная неделя
            a = i*2
        else:
            a = (i*2)-1
        if pdb.get_lesson(time_lesson.todayIs()+a,group):
            pass
        else: 
            check_lesson = True
            Lessons = pdb.ready_lesson(Lessons,group, a,i)
    if check_lesson is False:
        Lessons = "<b>Сегодня нету пар </b> ✨🎉\n Иди гуляй)"
    await message.reply(Lessons, parse_mode='HTML', disable_web_page_preview=True)

@dp.message_handler(commands=['tomorow','Пары на завтра'])
async def scheduler_today(message: types.Message):
    Lessons = f"<b> Пары на {time_lesson.TodayToEmoji(0)} | {time_lesson.NumberOfMonth()} неделя. </b> \n"
    group = pdb.get_group(message.chat.id)
    check_lesson = False
    for i in range(1,7):
        if time_lesson.NumberOfMonth() % 2 == 0: 
            a = i*2 + 12
        else:
            a = (i*2)-1 + 12
        if pdb.get_lesson(time_lesson.todayIs()+a,group):
            pass
        else: 
            check_lesson = True
            Lesson_obj = pdb.get_lesson(time_lesson.todayIs()+a,group)
            Lessons.join(f"{time_lesson.NumberToEmoji(i)} ")
    if check_lesson is False:
        Lessons = "<b>Завтра нету пар </b> ✨🎉\n Можешь спать и гулять))"
    await message.reply(Lessons, parse_mode='HTML', disable_web_page_preview=True)

@dp.message_handler(commands=['task'])
async def my_task(message: types.Message):
    await bot.send_message(message.chat.id, '<b> 💡 Твои задачи </b>', parse_mode='HTML')
    inline_button_complete = InlineKeyboardButton('Выполнено', callback_data='task_complete')
    inline_button_delete = InlineKeyboardButton('Удалить', callback_data='task_delete')
    inline_button_change = InlineKeyboardButton('Изменить', callback_data='task_change')
    inline_task = InlineKeyboardMarkup().row(inline_button_complete,inline_button_change,inline_button_delete)
    for task in db["task"].find({"chat_id":message.chat.id}):
        await bot.send_message(message.chat.id,"<b>" + task["name"] + "</b>@ " + task["lesson"] + " @ до " + task["timetodo"] + "  " + task['status'] , parse_mode='HTML', reply_markup=inline_task)
    

@dp.message_handler(commands=['addtask'])
async def my_task(message: types.Message, state: FSMContext):
    await TaskCreate.name_select.set()
    await message.reply("Окей, напиши короткое название задачи:")
    
@dp.message_handler(state=TaskCreate.name_select)
async def select_name(message: types.Message,state: FSMContext):  
    async with state.proxy() as data:
        data['name'] = message.text
    await TaskCreate.lesson.set()
    await message.reply("А по какому предмету?(Советую точно написать название предмета, иначе не будет появлятся в расписании)")

@dp.message_handler(state=TaskCreate.lesson)
async def select_lesson(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['lesson'] = message.text
    await message.reply("Лады, и до какого числа тебе нужно это сделать?(В формате число.месяц 3.02 21.05)")
    await TaskCreate.time.set()

@dp.message_handler(state=TaskCreate.time)
async def select_lesson(message: types.Message,state: FSMContext):
    async with state.proxy() as data:
        data['timetodo'] = message.text
        await bot.send_message(message.chat.id,"Так, окей. Тебе надо сделать: " + data['name'] + " до " + data['timetodo'])
        task = task_manager.Task(data['name'],data['timetodo'],data['lesson'],message.chat.id)
        task.addtodb(db["task"])
    await state.finish()

def register_commands(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start")
    dp.register_message_handler(cmd_play, commands="play")
    dp.register_message_handler(cmd_top, commands="top")