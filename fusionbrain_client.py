import json
import time
import base64
import os
from datetime import datetime
from typing import Optional, List

import requests
from dotenv import load_dotenv
from PIL import Image
import io

# Загружаем переменные окружения
load_dotenv('.env')


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
                
                print(f"Статус: {data['status']} (попытка {attempts + 1}/{max_attempts})")
                
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


def main():
    """Основная функция программы"""
    print("🎨 FusionBrain Image Generator")
    print("=" * 40)
    
    try:
        # Создаем клиент API
        api = FusionBrainAPI()
        
        # Запрашиваем промпт у пользователя
        prompt = input("Введите описание изображения: ").strip()
        
        if not prompt:
            print("❌ Промпт не может быть пустым!")
            return
        
        print(f"\n🚀 Генерируем изображение: '{prompt}'")
        print("⏳ Это может занять несколько минут...")
        
        # Запускаем генерацию
        request_id = api.generate_image(prompt, width=1024, height=1024)
        print(f"📋 ID задачи: {request_id}")
        
        # Ждем завершения и получаем результат
        files = api.check_generation_status(request_id)
        
        if files and len(files) > 0:
            # Создаем имя файла с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            
            # Сохраняем изображение
            filepath = api.save_image_from_base64(files[0], filename)
            
            print(f"✅ Изображение успешно сохранено: {filepath}")
            print(f"📁 Размер: 1024x1024 пикселей")
        else:
            print("❌ Не удалось получить изображение")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
