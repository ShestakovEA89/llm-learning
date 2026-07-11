number1 = int(input("Введите первое число: "))
number2 = int(input("Введите второе число: "))

if number2 == 0:
    print("Ошибка: деление на ноль невозможно")
else:
    print(f"Сумма чисел {number1} и {number2} равна {number1 + number2}")
    print(f"Разность чисел {number1} и {number2} равна {number1 - number2}")
    print(f"Произведение чисел {number1} и {number2} равно {number1 * number2}")
    print(f"Частное чисел {number1} и {number2} равно {number1 / number2}")