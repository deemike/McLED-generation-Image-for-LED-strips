# drawer.py
from PIL import Image, ImageDraw, ImageFont, ImageOps
import config
import re
import math
import os

class LedImageGenerator:
    def __init__(self, width=1000, height=450):
        self.width = width
        self.height = height
        self.size = 124
        self.gap = 15
        self.radius = 12  # Единый радиус скругления
        self.load_fonts()

    def load_fonts(self):
        try:
            self.f_val = ImageFont.truetype(config.FONT_BOLD, 30)
            self.f_rgb_small = ImageFont.truetype(config.FONT_BOLD, 36)
            self.f_rgb_big = ImageFont.truetype(config.FONT_BOLD, 48)
            self.f_dual_top = ImageFont.truetype(config.FONT_BOLD, 38)
            self.f_dual_bot = ImageFont.truetype(config.FONT_BOLD, 38)
            self.f_mid = ImageFont.truetype(config.FONT_REGULAR, 26)
            self.f_sub = ImageFont.truetype(config.FONT_REGULAR, 16)
            self.f_cut_num = ImageFont.truetype(config.FONT_BOLD, 26)
            self.f_cri_angle = ImageFont.truetype(config.FONT_BOLD, 26)
        except:
            self.f_val = self.f_mid = self.f_sub = self.f_cut_num = \
            self.f_rgb_small = self.f_rgb_big = self.f_dual_top = \
            self.f_dual_bot = self.f_cri_angle = ImageFont.load_default()

    def _find_image_path(self, base_name):
        """Helper to find image path case-insensitively and with different extensions"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "images")
        
        if not os.path.exists(base_dir):
            return None
            
        target_name = base_name.lower()
        for f in os.listdir(base_dir):
            name_part = os.path.splitext(f)[0]
            if name_part.lower() == target_name:
                return os.path.join(base_dir, f)
                
        print(f"WARNING: Obrázek '{base_name}' nebyl nalezen ve složce images.")
        return None

    def generate(self, data):
        has_dynamic = data.get("cri") == "90" or data.get("angle")
        canvas_height = self.height + 150 if has_dynamic else self.height
        canvas = Image.new('RGB', (self.width, canvas_height), 'white')
        draw = ImageDraw.Draw(canvas)

        grid = [
            ["color", "chip", "leds", "power", "lumen", "width"],
            ["ip", "voltage", "cut", "max_single", "max_double", "life"]
        ]
        
        num_cols = 6
        content_width = (num_cols * self.size) + ((num_cols - 1) * self.gap)
        x_start = (self.width - content_width) // 2
        y_start = 64

        volt_val = data.get("voltage", "").strip()
        v_text_circuit = f"{volt_val} V DC"

        for r_idx, row in enumerate(grid):
            for c_idx, field in enumerate(row):
                if not field: continue
                val = data.get(field, "").strip()
                if not val and "max_" not in field: continue

                val_up = val.upper()
                curr_x = x_start + c_idx * (self.size + self.gap)
                curr_y = y_start + r_idx * (self.size + self.gap)
                
                bg_color = "#EEEEEE"
                txt_color = "black"

                if field == "color":
                    prod_map = {
                        "OVOCE O": "o", "SÝRY S": "s", "PEČIVO P": "p", "UZENINY U": "u", "MASO M": "m", "MRAŽENÉ MR": "mr"
                    }
                    
                    found_prod_file = None
                    for key, fname_base in prod_map.items():
                        if key in val_up:
                            found_prod_file = fname_base
                            break
                    
                    if found_prod_file:
                        draw.rounded_rectangle([curr_x, curr_y, curr_x + self.size, curr_y + self.size], radius=self.radius, fill="#EEEEEE", outline="#6E6E6E", width=1)
                        icon_path = self._find_image_path(found_prod_file)
                        if icon_path:
                            try:
                                with Image.open(icon_path) as icon:
                                    icon = icon.resize((self.size, self.size), Image.Resampling.LANCZOS)
                                    if icon.mode == 'RGBA':
                                        draw._image.paste(icon, (int(curr_x), int(curr_y)), icon)
                                    else:
                                        draw._image.paste(icon, (int(curr_x), int(curr_y)))
                            except Exception as e:
                                print(f"Error loading product icon {found_prod_file}: {e}")
                        continue

                    # --- ЦВЕТА NW, WW, CW БЕЗ КЕЛЬВИНОВ ---
                    kelvin = data.get("kelvin", "").strip()
                    if val_up in ["NW", "WW", "CW"] and not kelvin:
                        draw.rounded_rectangle([curr_x, curr_y, curr_x + self.size, curr_y + self.size], radius=self.radius, fill="#EEEEEE", outline="#6E6E6E", width=1)
                        self._draw_field_content(draw, field, val, curr_x, curr_y, "black", data, v_text_circuit)
                        continue

                    if "SPI" in val_up:
                        draw.rounded_rectangle([curr_x, curr_y, curr_x + self.size, curr_y + self.size], radius=self.radius, fill="#EEEEEE", outline="#6E6E6E", width=1)
                        draw.text((curr_x + 12, curr_y + 15), "D", fill="#E30613", font=self.f_rgb_big)
                        draw.text((curr_x + 45, curr_y + 15), "I", fill="#D9005B", font=self.f_rgb_big)
                        draw.text((curr_x + 58, curr_y + 15), "G", fill="#662483", font=self.f_rgb_big)
                        draw.text((curr_x + 95, curr_y + 15), "I", fill="#009EE3", font=self.f_rgb_big)
                        s_y = curr_y + 75
                        draw.rectangle([curr_x + 15, s_y, curr_x + self.size - 15, s_y + 25], outline="black", width=1)
                        line_yt = curr_y + 82
                        draw.line([curr_x + 16, line_yt - 2, curr_x + 16, line_yt + 2], fill="black", width=4)
                        draw.line([curr_x + self.size - 17, line_yt - 2, curr_x + self.size - 17, line_yt + 2], fill="black", width=4)
                        line_yb = curr_y + 92
                        draw.line([curr_x + 16, line_yb - 2, curr_x + 16, line_yb + 2], fill="black", width=4)
                        draw.line([curr_x + self.size - 17, line_yb - 2, curr_x + self.size - 17, line_yb + 2], fill="black", width=4)
                        colors = ["#D9005B", "#009EE3", "#FFF100"]
                        for i, c in enumerate(colors):
                            draw.rectangle([curr_x + 27 + i*28, s_y + 7, curr_x + 37 + i*28, s_y + 17], fill=c, outline="black")
                        continue

                    if "UVA" in val_up or "UV" in val_up:
                        draw.rounded_rectangle([curr_x, curr_y, curr_x + self.size, curr_y + self.size], radius=self.radius, fill="#531E54")
                        tw = draw.textbbox((0,0), "UV", font=self.f_rgb_big)[2]
                        draw.text((curr_x + (self.size-tw)/2, curr_y + 35), "UV", fill="white", font=self.f_rgb_big)
                        continue
                    
                    if "+" in val or "RGB" in val: 
                        if "RGB" in val and "+" not in val: self._draw_rgb(canvas, draw, curr_x, curr_y)
                        elif "RGB" in val and "+" in val: self._draw_rgbw(canvas, draw, curr_x, curr_y, val)
                        else: self._draw_dual_white(canvas, draw, curr_x, curr_y, val)
                        continue

                if field == "life":
                    self._draw_life(canvas, draw, curr_x, curr_y, val, bg_color, data)
                    continue

                if field == "color": 
                    bg_color = config.COLOR_MAP_LIGHT.get(val.upper(), "#EEEEEE")
                elif field == "chip":
                    clean_val = val.upper().replace(" ", "").replace("-", "")
                    for k, h in config.COLOR_MAP_CHIP.items():
                        if k.upper() in clean_val: bg_color = h; txt_color = "white"; break
                elif field == "ip":
                    txt_color = config.COLOR_MAP_IP.get("IP"+val, config.COLOR_MAP_IP.get(val, "#A68FB8"))
                elif field == "voltage":
                    if "24" in val: txt_color = config.COLOR_MAP_VOLTAGE["24"]
                    elif "12" in val: txt_color = config.COLOR_MAP_VOLTAGE["12"]

                outline_color = "#6E6E6E" if bg_color.upper() == "#EEEEEE" else None
                outline_width = 1 if outline_color else 0
                
                draw.rounded_rectangle([curr_x, curr_y, curr_x + self.size, curr_y + self.size], radius=self.radius, fill=bg_color, outline=outline_color, width=outline_width)
                self._draw_field_content(draw, field, val, curr_x, curr_y, txt_color, data, v_text_circuit)

        extra_fields = []
        if data.get("cri") == "90": extra_fields.append("cri")
        try:
            p_val = float(data.get("power", "0").replace(",", "."))
            if p_val >= 28.8: extra_fields.append("al_profile")
        except: pass
        if data.get("angle"): extra_fields.append("angle")

        for idx, field in enumerate(extra_fields):
            curr_x = x_start + idx * (self.size + self.gap)
            curr_y = y_start + 2 * (self.size + self.gap)
            
            if field == "cri": self._draw_cri(draw, curr_x, curr_y)
            elif field == "angle": self._draw_angle(draw, curr_x, curr_y, data.get("angle"))
            elif field == "al_profile": self._draw_al_profile(draw, curr_x, curr_y)

        self._draw_large_scheme(canvas, data)

        # --- ЛОГИКА ДОБАВЛЕНИЯ НИЖНЕЙ ЧАСТИ (ФУТЕРА) ---
        final_canvas = Image.new('RGB', (1000, 1000), 'white')
        final_canvas.paste(canvas, (0, 0))

        model_full = str(data.get("model", "")).upper().strip()
        model_match = re.search(r'(\d{2}[A-Z])', model_full)
        model_code = model_match.group(1) if model_match else ""
        
        volt_str = str(data.get("voltage", "")).strip()
        volt_code = "".join(filter(str.isdigit, volt_str)) 
        
        color_val = str(data.get("color", "")).upper()
        
        white_keywords = ["NW", "CW", "WW", "EWW", "UWW", "DW", "DUAL", "CCT"]
        yellow_keywords = ["Y", "G", "B", "R", "A", "O", "P", "S", "M", "MR", "SPI", "RGB"]
        
        # suffix = "W"
        if any(kw in color_val for kw in yellow_keywords):
            suffix = "Y"
        elif any(kw in color_val for kw in white_keywords):
            suffix = "W"
        elif any(kw in color_val for kw in white_keywords + yellow_keywords):
            suffix = "" # Default to W if we see any color hint but can't determine


        if model_code and volt_code:
            # 1. Пробуем найти полное имя: МОДЕЛЬ + ВОЛЬТ + СУФФИКС (напр. 10A24Y)
            footer_name_full = f"{model_code}{volt_code}{suffix}"
            footer_path = self._find_image_path(footer_name_full)
            
            # 2. Если не нашли, пробуем без суффикса: МОДЕЛЬ + ВОЛЬТ (напр. 37A24)
            if not footer_path:
                footer_name_short = f"{model_code}{volt_code}"
                footer_path = self._find_image_path(footer_name_short)

            if footer_path:
                try:
                    with Image.open(footer_path) as footer:
                        # Масштабируем по ширине 1000px
                        ratio = 1000 / footer.width
                        new_h = int(footer.height * ratio)
                        footer = footer.resize((1000, new_h), Image.Resampling.LANCZOS)
                        
                        final_canvas.paste(footer, (0, 1000 - footer.height))
                        print(f"SUCCESS: Footer added: {os.path.basename(footer_path)}")
                except Exception as e:
                    print(f"ERROR adding footer: {e}")
            else:
                print(f"WARNING: No footer found for {model_code} {volt_code}")
        
        return final_canvas

    def _draw_cri(self, draw, x, y):
        """Отрисовка CRI 90 с использованием иконки"""
        draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, fill="#EEEEEE", outline="#6E6E6E", width=1)
        
        icon_loaded = False
        try:
            icon_path = self._find_image_path("CRI_90")
            
            if icon_path:
                with Image.open(icon_path) as icon:
                    icon = icon.resize((self.size, self.size), Image.Resampling.LANCZOS)
                    draw._image.paste(icon, (int(x), int(y)), icon if icon.mode == 'RGBA' else None)
                    return
        except: pass
        font = self.f_cri_angle
        draw.text((x + 35, y + 28), "CRI", fill="black", font=font)
        draw.text((x + 45, y + 68), "90", fill="black", font=font)

        # Fallback
        if not icon_loaded:
            font = self.f_cri_angle
            tw_cri = draw.textbbox((0,0), "CRI", font=font)[2]
            draw.text((x + (self.size - tw_cri) / 2, y + 28), "CRI", fill="black", font=font)
            draw.text((x + (self.size - tw_90) / 2, y + 68), "90", fill="black", font=font)

    def _draw_angle(self, draw, x, y, angle_val):
        """Отрисовка угла"""
        draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, fill="#EEEEEE", outline="#6E6E6E", width=1)
        
        txt = f"{angle_val}°"
        font = self.f_cri_angle
        tw = draw.textbbox((0,0), txt, font=font)[2]
        draw.text((x + (self.size-tw)/2, y + 15), txt, fill="black", font=font)
        
        upscale = 4
        temp_size = self.size * upscale
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(temp_img)
        
        cx, cy = temp_size / 2, temp_size - 20 * upscale
        line_len = 70 * upscale
        angle_spread_rad = math.radians(40) 
        line_w = 2 * upscale
        
        lx = cx - line_len * math.sin(angle_spread_rad)
        ly = cy - line_len * math.cos(angle_spread_rad)
        rx = cx + line_len * math.sin(angle_spread_rad)
        ry = cy - line_len * math.cos(angle_spread_rad)
        
        t_draw.line([cx, cy, lx, ly], fill="black", width=line_w)
        t_draw.line([cx, cy, rx, ry], fill="black", width=line_w)
        
        arc_r = 45 * upscale
        t_draw.arc([cx-arc_r, cy-arc_r, cx+arc_r, cy+arc_r], start=235, end=305, fill="black", width=line_w)
        
        temp_img = temp_img.resize((self.size, self.size), Image.Resampling.LANCZOS)
        canvas_ref = draw._image
        canvas_ref.paste(temp_img, (int(x), int(y)), temp_img)

    def _apply_rounded_mask(self, canvas, temp_sq, x, y):
        mask = Image.new('L', (self.size, self.size), 0)
        m_draw = ImageDraw.Draw(mask)
        m_draw.rounded_rectangle([0, 0, self.size, self.size], radius=self.radius, fill=255)
        canvas.paste(temp_sq, (int(x), int(y)), mask)

    def draw_circuit(self, draw, x, y, size, mode, voltage_text):
        rect_x1, rect_y1 = x + 19, y + 63
        rect_x2, rect_y2 = x + size - 19, y + 78
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], outline="black", width=2)
        for i in range(6): 
            dot_x = rect_x1 + 8 + i * 13
            draw.rectangle([dot_x, rect_y1 + 5, dot_x + 4, rect_y1 + 10], fill="black")

        try: f_circ = ImageFont.truetype(config.FONT_REGULAR, 18)
        except: f_circ = ImageFont.load_default()
            
        w_v = draw.textbbox((0,0), voltage_text, font=f_circ)[2]
        text_x = x + (size - w_v) / 2
        text_y = y + 90
        draw.text((text_x, text_y), voltage_text, fill="black", font=f_circ)

        h_v = draw.textbbox((0,0), voltage_text, font=f_circ)[3] - draw.textbbox((0,0), voltage_text, font=f_circ)[1]
        text_center_y = text_y + 4 + h_v / 2
        v_gap = 4 
        dot_y_top = text_center_y - v_gap
        dot_y_bot = text_center_y + v_gap
        dot_x_right = text_x + w_v + 6
        dot_x_left = text_x - 6
        dot_r = 2

        def draw_side(side):
            start_x = rect_x1 if side == "left" else rect_x2
            target_dot_x = dot_x_left if side == "left" else dot_x_right
            if side == "right": elbow_x_outer, elbow_x_inner = start_x + 14, start_x + 8
            else: elbow_x_outer, elbow_x_inner = start_x - 14, start_x - 8

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

    def _draw_al_profile(self, draw, x, y):
        """Отрисовка иконки AL-Profil"""
        draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, fill="#EEEEEE", outline="#6E6E6E", width=1)
        
        txt = "AL-Profil"
        font = self.f_val
        if draw.textbbox((0,0), txt, font=font)[2] > self.size - 10:
             font = self.f_mid
        tw = draw.textbbox((0,0), txt, font=font)[2]
        draw.text((x + (self.size - tw) / 2, y + 10), txt, fill="black", font=font)

        upscale = 8
        ts = self.size * upscale
        timg = Image.new('RGBA', (ts, ts), (0, 0, 0, 0))
        td = ImageDraw.Draw(timg)
        
        cx = ts // 2
        cy = ts // 2 + 6 * upscale
        w_inner = 70 * upscale
        h_wall = 31 * upscale
        base_y = cy + 10 * upscale
        top_y = base_y - h_wall
        wall_thick = 4 * upscale
        fin_len = 8 * upscale
        fin_h = 4 * upscale
        rib_step = 9 * upscale
        line_w = 1 * upscale 

        points = []
        x_wall_left = cx - w_inner // 2 - line_w // 2 - wall_thick
        x_fin_left = x_wall_left - fin_len
        for i in range(3):
            ry = top_y + (i * rib_step)
            points.append((x_fin_left, ry))
            points.append((x_fin_left, ry + fin_h))
            points.append((x_wall_left, ry + fin_h))
            points.append((x_wall_left, ry + rib_step))
            
        points.append((x_fin_left, base_y - fin_h))
        points.append((x_fin_left, base_y + fin_h))
        points.append((x_wall_left, base_y + wall_thick))
        x_wall_right = cx + w_inner // 2 + line_w // 2 + wall_thick
        points.append((x_wall_right, base_y + wall_thick))
        x_fin_right = x_wall_right + fin_len
        points.append((x_fin_right, base_y + fin_h))
        points.append((x_fin_right, base_y - fin_h))
        points.append((x_wall_right, base_y - wall_thick))
        for i in range(2, -1, -1):
            ry = top_y + (i * rib_step)
            points.append((x_wall_right, ry + fin_h + (rib_step - fin_h)))
            points.append((x_wall_right, ry + fin_h))
            points.append((x_fin_right, ry + fin_h))
            points.append((x_fin_right, ry))
        points.append((x_wall_right, top_y))
        points.append((cx + w_inner // 2, top_y))
        points.append((cx + w_inner // 2, base_y - line_w))
        points.append((cx - w_inner // 2, base_y - line_w))
        points.append((cx - w_inner // 2, top_y))
        points.append((x_wall_left, top_y))
        points.append((x_fin_left, top_y))

        td.line(points, fill="black", width=line_w, joint="curve")
        td.rectangle([cx-32*upscale, base_y-9*upscale, cx+32*upscale, base_y-3*upscale], outline="black", fill="#989898", width=1*upscale)
        td.rectangle([cx-8*upscale, base_y-18*upscale, cx+8*upscale, base_y-8*upscale], outline="black", width=1*upscale)

        arrow_y_start = base_y + 8 * upscale
        def draw_wavy_arrow(ax, ay, angle_deg=0):
            import math
            arc_size = 10 * upscale
            line_w = 1 * upscale
            td.arc([ax, ay - 52, ax + arc_size, ay + 88], 330, 66, fill="black", width=line_w)
            td.arc([ax + 4, ay + arc_size, ax + 98, ay + 3 * arc_size], 120, -87, fill="black", width=line_w)
            tip_x = ax - arc_size + 72
            tip_y = ay + 3 * arc_size - 38
            angle_rad = math.radians(angle_deg)
            tsize = 5 * upscale
            base_poly = [(0, 0), (-tsize // 1.5, -tsize), (tsize // 1.5, -tsize)]
            rotated_poly = []
            for px, py in base_poly:
                rx = px * math.cos(angle_rad) - py * math.sin(angle_rad)
                ry = px * math.sin(angle_rad) + py * math.cos(angle_rad)
                rotated_poly.append((rx + tip_x, ry + tip_y))
            td.polygon(rotated_poly, fill="black")

        draw_wavy_arrow(cx - 20*upscale, arrow_y_start, angle_deg=100)
        draw_wavy_arrow(cx - 5*upscale,  arrow_y_start, angle_deg=100)
        draw_wavy_arrow(cx + 10*upscale, arrow_y_start, angle_deg=100)

        timg = timg.resize((self.size, self.size), Image.Resampling.LANCZOS)
        draw._image.paste(timg, (int(x), int(y)), timg)

    def _draw_width_profile(self, draw, x, y, p_type):
        """ Рисует технические разрезы оболочек лент """
        upscale = 4
        tsize = self.size * upscale
        timg = Image.new('RGBA', (tsize, tsize), (0,0,0,0))
        td = ImageDraw.Draw(timg)
        
        cx = tsize // 2
        base_y = 45 * upscale
        w = 60 * upscale
        
        if p_type == "ip20" or p_type == "ip54" or p_type == "ip67_digital":
            td.rectangle([cx-34*upscale, base_y-2*upscale, cx+34*upscale, base_y+3*upscale], outline="black", fill="#989898", width=2*upscale)
            td.rectangle([cx-10*upscale, base_y-8*upscale, cx+10*upscale, base_y], outline="black", width=2*upscale)
        elif p_type == "ip20_cob":
            td.rectangle([cx-34*upscale, base_y-2*upscale, cx+34*upscale, base_y+3*upscale], outline="black", fill="#989898", width=2*upscale)
            td.chord([cx-13*upscale, base_y-8*upscale, cx+13*upscale, base_y+8*upscale], 180, 360, outline="black", width=2*upscale)
        elif p_type == "ip67" or p_type == "ip54_vlhke":
            td.chord([cx-34*upscale, base_y-20*upscale, cx+34*upscale, base_y+28*upscale], 180, 360, outline="black", width=2*upscale)
            td.chord([cx-30*upscale, base_y-16*upscale, cx+30*upscale, base_y+20*upscale], 180, 360, outline="black", width=2*upscale)
            td.rectangle([cx-w//2, base_y-2*upscale, cx+w//2, base_y+3*upscale], outline="black", fill="#989898", width=2*upscale)
            td.rectangle([cx-10*upscale, base_y-10*upscale, cx+10*upscale, base_y], outline="black", width=2*upscale)
        elif p_type == "ip68":
            td.rectangle([cx-34*upscale, base_y-18*upscale, cx+34*upscale, base_y+6*upscale], outline="black", width=2*upscale)
            td.rectangle([cx-w//2, base_y-14*upscale, cx+w//2, base_y+3*upscale], outline="black", width=2*upscale)
            td.rectangle([cx-w//2, base_y-2*upscale, cx+w//2, base_y+3*upscale], outline="black", fill="#989898", width=2*upscale)
            td.rectangle([cx-10*upscale, base_y-10*upscale, cx+10*upscale, base_y], outline="black", width=2*upscale)

        timg = timg.resize((self.size, self.size), Image.Resampling.LANCZOS)
        draw._image.paste(timg, (int(x), int(y)), timg)

    def _draw_large_scheme(self, canvas, data):
        """Отрисовка схемы ленты"""
        import re
        from PIL import Image, ImageDraw

        s = 4
        area_w, area_h = 450, 300
        upscale = 2.8 * s
        temp_img = Image.new("RGBA", (area_w * s, area_h * s), (255, 255, 255, 0))
        td = ImageDraw.Draw(temp_img)
        
        cx = (area_w * s) // 2 - (20 * s)
        base_y = (area_h * s) // 2 + (85 * s)
        
        ip_str = str(data.get("ip", "20")).upper()
        chip_type = str(data.get("chip", "")).upper()
        color_type = str(data.get("color", "")).upper()
        model_val = str(data.get("model", "")).upper().strip()
        if not model_val:
            m_search = re.search(r'(\d{2}B)', str(data))
            model_val = m_search.group(1) if m_search else ""
        
        target_models = ["79B", "80B", "81B", "82B", "83B", "84B"]
        p_type = "ip20"
        if "DIGITAL SPI" in color_type: p_type = "ip67_digital"
        elif "54" in ip_str:
            p_type = "ip54_vlhke" if (model_val in target_models or "VLHK" in ip_str or "NANO" in ip_str) else "ip54"
        elif "67" in ip_str: p_type = "ip67"
        elif "68" in ip_str: p_type = "ip68"
        elif "20" in ip_str: p_type = "ip20_cob" if "COB" in chip_type else "ip20"

        line_w = int(2.5 * s)
        w_rect = int(29 * upscale)
        
        if p_type in ["ip20", "ip54", "ip67_digital"]:
            td.rectangle([cx-w_rect, base_y-2*upscale, cx+w_rect, base_y+3*upscale], outline="black", fill="#989898", width=line_w)
            td.rectangle([cx-10*upscale, base_y-8*upscale, cx+10*upscale, base_y-1*upscale], outline="black", width=line_w)
        elif p_type == "ip20_cob":
            td.rectangle([cx-w_rect, base_y-2*upscale, cx+w_rect, base_y+3*upscale], outline="black", fill="#989898", width=line_w)
            td.chord([cx-13*upscale, base_y-8*upscale, cx+13*upscale, base_y+6*upscale], 180, 360, outline="black", width=line_w)
        elif p_type in ["ip67", "ip54_vlhke"]:
            td.chord([cx-35*upscale, base_y-22*upscale, cx+35*upscale, base_y+28*upscale], 178, 362, outline="black", width=line_w)
            td.chord([cx-31*upscale, base_y-18*upscale, cx+31*upscale, base_y+20*upscale], 178, 362, outline="black", width=line_w)
            td.rectangle([cx-w_rect, base_y-2*upscale, cx+w_rect, base_y+1*upscale], outline="black", fill="#989898", width=line_w)
            td.rectangle([cx-10*upscale, base_y-10*upscale, cx+10*upscale, base_y-1*upscale], outline="black", width=line_w)
        elif p_type == "ip68":
            td.rectangle([cx-w_rect-39, base_y-18*upscale, cx+w_rect+39, base_y+3*upscale], outline="black", width=line_w)
            td.rectangle([cx-w_rect, base_y-15*upscale, cx+w_rect, base_y], outline="black", width=line_w)
            td.rectangle([cx-w_rect+14, base_y-3*upscale, cx+w_rect-14, base_y], outline="black", fill="#989898", width=line_w)
            td.rectangle([cx-10*upscale, base_y-10*upscale, cx+10*upscale, base_y-2*upscale], outline="black", width=line_w)

        draw_line_w = max(1, s // 2)
        width_y = base_y + 45 * s
        x_left, x_right = cx - w_rect, cx + w_rect
        td.line([x_left, base_y + 10*s, x_left, width_y + 10*s], fill="black", width=draw_line_w)
        td.line([x_right, base_y + 10*s, x_right, width_y + 10*s], fill="black", width=draw_line_w)
        td.line([x_left, width_y, x_right, width_y], fill="black", width=draw_line_w)
        td.polygon([(x_left, width_y), (x_left + 6*s, width_y - 3*s), (x_left + 6*s, width_y + 3*s)], fill="black")
        td.polygon([(x_right, width_y), (x_right - 6*s, width_y - 3*s), (x_right - 6*s, width_y + 3*s)], fill="black")

        if p_type == "ip68": top_y = base_y - 18 * upscale
        elif p_type in ["ip67", "ip54_vlhke"]: top_y = base_y - 22 * upscale
        else: top_y = base_y - 10 * upscale
        
        bottom_y = base_y + 3 * upscale
        line_x = cx + w_rect + 25 * s
        td.line([line_x - 10*s, top_y, line_x + 5*s, top_y], fill="black", width=draw_line_w)
        td.line([line_x - 10*s, bottom_y, line_x + 5*s, bottom_y], fill="black", width=draw_line_w)
        td.line([line_x, top_y, line_x, bottom_y], fill="black", width=draw_line_w)
        td.polygon([(line_x, top_y), (line_x - 3*s, top_y + 6*s), (line_x + 3*s, top_y + 6*s)], fill="black")
        td.polygon([(line_x, bottom_y), (line_x - 3*s, bottom_y - 6*s), (line_x + 3*s, bottom_y - 6*s)], fill="black")

        smooth_scheme = temp_img.resize((area_w, area_h), resample=Image.LANCZOS)
        paste_x = self.width - area_w - 10
        paste_y = 280
        canvas.paste(smooth_scheme, (paste_x, paste_y), smooth_scheme)
        
        draw = ImageDraw.Draw(canvas)
        w_val = data.get("width", "10")
        h_val = data.get("height_val", data.get("height", "2,1"))
        
        w_txt = f"{w_val} mm"
        w_bbox = draw.textbbox((0, 0), w_txt, font=self.f_val)
        w_width = w_bbox[2] - w_bbox[0]
        draw.text((paste_x + (area_w - 40)//2 - w_width//2, paste_y + area_h - 50), w_txt, fill="black", font=self.f_val)
        
        h_txt = str(h_val).replace('.', ',')
        h_bbox = draw.textbbox((0, 0), h_txt, font=self.f_val)
        h_height = h_bbox[3] + h_bbox[1]
        line_top_final = paste_y + (top_y / s)
        line_bottom_final = paste_y + (bottom_y / s)
        line_center_y = (line_top_final + line_bottom_final) / 2
        text_y = line_center_y - h_height / 2
        text_x = paste_x + (line_x / s) + 10 
        draw.text((text_x, text_y), h_txt, fill="black", font=self.f_val)

    def _draw_rgb(self, canvas, main_draw, x, y):
        temp_sq = Image.new('RGBA', (self.size, self.size), (0,0,0,0))
        t_draw = ImageDraw.Draw(temp_sq)
        w_third = self.size / 3
        t_draw.rectangle([0, 0, w_third, self.size], fill=config.RGB_COLORS["R"])
        t_draw.rectangle([w_third, 0, 2*w_third, self.size], fill=config.RGB_COLORS["G"])
        t_draw.rectangle([2*w_third, 0, self.size, self.size], fill=config.RGB_COLORS["B"])
        self._apply_rounded_mask(canvas, temp_sq, x, y)
        main_draw.text((x + 2, y + 35), "R", fill="white", font=self.f_rgb_big)
        main_draw.text((x + w_third + 2, y + 35), "G", fill="white", font=self.f_rgb_big)
        main_draw.text((x + 2*w_third + 2, y + 35), "B", fill="white", font=self.f_rgb_big)
        main_draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, outline="#CCCCCC", width=1)

    def _draw_rgbw(self, canvas, main_draw, x, y, val):
        temp_sq = Image.new('RGBA', (self.size, self.size), (0,0,0,0))
        t_draw = ImageDraw.Draw(temp_sq)
        w_third, h_half = self.size / 3, self.size / 2
        t_draw.rectangle([0, 0, w_third, h_half], fill=config.RGB_COLORS["R"])
        t_draw.rectangle([w_third, 0, 2*w_third, h_half], fill=config.RGB_COLORS["G"])
        t_draw.rectangle([2*w_third, 0, self.size, h_half], fill=config.RGB_COLORS["B"])
        sub_part = val.split("+")[1]
        bottom_bg = config.RAW_COLORS.get(sub_part, "white")
        t_draw.rectangle([0, h_half, self.size, self.size], fill=bottom_bg)
        self._apply_rounded_mask(canvas, temp_sq, x, y)
        main_draw.text((x + 6, y + 5), "R", fill="white", font=self.f_rgb_small)
        main_draw.text((x + w_third + 6, y + 5), "G", fill="white", font=self.f_rgb_small)
        main_draw.text((x + 2*w_third + 6, y + 5), "B", fill="white", font=self.f_rgb_small)
        tw = main_draw.textbbox((0,0), sub_part, font=self.f_rgb_big)[2]
        main_draw.text((x + (self.size-tw)/2, y + h_half + 5), sub_part, fill="black", font=self.f_rgb_big)
        main_draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, outline="#CCCCCC", width=1)

    def _draw_dual_white(self, canvas, main_draw, x, y, val):
        temp_sq = Image.new('RGBA', (self.size, self.size), (0,0,0,0))
        t_draw = ImageDraw.Draw(temp_sq)
        h_half = self.size / 2
        parts = val.split("+")
        top_c, bot_c = (parts[0], parts[1]) if len(parts) == 2 else ("NW", "NW")
        bg_top = config.RAW_COLORS.get(top_c, "#EEEEEE")
        bg_bot = config.RAW_COLORS.get(bot_c, "#EEEEEE")
        t_draw.rectangle([0, 0, self.size, h_half], fill=bg_top)
        t_draw.rectangle([0, h_half, self.size, self.size], fill=bg_bot)
        self._apply_rounded_mask(canvas, temp_sq, x, y)
        w1 = main_draw.textbbox((0,0), top_c, font=self.f_dual_top)[2]
        main_draw.text((x + (self.size-w1)/2, y + 10), top_c, fill="black", font=self.f_dual_top)
        w2 = main_draw.textbbox((0,0), bot_c, font=self.f_dual_bot)[2]
        main_draw.text((x + (self.size-w2)/2, y + h_half + 10), bot_c, fill="black", font=self.f_dual_bot)
        main_draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, outline="#CCCCCC", width=1)

    def _draw_life(self, canvas, main_draw, x, y, val, bg_color, data):
        draw_outline = "#6E6E6E" if bg_color.upper() == "#EEEEEE" else None
        main_draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, fill=bg_color, outline=draw_outline, width=1)
        
        oversample = 4
        temp_size = self.size * oversample
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        circle_margin = 5 * oversample
        temp_draw.ellipse([circle_margin, circle_margin, temp_size - circle_margin, temp_size - circle_margin], 
                          outline="black", width=2 * oversample)
        
        l_x = 65 * oversample
        l_y_top = 60 * oversample
        l_y_bot = 105 * oversample
        temp_draw.line([l_x, l_y_top, l_x + 40 * oversample, l_y_top], fill="black", width=2 * oversample)
        temp_draw.line([l_x, l_y_top, l_x, l_y_bot], fill="black", width=2 * oversample)
        
        temp_img = temp_img.resize((self.size, self.size), Image.Resampling.LANCZOS)
        canvas.paste(temp_img, (int(x), int(y)), temp_img)

        full_val = val.replace(" ", "")
        main_part = full_val[:-3] if len(full_val) > 3 else full_val
        small_part = full_val[-3:] if len(full_val) > 3 else ""
        
        w_main = main_draw.textbbox((0, 0), main_part, font=self.f_val)[2]
        main_draw.text((x + 25, y + 18), main_part, fill="black", font=self.f_val)
        
        if small_part: 
            main_draw.text((x + 25 + w_main + 2, y + 24), small_part, fill="black", font=self.f_mid)
        
        try: f_h = ImageFont.truetype(config.FONT_REGULAR, 45)
        except: f_h = ImageFont.load_default()
        
        main_draw.text((x + 35, y + 53), "h", fill="black", font=f_h)

        l_num = data.get("life_l", "70")
        b_num = data.get("life_b", "50")
        l_text = f"L{l_num}"
        b_text = f"B{b_num}"
        main_draw.text((x + 70, y + 63), l_text, fill="black", font=self.f_sub)
        main_draw.text((x + 70, y + 80), b_text, fill="black", font=self.f_sub)

    def _draw_field_content(self, draw, field, val, x, y, txt_color, full_data, v_text):
        if field == "color":
            kelvin = full_data.get("kelvin", "").strip()
            special_colors = ["R", "G", "B", "Y", "UV", "UVA", "V", "A"]
            white_variants = ["NW", "WW", "CW"]
            
            if val in special_colors and not kelvin:
                font = self.f_rgb_big
                bbox = draw.textbbox((0, 0), val, font=font)
                w_c = bbox[2] - bbox[0]
                h_c = bbox[3] - bbox[1]
                draw.text((x + (self.size - w_c) / 2, y + (self.size - h_c) / 2 - 5), 
                          val, fill="white", font=font)
            elif val in white_variants and not kelvin:
                font = self.f_rgb_big
                bbox = draw.textbbox((0, 0), val, font=font)
                w_c = bbox[2] - bbox[0]
                h_c = bbox[3] - bbox[1]
                draw.text((x + (self.size - w_c) / 2, y + (self.size - h_c) / 2 - 5), 
                          val, fill="black", font=font)
            else:
                font_top = self.f_val
                bbox_t = draw.textbbox((0, 0), val, font=font_top)
                w_t = bbox_t[2] - bbox_t[0]
                draw.text((x + (self.size - w_t) / 2, y + 15), val, fill="black", font=font_top)
                
                if kelvin and "-" in kelvin:
                    k1, k2 = kelvin.split("-")
                    txt1 = f"{k1} -"
                    w1 = draw.textbbox((0,0), txt1, font=self.f_mid)[2]
                    draw.text((x + (self.size - w1) / 2, y + 50), txt1, fill="black", font=self.f_mid)
                    txt2 = f"{k2}K"
                    w2 = draw.textbbox((0,0), txt2, font=self.f_mid)[2]
                    draw.text((x + (self.size - w2) - 50 / 2, y + 75), txt2, fill="black", font=self.f_mid)
                elif kelvin:
                    w_k = draw.textbbox((0,0), kelvin, font=self.f_mid)[2]
                    draw.text((x + (self.size - w_k) / 2, y + 60), kelvin, fill="black", font=self.f_mid)
        elif field == "chip":
            val_up = val.upper().strip()
            if val_up == "COB":
                draw.text((x + 27, y + 40), "COB", fill=txt_color, font=self.f_val)
            else:
                s_part = "SMD" if "SMD" in val_up else val_up
                n_part = val.upper().replace("SMD", "").strip()
                draw.text((x + 27, y + 20), s_part, fill=txt_color, font=self.f_val)
                if n_part:
                    draw.text((x + 27, y + 60), n_part, fill=txt_color, font=self.f_val)
        elif field == "voltage":
            num_v = re.sub(r'\D', '', val) 
            draw.text((x + 35, y + 20), f"{num_v}V", fill=txt_color, font=self.f_val)
            draw.text((x + 40, y + 65), "DC", fill=txt_color, font=self.f_val)
        elif field == "ip":
            icon_loaded = False
            try:
                icon_path = self._find_image_path(f"IP_{val}")
                
                if icon_path:
                    with Image.open(icon_path) as icon:
                        target_size = (self.size, self.size)
                        icon = icon.resize(target_size, Image.Resampling.LANCZOS)
                        paste_x = int(x)
                        paste_y = int(y)
                        if icon.mode == 'RGBA':
                            draw._image.paste(icon, (paste_x, paste_y), icon)
                        else:
                            draw._image.paste(icon, (paste_x, paste_y))
                        icon_loaded = True
            except Exception as e:
                print(f"Error loading IP icon: {e}")

            if not icon_loaded:
                draw.text((x + 45, y + 20), "IP", fill=txt_color, font=self.f_val)
                draw.text((x + 40, y + 65), val, fill=txt_color, font=self.f_val)

        elif field in ["max_single", "max_double"]:
            # 1. Загрузка иконки (max-single.png или max-double.png)
            icon_name = field.replace("_", "-") 
            icon_path = self._find_image_path(icon_name)
            
            if icon_path:
                try:
                    with Image.open(icon_path) as icon:
                        # Растягиваем на весь квадрат (124x124)
                        icon = icon.resize((self.size, self.size), Image.Resampling.LANCZOS)
                        
                        # Вставляем на координаты x, y
                        if icon.mode == 'RGBA':
                            draw._image.paste(icon, (int(x), int(y)), icon)
                        else:
                            draw._image.paste(icon, (int(x), int(y)))
                except Exception as e:
                    print(f"Error loading {icon_name}: {e}")

            # 2. Отрисовка текста "≤ {val} m" поверх иконки
            # Вычисляем ширину всех частей текста для центрирования
            w_le = draw.textbbox((0,0), "≤", font=self.f_mid)[2]
            w_val = draw.textbbox((0,0), val, font=self.f_val)[2]
            w_m = draw.textbbox((0,0), " m", font=self.f_mid)[2]
            
            total_w = w_le + w_val + w_m
            
            # Координаты начала текста (по центру горизонтали)
            start_text_x = x + (self.size - total_w) / 2
            text_y = y + 15 # Отступ сверху
            
            # Рисуем части текста
            # Символ "≤"
            draw.text((start_text_x, text_y + 4), "≤", fill="black", font=self.f_mid)
            # Значение
            draw.text((start_text_x + w_le, text_y), val, fill="black", font=self.f_val)
            # Символ "m"
            draw.text((start_text_x + w_le + w_val, text_y + 4), " m", fill="black", font=self.f_mid)

            # 3. Отрисовка текста напряжения (V DC) внизу
            # v_text obsahuje строку, např. "24 V DC"
            w_volt = draw.textbbox((0,0), v_text, font=self.f_sub)[2]
            start_volt_x = x + (self.size - w_volt) / 2
            volt_y = y + 88 # Отступ для нижней части
            
            draw.text((start_volt_x, volt_y), v_text, fill="black", font=self.f_sub)

        elif field == "cut":
            led_val = str(full_data.get("led_segment", "")).strip()
            if not led_val or led_val == "0":
                all_text = " ".join(str(v) for v in full_data.values())
                match = re.search(r'(\d+)\s*LED', all_text, re.IGNORECASE)
                if match:
                    led_val = match.group(1)
            led_val = "".join(filter(str.isdigit, led_val)) if led_val else "0"
            w_l = draw.textbbox((0,0), led_val, font=self.f_cut_num)[2]
            draw.text((x + 35 - w_l/2, y + 15), led_val, fill="black", font=self.f_cut_num)
            draw.text((x + 40 + w_l/2, y + 15), "LED", fill="black", font=self.f_mid)
            line_y = y + 55
            draw.line([x + 15, line_y, x + self.size - 15, line_y], fill="black", width=2)
            draw.line([x + 15, line_y - 5, x + 15, line_y + 5], fill="black", width=2)
            draw.line([x + self.size - 15, line_y - 5, x + self.size - 15, line_y + 5], fill="black", width=2)
            w_m = draw.textbbox((0,0), val, font=self.f_cut_num)[2]
            draw.text((x + (self.size - w_m)/2, y + 65), val, fill="black", font=self.f_cut_num)
            w_mm = draw.textbbox((0,0), "mm", font=self.f_mid)[2]
            draw.text((x + (self.size - w_mm)/2, y + 90), "mm", fill="black", font=self.f_mid)
        elif field == "width":
            ip_val = str(full_data.get("ip", "")).strip()
            chip_val = str(full_data.get("chip", "")).upper()
            color_val = str(full_data.get("color", "")).upper()
            model_val = str(full_data.get("model", "")).upper().strip()
            if not model_val:
                all_data_str = str(full_data)
                m_search = re.search(r'(\d{2}B)', all_data_str)
                if m_search:
                    model_val = m_search.group(1)
            target_models = ["79B", "80B", "81B", "82B", "83B", "84B"]
            icon_to_draw = "ip20"
            if "DIGITAL SPI" in color_val:
                icon_to_draw = "ip67_digital"
            elif ip_val == "54" and model_val in target_models:
                icon_to_draw = "ip54_vlhke"
            elif ip_val == "54":
                icon_to_draw = "ip54"
            elif ip_val == "67":
                icon_to_draw = "ip67"
            elif ip_val == "68":
                icon_to_draw = "ip68"
            elif ip_val == "20":
                icon_to_draw = "ip20_cob" if "COB" in chip_val else "ip20"
            self._draw_width_profile(draw, x, y, icon_to_draw)
            line_y = y + 15
            draw.line([x + 26, line_y - 7, x + 26, line_y + 7], fill="black", width=1)
            draw.line([x + self.size - 26, line_y - 7, x + self.size - 26, line_y + 7], fill="black", width=1)
            arrow_y = 15
            draw.line([x + 26, y + arrow_y, x + self.size - 26, y + arrow_y], fill="black", width=1)
            draw.line([x + 26, y + arrow_y, x + 32, y + arrow_y - 3], fill="black", width=1)
            draw.line([x + 26, y + arrow_y, x + 32, y + arrow_y + 3], fill="black", width=1)
            draw.line([x + self.size - 26, y + arrow_y, x + self.size - 32, y + arrow_y - 3], fill="black", width=1)
            draw.line([x + self.size - 26, y + arrow_y, x + self.size - 32, y + arrow_y + 3], fill="black", width=1)
            w_v = draw.textbbox((0,0), val, font=self.f_val)[2]
            draw.text((x + (self.size - w_v) / 2, y + 50), val, fill="black", font=self.f_val)
            w_m = draw.textbbox((0,0), "mm", font=self.f_mid)[2]
            draw.text((x + (self.size - w_m) / 2, y + 78), "mm", fill="black", font=self.f_mid)
        else:
            sub = config.SUB_TEXTS.get(field, "")
            w_v = draw.textbbox((0,0), val, font=self.f_val)[2]
            draw.text((x + (self.size-w_v)/2, y + 20), val, fill=txt_color, font=self.f_val)
            if sub:
                w_s = draw.textbbox((0,0), sub, font=self.f_mid)[2]
                draw.text((x + (self.size-w_s)/2, y + 65), sub, fill=txt_color, font=self.f_mid)
