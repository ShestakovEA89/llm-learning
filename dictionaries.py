# # Список хранит просто значения
# words = ["laptop", "window", "key"]

# # Словарь хранит пары ключ: значение
# person = {
#     "name": "Женя",
#     "city": "Москва",
#     "age": 30
# }

# # Обращаться к значению через ключ
# print(person["name"])   # выведет: Женя
# print(person["city"])   # выведет: Москва

tools = {
    "name": "Kaggle",
    "url": "https://www.kaggle.com/",
    "category": "Data Science",
    "is_free": True
}

print(tools["name"])
print(tools["url"])
print(tools["category"])
print(tools["is_free"])

# Добавить новое поле в существующий словарь
tools["description"] = "Платформа для обучения Data Science и ML"

# Пройтись по всем полям словаря
for key, value in tools.items():
    print(f"{key}: {value}")