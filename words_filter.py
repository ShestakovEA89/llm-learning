# words = []

# for i in range(1, 6):
#     word = input(f"Введите слово {i}: ")
#     words.append(word)

# for word in words:
#     if len(word) > 4:
#         print(word)

# words_count = 0
# for word in words:
#     if len(word) > 4:
#         words_count += 1
# print(f"Количество слов, в которых больше 4 букв: {words_count}")

words = []

for i in range(1, 6):
    word = input(f"Введите слово {i}: ")
    words.append(word)

long_words = []
for word in words:
    if len(word) > 4:
        long_words.append(word)
        print(word)

print(f"Количество слов длиннее 4 букв: {len(long_words)}")