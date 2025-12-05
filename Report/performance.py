import argparse
import csv
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from tabulate import tabulate
from collections import defaultdict


class BaseReport(ABC):
    """Базовый класс для отчетов"""

    @abstractmethod
    def process_row(self, row: Dict[str, str]) -> None:
        """Обработка одной строки данных"""
        pass

    @abstractmethod
    def generate(self) -> List[List[Any]]:
        """Генерация данных для отчета"""
        pass

    @abstractmethod
    def get_headers(self) -> List[str]:
        """Получение заголовков отчета"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Получение названия отчета"""
        pass


class PerformanceReport(BaseReport):

    def __init__(self):
        self.data = defaultdict(lambda: {'total': 0.0, 'count': 0})

    def process_row(self, row: Dict[str, str]) -> None:
        position = row['position']
        performance = float(row['performance'])

        self.data[position]['total'] += performance
        self.data[position]['count'] += 1

    def generate(self) -> List[List[Any]]:
        if not self.data:
            return []

        # Сортируем по средней производительности (от большего к меньшему)
        sorted_items = sorted(
            self.data.items(),
            key=lambda x: x[1]['total'] / x[1]['count'],
            reverse=True
        )

        result = []
        for i, (position, stats) in enumerate(sorted_items, 1):
            avg = stats['total'] / stats['count']
            result.append([i, position, f"{avg:.2f}"])

        return result

    def get_headers(self) -> List[str]:
        return [" ", "Position", "Performance"]

    def get_name(self) -> str:
        return "Performance Report"


class TeamReport(BaseReport):

    def __init__(self):
        pass

    def process_row(self, row: Dict[str, str]) -> None:
        pass

    def generate(self) -> List[List[Any]]:
        return []

    def get_headers(self) -> List[str]:
        return []

    def get_name(self) -> str:
        return "Team Report"


class SkillsReport(BaseReport):

    def __init__(self):
        pass

    def process_row(self, row: Dict[str, str]) -> None:
        pass

    def generate(self) -> List[List[Any]]:
        return []

    def get_headers(self) -> List[str]:
        return []

    def get_name(self) -> str:
        return "Skills Report"


class ReportProcessor:

    def __init__(self):
        # Основной отчет + заглушки для расширения
        self.reports = {
            'performance': PerformanceReport(),
            'team': TeamReport(),
            'skills': SkillsReport(),
        }
        self.active_report = self.reports['performance']

    def process_file(self, filename: str) -> bool:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    self.active_report.process_row(row)

            return True

        except FileNotFoundError:
            print(f"Ошибка: Файл {filename} не найден")
            return False
        except Exception as e:
            print(f"Ошибка при чтении файла {filename}: {e}")
            return False

    def generate(self) -> List[List[Any]]:
        return self.active_report.generate()

    def print_report(self) -> None:
        data = self.generate()

        if not data:
            print("Нет данных для отображения.")
            return

        table = tabulate(data, headers=self.active_report.get_headers(), tablefmt="simple")
        print(table)

    def save_to_file(self, filename: str) -> bool:
        try:
            data = self.generate()

            with open(filename, 'w', encoding='utf-8') as f:
                if not data:
                    f.write("Нет данных для отчета.\n")
                else:
                    table = tabulate(data, headers=self.active_report.get_headers(), tablefmt="simple")
                    f.write(table + "\n")

            print(f"Отчет сохранен в: {filename}")
            return True

        except Exception as e:
            print(f"Ошибка при сохранении отчета: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Анализ производительности сотрудников')

    parser.add_argument('--files', nargs='+', required=True, help='CSV файлы для анализа')
    parser.add_argument('--report', default='report', help='Имя файла для отчета')

    args = parser.parse_args()

    processor = ReportProcessor()

    # Обработка файлов
    for file_path in args.files:
        processor.process_file(file_path)

    # Вывод и сохранение отчета
    processor.print_report()
    processor.save_to_file(args.report)

if __name__ == "__main__":
    main()