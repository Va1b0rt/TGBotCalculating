import gzip
import base64

def compress_string(input_string):
    # Преобразование строки в байты
    input_bytes = input_string.encode('utf-8')

    # Сжатие байтов с использованием gzip
    compressed_bytes = gzip.compress(input_bytes)

    # Кодирование сжатых байтов в base64 для сохранения
    compressed_string = base64.b64encode(compressed_bytes).decode('utf-8')

    return compressed_string

def decompress_string(compressed_string):
    # Декодирование base64
    compressed_bytes = base64.b64decode(compressed_string)

    # Разжатие байтов с использованием gzip
    decompressed_bytes = gzip.decompress(compressed_bytes)

    # Преобразование байтов в строку
    decompressed_string = decompressed_bytes.decode('utf-8')

    return decompressed_string


def shorten_name(full_name):
    # Разбить полное имя на компоненты
    parts = full_name.split()

    # Проверка наличия фамилии и имени
    if len(parts) < 2:
        return full_name  # Возвращаем исходную строку, если нет фамилии или имени

    # Сокращение имени и отчества
    shortened_name = parts[0] + " " + " ".join([name[0] + "." for name in parts[1:]])

    return shortened_name


if __name__ == "__main__":
    # Пример использования
    original_string = "Это очень длинная строка, которую мы сжимаем и разжимаем."
    compressed_string = compress_string(original_string)

    print(f"Исходная строка: {original_string}")
    print(f"Сжатая строка: {compressed_string}")

    decompressed_string = decompress_string(compressed_string)
    print(f"Разжатая строка: {decompressed_string}")