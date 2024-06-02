import random

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from db_models import Base, User, Word, UserWord
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup


db_url = 'postgresql://username:password@host:port/database_name'

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# Создание таблиц, если их еще не существует
Base.metadata.create_all(engine)


print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = ''
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word_add = State()
    translate_word_add = State()
    target_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []

    # Получаем случайное слово из базы данных
    random_word = session.query(Word).order_by(func.random()).first()
    target_word = random_word.target_word
    translate = random_word.translate_word

    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)

    # Получаем 3 случайных слова из базы данных
    other_words = session.query(Word).filter(Word.id != random_word.id).order_by(func.random()).limit(3).all()
    other_words_btns = [types.KeyboardButton(word.target_word) for word in other_words]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)

    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = [word.target_word for word in other_words]


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    user = session.query(User).filter_by(chat_id=message.chat.id).first()
    if user:
        user_words = session.query(UserWord).filter_by(user_id=user.id).all()
        if user_words:
            words = [session.query(Word).get(user_word.word_id) for user_word in user_words]
            markup = types.ReplyKeyboardMarkup(row_width=2)
            word_buttons = [types.KeyboardButton(word.target_word) for word in words]
            markup.add(*word_buttons)
            bot.send_message(message.chat.id, "Выберите слово, которое хотите удалить:", reply_markup=markup)
            bot.set_state(message.from_user.id, MyStates.another_words, message.chat.id)
        else:
            bot.send_message(message.chat.id, "У вас нет сохраненных слов для удаления.")
    else:
        bot.send_message(message.chat.id, "Вы еще не добавили ни одно слово.")


@bot.message_handler(state=MyStates.another_words, func=lambda message: message.text != Command.NEXT)
def delete_selected_word(message):
    user = session.query(User).filter_by(chat_id=message.chat.id).first()
    word = session.query(Word).filter_by(target_word=message.text).first()
    user_word = session.query(UserWord).filter_by(user_id=user.id, word_id=word.id).first()
    session.delete(user_word)
    session.commit()
    bot.send_message(message.chat.id, f"Слово '{word.target_word}' успешно удалено.")
    bot.set_state(message.from_user.id, None, message.chat.id)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    bot.send_message(cid, "Введите английское слово для добавления:")
    bot.set_state(message.from_user.id, MyStates.target_word_add, message.chat.id)

@bot.message_handler(state=MyStates.target_word_add, func=lambda message: message.text != Command.NEXT)
def save_new_word(message):
    target_word = message.text
    bot.send_message(message.chat.id, "Введите перевод этого слова на русский язык:")
    bot.set_state(message.from_user.id, MyStates.translate_word_add, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word

@bot.message_handler(state=MyStates.translate_word_add, func=lambda message: message.text != Command.NEXT)
def save_new_word_translation(message):
    translate_word = message.text
    user = session.query(User).filter_by(chat_id=message.chat.id).first()
    if not user:
        user = User(chat_id=message.chat.id, username=message.chat.username)
        session.add(user)
        session.commit()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        word = session.query(Word).filter_by(target_word=target_word).first()
        if not word:
            word = Word(target_word=target_word, translate_word=translate_word)
            session.add(word)
        user_word = UserWord(user_id=user.id, word_id=word.id)
        session.add(user_word)
        session.commit()
    bot.send_message(message.chat.id, f"Слово '{target_word}' с переводом '{translate_word}' успешно добавлено!")
    bot.set_state(message.from_user.id, None, message.chat.id)


@bot.message_handler(func=lambda message: message.text != Command.ADD_WORD and message.text != Command.DELETE_WORD and message.text != Command.NEXT)
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)