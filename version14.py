import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageFont
import io
import time
import re

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- КОНСТАНТЫ И СТИЛИ ---
COLOR_CODES = ["UWW", "EWW", "WW", "NW", "CW", "RGB", "RGBW", "R", "G", "B", "Y"]

# Цвета для иконок на картинке
COLOR_MAP_BG = {
    "UWW": "#FCE166", "EWW": "#FAF39D", "WW": "#AFAFAF", "NW": "#FFFFFF", "CW": "#EAF6FE",
    "SMD 2835": "#AFCB08", "SMD 5050": "#004F9F", "COB": "#A5C846"
}
COLOR_MAP_IP = {"IP20": "#14AC98", "IP67": "#774495"}

# Настройки темной темы интерфейса
DARK_BG = "#2D2D2D"
DARK_FIELD = "#3D3D3D"
TEXT_COLOR = "#FFFFFF"

BADGE_LAYOUT = {
    "color":   {"label": "Barva",    "x": 50,  "y": 50,  "sub": "1900-2100K", "src": "Barva světla:"},
    "chip":    {"label": "Čip",     "x": 185, "y": 50,  "sub": "",            "src": "Typ čipu:"},
    "leds":    {"label": "LED/m",   "x": 320, "y": 50,  "sub": "LED/m",       "src": "Počet LED:"},
    "power":   {"label": "W/m",     "x": 455, "y": 50,  "sub": "W/m",         "src": "Výkon на метр:"},
    "voltage": {"label": "Napětí",  "x": 185, "y": 185, "sub": "V DC",        "src": "Napětí světel:"},
    "ip":      {"label": "IP",      "x": 50,  "y": 185, "sub": "",            "src": "Stupeň krytí:"}
}

class LedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("McLED Dark Designer 14.0")
        self.root.geometry("900x800")
        self.root.configure(bg=DARK_BG)

        # Настройка стиля Combobox для темной темы
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=DARK_FIELD, background=DARK_FIELD, foreground=TEXT_COLOR)
        style.map("TCombobox", fieldbackground=[('readonly', DARK_FIELD)], foreground=[('readonly', TEXT_COLOR)])

        # URL блок
        frame_top = tk.Frame(root, bg=DARK_BG, pady=20)
        frame_top.pack(fill="x", padx=20)
        
        tk.Label(frame_top, text="URL:", bg=DARK_BG, fg=TEXT_COLOR).pack(side="left")
        self.url_input = tk.Entry(frame_top, width=50, bg=DARK_FIELD, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, borderwidth=0)
        self.url_input.pack(side="left", padx=10, ipady=3)
        self.url_input.insert(0, "https://www.mcled.cz/ml-126-076-90-x")
        
        tk.Button(frame_top, text="ЗАГРУЗИТЬ", command=self.fetch_data, bg="#E91E63", fg="white", font=("Arial", 9, "bold"), borderwidth=0, padx=15).pack(side="left")

        # Поля параметров
        self.combos = {}
        frame_mid = tk.LabelFrame(root, text=" Параметры ", bg=DARK_BG, fg="#00BCD4", padx=20, pady=20, font=("Arial", 10, "bold"))
        frame_mid.pack(fill="both", expand=True, padx=20)

        for key, info in BADGE_LAYOUT.items():
            f = tk.Frame(frame_mid, bg=DARK_BG, pady=8)
            f.pack(fill="x")
            tk.Label(f, text=info['label'], width=12, anchor="w", bg=DARK_BG, fg=TEXT_COLOR).pack(side="left")
            
            # Задаем предустановленные значения
            vals = []
            if key == "color": vals = COLOR_CODES
            elif key == "ip": vals = ["IP20", "IP54", "IP67", "IP68"]
            
            cb = ttk.Combobox(f, values=vals, width=35)
            cb.pack(side="left")
            self.combos[key] = cb

        # Кнопка генерации
        tk.Button(root, text="СГЕНЕРИРОВАТЬ ИЗОБРАЖЕНИЕ", command=self.build_image, 
                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), borderwidth=0, pady=15).pack(fill="x", padx=20, pady=30)

    def fetch_data(self):
        url = self.url_input.get()
        options = Options()
        options.add_argument("--headless")
        
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            time.sleep(4)
            source = driver.page_source
            driver.quit()

            for key, info in BADGE_LAYOUT.items():
                # Улучшенный поиск: ищем название параметра, идем до следующего значения
                pattern = re.escape(info['src']) + r".*?>(.*?)<"
                match = re.search(pattern, source, re.IGNORECASE | re.DOTALL)
                
                if match:
                    raw_val = re.sub('<[^<]+?>', '', match.group(1)).strip()
                    
                    if key == "color":
                        found = ""
                        for code in COLOR_CODES:
                            if re.search(r'\b' + code + r'\b', raw_val.upper()):
                                found = code; break
                        clean_val = found if found else raw_val
                    elif key == "leds" or key == "voltage":
                        # Берем только цифры (для LED/m и Напряжения)
                        num = re.search(r'\d+([\.,]\d+)?', raw_val)
                        clean_val = num.group(0) if num else raw_val
                    else:
                        clean_val = raw_val

                    self.combos[key].set(clean_val)
            
            self.show_status("OK", "Данные обновлены!")
        except Exception as e:
            self.show_status("Error", f"Ошибка: {e}")

    def build_image(self):
        canvas = Image.new('RGB', (1000, 1000), 'white')
        draw = ImageDraw.Draw(canvas)
        
        try:
            f_main = ImageFont.truetype("arialbd.ttf", 34)
            f_sub = ImageFont.truetype("arial.ttf", 18)
        except:
            f_main = f_sub = ImageFont.load_default()

        for key, info in BADGE_LAYOUT.items():
            val = self.combos[key].get().strip()
            if not val: continue

            bg, tc = "#EEEEEE", "black"
            for code, color in COLOR_MAP_BG.items():
                if code in val.upper(): bg = color; break
            if key == "ip":
                for code, color in COLOR_MAP_IP.items():
                    if code in val.upper(): tc = color; break

            x, y, size = info['x'], info['y'], 120
            draw.rectangle([x, y, x + size, y + size], fill=bg)

            # Текст в две строки
            txt_t, txt_b = val, info['sub']
            
            # Центрирование
            bt = draw.textbbox((0, 0), txt_t, font=f_main)
            wt, ht = bt[2]-bt[0], bt[3]-bt[1]
            bb = draw.textbbox((0, 0), txt_b, font=f_sub)
            wb, hb = bb[2]-bb[0], bb[3]-bb[1]

            y_off = (size - (ht + hb + 10)) / 2
            draw.text((x + (size - wt)/2, y + y_off), txt_t, fill=tc, font=f_main)
            draw.text((x + (size - wb)/2, y + y_off + ht + 10), txt_b, fill=tc, font=f_sub)

        canvas.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = LedApp(root)
    root.mainloop()