# Steganography


# Лаба 1 
Запуск: python3 lab1.py

Как работает?

Класс BitImageVisualizer содержит методы для отрисовки интерфейса приложения и подсвечивания выбранного бита в пикселе (визуальная атака на контейнер).
(см. статью Герлинг, Е. Ю. Исследование эффективности методов обнаружения стегосистем, использующих вложение в наименее значащие биты / Е. Ю. Герлинг // Информационные системы и технологии. – 2011. – № 4(66). – С. 137-144. – EDN NUREKZ.)

Метод initUI устанавливает параметры главного окна и вызывает методы для создания отдельных частей интерфейса.

Для большей наглядности реализована визуализация выбранного бита в отдельной панели.

Визуальная атака происходит в методе generate_bit_image. Из изначального изображения строится измененная версия, в которой каждый пиксель принимает значение выбранного бита.


# Лаба 2
Запуск: python3 lab2.py

Как работает?

В классе MainWindow реализованы методы отрисовки интерфейса, загрузки и сохранения изображений, а также функции скрытия и извлечения сообщения из контейнера и проверки работы метода CDB (Куттера-Джордана-Боссена).

Реализована возможность внедрения цвз - произвольного текста. Текст переводится в битовое представление, после чего побитово встраивается в случайный пиксель изображения, изменяя значение синего канала пропорционально яркости пикселя.
Для извлечения необходимо найти те пиксели, в которые встраивалось сообщение, и сделать предсказание его значения. В качестве такого предсказания используется линейная комбинация значений синего канала соседних битов.

Для наилучшего встраивания и извлечения нужно выбрать изображение как можно большего разрешения и качества.

После внедрения, контейнер можно сохранить и провести визуальный анализ.


# Лаба 3
Запуск: python3 lab3.py

Как работает?

Путем сравнения MSB с битами секретного сообщения в LSB записывается 1 в случае равенства, в другом случае 0.

Использовалась статья: Ali M.Z., Riaz O., Hasnain H.M., Sharif W., Ali T., Choi G.S. Elevating Image Steganography: A Fusion of MSB Matching and LSB Substitution for Enhanced Concealment Capabilities // Computers, Materials & Continua. — 2024. — Vol. 79. — No 2. — P. 2923–2943. — DOI: 10.32604/cmc.2024.049139


# Лаба 4
Запуск: python3 lab4.py

Как работает?

Изображение разбивается на блоки по 2x2 пикселя. Пиксель (0, 0) - опорный, остальные изменяются. Используя соседние блоки рассчитываются значения изменяемых пикселей, секретное сообщение встраивается путем разбивки на блоки, преобразования в число с основанием 10 и вычитанием из значения изменяемого пикселя.
Для восстановления нужно провести обратную операцию - восстановить изначальное значение изменяемых пикселей из соседних блоков и вычесть из него значение соответствующего пикселя стегоконтейнера. Полученное число переводится в биты, конкатенируется с другими блоками для получения сообщения.

Использовалась статья: Hu J., Li T. Reversible steganography using extended image interpolation technique // Computers and Electrical Engineering. 2015. Vol. 46. pp. 447-455.


# Лаба 5
Запуск: python3 lab5.py

Как работает?

Приложение реализует стегоанализ изображений. Можно выбрать множество файлов, провести визуальную атаку на выбранные биты или анализ методом Хи-квадрата, RS-анализом или методом AUMP. Ранее реализованные приложения в лабораторных работах 3 и 4 были дополнены возможностью встраивания секретного сообщения в множество изображений одновременно.
