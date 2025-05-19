import json
import os
from dotenv import load_dotenv
import MMpy # встроенная библиотека программы Micromine(в свободном доступе отсутствует)

#=== Данную библиотеку MMpy возможно, только загружать в интерпретаторе Micromine ===

# проектный путь Micromine
PATH_PROJECT = MMpy.Project.path()

# подгружаем пути с .env
load_dotenv(dotenv_path=".env")

# файл формата .STR
PATH_STRINGS = os.getenv("PATH_STRINGS")

# файл формата .DAT
PATH_SAMPLE =  os.getenv("PATH_SAMPLE")

# фильтрование по столбцу
FILTER_BY_EB = os.getenv("FILTER_BY_EB")

output_path = os.getenv("OUTPUT_PATH")


# === 1. Чтение скважин из .DAT ===

# создание экземпляра файла, для работы с ним
file_sample = MMpy.File()

# открываем файл
file_sample.open(PATH_PROJECT + PATH_SAMPLE)

# количество записей в данном файле
records_sample = file_sample.records_count

# константы столбцов, берем id каждого столбца у вас могут быть другие
ID_EB = file_sample.get_field_id("ЭБ")
ID_GRADE = file_sample.get_field_id("Au, г/т")
ID_X = file_sample.get_field_id("X")
ID_Y = file_sample.get_field_id("Y")

# создан пустой список для внесение данных с файла => skv_data
skv_data = []

# после получение все записей мы будем перебирать каждую запись
for record in range(records_sample):
    # фильтруем записи по названию акта готовности(950/6.5-10)
    if file_sample.get_str_field_value(ID_EB, record + 1) == FILTER_BY_EB:
        x = file_sample.get_num_field_value(ID_X, record + 1) # получаем координату X
        y = file_sample.get_num_field_value(ID_Y, record + 1) # получаем координату Y
        val = file_sample.get_num_field_value(ID_GRADE, record + 1) # получаем содержание скважины
        skv_data.append({"X": x, "Y": y, "Value": val}) # создаем словарь и добавляем в список => skv_data

# === 2. Чтение контуров из .STR ===

# новый экземпляр файла
file_str = MMpy.File()

# открываем файл формата .STR
file_str.open(PATH_PROJECT + PATH_STRINGS)

# количество записей
records_str = file_str.records_count

# id столбцов
ID_EAST = file_str.get_field_id("EAST")
ID_NORTH = file_str.get_field_id("NORTH")
ID_JOIN = file_str.get_field_id("JOIN")

# === 3. Группировка точек по JOIN ===
contour_dict = {} # создаем словарь для координат нашего стринга/strings
for i in range(records_str):
    join = file_str.get_num_field_value(ID_JOIN, i + 1)
    x = float(file_str.get_num_field_value(ID_EAST, i + 1))
    y = float(file_str.get_num_field_value(ID_NORTH, i + 1))
    if join not in contour_dict:
        contour_dict[join] = []
    contour_dict[join].append([x, y])

# === 4. Формирование валидных замкнутых контуров ===
external_contours = []

for coords in contour_dict.values():
    if len(coords) >= 3:
        if coords[0] != coords[-1]:
            coords.append(coords[0])  # замыкаем
        external_contours.append(coords)

# === 5. Сборка JSON-данных ===
threshold = 0.3 # бортовое содержание

data = {
    "skv_data": skv_data,
    "external_contours": external_contours,
    "threshold": threshold,
}

# === 6. Сохранение в input.json ===

os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w") as f:
    json.dump(data, f, indent=2)


print("input.json сохранён в:", output_path)
print("Скважин:", len(skv_data), "| Контуров:", len(external_contours))
