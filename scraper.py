# scraper.py
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import config

def fetch_data(url):
    options = Options()
    options.add_argument("--headless")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(url)
        time.sleep(3)
        source = driver.find_element(By.TAG_NAME, "body").text
    finally:
        driver.quit()

    res = {}

    # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ЦВЕТА (Barva světla) ---
    # Сначала ищем сложные типы, потом простые
    src_upper = source.upper()
    
    # 1. Digital SPI
    if re.search(r'Barva světla[:\s]+Digital SPI', source, re.IGNORECASE):
        res["color"] = "DIGITAL SPI"
    
    # 2. RGB+CCT
    elif re.search(r'Barva světla[:\s]+barevný RGB\+CCT', source, re.IGNORECASE):
        res["color"] = "RGB+CCT"
        
    # 3. RGBW (RGB+NW/CW/WW)
    elif re.search(r'Barva světla[:\s]+barevný RGB\+(NW|CW|WW)', source, re.IGNORECASE):
        match = re.search(r'Barva světla[:\s]+barevný RGB\+(NW|CW|WW)', source, re.IGNORECASE)
        res["color"] = f"RGB+{match.group(1).upper()}"
        
    # 4. Просто RGB
    elif re.search(r'Barva světla[:\s]+barevný - RGB\b', source, re.IGNORECASE):
        res["color"] = "RGB"

    # 5. Dual White (EWW-CW, WW-CW, WW-UWW)
    elif re.search(r'Barva světla[:\s]+duální bílá\s+([A-Z]+-[A-Z]+)', source, re.IGNORECASE):
        match = re.search(r'Barva světla[:\s]+duální bílá\s+([A-Z]+-[A-Z]+)', source, re.IGNORECASE)
        # Превращаем "EWW-CW" в "EWW+CW" для удобства
        res["color"] = match.group(1).upper().replace("-", "+")

    # 6. DW (Daylight White)
    elif re.search(r'Barva světla[:\s]+denní bílý DW', source, re.IGNORECASE):
        res["color"] = "DW"

    # 7. UVA
    elif re.search(r'Barva světla[:\s]+UVA', source, re.IGNORECASE):
        res["color"] = "UVA"

    # 8. Стандартные (EWW, WW, NW, CW, etc.) - если не найдено выше
    else:
        for c in config.COLOR_MAP_LIGHT.keys():
            # Ищем точное совпадение слова, чтобы UWW не находило внутри WW
            if re.search(r'\b' + c + r'\b', src_upper):
                res["color"] = c
                break

    # --- ОСТАЛЬНЫЕ ПАРАМЕТРЫ ---
    patterns = {
        "max_single": r'Max\. délka pásku při jednostranném napájení.*?(\d+)',
        "max_double": r'Max\. délka pásku při oboustranném napájení.*?(\d+)',
        "led_segment": r'Počet LED na segment[:\s]+(\d+)',
        "cut": r'Dělitelnost pásku po\s?\[mm\][:\s]+(\d+[.,]\d+|\d+)',
        "kelvin": r'Barevná teplota.*?(\d+\s?-\s?\d+)',
        "chip": r'(SMD\s?\d+|COB)',
        "leds": r'(\d+)\s?LED/m',
        "power": r'(\d+[.,]\d+|\d+)\s?W/m',
        "lumen": r'(\d+)\s?lm/m',
        "voltage": r'(\d+)\s?V\b',
        "ip": r'IP(\d+)',
        "width": r'(\d+)\s?mm\b',
        "life": r'(\d+)\s?h\b',
        # ДОБАВЛЕННЫЕ ПАРАМЕТРЫ:
        "cri": r'Index podání barev CRI[:\s]+(90-100|90)',
        "angle": r'Úhel vyzařování\s?\[°\][:\s]+(\d+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, source, re.IGNORECASE)
        if match:
            val = match.group(1)
            if key == "chip": val = val.upper()
            if key == "cut": val = val.replace('.', ',')
            # Специфическая логика для CRI: если нашли "90-100", запишем "90"
            if key == "cri" and "90" in val:
                val = "90"
            res[key] = val

    return res