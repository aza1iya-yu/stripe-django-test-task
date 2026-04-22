# Django + Stripe Test Project

Тестовое задание: backend на Django с интеграцией Stripe Checkout для оплаты товаров, плюс расширения в виде заказа/корзины, скидок, налогов и Docker-запуска.

## Что реализовано

### Основное задание

- Django-модель `Item` с базовыми полями товара.
- `GET /buy/<item_id>/` — создание Stripe Checkout Session для одного товара.
- `GET /item/<item_id>/` — HTML-страница товара с кнопкой оплаты.
- JS-редирект на Stripe Checkout по `session_url` из backend.

### Дополнительно

- Корзина и заказ:
  - добавление товаров в заказ (`POST /order/add/<item_id>/`);
  - просмотр корзины (`GET /cart/`);
  - оплата заказа целиком (`GET /buy/order/<order_id>/`).
- Модели `Order` и `OrderItem`.
- Модели `Discount` и `Tax` + передача в Stripe Checkout.
- Django Admin для управления товарами, заказами, скидками и налогами.
- Настройки через переменные окружения (`.env`).
- Запуск через Docker (`Dockerfile`, `docker-compose.yml`).

## Текущие ограничения

- В Checkout сейчас используется фиксированная валюта (`RUB`) на уровне формирования line items.

## Стек

- Python 3.12
- Django 6
- Stripe Python SDK
- django-bootstrap5
- django-debug-toolbar
- SQLite (по умолчанию)
- Docker / Docker Compose

## Модели

- `Item`: товар, цена, остаток, налог.
- `Order`: заказ, признак оплаты, скидка.
- `OrderItem`: позиции заказа (товар, количество, цена).
- `Discount`: скидка, stripe coupon/promotion code.
- `Tax`: налог, stripe tax rate.

## API и страницы

- `GET /` — список товаров.
- `GET /item/<item_id>/` — карточка товара.
- `GET /buy/<item_id>/` — создать Checkout Session для одного товара.
- `POST /order/add/<item_id>/` — добавить товар в текущий заказ (сессия пользователя).
- `GET /cart/` — корзина/заказ.
- `GET /buy/order/<order_id>/` — создать Checkout Session для заказа.
- `GET /success/` — страница успешной оплаты.
- `GET /admin/` — Django Admin.

## Переменные окружения

Создайте `.env` по примеру `.env.example`.

Минимально нужны:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `STRIPE_PUBLIC_KEY`
- `STRIPE_SECRET_KEY`

Для `debug-toolbar` в Docker:

- `INTERNAL_IPS`

## Локальный запуск (без Docker)

1. Создать и активировать виртуальное окружение.
2. Установить зависимости:
   - `pip install -r requirements.txt`
3. Создать `.env`.
4. Применить миграции:
   - `python manage.py migrate`
5. Создать суперпользователя:
   - `python manage.py createsuperuser`
6. Запустить сервер:
   - `python manage.py runserver`

Приложение будет доступно на: `http://127.0.0.1:8000`

## Запуск через Docker

1. Создать `.env` (как выше).
2. Собрать и запустить:
   - `docker compose up --build`
3. Применить миграции:
   - `docker compose exec web python manage.py migrate`
4. Создать суперпользователя:
   - `docker compose exec web python manage.py createsuperuser`

Приложение: `http://127.0.0.1:8000`  
Админка: `http://127.0.0.1:8000/admin`

## Тестирование платежей Stripe

- Для оплаты в Checkout применяйте тестовые карты Stripe (например, `4242 4242 4242 4242`).

## Debug Toolbar

Toolbar используется только для локальной разработки/отладки.

## Публикация

- Repository: `https://github.com/aza1iya-yu/stripe-django-test-task`
- Deploy: `ссылка на развернутое приложение>`
- Admin credentials для проверки: `<логин/пароль>`

