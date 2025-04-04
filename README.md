# Telegram Shared Bank Bot 🏦

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/) [![aiogram](https://img.shields.io/badge/aiogram-3.x-green.svg)](https://github.com/aiogram/aiogram)

Простой Telegram бот для управления общими виртуальными "банками" или счетами между пользователями. Позволяет создавать банки, вносить и снимать виртуальные средства, а также предоставлять доступ другим пользователям Telegram.

**Внимание:** Этот бот использует локальные JSON файлы для хранения данных. Он подходит для небольших групп или личного использования. Не рекомендуется для управления реальными финансами или для большого количества пользователей/операций из-за ограничений масштабируемости и отсутствия механизмов предотвращения гонки данных.

## ✨ Возможности

* **Создание банков:** Любой пользователь может создать новый виртуальный банк.
* **Управление средствами:** Внесение (➕) и снятие (➖) виртуальных сумм с баланса банка.
* **Обнуление банка:** Создатель банка может сбросить баланс до нуля (🗑️).
* **Управление доступом:** Создатель банка может добавлять других пользователей (по их Telegram ID), предоставляя им полный доступ к операциям банка (кроме добавления новых пользователей и обнуления).
* **Просмотр баланса:**
    * Просмотр деталей и баланса конкретного банка.
    * Просмотр списка всех банков, к которым у пользователя есть доступ, с их балансами ("Мой баланс").
* **История операций:** Все операции (депозит, снятие, сброс) записываются в историю банка (в JSON файле). *Примечание: В текущей версии бота нет команды для просмотра истории внутри Telegram.*
* **Локальное хранение:** Данные о пользователях и банках хранятся в файлах `users.json` и `banks.json`.

## 🐍 Технологический стек

* **Python 3.x**
* **aiogram 3.x:** Современный асинхронный фреймворк для создания Telegram ботов.
* **JSON:** Для простого хранения данных.

## ⚙️ Установка и запуск

1.  **Клонируйте репозиторий:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://www.google.com/search?q=https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Создайте и активируйте виртуальное окружение** (рекомендуется):
    ```bash
    python -m venv venv
    # Linux/macOS
    source venv/bin/activate
    # Windows
    # venv\Scripts\activate
    ```

3.  **Установите зависимости:**
    Сначала создайте файл `requirements.txt`, если его еще нет:
    ```bash
    pip freeze > requirements.txt
    ```
    Затем установите зависимости (включая aiogram):
    ```bash
    pip install -r requirements.txt
    # Если requirements.txt был пуст или не содержал aiogram:
    # pip install aiogram
    # И затем снова обновите requirements.txt:
    # pip freeze > requirements.txt
    ```

4.  **Получите токен Telegram бота:**
    * Поговорите с [@BotFather](https://t.me/BotFather) в Telegram.
    * Создайте нового бота с помощью команды `/newbot`.
    * Скопируйте полученный API токен.

5.  **Настройте токен:**
    * Откройте файл `your_script_name.py` (замените `your_script_name.py` на реальное имя вашего файла).
    * Найдите строку:
        ```python
        API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
        ```
    * **Замените** `'YOUR_TELEGRAM_BOT_TOKEN'` на ваш реальный API токен, полученный от BotFather.

    * **(Рекомендация по безопасности):** Лучшей практикой является использование переменных окружения для хранения токена, а не вставка его прямо в код. Вы можете адаптировать код для чтения токена из переменной окружения `os.getenv('TELEGRAM_BOT_TOKEN')`.

6.  **Запустите бота:**
    ```bash
    python your_script_name.py
    ```

## 🚀 Использование

1.  Найдите вашего бота в Telegram по имени, которое вы задали в BotFather.
2.  Отправьте команду `/start`. Бот зарегистрирует вас (если вы новый пользователь) и покажет основную клавиатуру.
3.  Используйте кнопки на клавиатуре:
    * **Создать новый банк:** Запускает процесс создания нового банка. Бот запросит название.
    * **Список банков:** Показывает кнопки с названиями банков, к которым у вас есть доступ. Нажатие на название банка покажет его детали и клавиатуру операций.
    * **Мой баланс:** Отображает список всех доступных вам банков и их текущие балансы.
4.  После выбора банка из списка станут доступны операции:
    * **Добавить деньги:** Запрашивает сумму для пополнения текущего выбранного банка.
    * **Снять деньги:** Запрашивает сумму для снятия с текущего выбранного банка.
    * **Обнулить банк:** (Только для создателя) Сбрасывает баланс текущего банка до 0.
    * **Добавить пользователя в {bank_name}:** (Только для создателя) Запрашивает Telegram ID пользователя, которому нужно дать доступ к текущему банку. Пользователь должен предварительно хотя бы раз запустить вашего бота (/start).
    * **Назад:** Возвращает в главное меню.

## 📁 Хранение данных

* **`users.json`:** Хранит информацию о пользователях, взаимодействовавших с ботом (ID, имя, дата первого контакта).
* **`banks.json`:** Хранит информацию о созданных банках, включая баланс, создателя, список допущенных пользователей и историю операций.

**Не забывайте делать резервные копии этих файлов!** При перезапуске бота данные будут прочитаны из этих файлов.

## 🤝 Вклад

Предложения и пул-реквесты приветствуются! Если вы нашли ошибку или у вас есть идея по улучшению, пожалуйста, создайте Issue или Pull Request.
