from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps

img = Image.open('./young.jpeg')
img_greyscale = img.convert('L')
img_greyscale.save('./filtered.jpg')
