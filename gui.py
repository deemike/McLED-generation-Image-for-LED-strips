# gui.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os

import config
from scraper import fetch_data
from drawer import LedImageGenerator

class LedApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("McLED Visual Pro 45.6")
        self.geometry("1000x750")
        
        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_ui()
        self.generator = LedImageGenerator()

    def _setup_ui(self):
        # Верхний блок
        self.frame_top = ctk.CTkFrame(self, corner_radius=10)
        self.frame_top.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(self.frame_top, text="Ссылка:", font=("Roboto Medium", 14)).pack(side="left", padx=20, pady=15)
        
        self.url_input = ctk.CTkEntry(self.frame_top, width=600)
        self.url_input.pack(side="left", padx=10)
        self.url_input.insert(0, "https://www.mcled.cz/ml-126-676-60-x")

        self.btn_parse = ctk.CTkButton(self.frame_top, text="СКАНИРОВАТЬ", command=self.run_fetch, fg_color="#E65100", hover_color="#BF360C")
        self.btn_parse.pack(side="left", padx=20)

        # Средний блок
        self.frame_mid = ctk.CTkFrame(self, corner_radius=10)
        self.frame_mid.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_mid, text="Параметры", font=("Roboto Medium", 18)).pack(pady=10)
        
        self.grid_container = ctk.CTkFrame(self.frame_mid, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=20)

        self.entries = {}
        fields = [
            "color", "kelvin", "chip", "leds", "power", "lumen", "voltage", "ip", "width", 
            "life", "cut", "led_segment", "max_single", "max_double", "cri", "angle", "model"
          ]
        
        for i, field in enumerate(fields):
            row, col = i // 4, i % 4
            cell = ctk.CTkFrame(self.grid_container, fg_color="transparent")
            cell.grid(row=row, column=col, padx=10, pady=10, sticky="w")
            
            lbl = "CUT (mm)" if field == "cut" else ("CUT (LED)" if field == "led_segment" else field.upper())
            ctk.CTkLabel(cell, text=lbl, width=100, anchor="w").pack(anchor="w")
            
            en = ctk.CTkEntry(cell, width=160)
            en.pack(pady=(5,0))
            self.entries[field] = en

        # Нижний блок
        self.btn_gen = ctk.CTkButton(self, text="ГЕНЕРИРОВАТЬ", command=self.run_generate, height=50, fg_color="#2E7D32", hover_color="#1B5E20")
        self.btn_gen.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

    def run_fetch(self):
        # Запускаем в отдельном потоке, чтобы UI не вис
        url = self.url_input.get().strip()
        self.btn_parse.configure(text="Загрузка...", state="disabled")
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url):
        try:
            data = fetch_data(url)
            # Обновление UI должно быть в основном потоке (или через after, но тут customtkinter обычно справляется)
            # Для надежности лучше использовать after, но для простоты оставим прямое обращение
            self.after(0, lambda: self._update_fields(data))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
        finally:
            self.after(0, lambda: self.btn_parse.configure(text="СКАНИРОВАТЬ", state="normal"))

    def _update_fields(self, data):
        for k, v in self.entries.items():
            v.delete(0, tk.END)
        
        for k, v in data.items():
            if k in self.entries:
                self.entries[k].insert(0, str(v))
        messagebox.showinfo("Успех", "Данные загружены")

    def run_generate(self):
        # Собираем данные из полей
        data = {k: v.get().strip() for k, v in self.entries.items()}
        
        try:
            img = self.generator.generate(data)
            
            sku = self.url_input.get().split('/')[-1].upper().replace('-', '.')
            filename = f"{sku}_30.jpg"
            img.save(filename, "JPEG", quality=95)
            
            if os.name == 'nt':
                os.startfile(filename)
            else:
                img.show()
                
            messagebox.showinfo("Готово", f"Файл сохранен:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка генерации", str(e))