#  AISearcheBooks — AI Помощник по книгам

Telegram-бот, который анализирует присланные текстовые сказки и отвечает на вопросы по их содержанию в режиме реального времени. Работает локально через **Ollama**.

##  Технологический стек
* **Язык:** Python 3.10.6
* **AI движок:** Ollama (локальный запуск моделей)
* **Библиотеки:** 
    * `python-telegram-bot` (взаимодействие с API Telegram)
    * `langchain` / `langchain-ollama` (связка с нейросетью)
    * `python-dotenv` (управление конфигами)

##  Быстрый старт

### 1. Подготовка окружения
1. Скачайте и установите **[Python 3.10.6](https://www.python.org)**. 
   >  **Важно:** При установке обязательно поставьте галочку **"Add Python to PATH"**.
2. Скачайте и установите **[Ollama](https://ollama.com)**.
3. Скачайте и установите **[PyCharm](https://download.jetbrains.com)**.

### 2. Настройка Ollama
* Запустите Ollama.
* Скачайте модель по умолчанию (в проекте используется `gemma2:2b`), выполнив в терминале:
  ollama run gemma2:2b
* В терминале Pycharm выполните:
  pip install python-telegram-bot python-dotenv langchain langchain-ollama langchain-core
### 3. Дополнително 
* по желанию замените в .env токен бота на свой
* Бот: @FairyTailForBot
