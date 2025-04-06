from typing import List, Optional,Dict
# https://docs.python.org/3/library/typing.html
# https://docs-python.ru/standart-library/modul-typing-python/

class UsageResponse:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class MessageResponse:
    role: str
    content: str

class ChoiceResponse:
    index: int
    message: MessageResponse
    logprobs: Optional[str]
    finish_reason: str

class ModelResponse:
    id: str
    object: str
    created: int
    model: str
    choices: List[ChoiceResponse]
    usage: UsageResponse
    system_fingerprint: str


import telebot
import requests
import jsons



API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)

user_context: Dict[int, List[Dict[str, str]]] = {}
# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очищает контекст беседы пользователя\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
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
    user_context.pop(user_id, None)
    bot.reply_to(message, 'Контекст очищен.')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    if user_id not in user_context:
        user_context[user_id] = []

    # Добавляем пользовательский запрос в контекст
    user_context[user_id].append({"role": "user", "content": user_query})

    request = {
        "messages": user_context[user_id]
    }

    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        bot.reply_to(message, model_response.choices[0].message.content)

        # Добавляем ответ модели в контекст
        user_context[user_id].append({"role": "assistant", "content": model_response.choices[0].message.content})
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
