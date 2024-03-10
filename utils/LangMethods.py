from langdetect import detect


def is_ukrainian(text):
    # Проверяем язык текста, используя библиотеку langdetect
    language = detect(text)
    # Если язык - украинский, возвращаем True
    return language == 'uk'


def latin_to_cyrillic(text):
    if is_ukrainian(text):
        # Словарь для замены латинских букв на кириллические
        latin_to_cyrillic_dict = {
            'i': 'і', 'I': 'І', 'a': 'а', 'A': 'А', 'o': 'о', 'O': 'О', 'e': 'Е', 'E': 'Е', 'c': 'с', 'C': 'С',
            'p': 'з', 'P': 'З', 'x': 'х', 'X': 'Х', 'y': 'у', 'Y': 'У', 'k': 'к', 'K': 'К', 'm': 'м', 'M': 'М',
            'T': 'Т', 'B': 'В', 'H': 'Н'
        }

        cyrillic_text = ''
        for char in text:
            # Если символ - кириллица, оставляем его без изменений
            if char.isalpha() and ord(char) >= 0x0400 and ord(char) <= 0x04FF:
                cyrillic_text += char
            # Если символ - латиница, заменяем его на кириллицу (если есть замена в словаре)
            elif char in latin_to_cyrillic_dict:
                cyrillic_text += latin_to_cyrillic_dict[char]
            else:
                cyrillic_text += char

        return cyrillic_text
    else:
        # Если текст на английском, возвращаем исходную строку
        return text

