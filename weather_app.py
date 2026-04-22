import requests
import json 
import tkinter as tk
from tkinter import messagebox

# Функция для запроса погоды
def get_weather(city, api_key):
    '''
    Получает погоду для указанного города через OpenWeatherMap API
    '''
    #Базовый URL для запроса
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    # Параметры запроса
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric', # Температура в Цельсиях
        'lang': 'ru' # Описание на русском
    }
    
    try:
        # Отправляем GET-запрос к API [citation:2][citation:6]
        response = requests.get(base_url, params=params, timeout=10)
        
        # Проверяем статус ответа [citation:6]
        if response.status_code == 200:
            # Преобразуем JSON-ответ в словарь Python
            weather_data = response.json()
            return weather_data
        elif response.status_code == 404:
            return {'error': 'Город не неайден'}
        else:
            return {'error': f'Ошибка API: {response.status_code}'}
    except requests.exceptions.ConnectionError:
        return {'error': 'Ошибка подключения к интернету'}
    except requests.exceptions.Timeout:
        return {'error': 'Превышено время ожидания ответа'}
    except Exception as e:
        return {'error':f'Неизвестная ошибка: {str(e)}'}

# Функция для обработки данных погоды
def parse_weather_data(weather_data):
    '''
    Извлекает нужную информацию из данных, полученных от API
    '''
    if 'error' in weather_data:
        return weather_data['error'], None, None
    
    try:
        # Извлекаем данные из JSON-структуры [citation:1]
        city_name = weather_data['name']
        temperature =weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        weather_description = weather_data['weather'][0]['description']
        weather_main = weather_data['weather'][0]['main']
        
        """
        weather_emoji = {
            'Clear': '☀️',
            'Clouds': '☁️',
            'Rain': '🌧️',
            'Snow': '❄️',
            'Thunderstorm': '⛈️',
            'Drizzle': '🌦️',
            'Mist': '🌫️',
            'Fog': '🌫️'
        }.get(weather_main,'🌡️')
        """
    
        # Формируем строку с результатом
        # result = f"{weather_emoji} Погода в городе {city_name}:\n"
        result = f'Погода в городе {city_name}:\n'
        result += f'Температура: {temperature:.1f}°C\n'
        result += f'Ощущается как: {feels_like:.1f}°C\n'
        result += f'Влажность: {humidity}%\n'
        result += f'Описание: {weather_description}'
    
        return result, temperature, weather_description

    except KeyError as e:
        return f'Ошибка при обработке данных: {str(e)}', None, None
    
# Графический интерфейс с Tkinter
def create_weather_app():
    '''Создаём главное окно приложения'''
    
    # Ваш API-ключ от OpenWeaterMap
    API_KEY = "9e7051ac97e49c3521ebc6abed882902"
    
    # Создаём главное окно [citation:7]
    window = tk.Tk()
    window.title('Погодное приложение')
    window.geometry('450x350')
    window.resizable(False, False) # Запрещаем изменение размеров окна
    
    # Заголовок
    title_lable = tk.Label(
        window,
        text='Погодное приложение',
        font=("Apial", 18, 'bold')
    )
    title_lable.pack(pady=10)
    
    # Создаём рамку для ввода города [citation:7]
    input_frame = tk.Frame(window, padx=20, pady=10)
    input_frame.pack()
    
    # Метка "Введите город"
    city_label = tk.Label(
        input_frame,
        text='Введите название города:',
        font=('Arial', 12)
    )
    city_label.pack(anchor='w')
    
    # Поле для ввода названия города [citation:3]
    city_entry = tk.Entry(
        input_frame,
        width=30,
        font=('Arial', 12),
        bd=2,
        relief='solid'
    )
    city_entry.pack(pady=5)
    city_entry.focus() # Устанавливаем курсор в это поле
    
    # Кнопка для получения погоды
    def on_get_weather():
        """Обработчик нажатия на кнопку"""
        city = city_entry.get().strip()
        
        if not city:
            messagebox.showwarning('Предупреждение!', 'Введите название города!')
            return
        
        # Показываем сообщение о загрузке
        result_text.config(state='normal')
        result_text.delete('1.0', tk.END)
        result_text.insert('1.0', 'Загружаем данные...')
        result_text.config(state='disabled')
        window.update()
        
        # Получаем погоду
        weather_data = get_weather(city, API_KEY)
        result, temp, desc = parse_weather_data(weather_data)
        
        # Отображаем результат
        result_text.config(state='normal')
        result_text.delete('1.0', tk.END)
        result_text.insert('1.0', result)
        result_text.config(state='disabled')
    
    get_weather_btn = tk.Button(
        input_frame,
        text="Узнать погоду",
        font=('Arial', 12),
        bg='#4CAF50',
        fg='white',
        padx=20,
        pady=5,
        command=on_get_weather
    )
    get_weather_btn.pack(pady=10)
    
    # Рамка для отображения результата 
    result_frame = tk.Frame(window, padx=20, pady=10)
    result_frame.pack(fill='both', expand=True)
    
    # Текстовое поле для результата [citation:3]
    result_text = tk.Text(
        result_frame,
        height=8,
        width=45,
        font=('Arial', 11),
        wrap='word',
        bd=2,
        relief='solid',
        bg='#f0f0f0'
    )
    result_text.pack(fill='both', expand=True)
    result_text.config(state='disabled') # Запрещаем редактирование
    
    # Кнопка для очистки
    def on_clear():
        city_entry.delete(0, tk.END)
        result_text.config(state='normal')
        result_text.delete('1.0', tk.END)
        result_text.config(state='disabled')
        
    clear_btn = tk.Button(
        window,
        text="Очистить",
        font=('Arial', 10),
        bg='#f44336',
        fg='white',
        command=on_clear
    )
    clear_btn.pack(pady=5)
    
    return window

# Запуск приложения
def main():
    app = create_weather_app()
    app.mainloop() # Запускаем цикл обработки событий [citation:3][citation:7]
    
if __name__ == '__main__':
    main()