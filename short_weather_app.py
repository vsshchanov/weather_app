import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from io import BytesIO
from collections import namedtuple, defaultdict
from itertools import islice
from PIL import Image, ImageTk

# ========== КОНФИГУРАЦИЯ ==========
API_KEY = "9e7051ac97e49c3521ebc6abed882902"
LAST_CITY_FILE = "last_city.json"
HISTORY_FILE = "history.json"

# ========== КЭШ ИКОНОК ==========
_icon_cache = {}

# ========== РАБОТА С ФАЙЛАМИ ==========
def save_last_city(city):
    try:
        with open(LAST_CITY_FILE, "w", encoding="utf-8") as f:
            json.dump({"city": city}, f)
    except Exception as e:
        print(f"Не удалось сохранить последний город: {e}")

def load_last_city():
    if os.path.exists(LAST_CITY_FILE):
        try:
            with open(LAST_CITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("city", "")
        except Exception as e:
            print(f"Ошибка чтения last_city: {e}")
    return ""

def update_history(city):
    history = load_history()
    if city in history:
        history.remove(city)
    history.insert(0, city)
    history = history[:5]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"cities": history}, f)
    except Exception as e:
        print(f"Не удалось сохранить историю: {e}")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("cities", [])
        except Exception as e:
            print(f"Ошибка чтения истории: {e}")
    return []

# ========== ОБЩИЙ ЗАПРОС К API ==========
def fetch_weather_data(city, forecast=False):
    """Универсальная функция для запроса текущей погоды или прогноза"""
    endpoint = "forecast" if forecast else "weather"
    url = f"https://api.openweathermap.org/data/2.5/{endpoint}"
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'ru'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {'error': 'Город не найден'}
        else:
            return {'error': f'Ошибка API: {response.status_code}'}
    except requests.exceptions.ConnectionError:
        return {'error': 'Ошибка подключения к интернету'}
    except requests.exceptions.Timeout:
        return {'error': 'Превышено время ожидания'}
    except Exception as e:
        return {'error': f'Ошибка: {str(e)}'}

# ========== ЗАГРУЗКА ИКОНОК (С КЭШЕМ) ==========
def load_weather_icon(icon_code):
    if icon_code in _icon_cache:
        return _icon_cache[icon_code]
    url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
    try:
        response = requests.get(url, timeout=5)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        photo = ImageTk.PhotoImage(img)
        _icon_cache[icon_code] = photo
        return photo
    except Exception:
        return None

# ========== ПАРСИНГ ТЕКУЩЕЙ ПОГОДЫ ==========
WeatherInfo = namedtuple('WeatherInfo', ['text', 'temp', 'desc', 'icon'])

def parse_weather_data(weather_data):
    if 'error' in weather_data:
        return WeatherInfo(weather_data['error'], None, None, None)

    try:
        city_name = weather_data['name']
        main = weather_data['main']
        wind = weather_data['wind']
        weather = weather_data['weather'][0]
        sys = weather_data['sys']

        temp = main['temp']
        feels_like = main['feels_like']
        humidity = main['humidity']
        pressure = main['pressure']
        wind_speed = wind['speed']
        weather_desc = weather['description']
        weather_main = weather['main']
        icon_code = weather['icon']

        sunrise = datetime.fromtimestamp(sys['sunrise']).strftime('%H:%M')
        sunset = datetime.fromtimestamp(sys['sunset']).strftime('%H:%M')
        
        result = f"Погода в городе {city_name}:\n"
        result += f"Температура: {temp:.1f}°C (ощущается как {feels_like:.1f}°C)\n"
        result += f"Влажность: {humidity}%\n"
        result += f"Ветер: {wind_speed:.1f} м/с\n"
        result += f"Атмосферное давление {pressure} гПа\n"
        result += f"Восход: {sunrise}, Закат: {sunset}\n"
        result += f"{weather_desc.capitalize()}"

        return WeatherInfo(result, temp, weather_desc, icon_code)

    except KeyError as e:
        return WeatherInfo(f'Ошибка обработки данных: {str(e)}', None, None, None)

# ========== ПАРСИНГ ПРОГНОЗА ==========
def parse_forecast_data(forecast_data):
    if 'error' in forecast_data:
        return forecast_data['error']

    try:
        forecast_list = forecast_data.get('list', [])
        if not forecast_list:
            return "Нет данных прогноза"

        days = defaultdict(list)
        for item in forecast_list:
            dt_str = item['dt_txt']
            date = dt_str.split()[0]
            time = dt_str.split()[1][:5]
            temp = item['main']['temp']
            desc = item['weather'][0]['description']
            days[date].append((time, temp, desc))

        result = "Прогноз на 5 дня (каждые 3 часа):\n\n"
        for i, (date, forecasts) in enumerate(islice(days.items(), 5)):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_str = date_obj.strftime('%d.%m.%Y')
            result += f"{date_str}:\n"
            for time, temp, desc in forecasts:
                result += f"   {time} - {temp:.1f}°C, {desc}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"Ошибка при обработке прогноза: {str(e)}"

# ========== ГЛАВНОЕ ОКНО ==========
class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Погодное приложение")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.current_icon = None

        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        # Заголовок
        tk.Label(self.root, text="Погодное приложение", font=("Arial", 18, "bold")).pack(pady=10)

        # Рамка ввода
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="Город:", font=("Arial", 12)).grid(row=0, column=0, padx=5)
        self.city_entry = tk.Entry(input_frame, width=20, font=("Arial", 12))
        self.city_entry.grid(row=0, column=1, padx=5)
        self.city_entry.bind("<Return>", lambda e: self.get_current_weather())

        tk.Label(input_frame, text="История:", font=("Arial", 12)).grid(row=0, column=2, padx=5)
        self.history_combo = ttk.Combobox(input_frame, width=15, font=("Arial", 10))
        self.history_combo.grid(row=0, column=3, padx=5)
        self.history_combo.bind("<<ComboboxSelected>>", self.on_history_selected)

        # Кнопки
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        self.weather_btn = tk.Button(btn_frame, text="Текущая погода", command=self.get_current_weather,
                                     bg="#4CAF50", fg="white", font=("Arial", 11), padx=10)
        self.weather_btn.grid(row=0, column=0, padx=10)
        self.forecast_btn = tk.Button(btn_frame, text="Прогноз на 3 дня", command=self.get_forecast_weather,
                                      bg="#2196F3", fg="white", font=("Arial", 11), padx=10)
        self.forecast_btn.grid(row=0, column=1, padx=10)

        # Иконка
        self.icon_label = tk.Label(self.root, text="")
        self.icon_label.pack(pady=5)

        # Текстовое поле
        self.result_text = tk.Text(self.root, height=18, width=70, font=("Arial", 10),
                                   wrap="word", bd=2, relief="solid", bg="#f0f0f0")
        self.result_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.result_text.config(state="disabled")

        # Кнопка очистки
        tk.Button(self.root, text="Очистить", command=self.clear_output,
                  bg="#f44336", fg="white", font=("Arial", 10)).pack(pady=5)

    def load_initial_data(self):
        self.history_combo['values'] = load_history()
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
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state="disabled")
        self.icon_label.config(image='', text='')
        self.current_icon = None

    def update_result(self, text):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self.result_text.config(state="disabled")

    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (устранение дублирования) =====
    def _save_city_state(self, city):
        save_last_city(city)
        update_history(city)
        self.history_combo['values'] = load_history()

    def _validate_and_prepare(self, request_type="погоду"):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Предупреждение", "Введите название города!")
            return None
        self.update_result(f"Загружаем {request_type}...")
        self.root.update()
        return city

    def _update_icon(self, icon_code):
        if icon_code:
            img = load_weather_icon(icon_code)
            if img:
                self.current_icon = img
                self.icon_label.config(image=self.current_icon, text='')
            else:
                self.icon_label.config(image='', text='(иконка не загружена)')
        else:
            self.icon_label.config(image='', text='')

    # ===== ОСНОВНЫЕ МЕТОДЫ =====
    def get_current_weather(self):
        city = self._validate_and_prepare("погоду")
        if not city:
            return

        data = fetch_weather_data(city, forecast=False)
        if 'error' in data:
            self.update_result(f"Ошибка: {data['error']}")
            return

        info = parse_weather_data(data)
        self.update_result(info.text)
        self._update_icon(info.icon)
        self._save_city_state(city)

    def get_forecast_weather(self):
        city = self._validate_and_prepare("прогноз")
        if not city:
            return

        data = fetch_weather_data(city, forecast=True)
        if 'error' in data:
            self.update_result(f"Ошибка: {data['error']}")
            return

        forecast_text = parse_forecast_data(data)
        self.update_result(forecast_text)
        self.icon_label.config(image='', text='')
        self._save_city_state(city)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()