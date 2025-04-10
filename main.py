import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

API_TOKEN = 'API_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения контекста пользователей
user_context = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить контекст\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['model'])
def send_model_name(message):
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')

@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id
    user_context.pop(user_id, None)  # Удаляем контекст пользователя, если он есть
    bot.reply_to(message, 'Ваш контекст очищен.')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    # Получаем контекст пользователя, если он есть
    context = user_context.get(user_id, [])

    # Добавляем новый запрос пользователя к контексту
    context.append({"role": "user", "content": user_query})

    request = {
        "messages": context
    }
    
    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        bot.reply_to(message, model_response.choices[0].message.content)
        
        # Добавляем ответ модели к контексту
        context.append({"role": "assistant", "content": model_response.choices[0].message.content})
        
        # Обновляем словарь контекста
        user_context[user_id] = context
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
