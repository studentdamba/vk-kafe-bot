# VK Bot для кафе «Кимчи»

Бот для автоматизации приёма заказов в кафе через ВКонтакте.

## 📋 Требования

- Python 3.14+
- Windows 11 / Linux
- Токен группы ВКонтакте с правами на сообщения

## 🚀 Установка

### 1. Клонируйте проект или скопируйте файлы

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте окружение

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

Откройте `.env` и укажите:

```env
VK_TOKEN=ваш_токен_vk
ADMIN_IDS=123456789,987654321
DATABASE_PATH=database/kimchi_bot.db
LOG_LEVEL=INFO
```

#### Как получить токен VK:

1. Зайдите в [управление сообществом](https://vk.com/editact)
2. Выберите ваше сообщество → Работа с API
3. Нажмите «Создать ключ»
4. Выберите права: **Сообщения**, **Фотографии**
5. Скопируйте токен в `.env`

#### Как узнать VK ID администратора:

1. Зайдите на свою страницу VK
2. Посмотрите в адресной строке (например, `vk.com/id123456789`)
3. Или используйте сервисы типа reg.ru/vk/

## ▶️ Запуск

```bash
python bot.py
```

При первом запуске бот:
- Создаст базу данных `database/kimchi_bot.db`
- Заполнит меню начальными данными

## 🤖 Команды бота

### Для клиентов:

- `/start` — Начать работу, главное меню
- Кнопки: 📖 Меню, 🛒 Корзина, 📦 Мои заказы, 📞 Поддержка

### Для администраторов:

- `/admin` — Войти в режим админа
- `/menu_list` — Показать всё меню
- `/orders [today|pending|all]` — Список заказов
- `/stats` — Статистика
- `/export` — Экспорт заказов в CSV

## 📁 Структура проекта

```
kimchi_bot/
├── bot.py              # Главный файл запуска
├── config.py           # Конфигурация
├── requirements.txt    # Зависимости
├── .env                # Переменные окружения (не в git!)
├── .env.example        # Пример .env
├── database/
│   ├── __init__.py
│   ├── db.py          # Инициализация БД
│   └── queries.py     # Запросы к БД
├── models/
│   ├── __init__.py
│   └── models.py      # SQLAlchemy модели
├── handlers/
│   ├── __init__.py
│   ├── states.py      # Состояния FSM
│   ├── client_handlers.py    # Обработчики клиента
│   ├── checkout_handlers.py  # Оформление заказа
│   └── admin_handlers.py     # Админ-команды
├── utils/
│   ├── __init__.py
│   ├── logger.py      # Логирование
│   ├── keyboards.py   # Клавиатуры
│   └── validators.py  # Валидаторы
├── logs/              # Логи бота
└── database/          # Файл БД SQLite
```

## 🔐 Безопасность

- Токены хранятся только в `.env`
- Админ-команды проверяют `vk_id`
- Валидация всех пользовательских вводов
- Защита от SQL-инъекций через ORM

## 📊 База данных

Используется SQLite с таблицами:
- `users` — пользователи
- `categories` — категории меню
- `items` — товары
- `cart` — корзина
- `orders` — заказы
- `order_items` — позиции заказа

## ⚙️ Деплой на VPS (Ubuntu)

### 1. Установка Python

```bash
sudo apt update
sudo apt install python3.14 python3.14-venv -y
```

### 2. Настройка

```bash
cd /opt/kimchi_bot
python3.14 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Заполните токеном
```

### 3. systemd сервис

Создайте `/etc/systemd/system/kimchi-bot.service`:

```ini
[Unit]
Description=Kimchi Cafe VK Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/kimchi_bot
Environment="PATH=/opt/kimchi_bot/venv/bin"
ExecStart=/opt/kimchi_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kimchi-bot
sudo systemctl start kimchi-bot
sudo systemctl status kimchi-bot
```

## 📝 Логирование

Логи сохраняются в `logs/kimchi_bot.log`

Уровень логирования настраивается в `.env`:
- `DEBUG` — полная отладка
- `INFO` — стандартный
- `WARNING` — только предупреждения
- `ERROR` — только ошибки

## 🛠️ Разработка

Для добавления новых функций:

1. Добавьте модель в `models/models.py`
2. Добавьте запросы в `database/queries.py`
3. Создайте обработчик в `handlers/`
4. Обновите `bot.py`

## 📄 Лицензия

MIT

---

**Кафе «Кимчи»** © 2024
