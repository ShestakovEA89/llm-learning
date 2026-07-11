words = []

for i in range(1, 6):
    word = input(f"Введите слово {i}: ")
    words.append(word)

words.sort()
print(f"Слова по алфавиту: {words}")

max_word = max(words, key=len)
print(f"Самое длинное слово: {max_word}")

min_word = min(words, key=len)
print(f"Самое короткое слово: {min_word}")