# bot.py
"""
Telegram-бот для работы со сказками.
Принимает текстовые файлы со сказками и отвечает на вопросы по ним.

Команды:
  /start – начать диалог (очищает историю и данные)
  /help  – справка
  /clear – обнулить историю и удалить сказку
"""

import os
import sys
import logging
from collections import defaultdict
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
)
from dotenv import load_dotenv


load_dotenv()  

if not os.path.exists(".env"):
    sys.exit("❌ .env не найден! Создайте файл .env с переменной TELEGRAM_BOT_TOKEN.")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("ваш_токен"):
    sys.exit("❌ Установите корректный TELEGRAM_BOT_TOKEN в .env")

Path("stories").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)


if sys.platform.startswith('win'):
    
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler("logs/bot.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
else:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler("logs/bot.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)


user_data = defaultdict(dict)  # {user_id: {"story": "...", "history": [...]}}


def save_story(user_id: int, story_text: str) -> None:
   
    user_data[user_id]["story"] = story_text


def get_story(user_id: int) -> str:
  
    return user_data[user_id].get("story", "")


def clear_user_data(user_id: int) -> None:

    user_data.pop(user_id, None)


def save_history(user_id: int, role: str, content: str) -> None:

    if "history" not in user_data[user_id]:
        user_data[user_id]["history"] = []

    user_data[user_id]["history"].append({"role": role, "content": content})
    # Обрезаем, если превысили лимит
    if len(user_data[user_id]["history"]) > 20:  # 10 пар вопрос-ответ
        user_data[user_id]["history"] = user_data[user_id]["history"][-20:]


def get_history(user_id: int) -> list:
  
    return user_data[user_id].get("history", [])


def clear_history(user_id: int) -> None:
  
    if "history" in user_data[user_id]:
        user_data[user_id]["history"] = []



def query_story(story_text: str, question: str, history: list = None) -> str:
    """
    Отправляет запрос к ИИ с текстом сказки и вопросом через Ollama.
    """
    try:
        
        try:
            from langchain_ollama import ChatOllama
            from langchain_core.prompts import ChatPromptTemplate
        except ImportError:
            return "Для работы с ИИ необходимо установить дополнительные библиотеки:\npip install langchain langchain-ollama"

      
        MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma2:2b")  # По умолчанию gemma2:2b
        MAX_STORY_LENGTH = int(os.getenv("MAX_STORY_LENGTH", "8000"))  # Максимальная длина сказки

        template = """
        Ты помощник, который отвечает на вопросы по сказкам.
        Вот текст сказки:
        {story}

        История разговора:
        {history}

        Вопрос пользователя: {question}

        Ответь кратко и по существу, используя только информацию из сказки.
        Если в сказке нет информации для ответа, скажи "В сказке не говорится об этом".
        """

        prompt = ChatPromptTemplate.from_template(template)

        history_str = ""
        if history:
            for item in history[-4:]:  # последние 2 пары
                role = "Пользователь" if item["role"] == "user" else "Ассистент"
                history_str += f"{role}: {item['content']}\n"

       
        try:
            model = ChatOllama(model=MODEL_NAME)
        except Exception as model_error:
            return f"Не удалось подключиться к модели {MODEL_NAME}. Убедитесь, что Ollama запущена и модель установлена.\nОшибка: {str(model_error)}"

      
        try:
            response = model.invoke(
                prompt.format(
                    story=story_text[:MAX_STORY_LENGTH],  # ограничиваем длину
                    history=history_str,
                    question=question
                )
            )

            return response.content

        except Exception as invoke_error:
            return f"Ошибка при выполнении запроса к модели: {str(invoke_error)}"

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        return f"Произошла ошибка при обработке вашего запроса: {str(e)}"



async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    clear_user_data(user.id)
    # Используем только ASCII символы для совместимости
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! \n\n"
        "Я бот, который поможет тебе работать со сказками! \n\n"
        "Как это работает:\n"
        "1. Отправь мне текстовый файл со сказкой \n"
        "2. Задавай любые вопросы по этой сказке \n"
        "3. Я отвечу, используя информацию из текста сказки \n\n"
        "Команды:\n"
        "/help - показать справку\n"
        "/clear - очистить сказку и историю"
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    model_name = os.getenv("OLLAMA_MODEL", "gemma2:2b")
    await update.message.reply_text(
        f"  Бот для работы со сказками\n\n"
        "Как пользоваться:\n"
        "1. Отправь текстовый файл (.txt) со сказкой\n"
        "2. После загрузки сказки задавай вопросы\n"
        "3. Получай ответы на основе текста сказки\n\n"
        f"Используется модель ИИ: {model_name}\n\n"
        "Команды:\n"
        "/start - начать заново\n"
        "/clear - очистить сказку и историю\n"
        "/help - эта справка\n\n"
        "Поддерживаются только текстовые файлы (.txt)"
    )


async def clear_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    clear_user_data(user.id)
    await update.message.reply_text("  Все данные очищены. Можете загрузить новую сказку.")


async def handle_document(update: Update, context: CallbackContext) -> None:

    user = update.effective_user
    document = update.message.document

    # Проверяем тип файла
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("Пожалуйста, отправьте текстовый файл (.txt) со сказкой.")
        return

    try:
        # Скачиваем файл
        file = await document.get_file()
        file_path = f"stories/{user.id}_{document.file_name}"
        await file.download_to_drive(file_path)

        # Читаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as f:
            story_text = f.read()

        # Сохраняем текст сказки
        save_story(user.id, story_text)

        # Удаляем временный файл
        os.remove(file_path)

        await update.message.reply_text(
            f"  Сказка загружена успешно!\n"
            f"Количество символов: {len(story_text)}\n\n"
            f"Теперь вы можете задавать вопросы по этой сказке!"
        )

    except UnicodeDecodeError:
        await update.message.reply_text(
            "Ошибка: файл должен быть в кодировке UTF-8. Пожалуйста, проверьте кодировку файла.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла от пользователя {user.id}: {e}")
        await update.message.reply_text("Произошла ошибка при загрузке файла. Попробуйте еще раз.")


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений (вопросов)"""
    user = update.effective_user
    user_msg = update.message.text.strip()

    # Проверяем, есть ли у пользователя загруженная сказка
    story_text = get_story(user.id)
    if not story_text:
        await update.message.reply_text(
            "Пожалуйста, сначала отправьте текстовый файл со сказкой.\n"
            "Поддерживаются только файлы в формате .txt"
        )
        return

    # Сохраняем вопрос пользователя
    save_history(user.id, "user", user_msg)

    try:
        # Сообщаем клиенту, что бот «печатает»
        await update.message.chat.send_action(action="typing")

        # Получаем историю для контекста
        history = get_history(user.id)

        # Получаем ответ от ИИ
        answer = query_story(story_text, user_msg, history)

        # Сохраняем ответ бота
        save_history(user.id, "assistant", answer)

        # Ограничиваем длину сообщения Telegram (4096 символов)
        if len(answer) > 4000:
            answer = answer[:4000] + "\n\n... (сообщение было сокращено)"

        await update.message.reply_text(answer)

    except Exception as exc:
        logger.exception("Ошибка при обработке сообщения от %s", user.id)
        await update.message.reply_text(
            "  Произошла ошибка при формировании ответа. Попробуйте позже "
            "или используйте /clear, чтобы начать заново."
        )


# ----------------------------------------------------------------------
# 7️⃣ Запуск бота
# ----------------------------------------------------------------------
def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))

    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("  Bot started and listening for messages")
    app.run_polling()


if __name__ == "__main__":
    main()
