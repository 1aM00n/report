# Performance Report Generator

Утилита для анализа производительности сотрудников по должностям.

## Функциональность

- Анализирует CSV файлы с данными о производительности
- Группирует данные по должностям (position)
- Вычисляет среднюю производительность для каждой должности
- Сортирует результаты от наибольшей к наименьшей производительности
- Выводит результаты в консоль в виде таблицы
- Сохраняет отчет в текстовый файл

## Установка

```bash
pip install -r requirements.txt
```


## Пример запуска

```bash
python performance.py --files "./test_files/employees1.csv" "./test_files/employees2.csv" --report performance
```
<img width="352" height="243" alt="Пример работы" src="https://github.com/user-attachments/assets/198679de-a287-435c-8580-fa40f490f3d2" />
