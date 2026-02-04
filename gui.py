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
        
        self.title("McLED Visual Pro v1.0")
        self.geometry("1000x800")
        
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
        
        ctk.CTkLabel(self.frame_top, text="URL pásku:", font=("Roboto Medium", 14)).pack(side="left", padx=20, pady=15)
        
        self.url_input = ctk.CTkEntry(self.frame_top, width=600)
        self.url_input.pack(side="left", padx=10)
        self.url_input.insert(0, "https://www.mcled.cz/ml-126-676-60-x")

        self.btn_parse = ctk.CTkButton(self.frame_top, text="SKENOVAT", command=self.run_fetch, fg_color="#E65100", hover_color="#BF360C")
        self.btn_parse.pack(side="left", padx=20)

        # Средний блок
        self.frame_mid = ctk.CTkFrame(self, corner_radius=10)
        self.frame_mid.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_mid, text="Parametry pásku", font=("Roboto Medium", 18)).pack(pady=10)
        
        self.grid_container = ctk.CTkFrame(self.frame_mid, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=20)

        self.entries = {}
        # fields = [
        #     "color", "kelvin", "chip", "leds", "power", "lumen", "voltage", "ip", "width", 
        #     "life", "life_l", "life_b", "cut", "led_segment", "max_single", "max_double", "cri", "angle", "model"
        #   ]
        
        translations = {
            "color": "Barva světla", "kelvin": "Barevná teplota (K)", "chip": "Typ čipu", "leds": "LED/m", "power": "Výkon (W/m)", 
            "lumen": "Světelný tok (lm/m)", "voltage": "Napětí (V)", "ip": "Krytí (IP)", "width": "Šířka (mm)", "life": "Životnost (h)", 
            "life_l": "L parametr", "life_b": "B parametr", "cut": "Dělitelnost (mm)", "led_segment": "Počet LED na segment", 
            "max_single": "Max.délka pásku single (m)", "max_double": "Max.délka pásku double (m)", "cri": "CRI",
            "angle": "Úhel vyzařování (°)", "model": "Model"
        }

        # Используем ключи словаря для создания полей
        for i, (field_key, display_name) in enumerate(translations.items()):
            row, col = i // 4, i % 4
            cell = ctk.CTkFrame(self.grid_container, fg_color="transparent")
            cell.grid(row=row, column=col, padx=10, pady=10, sticky="w")
            
            # Используем display_name из словаря для текста метки
            ctk.CTkLabel(cell, text=display_name, width=120, anchor="w").pack(anchor="w")
            
            en = ctk.CTkEntry(cell, width=160)
            en.pack(pady=(5,0))
            self.entries[field_key] = en

        # Нижний блок
        self.btn_gen = ctk.CTkButton(self, text="GENEROVAT OBRÁZEK", command=self.run_generate, height=50, fg_color="#2E7D32", hover_color="#1B5E20")
        self.btn_gen.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        # --- СТАТУС-БАР ---
        self.status_container = ctk.CTkFrame(self, fg_color="transparent")
        self.status_container.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")

        # Профессиональный индикатор загрузки (скрыт по умолчанию)
        self.progress_bar = ctk.CTkProgressBar(self.status_container, height=2, corner_radius=0)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.pack_forget() # Прячем, пока нет работы

        # Текст статуса (статичный, без дерганий)
        self.status_label = ctk.CTkLabel(self.status_container, text="", font=("Roboto Medium", 13))
        self.status_label.pack()

    def _animate_loading(self, base_text, count=0):
        """Анимация бегущих точек: . .. ..."""
        if not self._anim_active:
            return
        
        dots = "." * (count % 4)
        self.status_label.configure(text=f"{base_text}{dots}", text_color="#FFFFFF")
        self.after(400, lambda: self._animate_loading(base_text, count + 1))

    def _animate_pulse(self, text, base_color, step=0):
        """Анимация пульсации яркости для успеха/ошибки"""
        if not self._anim_active:
            return

        # Список оттенков для плавного затухания и вспышки
        # Для успеха (зеленоватые), для ошибки (красноватые) - вычисляется по base_color
        colors = ["#FFFFFF", "#D1D1D1", "#A2A2A2", "#747474", "#A2A2A2", "#D1D1D1"]
        current_color = colors[step % len(colors)]
        
        # Если это ошибка, можно сделать пульсацию Красный -> Темно-красный
        if base_color == "error":
            error_colors = ["#FF5252", "#B71C1C", "#FF5252", "#B71C1C"]
            current_color = error_colors[step % len(error_colors)]

        self.status_label.configure(text=text, text_color=current_color)
        self.after(300, lambda: self._animate_pulse(text, base_color, step + 1))

    def show_status(self, message, mode="info"):
        # Сброс
        self.progress_bar.pack_forget()
        
        if mode == "loading":
            self.progress_bar.pack(fill="x", pady=(0, 5))
            self.progress_bar.configure(mode="indeterminate", progress_color="#E65100")
            self.progress_bar.start()
            self.status_label.configure(text=message, text_color="#FFFFFF")
            
        elif mode == "success":
            self.progress_bar.stop()
            self.status_label.configure(text=f"✓ {message}", text_color="#66BB6A")
            self.after(4000, self._clear_status)
            
        elif mode == "error":
            self.progress_bar.stop()
            self.status_label.configure(text=f"⚠ {message}", text_color="#FF5252")
            self.after(5000, self._clear_status)

    def _clear_status(self):
        self.status_label.configure(text="")
        self.progress_bar.pack_forget()

    def run_fetch(self):
        url = self.url_input.get().strip()
        if not url:
            self.show_status("Zadejte prosím platnou URL adresu", mode="error")
            return

        self.btn_parse.configure(text="...", state="disabled")
        # Запускаем анимацию точек
        self.show_status("Probíhá stahování dat", mode="loading")
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url):
        try:
            data = fetch_data(url)
            self.after(0, lambda: self._update_fields(data))
        except Exception as e:
            self.after(0, lambda: self.show_status(f"Chyba: {str(e)}", is_error=True))
        finally:
            self.after(0, lambda: self.btn_parse.configure(text="SKENOVAT", state="normal"))

    def _update_fields(self, data):
        for k, v in self.entries.items():
            v.delete(0, tk.END)
        
        for k, v in data.items():
            if k in self.entries:
                self.entries[k].insert(0, str(v))
        self._anim_active = False # Останавливаем загрузку
        self.after(100, lambda: self.show_status("Supr! Data byla úspěšně načtena", mode="success"))

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
                
            self.show_status(f"Hotovo! Obrázek {filename} byl uložen", mode="success")
        except Exception as e:
            self.show_status("Chyba při generování", mode="error")