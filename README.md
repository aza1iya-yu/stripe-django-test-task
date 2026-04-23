# Django + Stripe Test Project

Тестовое задание: backend на Django с интеграцией Stripe Checkout для оплаты товаров, плюс расширения в виде заказа/корзины, скидок, налогов, поддержки двух валют (EUR, USD) и Docker-запуска.

## Что реализовано

### Основное задание

- Django-модель `Item` (товар, цена, валюта, остаток, налог).
- `GET /buy/<item_id>/` — создание Stripe Checkout Session для одного товара.
- `GET /item/<item_id>/` — HTML-страница карточки товара.
- Редирект в Stripe Checkout по `session_url`, который возвращает backend.

### Дополнительно

- Корзина и заказ:
  - добавление товара в заказ: `POST /cart/add/<item_id>/`;
  - просмотр корзины: `GET /cart/`;
  - оплата заказа: `GET /buy/order/<order_id>/`.
- Разделение корзины по валютам (если в заказе есть и USD, и EUR).
- Модели `Order` и `OrderItem`.
- Модели `Discount` и `Tax` с хранением Stripe ID для USD и EUR.
- Обновление статусов оплаты после `success` и списание остатков товара.
- Django Admin для управления товарами, заказами, скидками и налогами.
- Настройки через переменные окружения.
- Docker-конфигурации для локальной разработки и production.

## Стек

- Python 3.12
- Django 6.0.4
- Stripe Python SDK (`stripe==15.0.1`)
- django-bootstrap5
- django-debug-toolbar (только при `DJANGO_DEBUG=True`)
- SQLite (по умолчанию)
- Docker / Docker Compose
- Gunicorn + Nginx (в production-конфигурации)

## Модели

- `Item`: товар, описание, валюта (`usd`/`eur`), цена, остаток, налог.
- `Order`: заказ, признак оплаты, скидка.
- `OrderItem`: позиция заказа (товар, количество, цена, признак оплаты).
- `Discount`: скидка с Stripe coupon/promotion code для USD/EUR.
- `Tax`: налог с Stripe tax rate для USD/EUR.

## Маршруты

- `GET /` — список товаров.
- `GET /item/<item_id>/` — карточка товара.
- `GET /buy/<item_id>/` — checkout для одного товара.
- `POST /cart/add/<item_id>/` — добавить товар в текущий заказ (в сессии пользователя).
- `GET /cart/` — корзина/заказ.
- `GET /buy/order/<order_id>/?currency=<usd|eur>` — checkout по заказу (можно для конкретной валюты).
- `GET /success/?session_id=...` — страница успешной оплаты (обновляет состояние заказа).
- `GET /admin/` — Django Admin.

## Переменные окружения

Создайте `.env` по примеру `.env.example`.

Обязательные:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `STRIPE_PUBLIC_KEY_USD`
- `STRIPE_SECRET_KEY_USD`
- `STRIPE_PUBLIC_KEY_EUR`
- `STRIPE_SECRET_KEY_EUR`

Дополнительно:

- `DJANGO_ALLOWED_HOSTS` (через запятую)
- `CSRF_TRUSTED_ORIGINS` (через запятую)
- `INTERNAL_IPS` (для debug toolbar в Docker)

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
   - `docker compose up --build -d`
3. Применить миграции:
   - `docker compose exec web python manage.py migrate`
4. Создать суперпользователя:
   - `docker compose exec web python manage.py createsuperuser`

Приложение: `http://127.0.0.1:8000`  
Админка: `http://127.0.0.1:8000/admin`

## Запуск в Docker (prod)

Используется `docker-compose.prod.yml` (`web` на Gunicorn + `nginx`).

1. Создать `.env.prod` с теми же переменными окружения.
2. Запустить: `docker compose -f docker-compose.prod.yml up --build -d`

По умолчанию приложение доступно на порту `80`.

## Тестирование Stripe

Используйте тестовые карты Stripe (например, `4242 4242 4242 4242`).

## Примечания

- `debug-toolbar` включается только в debug-режиме.
- При оплате заказа с товарами в разных валютах оплата производится отдельно по каждой валюте.

## Публикация

- Repository: `https://github.com/aza1iya-yu/stripe-django-test-task`
- Deploy: `http://85.193.89.236/`