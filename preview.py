from PIL import Image, ImageDraw
from drawer import LedImageGenerator
import config

def show_preview():
    gen = LedImageGenerator()
    # Создаем холст чуть больше иконки, чтобы видеть границы
    canvas_size = gen.size + 40
    test_img = Image.new('RGBA', (canvas_size, canvas_size), "white")
    draw = ImageDraw.Draw(test_img)

    # Рисуем иконку
    gen._draw_al_profile(draw, 20, 20)

    # Показываем результат (откроется стандартным просмотрщиком фото)
    test_img.show()

if __name__ == "__main__":
    show_preview()