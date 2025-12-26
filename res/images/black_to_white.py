from PIL import Image
import numpy as np
import glob
import os

FILENAME = os.path.basename(__file__)

def black_to_white_png_files(threshold=50, name: str = "*"):
    """
    Обрабатывает все PNG файлы в текущей папке, заменяя черный на белый
    """
    # Получаем список всех PNG файлов в текущей папке
    
    png_files = glob.glob(__file__.removesuffix(FILENAME) + f"{name}.png")

    if not png_files and name != "*":
        print(f"✗ Файл {name}.png не найден в текущей папке")
        return

    if not png_files:
        print("✗ В текущей папке не найдено PNG файлов")
        return
    
    files_list = '\n- '.join(png_files).replace(__file__.removesuffix(FILENAME), "")
    print(f"Найдено {len(png_files)} PNG файлов для обработки:\n- {files_list}")
    
    for filename in png_files:
        try:
            # Открываем изображение
            img = Image.open(filename)
            img = img.convert("RGBA")
            data = np.array(img)
            
            # Создаем маску черных пикселей
            black_mask = np.all(data[:, :, :3] <= threshold, axis=2) & (data[:, :, 3] > 0)
            
            # Заменяем RGB на белый, сохраняя альфа-канал
            data[black_mask, :3] = 255
            
            # Сохраняем результат (перезаписываем исходный файл)
            result = Image.fromarray(data, 'RGBA')
            result.save(filename)
            print(f"✓ Обработан файл: {filename.replace(__file__.removesuffix(FILENAME), '')}" + " " * 100 + "\r", end="")
            
        except Exception as e:
            print(f"\n✗ Ошибка при обработке {filename}: {e}")

    print("\n✓ Обработка завершена.")

# Запуск обработки
if __name__ == "__main__":
    print("=== Black to White PNG Converter ===")
    images = input("Введите имя файла .png (без формата) для обработки или оставьте поле пустым для обработки всех файлов: ")
    if images.strip():
        black_to_white_png_files(threshold=50, name=images.strip())
    else:
        black_to_white_png_files(threshold=50)
