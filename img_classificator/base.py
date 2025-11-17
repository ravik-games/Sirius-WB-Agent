import base64
import sys

def image_to_base64(image_path):
    """Конвертирует изображение в base64 строку"""
    with open(image_path, "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_string

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python base64_converter.py /mnt/c/Yulia/sirius/Sirius-WB-Agent/img/image.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        base64_str = image_to_base64(image_path)
        print("Base64 строка:")
        print(base64_str)
        print(f"\nДлина строки: {len(base64_str)} символов")
    except Exception as e:
        print(f"Ошибка: {e}")