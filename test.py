import requests

url = 'http://127.0.0.1:8888/employers?_filter=%7B%7D&_range=%5B0%2C4%5D&_sort=%5B%22ASC_ident_EDRPOU%22%5D'  # Замените на нужный URL

# Отправляем GET-запрос по указанному URL
response = requests.get(url)

# Печатаем заголовки ответа
print("Заголовки:")
for header, value in response.headers.items():
    print(f"{header}: {value}")

# Печатаем содержимое ответа
print("\nСодержимое:")
print(response.text)
