from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

img = Image.open('sample.png')

# 이미지에서 텍스트 추출
text = pytesseract.image_to_string(img, lang='kor')

print("이미지에서 추출한 텍스트:")
print(text)
