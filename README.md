# 🎨 FusionBrain Image Generator (Python + FusionBrain API)

Небольшой учебный проект: консольный и веб-клиент на Python для автоматической генерации изображений с помощью ИИ через FusionBrain API (модель Kandinsky).

Проект создан в рамках изучения **API для генерации изображений с помощью ИИ**.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)
![requests](https://img.shields.io/badge/requests-2496ED?logo=python&logoColor=white)
![python-dotenv](https://img.shields.io/badge/python--dotenv-3776AB?logo=python&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-3776AB?logo=python&logoColor=white)
![FusionBrain](https://img.shields.io/badge/FusionBrain-Kandinsky-FF6B00)

---

## 🚀 Возможности

### Консольная версия (`fusionbrain_client.py`)
* Генерация изображений по текстовому описанию
* Автоматическое сохранение в папку `output/`
* Размер изображения: 1024x1024 пикселей (1:1)
* Поддержка русского и английского языков
* Красивый интерфейс с эмодзи и прогресс-индикаторами

### Веб-версия (`web_app.py`)
* **Современный веб-интерфейс** с адаптивным дизайном
* **Выбор размеров изображения** (6 вариантов): 512×512, 768×768, 1024×1024, 512×768, 768×512, 1024×768
* **Прогресс-бар** с анимацией
* **Кнопка копирования** и **скачивания** изображения
* **Toast-уведомления** об успехе/ошибках
* **Автоматическое открытие браузера** при запуске

---

## 📂 Структура проекта

```
fusionbrain_api/
├── fusionbrain_client.py # консольный клиент
├── web_app.py # веб-приложение Flask
├── .env # ключи API (не попадает в Git)
├── requirements.txt # зависимости
├── templates/ # HTML шаблоны
├── static/ # CSS, JS
├── output/ # готовые изображения
└── README.md
```

---

## ⚙️ Установка и запуск

1. Клонируйте проект и создайте venv
2. `pip install -r requirements.txt`
3. Добавьте в `.env`:
```env
FUSIONBRAIN_API_KEY=ваш_api_ключ
FUSIONBRAIN_SECRET_KEY=ваш_secret_ключ
FUSIONBRAIN_URL=https://api-key.fusionbrain.ai/
```
4. Консоль: `python fusionbrain_client.py`
5. Веб: `python web_app.py` (http://localhost:8080)

---

## 📖 Технологии

Python 3.8+, Flask, requests, python-dotenv, Pillow, FusionBrain API (Kandinsky 3.0)

---

**Репозиторий:** [https://github.com/andreyko75/fusionbrain_api](https://github.com/andreyko75/fusionbrain_api)
