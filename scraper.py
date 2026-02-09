# scraper.py
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import config

def get_driver():
    """Vytvoří a vrátí instanci prohlížeče pro opakované použití."""
    options = Options()
    options.add_argument("--headless")
    # Přidáme user-agent, aby to vypadalo více jako běžný prohlížeč
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Potlačení logů
    options.add_argument("--log-level=3")
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def fetch_data(url, driver=None):
    """
    Stáhne data z URL.
    Pokud je předán 'driver', použije ho (a nezavře).
    Pokud 'driver' není předán, vytvoří si nový a po dokončení ho zavře.
    """
    should_quit = False
    if driver is None:
        driver = get_driver()
        should_quit = True

    try:
        driver.get(url)
        # Krátká pauza pro načtení JavaScriptu
        time.sleep(2)
        
        source = driver.find_element(By.TAG_NAME, "body").text
    except Exception as e:
        print(f"Chyba při stahování {url}: {e}")
        source = ""
    finally:
        if should_quit:
            driver.quit()

    if not source:
        return {}

    res = {}

    # --- LOGIKA OPRЕДELENÍ ЦВЕТА (Barva světla) ---
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
        res["color"] = match.group(1).upper().replace("-", "+")

    # 6. DW (Daylight White)
    elif re.search(r'Barva světla[:\s]+denní bílý DW', source, re.IGNORECASE):
        res["color"] = "DW"
    elif re.search(r'Barva světla[:\s]+studeně bílý CW', source, re.IGNORECASE):
        res["color"] = "CW"
    elif re.search(r'Barva světla[:\s]+neutrálně bílý NW', source, re.IGNORECASE):
        res["color"] = "NW"
    elif re.search(r'Barva světla[:\s]+teple bílý WW', source, re.IGNORECASE):
        res["color"] = "WW"

    # 7. UVA
    elif re.search(r'Barva světla[:\s]+UVA', source, re.IGNORECASE):
        res["color"] = "UVA"
    
    # 8. Jednobarevné (R, G, B, Y)
    elif re.search(r'Modrá|modrý B', source, re.IGNORECASE):
        res["color"] = "B"
    elif re.search(r'Červená|červený R', source, re.IGNORECASE):
        res["color"] = "R"
    elif re.search(r'Zelená|zelený G', source, re.IGNORECASE):
        res["color"] = "G"
    elif re.search(r'Žlutá|žlutý Y', source, re.IGNORECASE):
        res["color"] = "Y"

    # 8. Стандартные (EWW, WW, NW, CW, etc.)
    else:
        for c in config.COLOR_MAP_LIGHT.keys():
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
        "leds": r'Počet LED na metr\s?\[-\][:\s]+(\d+)',
        "power": r'(\d+[.,]\d+|\d+)\s?W/m',
        "lumen": r'(\d+)\s?lm/m',
        "voltage": r'(\d+)\s?V\b',
        "ip": r'IP(\d+)',
        "width": r'Šířka\s?\[mm\][:\s]+(\d+)',
        "height": r'Výška / hloubka\s?\[mm\][:\s]+(\d+)',
        "model": r'Model\s*(\d{2,3}B)',
        "life_full": r'L(\d+)/B(\d+).*?\[h\]:\s*(\d+[\s.]\d+|\d+)',
        "cri": r'Index podání barev CRI[:\s]+(90-100|90)',
        "angle": r'Úhel vyzařování\s?\[°\][:\s]+(\d+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, source, re.IGNORECASE | re.DOTALL)
        if match:
            val = match.group(1)
            if key == "chip": val = val.upper()
            if key == "cut": val = val.replace('.', ',')
            if key == "height":
                val = val.replace(',', '.')
            
            res[key] = val
            
            if key == "cri" and "90" in val:
                val = "90"
                res[key] = val
            
            if key == "life_full":
                res["life_l"] = match.group(1)
                res["life_b"] = match.group(2)
                res["life"] = match.group(3).replace(" ", "").replace(".", "")

    if "model" not in res or not res["model"]:
        check_model = re.search(r'Model\s*(\d{2,3}B)', source, re.IGNORECASE)
        if check_model:
            res["model"] = check_model.group(1).upper()
        # Pokud model nebyl nalezen, nevracíme ho, aby volající poznal chybu

    return res
