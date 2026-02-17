# gui.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os
import csv
import time
import random

import config
from scraper import fetch_data, get_driver
from drawer import LedImageGenerator
from pathlib import Path

class LedApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("McLED Visual Pro v1.5 (Complete Image)")
        self.geometry("1000x850")
        
        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_ui()
        self.generator = LedImageGenerator()
        self._anim_active = False

    def _setup_ui(self):
        # --- Horní blok (URL a tlačítka) ---
        self.frame_top = ctk.CTkFrame(self, corner_radius=10)
        self.frame_top.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(self.frame_top, text="URL pásku:", font=("Roboto Medium", 14)).pack(side="left", padx=20, pady=15)
        
        self.url_input = ctk.CTkEntry(self.frame_top, width=400)
        self.url_input.pack(side="left", padx=10)
        self.url_input.insert(0, "https://www.mcled.cz/ml-126-676-60-x")

        # Tlačítko pro jeden produkt
        self.btn_parse = ctk.CTkButton(self.frame_top, text="SKENOVAT", command=self.run_fetch, width=100, fg_color="#E65100", hover_color="#BF360C")
        self.btn_parse.pack(side="left", padx=10)

        # Oddělovač
        ctk.CTkLabel(self.frame_top, text="|", text_color="gray").pack(side="left", padx=5)

        # Tlačítko pro hromadné nahrání (CSV)
        self.btn_batch = ctk.CTkButton(self.frame_top, text="NAHRÁT CSV", command=self.load_batch_file, width=120, fg_color="#0277BD", hover_color="#01579B")
        self.btn_batch.pack(side="left", padx=10)

        # --- Střední blok (Parametry) ---
        self.frame_mid = ctk.CTkFrame(self, corner_radius=10)
        self.frame_mid.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_mid, text="Parametry pásku", font=("Roboto Medium", 18)).pack(pady=10)
        
        self.grid_container = ctk.CTkFrame(self.frame_mid, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=20)

        self.entries = {}
        
        translations = {
            "color": "Barva světla", "kelvin": "Barevná teplota (K)", "chip": "Typ čipu", "leds": "LED/m", "power": "Výkon (W/m)", 
            "lumen": "Světelný tok (lm/m)", "voltage": "Napětí (V)", "ip": "Krytí (IP)", "width": "Šířka (mm)", "height": "Výška (mm)", 
            "life": "Životnost (h)", "life_l": "L parametr", "life_b": "B parametr", "cut": "Dělitelnost (mm)", "led_segment": "Počet LED na segment", 
            "max_single": "Max.délka pásku single (m)", "max_double": "Max.délka pásku double (m)", "cri": "CRI",
            "angle": "Úhel vyzařování (°)", "model": "Model"
        }

        # Vytvoření mřížky polí
        for i, (field_key, display_name) in enumerate(translations.items()):
            row, col = i // 4, i % 4
            cell = ctk.CTkFrame(self.grid_container, fg_color="transparent")
            cell.grid(row=row, column=col, padx=10, pady=10, sticky="w")
            
            ctk.CTkLabel(cell, text=display_name, width=120, anchor="w").pack(anchor="w")
            
            en = ctk.CTkEntry(cell, width=160)
            en.pack(pady=(5,0))
            self.entries[field_key] = en

        # --- Dolní blok (Tlačítko generovat) ---
        self.btn_gen = ctk.CTkButton(self, text="GENEROVAT OBRÁZEK", command=self.run_generate, height=50, fg_color="#2E7D32", hover_color="#1B5E20")
        self.btn_gen.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        # --- STATUS BAR ---
        self.status_container = ctk.CTkFrame(self, fg_color="transparent")
        self.status_container.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.status_container, height=12, corner_radius=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.pack_forget()

        # Text statusu
        self.status_label = ctk.CTkLabel(self.status_container, text="", font=("Roboto Medium", 13))
        self.status_label.pack()

    def _animate_loading(self, base_text, count=0):
        if not self._anim_active:
            return
        dots = "." * (count % 4)
        self.status_label.configure(text=f"{base_text}{dots}", text_color="#FFFFFF")
        self.after(400, lambda: self._animate_loading(base_text, count + 1))

    def show_status(self, message, mode="info", progress=None):
        self.progress_bar.pack_forget()
        
        if mode == "loading":
            self.progress_bar.pack(fill="x", pady=(0, 5))
            if progress is None:
                self.progress_bar.configure(mode="indeterminate", progress_color="#E65100")
                self.progress_bar.start()
            else:
                self.progress_bar.configure(mode="determinate", progress_color="#0277BD")
                self.progress_bar.stop()
                self.progress_bar.set(progress)
            
            self.status_label.configure(text=message, text_color="#FFFFFF")
            
        elif mode == "success":
            self.progress_bar.stop()
            self.status_label.configure(text=f"✓ {message}", text_color="#66BB6A")
            self.after(5000, self._clear_status)
            
        elif mode == "error":
            self.progress_bar.stop()
            self.status_label.configure(text=f"⚠ {message}", text_color="#FF5252")
            self.after(6000, self._clear_status)

    def _clear_status(self):
        self.status_label.configure(text="")
        self.progress_bar.pack_forget()

    def run_fetch(self):
        url = self.url_input.get().strip()
        if not url:
            self.show_status("Zadejte prosím platnou URL adresu", mode="error")
            return

        self.btn_parse.configure(text="...", state="disabled")
        self._anim_active = True
        self.show_status("Probíhá stahování dat", mode="loading")
        self._animate_loading("Probíhá stahování dat")
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url):
        try:
            data = fetch_data(url)
            self.after(0, lambda: self._update_fields(data))
        except Exception as e:
            self.after(0, lambda: self.show_status(f"Chyba: {str(e)}", mode="error"))
        finally:
            self.after(0, lambda: self.btn_parse.configure(text="SKENOVAT", state="normal"))
            self._anim_active = False

    def _update_fields(self, data):
        for k, v in self.entries.items():
            v.delete(0, tk.END)
        for k, v in data.items():
            if k in self.entries:
                self.entries[k].insert(0, str(v))
        self.show_status("Supr! Data byla úspěšně načtena", mode="success")

    def run_generate(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}
        # Настройка путей
        downloads_path = Path.home() / "Downloads"
        target_dir = downloads_path / "McLED_LED-pasky"
        
        # Создаем папку, если ее нет
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            img = self.generator.generate(data)
            sku = self.url_input.get().split('/')[-1].upper().replace('-', '.')
            filename = f"{sku}_30.jpg"
            
            full_path = target_dir / filename
            
            img.save(str(full_path), "JPEG", quality=95)
            
            if os.name == 'nt':
                os.startfile(str(full_path))
            else:
                img.show()
            self.show_status(f"Hotovo! Uloženo v McLED_LED-pasky", mode="success")
        except Exception as e:
            self.show_status(f"Chyba při generování: {e}", mode="error")

    # --- HROMADNÉ ZPRACOVÁNÍ (ROBUST BATCH) ---

    def transform_code_to_url(self, code):
        clean_code = code.strip().lower().replace('.', '-')
        parts = clean_code.split('-')
        
        if len(parts) >= 4:
            base = "-".join(parts[:-1])
            return f"https://www.mcled.cz/{base}-x"
        
        return f"https://www.mcled.cz/{clean_code}"

    def load_batch_file(self):
        file_path = filedialog.askopenfilename(
            title="Vyberte soubor CSV (s ML kódy)",
            filetypes=[("CSV/Text soubory", "*.csv;*.txt"), ("Všechny soubory", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            codes = []
            with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    val = line
                    if ';' in line: val = line.split(';')[0].strip()
                    elif ',' in line: val = line.split(',')[0].strip()
                    
                    val = val.replace('"', '').replace("'", "")
                    
                    if val.upper().startswith("ML"):
                        codes.append(val)
            
            if not codes:
                self.show_status("Nebyly nalezeny žádné platné ML kódy.", mode="error")
                return

            self.show_status(f"Načteno {len(codes)} položek. Startuji prohlížeč...", mode="loading", progress=0.0)
            self.btn_batch.configure(state="disabled")
            
            threading.Thread(target=self._process_batch_thread, args=(codes,), daemon=True).start()
            
        except Exception as e:
            self.show_status(f"Chyba při čtení souboru: {e}", mode="error")

    def _process_batch_thread(self, codes):
        total = len(codes)
        success_count = 0
        errors = []
        driver = None

        try:
            # 1. Start prohlížeče
            driver = get_driver()
            
            for i, code in enumerate(codes):
                try:
                    progress = i / total
                    remaining = total - i
                    
                    self.after(0, lambda i=i, remaining=remaining, progress=progress, code=code: 
                               self.show_status(f"Zpracovávám {i+1}/{total}: {code}", mode="loading", progress=progress))
                    
                    url = self.transform_code_to_url(code)
                    print(f"Batch ({i+1}/{total}): {code} -> {url}")
                    
                    # 2. Inteligentní pauza proti blokování (1.5 - 3.5 sekund stačí)
                    if i > 0:
                        delay = random.uniform(1.5, 3.5)
                        time.sleep(delay)
                    
                    # 3. Stáhnout data
                    data = fetch_data(url, driver=driver)
                    
                    # Настройка путей для батча
                    downloads_path = Path.home() / "Downloads"
                    target_dir = downloads_path / "McLED_LED-pasky"
                    target_dir.mkdir(parents=True, exist_ok=True)

                    if not data:
                        # ... (код обработки отсутствия данных)
                        continue

                    # 4. Generovat a uložit
                    try:
                        img = self.generator.generate(data)
                        clean_name = code.strip().replace('/', '-').replace('\\', '-')
                        filename = f"{clean_name}_30.jpg"
                        
                        full_path = target_dir / filename

                        img.save(str(full_path), "JPEG", quality=95)
                        success_count += 1
                    except Exception as gen_err:
                        print(f"Chyba při kreslení {code}: {gen_err}")
                        errors.append(code)
                    
                except Exception as e:
                    print(f"Error processing {code}: {e}")
                    errors.append(code)

        except Exception as global_e:
            print(f"Critical Batch Error: {global_e}")
            self.after(0, lambda: self.show_status(f"Kritická chyba: {global_e}", mode="error"))
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            # Finální zpráva
            final_msg = f"HOTOVO! Vygenerováno {success_count} z {total}."
            if errors:
                final_msg += f" (Chyby: {len(errors)})"
                
            self.after(0, lambda: self.btn_batch.configure(state="normal"))
            self.after(0, lambda: self.show_status(final_msg, mode="success" if success_count > 0 else "error"))

if __name__ == "__main__":
    app = LedApp()
    app.mainloop()
