import logging

from aiogram import *
import psycopg2
import python_qiwi

logging.basicConfig(level=logging.INFO)

API_TOKEN = '5803045003:AAFx7bitZ8OxsCnukcfx47AfpRqLHi1QBjY'
bot = Bot(API_TOKEN)
dp = Dispatcher(bot)


con = psycopg2.connect(database = 'database', user = 'postgres', password = '123123', host = '127.0.0.1', port = '5432')
cur = con.cursor()

cur.execute('SELECT * FROM telegram_bot')

user_id = []
rows = cur.fetchall()
for row in rows:
    user_id.append(str(row[2]))
print(user_id)


@dp.message_handler(commands = ['start'])
async def send_welcome(message: types.Message):
    global user_id, qiwi_number, qiwi_token
    await message.answer('Привет, я бот киви-помощник. Хочешь узнать что я умею присылай /help')
    if str(message.from_user.id) not in user_id:
        cur.execute('INSERT INTO telegram_bot (first_name,user_id) VALUES (%s, %s)', (message.from_user.first_name, str(message.from_user.id)))
    user_id = []
    cur.execute('SELECT * FROM telegram_bot')
    rows = cur.fetchall()
    for row in rows:
        user_id.append(str(row[2]))
    con.commit()

@dp.message_handler(commands = ['help'])
async def send_help(message: types.Message):
    await message.answer('Этот бот создан для использовани  киви кошелька через телеграм. Если хочешь посмотреть все комманды нажми на /commands')

@dp.message_handler(commands=['commands'])
async def send_commands(message: types.Message):
    await message.answer('Команды доступные на данный момент:\n/start - перезапуск бота\n/help - общая информация о боте\n/number - ввод своего номера киви\n/token - ввод своего киви токена\n/info - информация о номере и токене\n/qiwi - команды для работы с qiwi')

@dp.message_handler(commands=['number'])
async def message_qiwi_number(message: types.Message):
    await message.answer("Пожалуйста введите номер киви: +375*******, +7*******")
    @dp.message_handler(regexp='(\+7|8|7).*?(\d{3}).*?(\d{3}).*?(\d{2}).*?(\d{2})')
    async def get_qiwi_number(message: types.Message):
        await message.answer('Ваш введенный номер - ' + message.text)
        cur.execute('UPDATE telegram_bot SET number = %s WHERE user_id = %s', (message.text, str(message.from_user.id)))
        con.commit()
    @dp.message_handler()
    async def dolbaeb(message: types.Message):
        await message.answer("Вы неверно ввели номер телефона")

@dp.message_handler(commands=['token'])
async def mesage_qiwi_token(message: types.Message):
    await message.answer('Пожалуйста введите ваш токен')
    @dp.message_handler()
    async def get_qiwi_token(message: types.Message):
        await message.answer('Ваш введенный токен - ' + message.text)
        cur.execute('UPDATE telegram_bot SET token = %s WHERE user_id = %s', (message.text, str(message.from_user.id)))
        con.commit()

@dp.message_handler(commands=['info'])
async def get_qiwi_information(message: types.Message):
    cur.execute('SELECT number, token FROM telegram_bot WHERE user_id = %s', (str(message.from_user.id),))
    await message.answer(cur.fetchmany(1)[0])

@dp.message_handler(commands=['qiwi'])
async def work_with_qiwi(message: types.Message):
    global qiwi_number, qiwi_token
    wallet = python_qiwi.QiwiWallet(qiwi_number, qiwi_token)
    await('/balance - узнать баланс, /pay - перевод по номеру телефона, /payment - информация о платеже, /payments - история платежей, /profile - информация о профиле')
    @dp.message_handler(commands=['balance'])
    async def get_balance(message: types.Message):
        await message.answer(wallet.balance())
    @dp.message_handler(commands=['pay'])
    async def before_pay(message: types.Message):
        await message.answer('Введите номер для перевода и сумму в формате: +7*********, 100')
        @dp.message_handler()
        async def pay(message: types.Message):
            lst = message.from_user.text.split(', ')
            wallet.pay(to_qw = lst[0], sum = int(lst[1]))
            bill = wallet.bill()
    @dp.message_handler(commands=['payment'])
    async def bill(message: types.Message):
        await message.answer(wallet.get_payment(bill))
    @dp.message_handler(commands=['payments'])
    async def get_rows_for_payments(message: types.Message):
        await message.answer('Введите кол-во платежей о которых вы хотите получить информацию')
        @dp.message_handler()
        async def get_payments_info(message: types.Message):
            await message.answer(wallet.payment_history(int(message.from_user.text)))
    @dp.message_handler(commands=['profile'])
    async def get_profile_info(message:types.Message):
        await message.answer(wallet.get_profile())
    @dp.message_handler()
    async def huinya(message: types.Message):
        await message.answer('Такой команды не существует, посмотрите доступные команды в /commands')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)