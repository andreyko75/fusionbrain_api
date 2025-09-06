import json
import time
import base64
import os
import webbrowser
import threading
from datetime import datetime
from typing import Optional, List
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import requests
from dotenv import load_dotenv
from PIL import Image
import io

# Загружаем переменные окружения
load_dotenv('.env')

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # В продакшене используйте случайный ключ

class FusionBrainAPI:
    """Клиент для работы с FusionBrain API"""
    
    def __init__(self):
        self.url = os.getenv('FUSIONBRAIN_URL', 'https://api-key.fusionbrain.ai/')
        self.api_key = os.getenv('FUSIONBRAIN_API_KEY')
        self.secret_key = os.getenv('FUSIONBRAIN_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("API ключи не найдены в .env файле")
        
        self.auth_headers = {
            'X-Key': f'Key {self.api_key}',
            'X-Secret': f'Secret {self.secret_key}',
        }
    
    def get_pipeline(self) -> str:
        """Получает ID доступного пайплайна (модели)"""
        try:
            response = requests.get(
                self.url + 'key/api/v1/pipelines', 
                headers=self.auth_headers
            )
            response.raise_for_status()
            data = response.json()
            return data[0]['id']
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при получении пайплайна: {e}")
    
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024) -> str:
        """Запускает генерацию изображения и возвращает UUID задачи"""
        pipeline_id = self.get_pipeline()
        
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {
                "query": prompt
            }
        }
        
        data = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        
        try:
            response = requests.post(
                self.url + 'key/api/v1/pipeline/run', 
                headers=self.auth_headers, 
                files=data
            )
            response.raise_for_status()
            result = response.json()
            return result['uuid']
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при запуске генерации: {e}")
    
    def check_generation_status(self, request_id: str, max_attempts: int = 30, delay: int = 10) -> Optional[List[str]]:
        """Проверяет статус генерации и возвращает файлы когда готово"""
        attempts = 0
        
        while attempts < max_attempts:
            try:
                response = requests.get(
                    self.url + f'key/api/v1/pipeline/status/{request_id}', 
                    headers=self.auth_headers
                )
                response.raise_for_status()
                data = response.json()
                
                if data['status'] == 'DONE':
                    return data['result']['files']
                elif data['status'] == 'FAIL':
                    error_msg = data.get('errorDescription', 'Неизвестная ошибка')
                    raise Exception(f"Генерация не удалась: {error_msg}")
                
                attempts += 1
                time.sleep(delay)
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Ошибка при проверке статуса: {e}")
        
        raise Exception("Превышено максимальное количество попыток")
    
    def save_image_from_base64(self, base64_data: str, filename: str) -> str:
        """Сохраняет изображение из base64 в файл"""
        try:
            # Декодируем base64
            image_data = base64.b64decode(base64_data)
            
            # Создаем изображение из байтов
            image = Image.open(io.BytesIO(image_data))
            
            # Создаем папку output если её нет
            os.makedirs('output', exist_ok=True)
            
            # Сохраняем изображение
            filepath = os.path.join('output', filename)
            image.save(filepath)
            
            return filepath
        except Exception as e:
            raise Exception(f"Ошибка при сохранении изображения: {e}")

# Инициализируем API клиент
try:
    api = FusionBrainAPI()
except ValueError as e:
    print(f"Ошибка инициализации API: {e}")
    api = None

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Генерация изображения"""
    if not api:
        return jsonify({'error': 'API не инициализирован. Проверьте настройки в .env файле'}), 500
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        width = int(data.get('width', 1024))
        height = int(data.get('height', 1024))
        
        if not prompt:
            return jsonify({'error': 'Промпт не может быть пустым'}), 400
        
        # Валидация размеров
        valid_sizes = [
            (512, 512), (768, 768), (1024, 1024),
            (512, 768), (768, 512), (1024, 768), (768, 1024)
        ]
        
        if (width, height) not in valid_sizes:
            return jsonify({'error': 'Недопустимый размер изображения'}), 400
        
        # Запускаем генерацию
        request_id = api.generate_image(prompt, width, height)
        
        return jsonify({
            'success': True,
            'request_id': request_id,
            'message': 'Генерация запущена'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status/<request_id>')
def check_status(request_id):
    """Проверка статуса генерации"""
    if not api:
        return jsonify({'error': 'API не инициализирован'}), 500
    
    try:
        # Проверяем статус один раз без ожидания
        response = requests.get(
            api.url + f'key/api/v1/pipeline/status/{request_id}', 
            headers=api.auth_headers
        )
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'DONE':
            files = data['result']['files']
            if files and len(files) > 0:
                # Создаем имя файла с временной меткой
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_{timestamp}.png"
                
                # Сохраняем изображение
                filepath = api.save_image_from_base64(files[0], filename)
                
                return jsonify({
                    'status': 'DONE',
                    'image_url': f'/image/{filename}',
                    'filename': filename
                })
            else:
                return jsonify({'status': 'FAIL', 'error': 'Файлы не найдены в результате'})
                
        elif data['status'] == 'FAIL':
            error_msg = data.get('errorDescription', 'Неизвестная ошибка')
            return jsonify({'status': 'FAIL', 'error': f"Генерация не удалась: {error_msg}"})
            
        else:
            # INITIAL или PROCESSING
            return jsonify({'status': 'PROCESSING'})
            
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'FAIL', 'error': f"Ошибка при проверке статуса: {e}"})
    except Exception as e:
        return jsonify({'status': 'FAIL', 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    """Скачивание сгенерированного изображения"""
    try:
        filepath = os.path.join('output', filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'Файл не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/image/<filename>')
def serve_image(filename):
    """Отображение изображения"""
    try:
        filepath = os.path.join('output', filename)
        if os.path.exists(filepath):
            return send_file(filepath)
        else:
            return jsonify({'error': 'Файл не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def open_browser():
    """Открывает браузер с веб-интерфейсом"""
    time.sleep(1.5)  # Ждем запуска сервера
    webbrowser.open('http://localhost:8080')

if __name__ == '__main__':
    print("🚀 Запускаем FusionBrain Image Generator...")
    print("🌐 Веб-интерфейс будет доступен по адресу: http://localhost:8080")
    print("📱 Браузер откроется автоматически...")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    # Запускаем браузер в отдельном потоке
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Запускаем Flask сервер
    app.run(debug=False, host='127.0.0.1', port=8080, use_reloader=False)
