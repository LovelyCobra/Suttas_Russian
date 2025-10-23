from PIL import Image, ImageDraw, ImageFont
import re, os
from cobraprint import col

# Adding one title to an image in horizontally centered position
def cover_gen(title, img_path, output_path, color, font_path, vertical_pos=None, show=True):
    image = Image.open(img_path)
    (width, height) = image.size
    horizontal_pos = width//2
    if not vertical_pos:
        vertical_pos = height - 50


    title_font = ImageFont.truetype(font_path, size=30)
    draw = ImageDraw.Draw(image)

    draw.text((horizontal_pos, vertical_pos), title, fill=color, anchor='mm', font=title_font)

    image.save(output_path)
    if show:
        image.show()

if __name__ == "__main__":
    title = 'Ebook: www.github.com/LovelyCobra'
    title2 = '       с ударениями\nдля студентов русскoвo'
    img_path = 'Russ_suttas/Digha-cover_stressed.jpg'
    output_path = 'Russ_suttas/Digha-cover_stressed_.jpg'
    color = "#EAF1ED"
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf'

    cover_gen(title, img_path, output_path, color, font_path)

    # Digha_cover.jpg, Digha-cover.jpg