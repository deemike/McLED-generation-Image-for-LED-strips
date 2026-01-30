import customtkinter as ctk  # Основная библиотека для современного UI
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont, ImageOps
import time
import re
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- НАСТРОЙКИ UI ---
ctk.set_appearance_mode("Dark")  # Режимы: "System" (как в ОС), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Темы: "blue" (стандарт), "green", "dark-blue"

# --- НАСТРОЙКИ ЦВЕТОВ ГЕНЕРАЦИИ ---
COLOR_MAP_LIGHT = {
    "UWW": "#FCE166", "EWW": "#FAF39D", "WW": "#FFFBDB", "NW": "#FFFFFF", "CW": "#EAF6FE",
    "R": "#FF5252", "G": "#66BB6A", "B": "#42A5F5", "Y": "#FFF176", "UV": "#531E54" 
}
COLOR_MAP_CHIP = { "SMD2835": "#AFCB08",  "SMD5050": "#004F9F",  "COB": "#A5C846" }
COLOR_MAP_IP = { "IP20": "#14AC98", "IP54": "#A68FB8",  "IP67": "#774495",  "IP68": "#774495" }
COLOR_MAP_VOLTAGE = { "24": "#009640",  "12": "#004F9F" }
RGB_COLORS = {"R": "#ED1C24", "G": "#39B54A", "B": "#0071BC"}
SUB_TEXTS = { "leds": "LED/m", "power": "W/m", "lumen": "lm/m", "width": "mm", "life": "h" }

class LedApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Настройка главного окна
        self.title("McLED Visual Pro 45.0 - Modern UI")
        self.geometry("1100x750")
        
        # Сетка для адаптивности
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- ВЕРХНИЙ БЛОК (URL) ---
        self.frame_top = ctk.CTkFrame(self, corner_radius=10)
        self.frame_top.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.lbl_url = ctk.CTkLabel(self.frame_top, text="Ссылка на товар:", font=("Roboto Medium", 14))
        self.lbl_url.pack(side="left", padx=(20, 10), pady=15)

        self.url_input = ctk.CTkEntry(self.frame_top, width=600, placeholder_text="Вставьте ссылку https://...")
        self.url_input.pack(side="left", padx=10, ipady=3)
        self.url_input.insert(0, "https://www.mcled.cz/ml-128-635-60-x")

        # Кнопка парсинга (оранжевая, как у вас было)
        self.btn_parse = ctk.CTkButton(
            self.frame_top, 
            text="СКАНИРОВАТЬ САЙТ", 
            command=self.fetch_data,
            fg_color="#E65100", 
            hover_color="#BF360C",
            font=("Roboto Medium", 13)
        )
        self.btn_parse.pack(side="left", padx=20)

        # --- СРЕДНИЙ БЛОК (ПОЛЯ ВВОДА) ---
        self.frame_mid = ctk.CTkFrame(self, corner_radius=10)
        self.frame_mid.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Заголовок блока
        ctk.CTkLabel(self.frame_mid, text="Параметры ленты", font=("Roboto Medium", 18), text_color="#4FC3F7").pack(pady=(20, 10))

        # Контейнер для сетки полей
        self.grid_container = ctk.CTkFrame(self.frame_mid, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.entries = {}
        fields = ["color", "kelvin", "chip", "leds", "power", "lumen", "voltage", "ip", "width", "life", "cut", "led_segment", "max_single", "max_double"]
        
        # Создаем сетку 4 колонки
        for i, field in enumerate(fields):
            row = i // 4
            col = i % 4
            
            # Фрейм для одной ячейки
            cell_frame = ctk.CTkFrame(self.grid_container, fg_color="transparent")
            cell_frame.grid(row=row, column=col, padx=10, pady=10, sticky="w")
            
            label_text = "CUT (mm)" if field == "cut" else ("CUT (LED)" if field == "led_segment" else field.upper())
            
            ctk.CTkLabel(cell_frame, text=label_text, width=100, anchor="w", font=("Roboto", 12)).pack(anchor="w")
            
            en = ctk.CTkEntry(cell_frame, width=160, border_color="#555555")
            en.pack(pady=(5, 0))
            self.entries[field] = en

        # --- НИЖНИЙ БЛОК (КНОПКА ГЕНЕРАЦИИ) ---
        self.btn_gen = ctk.CTkButton(
            self, 
            text="ГЕНЕРИРОВАТЬ И СОХРАНИТЬ JPG", 
            command=self.build_image,
            height=50,
            fg_color="#2E7D32", 
            hover_color="#1B5E20",
            font=("Roboto Medium", 16)
        )
        self.btn_gen.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

    # --- ВСЯ ЛОГИКА ОСТАЛАСЬ БЕЗ ИЗМЕНЕНИЙ ---
    
    def fetch_data(self):
        url = self.url_input.get().strip()
        options = Options()
        options.add_argument("--headless")
        try:
            self.btn_parse.configure(text="Загрузка...", state="disabled") # Визуальный эффект
            self.update()
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            time.sleep(3)
            source = driver.find_element(By.TAG_NAME, "body").text
            driver.quit()
            
            for en in self.entries.values(): en.delete(0, tk.END)
            res = {}
            
            if re.search(r'RGBW', source.upper()):
                color_match = re.search(r'Barva světla[:\s]+.*?(NW|CW|WW)', source, re.IGNORECASE)
                res["color"] = f"RGB+{color_match.group(1).upper()}" if color_match else "RGBW"
            else:
                for c in COLOR_MAP_LIGHT.keys():
                    if re.search(r'\b' + c + r'\b', source.upper()): res["color"] = c; break
            
            m_s = re.search(r'Max\. délka pásku při jednostranném napájení.*?(\d+)', source, re.IGNORECASE)
            if m_s: res["max_single"] = m_s.group(1)
            m_d = re.search(r'Max\. délka pásku při oboustranném napájení.*?(\d+)', source, re.IGNORECASE)
            if m_d: res["max_double"] = m_d.group(1)
            m_led_seg = re.search(r'Počet LED na segment[:\s]+(\d+)', source, re.IGNORECASE)
            if m_led_seg: res["led_segment"] = m_led_seg.group(1)
            m_cut_mm = re.search(r'Dělitelnost pásku po\s?\[mm\][:\s]+(\d+[.,]\d+|\d+)', source, re.IGNORECASE)
            if m_cut_mm: res["cut"] = m_cut_mm.group(1).replace('.', ',')

            pats = {
                "kelvin": r'Barevná teplota.*?(\d+\s?-\s?\d+)',
                "chip": r'(SMD\s?\d+|COB)',
                "leds": r'(\d+)\s?LED/m',
                "power": r'(\d+[.,]\d+|\d+)\s?W/m',
                "lumen": r'(\d+)\s?lm/m', 
                "voltage": r'(\d+)\s?V\b',
                "ip": r'IP(\d+)',
                "width": r'(\d+)\s?mm\b',
                "life": r'(\d+)\s?h\b'
            }
            for k, p in pats.items():
                m = re.search(p, source, re.IGNORECASE)
                if m: res[k] = m.group(1).upper() if k == "chip" else m.group(1)

            for k, v in res.items():
                if k in self.entries: self.entries[k].insert(0, v)
            
            self.btn_parse.configure(text="СКАНИРОВАТЬ САЙТ", state="normal")
            messagebox.showinfo("Успех", "Данные успешно загружены")
        except Exception as e: 
            self.btn_parse.configure(text="СКАНИРОВАТЬ САЙТ", state="normal")
            messagebox.showerror("Ошибка", str(e))

    def draw_circuit(self, draw, x, y, size, mode, voltage_text):
        rect_x1, rect_y1 = x + 20, y + 50
        rect_x2, rect_y2 = x + size - 20, y + 65
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], outline="black", width=2)
        for i in range(6): 
            dot_x = rect_x1 + 5 + i * 13
            draw.rectangle([dot_x, rect_y1 + 4, dot_x + 4, rect_y1 + 8], fill="black")

        f_v = ImageFont.truetype("arial.ttf", 18)
        w_v, h_v = draw.textbbox((0,0), voltage_text, font=f_v)[2:]
        text_x = x + (size - w_v) / 2
        text_y = y + 85
        draw.text((text_x, text_y), voltage_text, fill="black", font=f_v)

        dot_r = 3
        text_center_y = text_y + h_v / 2
        v_gap = 8 
        dot_y_top = text_center_y - v_gap
        dot_y_bot = text_center_y + v_gap
        dot_x_right = text_x + w_v + 12
        dot_x_left = text_x - 12

        def draw_side(side):
            start_x = rect_x1 if side == "left" else rect_x2
            target_dot_x = dot_x_left if side == "left" else dot_x_right
            if side == "right":
                elbow_x_outer = start_x + 15
                elbow_x_inner = start_x + 8
            else:
                elbow_x_outer = start_x - 15
                elbow_x_inner = start_x - 8

            draw.line([start_x, rect_y1 + 4, elbow_x_outer, rect_y1 + 4], fill="black", width=1)
            draw.line([elbow_x_outer, rect_y1 + 4, elbow_x_outer, dot_y_bot], fill="black", width=1)
            draw.line([elbow_x_outer, dot_y_bot, target_dot_x, dot_y_bot], fill="black", width=1)
            draw.ellipse([target_dot_x-dot_r, dot_y_bot-dot_r, target_dot_x+dot_r, dot_y_bot+dot_r], fill="black")

            draw.line([start_x, rect_y2 - 4, elbow_x_inner, rect_y2 - 4], fill="black", width=1)
            draw.line([elbow_x_inner, rect_y2 - 4, elbow_x_inner, dot_y_top], fill="black", width=1)
            draw.line([elbow_x_inner, dot_y_top, target_dot_x, dot_y_top], fill="black", width=1)
            draw.ellipse([target_dot_x-dot_r, dot_y_top-dot_r, target_dot_x+dot_r, dot_y_top+dot_r], fill="black")

        draw_side("right")
        if mode == "double": draw_side("left")

    def build_image(self):
        canvas = Image.new('RGB', (850, 320), 'white')
        draw = ImageDraw.Draw(canvas)
        try:
            f_val = ImageFont.truetype("arialbd.ttf", 30)
            f_rgb_small = ImageFont.truetype("arialbd.ttf", 36)
            f_rgb_big = ImageFont.truetype("arialbd.ttf", 48)
            f_mid = ImageFont.truetype("arial.ttf", 26)
            f_sub = ImageFont.truetype("arial.ttf", 16)
            f_cut_num = ImageFont.truetype("arialbd.ttf", 26) 
        except:
            f_val = f_mid = f_sub = f_cut_num = f_rgb_small = f_rgb_big = ImageFont.load_default()

        grid = [["color", "chip", "leds", "power", "lumen", "width"], ["ip", "voltage", "cut", "max_single", "max_double", "life"]]
        x_start, y_start, size, gap = 20, 20, 120, 15
        volt_val = self.entries["voltage"].get().strip()
        v_text = f"{volt_val} V DC"

        for r_idx, row in enumerate(grid):
            for c_idx, field in enumerate(row):
                if not field: continue
                val = self.entries[field].get().strip()
                curr_x, curr_y = x_start + c_idx * (size + gap), y_start + r_idx * (size + gap)
                bg_color, txt_color = "#EEEEEE", "black"
                
                if field == "color" and "RGB+" in val.upper():
                    temp_sq = Image.new('RGBA', (size, size), (0,0,0,0))
                    t_draw = ImageDraw.Draw(temp_sq)
                    w_third, h_half = size / 3, size / 2
                    
                    t_draw.rectangle([0, 0, w_third, h_half], fill=RGB_COLORS["R"])
                    t_draw.rectangle([w_third, 0, 2*w_third, h_half], fill=RGB_COLORS["G"])
                    t_draw.rectangle([2*w_third, 0, size, h_half], fill=RGB_COLORS["B"])
                    
                    sub_color_name = val.split("+")[1]
                    bottom_bg = COLOR_MAP_LIGHT.get(sub_color_name, "white")
                    t_draw.rectangle([0, h_half, size, size], fill=bottom_bg)
                    
                    mask = Image.new('L', (size, size), 0)
                    m_draw = ImageDraw.Draw(mask)
                    m_draw.rounded_rectangle([0, 0, size, size], radius=size*0.1, fill=255)
                    
                    canvas.paste(temp_sq, (curr_x, curr_y), mask)
                    
                    draw.text((curr_x + 6, curr_y + 5), "R", fill="white", font=f_rgb_small)
                    draw.text((curr_x + w_third + 6, curr_y + 5), "G", fill="white", font=f_rgb_small)
                    draw.text((curr_x + 2*w_third + 6, curr_y + 5), "B", fill="white", font=f_rgb_small)
                    tw, th = draw.textbbox((0,0), sub_color_name, font=f_rgb_big)[2:]
                    draw.text((curr_x + (size-tw)/2, curr_y + h_half + 5), sub_color_name, fill="black", font=f_rgb_big)
                    draw.rounded_rectangle([curr_x, curr_y, curr_x + size, curr_y + size], radius=size*0.1, outline="#CCCCCC", width=1)
                    continue

                if field == "color":
                    bg_color = COLOR_MAP_LIGHT.get(val.upper(), "#EEEEEE")
                elif field == "chip":
                    clean_val = val.upper().replace(" ", "").replace("-", "")
                    for k, h in COLOR_MAP_CHIP.items():
                        if k.upper() in clean_val:
                            bg_color = h
                            txt_color = "white"
                            break
                elif field == "ip":
                    txt_color = COLOR_MAP_IP.get("IP"+val, COLOR_MAP_IP.get(val, "#A68FB8"))
                elif field == "voltage":
                    if "24" in val: txt_color = COLOR_MAP_VOLTAGE["24"]
                    elif "12" in val: txt_color = COLOR_MAP_VOLTAGE["12"]

                if field != "life":
                    draw.rounded_rectangle([curr_x, curr_y, curr_x + size, curr_y + size], radius=size*0.1, fill=bg_color)

                if field == "color":
                    kelvin = self.entries["kelvin"].get().strip()
                    draw.text((curr_x + 20, curr_y + 15), val, fill="black", font=f_val)
                    if kelvin and "-" in kelvin:
                        k1, k2 = kelvin.split("-")
                        draw.text((curr_x + 22, curr_y + 50), f"{k1} -", fill="black", font=f_mid)
                        draw.text((curr_x + 22, curr_y + 75), f"{k2}K", fill="black", font=f_mid)

                elif field in ["max_single", "max_double"]:
                    draw.text((curr_x + 20, curr_y + 15), "≤", fill="black", font=f_mid)
                    w_n = draw.textbbox((0,0), val, font=f_val)[2]
                    draw.text((curr_x + 40, curr_y + 10), val, fill="black", font=f_val)
                    draw.text((curr_x + 45 + w_n, curr_y + 15), "m", fill="black", font=f_mid)
                    line_y = curr_y + 45
                    draw.line([curr_x + 20, line_y - 5, curr_x + 20, line_y + 5], fill="black", width=1)
                    draw.line([curr_x + size - 20, line_y - 5, curr_x + size - 20, line_y + 5], fill="black", width=1)
                    arrow_y = 45
                    draw.line([curr_x + 20, curr_y + arrow_y, curr_x + size - 20, curr_y + arrow_y], fill="black", width=1)
                    draw.line([curr_x + 20, curr_y + arrow_y, curr_x + 25, curr_y + arrow_y - 3], fill="black", width=1)
                    draw.line([curr_x + 20, curr_y + arrow_y, curr_x + 25, curr_y + arrow_y + 3], fill="black", width=1)
                    draw.line([curr_x + size - 20, curr_y + arrow_y, curr_x + size - 25, curr_y + arrow_y - 3], fill="black", width=1)
                    draw.line([curr_x + size - 20, curr_y + arrow_y, curr_x + size - 25, curr_y + arrow_y + 3], fill="black", width=1)
                    self.draw_circuit(draw, curr_x, curr_y, size, "single" if field == "max_single" else "double", v_text)

                elif field == "cut":
                    led_val = self.entries["led_segment"].get().strip()
                    mm_val = val
                    w_l = draw.textbbox((0,0), led_val, font=f_cut_num)[2]
                    draw.text((curr_x + 35 - w_l/2, curr_y + 15), led_val, fill="black", font=f_cut_num)
                    draw.text((curr_x + 40 + w_l/2, curr_y + 15), "LED", fill="black", font=f_mid)
                    line_y = curr_y + 55
                    draw.line([curr_x + 15, line_y, curr_x + size - 15, line_y], fill="black", width=2)
                    draw.line([curr_x + 15, line_y - 5, curr_x + 15, line_y + 5], fill="black", width=2)
                    draw.line([curr_x + size - 15, line_y - 5, curr_x + size - 15, line_y + 5], fill="black", width=2)
                    w_m = draw.textbbox((0,0), mm_val, font=f_cut_num)[2]
                    draw.text((curr_x + (size - w_m)/2, curr_y + 65), mm_val, fill="black", font=f_cut_num)
                    draw.text((curr_x + 45, curr_y + 90), "mm", fill="black", font=f_mid)

                elif field == "voltage":
                    num_v = re.sub(r'\D', '', val) 
                    draw.text((curr_x + 35, curr_y + 20), f"{num_v}V", fill=txt_color, font=f_val)
                    draw.text((curr_x + 40, curr_y + 65), "DC", fill=txt_color, font=f_val)

                elif field == "ip":
                    draw.text((curr_x + 45, curr_y + 20), "IP", fill=txt_color, font=f_val)
                    draw.text((curr_x + 40, curr_y + 65), val, fill=txt_color, font=f_val)

                elif field == "chip":
                    val_up = val.upper().strip()
                    if val_up == "COB":
                        draw.text((curr_x + 27, curr_y + 40), "COB", fill=txt_color, font=f_val)
                    else:
                        s_part = "SMD" if "SMD" in val_up else val_up
                        n_part = val.upper().replace("SMD", "").strip()
                        draw.text((curr_x + 27, curr_y + 20), s_part, fill=txt_color, font=f_val)
                        if n_part:
                            draw.text((curr_x + 27, curr_y + 60), n_part, fill=txt_color, font=f_val)

                elif field == "life":
                    draw.rounded_rectangle([curr_x, curr_y, curr_x + size, curr_y + size], radius=size*0.1, fill=bg_color)
                    oversample = 4
                    temp_size = size * oversample
                    temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
                    temp_draw = ImageDraw.Draw(temp_img)
                    circle_margin = 5 * oversample
                    temp_draw.ellipse([circle_margin, circle_margin, temp_size - circle_margin, temp_size - circle_margin], outline="black", width=2 * oversample)
                    l_x, l_y_top, l_y_bot = 65 * oversample, 60 * oversample, 105 * oversample
                    temp_draw.line([l_x, l_y_top, l_x + 40 * oversample, l_y_top], fill="black", width=2 * oversample)
                    temp_draw.line([l_x, l_y_top, l_x, l_y_bot], fill="black", width=2 * oversample)
                    temp_img = temp_img.resize((size, size), Image.Resampling.LANCZOS)
                    canvas.paste(temp_img, (curr_x, curr_y), temp_img)

                    full_val = val.replace(" ", "")
                    main_part = full_val[:-3] if len(full_val) > 3 else full_val
                    small_part = full_val[-3:] if len(full_val) > 3 else ""
                    w_main = draw.textbbox((0, 0), main_part, font=f_val)[2]
                    draw.text((curr_x + 25, curr_y + 18), main_part, fill="black", font=f_val)
                    if small_part: draw.text((curr_x + 25 + w_main + 2, curr_y + 24), small_part, fill="black", font=f_mid)
                    draw.text((curr_x + 35, curr_y + 53), "h", fill="black", font=ImageFont.truetype("arial.ttf", 45))
                    draw.text((curr_x + 70, curr_y + 63), "L70", fill="black", font=f_sub)
                    draw.text((curr_x + 70, curr_y + 80), "B50", fill="black", font=f_sub)

                else:
                    sub = SUB_TEXTS.get(field, "")
                    w_v = draw.textbbox((0,0), val, font=f_val)[2]
                    draw.text((curr_x + (size-w_v)/2, curr_y + 20), val, fill=txt_color, font=f_val)
                    if sub:
                        w_s = draw.textbbox((0,0), sub, font=f_mid)[2]
                        draw.text((curr_x + (size-w_s)/2, curr_y + 65), sub, fill=txt_color, font=f_mid)

        filename = f"{self.url_input.get().split('/')[-1].upper().replace('-', '.')}_30.jpg"
        canvas.save(filename, "JPEG", quality=95)
        os.startfile(filename) if os.name == 'nt' else canvas.show()
        messagebox.showinfo("Готово", f"Файл сохранен:\n{filename}")

if __name__ == "__main__":
    app = LedApp()
    app.mainloop()