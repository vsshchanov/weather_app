import requests
import json 
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageTk

# API-ключ OpenWeatherMap
API_KEY = "9e7051ac97e49c3521ebc6abed882902"

LAST_CITY_FILE = 'last_city.json'
HISTORY_FILE = 'history.json'

# Сохраняет последний запрошенный город
def save_last_city(city):
    '''Сохраняет последний запрошенный город'''
    try:
        with open(LAST_CITY_FILE, 'w', encoding='utf-8') as f:
            json.dump({'city': city}, f)
    except Exception:
        pass

# Загружает последний город из файла
def load_last_city():
    """Загружает последний город из файла"""
    if os.path.exists(LAST_CITY_FILE):
        try:
            with open(LAST_CITY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('city', '')
        except Exception:
            return ""
    return

# Обновляет историю запросов
def update_history(city):
    """Обновляет историю запросов (до 5 уникальных городов)"""
    history = load_history()
    if city in history:
        history.remove(city)
    history.insert(0, city)
    history = history[:5]
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"cities": history}, f)
        print(f'История сохранена: {history}')
    except Exception as e:
        print(f"Ошибка при сохранении истории: {e}")
    
# Загружает историю запросов
def load_history():
    """Загружает историю запросов"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding="utf-8") as f:
                data = json.load(f)
                return data.get('cities', [])
        except Exception as e:
            print(f"Ошибка при загрузке истории: {e}")
            return []
    return[]

# Функция для запроса погоды
def get_weather(city):
    '''
    Получает погоду для указанного города через OpenWeatherMap API
    '''
    #Базовый URL для запроса
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    # Параметры запроса
    params = {
        'q': city,
        'appid': API_KEY,
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

# Прогноз на несколько дней
def get_forecast(city):
    '''
    Прогноз на несколько дней 
    OpenWeatherMap предоставляет бесплатный прогноз 
    на 5 дней с шагом 3 часа
    '''
    forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'ru',
        #'cnt': 8 # Ограничиваем до 8 записей = 1 день 
    }

    try:
        response = requests.get(forecast_url, params=params, timeout=10)
        # Проверяем статус ответа [citation:6]
        if response.status_code == 200:
            # Преобразуем JSON-ответ в словарь Python
            weather_data = response.json()
            return weather_data
        elif response.status_code == 404:
            return {'error': 'Город не неайден'}
        else:
            return {'error': f'Ошибка API: {response.status_code}'}
    except Exception as e:
        return {'error':f'Неизвестная ошибка: {str(e)}'}

def load_weather_icon(icon_code):
    """Загружаем иконку погоды из OpenWeatherMap и возвращает PhotoImage""" 
    icon_url = f'https://openweathermap.org/img/wn/{icon_code}@2x.png'
    try:
        response = requests.get(icon_url, timeout=5)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        return ImageTk.PhotoImage(img)
    except Exception:
        return None
    
# Функция для обработки данных погоды
def parse_weather_data(weather_data):
    '''
    Извлекает нужную информацию из данных, полученных от API
    Возвращает: (текст_для_вывода, температура, описание, иконка_код, доп_текст)
    '''
    if 'error' in weather_data:
        return weather_data['error'], None, None, None, None
    
    try:
        # Извлекаем данные из JSON-структуры [citation:1]
        city_name = weather_data['name']
        temperature = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        pressure = weather_data['main']['pressure']
        wind_speed = weather_data['wind']['speed']
        weather_desc = weather_data['weather'][0]['description']
        weather_main = weather_data['weather'][0]['main']
        icon_code = weather_data['weather'][0]['icon']
        
        # Время восхода и заката 
        sunrise_ts = weather_data['sys']['sunrise']
        sunset_ts = weather_data['sys']['sunset']
        sunrise = datetime.fromtimestamp(sunrise_ts).strftime('%H:%M')
        sunset = datetime.fromtimestamp(sunset_ts).strftime('%H:%M')  
        
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
        result += f'Температура: {temperature:.1f}°C (ощущается как {feels_like:.1f}°C)\n'
        result += f'Влажность: {humidity}%\n'
        result += f'Ветер: {wind_speed:.1f} м/с\n'
        result += f'Давление: {pressure} гПа\n'
        result += f'Восход: {sunrise}, Заказ: {sunset}\n'
        result += f'Описание: {weather_desc.capitalize()}'
        
        return result, temperature, weather_desc, icon_code

    except KeyError as e:
        return f'Ошибка при обработке данных: {str(e)}', None, None, None, None

# Извлекает прогноз на 3 дня
def parse_forecast_data(forecast_data):
    """Извлекает прогноз на 5 днtq (группирует по дням, 
    показывает время и температуру)"""
    
    if 'error' in forecast_data:
        return forecast_data['error']
    
    try:
        # Получаем список прогнозов (каждые 3 часа)
        forecast_list = forecast_data.get('list', [])
        if not forecast_list:
            return "Нет данных прогноза"
        
        # Группируем по дате
        from collections import defaultdict
        days = defaultdict(list)
        for item in forecast_list:
            dt_str = item['dt_txt'] # '2025-04-23 12:00:00'
            date = dt_str.split()[0]
            time = dt_str.split()[1][:5]
            temp = item['main']['temp']
            desc = item['weather'][0]['description']
            days[date].append((time, temp, desc))
            
        # Берём первые 5 дня 
        result = " Прогноз на 5 дней (каждые 3 часа):\n\n"
        for i, (date, forecasts) in enumerate(days.items()):
            if i >= 5:
                break
            # Преобразуем дату в читаемый формат
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_str = date_obj.strftime('%d.%m.%Y')
            result += f"{date_str}:\n"
            for time, temp, desc in forecasts:
                result += f"{time} - {temp:.1f}°C, {desc}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"Ошибка при обработке прогноза: {str(e)}" 
            
# Графический интерфейс с Tkinter
class WeatherApp:
    def __init__(self, root):
        self.root = root 
        self.root.title("Погодное приложение")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # Переменна для хранения тукещей иконки 
        self.current_icon = None
        
        self.create_widgets()
        self.load_initial_data()
        
    def create_widgets(self):
        # Заголовок
        title = tk.Label(self.root, text="Погодное приложение", font=('Arial', 18, 'bold'))
        title.pack(pady=10)
        
        # Рамка для ввода города
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=5)
        
        tk.Label(input_frame, text='Город:', font=('Arial', 12)).grid(row=0, column=0, padx=5)
        self.city_entry = tk.Entry(input_frame, width=20, font=('Arial', 12))
        self.city_entry.grid(row=0, column=1, padx=5)
        self.city_entry.bind("<Return>", lambda e: self.get_current_weather())
        
        # Выпадающий список историй 
        tk.Label(input_frame, text='История запросов:', font=("Arial", 12)).grid(row=0, column=2, padx=5)
        self.history_combo = ttk.Combobox(input_frame, width=15, font=("Arial", 10))
        self.history_combo.grid(row=0, column=3, padx=5)
        self.history_combo.bind("<<ComboboxSelected>>", self.on_history_selected)
        
        
        # Кнопки
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.weather_btn = tk.Button(btn_frame, text="Текущая погода", command=self.get_current_weather, 
                                     bg="#4CAF50", fg="white", font=("Arial", 11), padx=10)
        self.weather_btn.grid(row=0, column=0, padx=10)

        self.forecast_btn = tk.Button(btn_frame, text="Прогноз на 5 дней", command=self.get_forecast_weather,
                                      bg="#2196F3", fg="white", font=('Arial', 11), padx=10)
        self.forecast_btn.grid(row=0, column=1, padx=10)
        
        # Рамка для иконки и результата
        icon_frame = tk.Frame(self.root)
        icon_frame.pack(pady=5)
        
        self.icon_label = tk.Label(icon_frame, text="", font=("Arial", 10))
        self.icon_label.pack()
        
        # Текстовое поле для результата
        self.result_text = tk.Text(self.root, height=18, width=70, font=('Arial', 10),
                             wrap="word", bd=2, relief="solid", bg="#f0f0f0")
        self.result_text.pack(pady=10, padx=10, fill='both', expand=True)
        self.result_text.config(state="disabled")
        
        # Кнопка очистки
        clear_btn = tk.Button(self.root, text="Очистить", command=self.clear_output,
                               bg='#f44336', fg="white", font=("Arial", 10))
        clear_btn.pack(pady=5)
        
    def load_initial_data(self):
        # Загружаем историю
        history = load_history()
        self.history_combo['values'] = history
        # Загружаем последний город
        last_city = load_last_city()
        if last_city:
            self.city_entry.insert(0, last_city)
            self.get_current_weather()
    
    def on_history_selected(self, event):
        city = self.history_combo.get()
        if city:
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, city)
            self.get_current_weather()
    def clear_output(self):
        self.result_text.config(state="normal")
        self.result_text.delete('1.0', tk.END)
        self.result_text.config(state='disabled')
        self.icon_label.config(image='', text='')
        self.current_icon = None
        
    def update_result(self, text):
        self.result_text.config(state="normal")
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', text)
        self.result_text.config(state='disabled')

    def get_current_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning('Предупреждение!', 'Введите название города!')
            return
        
        self.update_result("Загружаем данные...")
        self.root.update()
        
        # Запрос погоды
        data = get_weather(city)
        if 'error' in data:
            self.update_result(f"Ошибка: {data['error']}")
            return
        
        # Парсинг
        result_text, temp, desc, icon_code = parse_weather_data(data)
        self.update_result(result_text)

        # Обноаяем иконку
        if icon_code:
            icon_img = load_weather_icon(icon_code)
            if icon_img:
                self.current_icon = icon_img # сохраняем ссылку
                self.icon_label.config(image=self.current_icon, text='')
            else:
                self.icon_label.config(image='', text='(Иконка не загружена)')
        else:
            self.icon_label.config(image='', text='')
        
        # Сохраняем послдений город и обновляыем историю
        save_last_city(city)
        update_history(city)
        self.history_combo['values'] = load_history()
        
    def get_forecast_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Предупреждение", "Введите название города!")
            return
        
        self.update_result('Загружаем прогноз...')
        self.root.update()
        
        data = get_forecast(city)
        if 'error' in data:
            self.update_result(f"Ошибка: {data['error']}")
            return
        
        forecast_text = parse_forecast_data(data)
        self.update_result(forecast_text)
        
        # Иконку для прогноза не показываем (или можно показать общую)
        self.icon_label.config(image='', text='')
        
        # Сохраняем город в историю
        save_last_city(city)
        update_history(city)
        self.history_combo['values'] = load_history()
        
# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()