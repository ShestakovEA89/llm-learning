words = []

for i in range(1, 6):
    word = input(f"Введите слово {i}: ")
    words.append(word)

for word in words:
    print(word)

print(f"Количество слов: {len(words)}")