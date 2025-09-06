class FusionBrainApp {
    constructor() {
        this.selectedWidth = 1024;
        this.selectedHeight = 1024;
        this.currentRequestId = null;
        this.statusCheckInterval = null;
        
        this.initializeEventListeners();
        this.updateCharCounter();
    }
    
    initializeEventListeners() {
        // Счетчик символов
        const promptTextarea = document.getElementById('prompt');
        promptTextarea.addEventListener('input', () => this.updateCharCounter());
        
        // Выбор размера изображения
        const sizeOptions = document.querySelectorAll('.size-option');
        sizeOptions.forEach(option => {
            option.addEventListener('click', () => this.selectSize(option));
        });
        
        // Кнопка генерации
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.addEventListener('click', () => this.generateImage());
        
        // Кнопки действий
        const copyBtn = document.getElementById('copyBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        
        copyBtn.addEventListener('click', () => this.copyImage());
        downloadBtn.addEventListener('click', () => this.downloadImage());
    }
    
    updateCharCounter() {
        const prompt = document.getElementById('prompt');
        const charCount = document.getElementById('charCount');
        charCount.textContent = prompt.value.length;
        
        if (prompt.value.length > 900) {
            charCount.style.color = '#dc3545';
        } else if (prompt.value.length > 700) {
            charCount.style.color = '#ffc107';
        } else {
            charCount.style.color = '#666';
        }
    }
    
    selectSize(option) {
        // Убираем активный класс со всех опций
        document.querySelectorAll('.size-option').forEach(opt => {
            opt.classList.remove('active');
        });
        
        // Добавляем активный класс к выбранной опции
        option.classList.add('active');
        
        // Сохраняем выбранные размеры
        this.selectedWidth = parseInt(option.dataset.width);
        this.selectedHeight = parseInt(option.dataset.height);
    }
    
    async generateImage() {
        const prompt = document.getElementById('prompt').value.trim();
        
        if (!prompt) {
            this.showToast('Введите описание изображения', 'error');
            return;
        }
        
        if (prompt.length > 1000) {
            this.showToast('Описание слишком длинное (максимум 1000 символов)', 'error');
            return;
        }
        
        // Блокируем кнопку и показываем результат
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерируем...';
        
        const resultSection = document.getElementById('resultSection');
        const imageContainer = document.getElementById('imageContainer');
        
        resultSection.style.display = 'block';
        imageContainer.style.display = 'none';
        
        this.updateStatus('Генерируем изображение...', 'processing');
        this.updateProgress(10);
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    width: this.selectedWidth,
                    height: this.selectedHeight
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentRequestId = data.request_id;
                this.updateStatus('Обрабатываем запрос...', 'processing');
                this.updateProgress(30);
                this.startStatusCheck();
            } else {
                throw new Error(data.error || 'Ошибка генерации');
            }
            
        } catch (error) {
            this.showToast(`Ошибка: ${error.message}`, 'error');
            this.resetGenerateButton();
        }
    }
    
    startStatusCheck() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
        
        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${this.currentRequestId}`);
                const data = await response.json();
                
                if (data.status === 'DONE') {
                    this.updateProgress(100);
                    this.updateStatus('Готово!', 'success');
                    this.displayImage(data.image_url, data.filename);
                    this.resetGenerateButton();
                    clearInterval(this.statusCheckInterval);
                } else if (data.status === 'FAIL') {
                    throw new Error(data.error || 'Генерация не удалась');
                } else {
                    // Продолжаем ждать
                    this.updateProgress(Math.min(90, this.getCurrentProgress() + 2));
                }
                
            } catch (error) {
                this.showToast(`Ошибка: ${error.message}`, 'error');
                this.resetGenerateButton();
                clearInterval(this.statusCheckInterval);
            }
        }, 2000);
    }
    
    displayImage(imageUrl, filename) {
        const imageContainer = document.getElementById('imageContainer');
        const generatedImage = document.getElementById('generatedImage');
        const imageSize = document.getElementById('imageSize');
        const imageFilename = document.getElementById('imageFilename');
        
        generatedImage.src = imageUrl;
        imageSize.textContent = `${this.selectedWidth}×${this.selectedHeight} пикселей`;
        imageFilename.textContent = filename;
        
        imageContainer.style.display = 'block';
        
        // Сохраняем данные для копирования/скачивания
        this.currentImageUrl = imageUrl;
        this.currentFilename = filename;
        
        this.showToast('Изображение готово!', 'success');
    }
    
    async copyImage() {
        try {
            const response = await fetch(this.currentImageUrl);
            const blob = await response.blob();
            
            await navigator.clipboard.write([
                new ClipboardItem({
                    [blob.type]: blob
                })
            ]);
            
            this.showToast('Изображение скопировано в буфер обмена!', 'success');
        } catch (error) {
            this.showToast('Не удалось скопировать изображение', 'error');
        }
    }
    
    downloadImage() {
        const link = document.createElement('a');
        link.href = `/download/${this.currentFilename}`;
        link.download = this.currentFilename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.showToast('Скачивание началось!', 'success');
    }
    
    updateStatus(text, type) {
        const statusText = document.getElementById('statusText');
        const statusIndicator = document.getElementById('statusIndicator');
        
        statusText.textContent = text;
        
        // Обновляем иконку в зависимости от типа
        const icon = statusIndicator.querySelector('i');
        icon.className = '';
        
        switch (type) {
            case 'processing':
                icon.className = 'fas fa-spinner fa-spin';
                break;
            case 'success':
                icon.className = 'fas fa-check-circle';
                icon.style.color = '#28a745';
                break;
            case 'error':
                icon.className = 'fas fa-exclamation-circle';
                icon.style.color = '#dc3545';
                break;
        }
    }
    
    updateProgress(percentage) {
        const progressFill = document.getElementById('progressFill');
        progressFill.style.width = `${percentage}%`;
    }
    
    getCurrentProgress() {
        const progressFill = document.getElementById('progressFill');
        return parseInt(progressFill.style.width) || 0;
    }
    
    resetGenerateButton() {
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> Сгенерировать изображение';
    }
    
    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastIcon = toast.querySelector('.toast-icon');
        const toastMessage = toast.querySelector('.toast-message');
        
        // Убираем предыдущие классы
        toast.className = 'toast';
        
        // Добавляем новый класс типа
        toast.classList.add(type);
        
        // Устанавливаем иконку
        if (type === 'success') {
            toastIcon.className = 'toast-icon fas fa-check-circle';
        } else if (type === 'error') {
            toastIcon.className = 'toast-icon fas fa-exclamation-circle';
        }
        
        // Устанавливаем сообщение
        toastMessage.textContent = message;
        
        // Показываем toast
        toast.classList.add('show');
        
        // Скрываем через 3 секунды
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Инициализируем приложение когда DOM загружен
document.addEventListener('DOMContentLoaded', () => {
    new FusionBrainApp();
});
