# drawer.py
from PIL import Image, ImageDraw, ImageFont, ImageOps
import config
import re
import math

class LedImageGenerator:
    def __init__(self, width=1000, height=320):
        self.width = width
        self.height = height
        self.size = 120
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
            # Специальный крупный шрифт для CRI и Angle
            self.f_cri_angle = ImageFont.truetype(config.FONT_BOLD, 26)
        except:
            self.f_val = self.f_mid = self.f_sub = self.f_cut_num = \
            self.f_rgb_small = self.f_rgb_big = self.f_dual_top = \
            self.f_dual_bot = self.f_cri_angle = ImageFont.load_default()

    def generate(self, data):
        has_dynamic = data.get("cri") == "90" or data.get("angle")
        canvas_height = self.height + 150 if has_dynamic else self.height
        canvas = Image.new('RGB', (self.width, canvas_height), 'white')
        draw = ImageDraw.Draw(canvas)

        grid = [
            ["color", "chip", "leds", "power", "lumen", "width"],
            ["ip", "voltage", "cut", "max_single", "max_double", "life"]
        ]
        
        # --- РАСЧЕТ ЦЕНТРИРОВАНИЯ ---
        # Считаем общую ширину контента: 6 колонок * ширину + 5 отступов
        num_cols = 6
        content_width = (num_cols * self.size) + ((num_cols - 1) * self.gap)
        
        # Вычисляем начальную точку X, чтобы отступы слева и справа были равны
        x_start = (self.width - content_width) // 2
        y_start = 20

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
                    if "SPI" in val_up:
                        draw.rounded_rectangle([curr_x, curr_y, curr_x + self.size, curr_y + self.size], radius=self.radius, fill="#EEEEEE")
                        # Digital SPI logic
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
                        if "RGB" in val and "+" not in val:
                             self._draw_rgb(canvas, draw, curr_x, curr_y)
                        elif "RGB" in val and "+" in val:
                             self._draw_rgbw(canvas, draw, curr_x, curr_y, val)
                        else:
                             self._draw_dual_white(canvas, draw, curr_x, curr_y, val)
                        continue

                if field == "life":
                    self._draw_life(canvas, draw, curr_x, curr_y, val, bg_color)
                    continue

                if field == "color":
                    bg_color = config.COLOR_MAP_LIGHT.get(val.upper(), "#EEEEEE")
                elif field == "chip":
                    clean_val = val.upper().replace(" ", "").replace("-", "")
                    for k, h in config.COLOR_MAP_CHIP.items():
                        if k.upper() in clean_val:
                            bg_color = h; txt_color = "white"; break
                elif field == "ip":
                    txt_color = config.COLOR_MAP_IP.get("IP"+val, config.COLOR_MAP_IP.get(val, "#A68FB8"))
                elif field == "voltage":
                    if "24" in val: txt_color = config.COLOR_MAP_VOLTAGE["24"]
                    elif "12" in val: txt_color = config.COLOR_MAP_VOLTAGE["12"]

                draw.rounded_rectangle([curr_x, curr_y, curr_x + self.size, curr_y + self.size], radius=self.radius, fill=bg_color)
                self._draw_field_content(draw, field, val, curr_x, curr_y, txt_color, data, v_text_circuit)

        extra_fields = []
        if data.get("cri") == "90": extra_fields.append("cri")
        if data.get("angle"): extra_fields.append("angle")

        for idx, field in enumerate(extra_fields):
            curr_x = x_start + idx * (self.size + self.gap)
            curr_y = y_start + 2 * (self.size + self.gap)
            
            if field == "cri":
                self._draw_cri(draw, curr_x, curr_y)
            elif field == "angle":
                self._draw_angle(draw, curr_x, curr_y, data.get("angle"))

        return canvas

    # --- МЕТОДЫ ОТРИСОВКИ С ВЫСОКИМ КАЧЕСТВОМ (Super-sampling) ---

    def _draw_cri(self, draw, x, y):
        """Отрисовка CRI 90: Желтая звезда через суперсэмплинг для идеальной гладкости"""
        # 1. Создаем временное изображение в 4 раза больше целевого размера
        upscale = 4
        temp_size = self.size * upscale
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Центр и радиусы во вспомогательном пространстве
        cx, cy = temp_size / 2, temp_size / 2
        r_outer = 56 * upscale
        r_inner = 38 * upscale
        num_points = 12
        
        points = []
        for i in range(num_points * 2):
            angle = math.radians(i * (360 / (num_points * 2)) - 90)
            r = r_outer if i % 2 == 0 else r_inner
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            
        # Рисуем звезду
        temp_draw.polygon(points, fill="#FFF200", outline="#FFA500")
        temp_draw.line(points + [points[0]], fill="#FFA500", width=2 * upscale)
        
        # 2. Уменьшаем изображение с качественным сглаживанием
        temp_img = temp_img.resize((self.size, self.size), Image.Resampling.LANCZOS)
        
        # 3. Рисуем фон и накладываем звезду
        draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, fill="#EEEEEE")
        
        # Накладываем через доступ к основному изображению
        canvas_ref = draw._image 
        canvas_ref.paste(temp_img, (int(x), int(y)), temp_img)
        
        # 4. Текст рисуем поверх (шрифты в Pillow и так имеют сглаживание)
        font = self.f_cri_angle
        tw_cri = draw.textbbox((0,0), "CRI", font=font)[2]
        tw_90 = draw.textbbox((0,0), "90", font=font)[2]
        
        # Текст позиционируется относительно оригинальных координат x, y
        draw.text((x + (self.size - tw_cri) / 2, y + 28), "CRI", fill="black", font=font)
        draw.text((x + (self.size - tw_90) / 2, y + 68), "90", fill="black", font=font)

    def _draw_angle(self, draw, x, y, angle_val):
        """Отрисовка угла: Тонкие линии без лесенки через суперсэмплинг"""
        draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, fill="#EEEEEE")
        
        # Текст
        txt = f"{angle_val}°"
        font = self.f_cri_angle
        tw = draw.textbbox((0,0), txt, font=font)[2]
        draw.text((x + (self.size-tw)/2, y + 15), txt, fill="black", font=font)
        
        # Пиктограмма через суперсэмплинг
        upscale = 4
        temp_size = self.size * upscale
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(temp_img)
        
        cx, cy = temp_size / 2, temp_size - 20 * upscale
        line_len = 70 * upscale
        angle_spread_rad = math.radians(40) 
        line_w = 2 * upscale
        
        # Левая и правая линии
        lx = cx - line_len * math.sin(angle_spread_rad)
        ly = cy - line_len * math.cos(angle_spread_rad)
        rx = cx + line_len * math.sin(angle_spread_rad)
        ry = cy - line_len * math.cos(angle_spread_rad)
        
        t_draw.line([cx, cy, lx, ly], fill="black", width=line_w)
        t_draw.line([cx, cy, rx, ry], fill="black", width=line_w)
        
        # Дуга
        arc_r = 45 * upscale
        t_draw.arc([cx-arc_r, cy-arc_r, cx+arc_r, cy+arc_r], start=235, end=305, fill="black", width=line_w)
        
        # Ресайз и вставка
        temp_img = temp_img.resize((self.size, self.size), Image.Resampling.LANCZOS)
        canvas_ref = draw._image
        canvas_ref.paste(temp_img, (int(x), int(y)), temp_img)

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (Без изменений логики, но с новыми координатами) ---
    def _apply_rounded_mask(self, canvas, temp_sq, x, y):
        mask = Image.new('L', (self.size, self.size), 0)
        m_draw = ImageDraw.Draw(mask)
        m_draw.rounded_rectangle([0, 0, self.size, self.size], radius=self.radius, fill=255)
        canvas.paste(temp_sq, (int(x), int(y)), mask)

    def draw_circuit(self, draw, x, y, size, mode, voltage_text):
        rect_x1, rect_y1 = x + 20, y + 50
        rect_x2, rect_y2 = x + size - 20, y + 65
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], outline="black", width=2)
        for i in range(6): 
            dot_x = rect_x1 + 5 + i * 13
            draw.rectangle([dot_x, rect_y1 + 4, dot_x + 4, rect_y1 + 8], fill="black")

        try: f_circ = ImageFont.truetype(config.FONT_REGULAR, 18)
        except: f_circ = ImageFont.load_default()
            
        w_v = draw.textbbox((0,0), voltage_text, font=f_circ)[2]
        text_x = x + (size - w_v) / 2
        text_y = y + 85
        draw.text((text_x, text_y), voltage_text, fill="black", font=f_circ)

        h_v = draw.textbbox((0,0), voltage_text, font=f_circ)[3] - draw.textbbox((0,0), voltage_text, font=f_circ)[1]
        text_center_y = text_y + h_v / 2
        v_gap = 8 
        dot_y_top = text_center_y - v_gap
        dot_y_bot = text_center_y + v_gap
        dot_x_right = text_x + w_v + 12
        dot_x_left = text_x - 12
        dot_r = 3

        def draw_side(side):
            start_x = rect_x1 if side == "left" else rect_x2
            target_dot_x = dot_x_left if side == "left" else dot_x_right
            if side == "right": elbow_x_outer, elbow_x_inner = start_x + 15, start_x + 8
            else: elbow_x_outer, elbow_x_inner = start_x - 15, start_x - 8

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

    def _draw_width_profile(self, draw, x, y, p_type):
        """ Рисует технические разрезы оболочек лент """
        upscale = 4
        tsize = self.size * upscale
        timg = Image.new('RGBA', (tsize, tsize), (0,0,0,0))
        td = ImageDraw.Draw(timg)
        
        cx = tsize // 2
        base_y = 45 * upscale # Линия платы
        w = 60 * upscale      # Ширина профиля
        h = 32 * upscale      # Высота профиля
        
        if p_type == "ip20" or p_type == "ip54" or p_type == "ip67_digital":
            # IP20, IP54, IP67(DIGI SPI): Просто плата и чип сверху
            td.rectangle([cx-34*upscale, base_y-2*upscale, cx+34*upscale, base_y+3*upscale], outline="black", fill="#989898", width=2*upscale)
            td.rectangle([cx-10*upscale, base_y-8*upscale, cx+10*upscale, base_y], outline="black", width=2*upscale)
            
        elif p_type == "ip20_cob":
            # IP20 COB: Плата и чип дугообразный
            td.rectangle([cx-34*upscale, base_y-2*upscale, cx+34*upscale, base_y+3*upscale], outline="black", width=2*upscale)
            td.chord([cx-13*upscale, base_y-8*upscale, cx+13*upscale, base_y+8*upscale], 180, 360, outline="black", width=2*upscale)
        
        # elif p_type == "ip54_vlhke":
        #     # IP54 / Vlhke prostredi: Плата под куполом
        #     td.line([cx-w//2, base_y, cx+w//2, base_y], fill="black", width=2*upscale)
        #     td.arc([cx-w//2, base_y-30*upscale, cx+w//2, base_y+10*upscale], 180, 360, fill="black", width=2*upscale)

        elif p_type == "ip67" or p_type == "ip54_vlhke":
            # IP67: В полукруглом корпусе со стенками находится плата и чип
            td.chord([cx-34*upscale, base_y-20*upscale, cx+34*upscale, base_y+28*upscale], 180, 360, outline="black", width=2*upscale)
            td.chord([cx-30*upscale, base_y-16*upscale, cx+30*upscale, base_y+20*upscale], 180, 360, outline="black", width=2*upscale)
            td.rectangle([cx-w//2, base_y-2*upscale, cx+w//2, base_y+3*upscale], outline="black", fill="#989898", width=2*upscale)
            td.rectangle([cx-10*upscale, base_y-10*upscale, cx+10*upscale, base_y], outline="black", width=2*upscale)

        elif p_type == "ip68":
            # IP68: В прямоугольнике со стенками находится плата и чип
            td.rectangle([cx-34*upscale, base_y-18*upscale, cx+34*upscale, base_y+6*upscale], outline="black", width=2*upscale)
            td.rectangle([cx-w//2, base_y-14*upscale, cx+w//2, base_y+3*upscale], outline="black", width=2*upscale)
            td.rectangle([cx-w//2, base_y-2*upscale, cx+w//2, base_y+3*upscale], outline="black", fill="#989898", width=2*upscale)
            td.rectangle([cx-10*upscale, base_y-10*upscale, cx+10*upscale, base_y], outline="black", width=2*upscale)

        timg = timg.resize((self.size, self.size), Image.Resampling.LANCZOS)
        draw._image.paste(timg, (int(x), int(y)), timg)

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

    def _draw_life(self, canvas, main_draw, x, y, val, bg_color):
        main_draw.rounded_rectangle([x, y, x + self.size, y + self.size], radius=self.radius, fill=bg_color)
        oversample = 4
        temp_size = self.size * oversample
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        circle_margin = 5 * oversample
        temp_draw.ellipse([circle_margin, circle_margin, temp_size - circle_margin, temp_size - circle_margin], outline="black", width=2 * oversample)
        l_x = 65 * oversample; l_y_top = 60 * oversample; l_y_bot = 105 * oversample
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
        main_draw.text((x + 70, y + 63), "L70", fill="black", font=self.f_sub)
        main_draw.text((x + 70, y + 80), "B50", fill="black", font=self.f_sub)

    def _draw_field_content(self, draw, field, val, x, y, txt_color, full_data, v_text):
        if field == "color":
            kelvin = full_data.get("kelvin", "").strip()
            draw.text((x + 20, y + 15), val, fill="black", font=self.f_val)
            if kelvin and "-" in kelvin:
                k1, k2 = kelvin.split("-")
                draw.text((x + 22, y + 50), f"{k1} -", fill="black", font=self.f_mid)
                draw.text((x + 18, y + 75), f"{k2}K", fill="black", font=self.f_mid)
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
            draw.text((x + 45, y + 20), "IP", fill=txt_color, font=self.f_val)
            draw.text((x + 40, y + 65), val, fill=txt_color, font=self.f_val)
        elif field in ["max_single", "max_double"]:
            draw.text((x + 20, y + 15), "≤", fill="black", font=self.f_mid)
            w_n = draw.textbbox((0,0), val, font=self.f_val)[2]
            draw.text((x + 40, y + 10), val, fill="black", font=self.f_val)
            draw.text((x + 45 + w_n, y + 15), "m", fill="black", font=self.f_mid)
            line_y = y + 45
            draw.line([x + 20, line_y - 5, x + 20, line_y + 5], fill="black", width=1)
            draw.line([x + self.size - 20, line_y - 5, x + self.size - 20, line_y + 5], fill="black", width=1)
            arrow_y = 45
            draw.line([x + 20, y + arrow_y, x + self.size - 20, y + arrow_y], fill="black", width=1)
            draw.line([x + 20, y + arrow_y, x + 25, y + arrow_y - 3], fill="black", width=1)
            draw.line([x + 20, y + arrow_y, x + 25, y + arrow_y + 3], fill="black", width=1)
            draw.line([x + self.size - 20, y + arrow_y, x + self.size - 25, y + arrow_y - 3], fill="black", width=1)
            draw.line([x + self.size - 20, y + arrow_y, x + self.size - 25, y + arrow_y + 3], fill="black", width=1)
            self.draw_circuit(draw, x, y, self.size, "single" if field == "max_single" else "double", v_text)
        elif field == "cut":
            led_val = full_data.get("led_segment", "").strip()
            w_l = draw.textbbox((0,0), led_val, font=self.f_cut_num)[2]
            draw.text((x + 35 - w_l/2, y + 15), led_val, fill="black", font=self.f_cut_num)
            draw.text((x + 40 + w_l/2, y + 15), "LED", fill="black", font=self.f_mid)
            line_y = y + 55
            draw.line([x + 15, line_y, x + self.size - 15, line_y], fill="black", width=2)
            draw.line([x + 15, line_y - 5, x + 15, line_y + 5], fill="black", width=2)
            draw.line([x + self.size - 15, line_y - 5, x + self.size - 15, line_y + 5], fill="black", width=2)
            w_m = draw.textbbox((0,0), val, font=self.f_cut_num)[2]
            draw.text((x + (self.size - w_m)/2, y + 65), val, fill="black", font=self.f_cut_num)
            draw.text((x + 40, y + 90), "mm", fill="black", font=self.f_mid)
        elif field == "width":
            # Логика выбора иконки по твоим пунктам
            ip_val = str(full_data.get("ip", "")).strip()
            chip_val = str(full_data.get("chip", "")).upper()
            color_val = str(full_data.get("color", "")).upper()
            model_val = str(full_data.get("model", "")).upper().strip()
            # all_text = str(full_data).lower()
            
            if not model_val:
                all_data_str = str(full_data)
                m_search = re.search(r'(\d{2}B)', all_data_str)
                if m_search:
                    model_val = m_search.group(1)

            target_models = ["79B", "80B", "81B", "82B", "83B", "84B"]

            icon_to_draw = "ip20" # По умолчанию
            

            print(f"--- DEBUG INFO ---")
            print(f"Full Data Keys: {list(full_data.keys())}") # Проверим, какие ключи вообще есть
            print(f"MODEL_VAL: '{model_val}'")
            print(f"------------------")

            # Приоритет 1: Digital SPI
            if "DIGITAL SPI" in color_val:
                icon_to_draw = "ip67_digital"
            # УСЛОВИЕ: Если IP54 и модель входит в наш список
            elif ip_val == "54" and model_val in target_models:
                icon_to_draw = "ip54_vlhke"
            elif ip_val == "54":
                icon_to_draw = "ip54"
            # Приоритет 3: Конкретные IP
            elif ip_val == "67":
                icon_to_draw = "ip67"
            elif ip_val == "68":
                icon_to_draw = "ip68"
            # Приоритет 4: IP20 (обычная или COB)
            elif ip_val == "20":
                icon_to_draw = "ip20_cob" if "COB" in chip_val else "ip20"

            # Рисуем иконку
            self._draw_width_profile(draw, x, y, icon_to_draw)
            
            # Рисуем текст (число и mm)
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
    
    