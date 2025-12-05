# test_performance_report.py

import pytest
import os
import sys
from unittest.mock import patch, mock_open, MagicMock
import tempfile
from io import StringIO
import csv

# Импортируем модуль для тестирования
from performance import (
    BaseReport,
    PerformanceReport,
    TeamReport,
    SkillsReport,
    ReportProcessor,
    main
)

# Тестовые данные
SAMPLE_CSV = """name,position,completed_tasks,performance,skills,team,experience_years
Alex Ivanov,Backend Developer,45,4.8,"Python, Django, PostgreSQL, Docker",API Team,5
Maria Petrova,Frontend Developer,38,4.7,"React, TypeScript, Redux, CSS",Web Team,4
John Smith,Data Scientist,29,4.6,"Python, ML, SQL, Pandas",AI Team,3
Anna Lee,DevOps Engineer,52,4.9,"AWS, Kubernetes, Terraform, Ansible",Infrastructure Team,6
Mike Brown,QA Engineer,41,4.5,"Selenium, Jest, Cypress, Postman",Testing Team,4"""

SAMPLE_CSV_TWO_POSITIONS = """name,position,completed_tasks,performance,skills,team,experience_years
Alex Ivanov,Backend Developer,45,4.8,"Python, Django",API Team,5
Bob Smith,Backend Developer,50,4.9,"Python, FastAPI",API Team,6
Maria Petrova,Frontend Developer,38,4.7,"React",Web Team,4"""

SAMPLE_CSV_EMPTY = """name,position,completed_tasks,performance,skills,team,experience_years"""

SAMPLE_CSV_SINGLE = """name,position,completed_tasks,performance,skills,team,experience_years
Alex Ivanov,Backend Developer,45,4.8,"Python",API Team,5"""


class TestBaseReport:
    """Тесты абстрактного базового класса"""

    def test_base_report_is_abstract(self):
        """Проверка, что BaseReport является абстрактным классом"""
        # Нельзя создать экземпляр абстрактного класса
        with pytest.raises(TypeError):
            BaseReport()

    def test_base_report_methods_exist(self):
        """Проверка наличия абстрактных методов"""
        assert hasattr(BaseReport, 'process_row')
        assert hasattr(BaseReport, 'generate')
        assert hasattr(BaseReport, 'get_headers')
        assert hasattr(BaseReport, 'get_name')


class TestPerformanceReport:
    """Тесты отчета по производительности"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.report = PerformanceReport()

    def test_initial_state(self):
        """Проверка начального состояния"""
        # Внутренний словарь должен быть пустым
        assert len(self.report.data) == 0

    def test_process_row_single(self):
        """Обработка одной строки данных"""
        row = {
            'position': 'Developer',
            'performance': '4.5'
        }

        self.report.process_row(row)

        assert 'Developer' in self.report.data
        assert self.report.data['Developer']['total'] == 4.5

    def test_process_row_multiple_same_position(self):
        """Обработка нескольких строк с одинаковой должностью"""
        rows = [
            {'position': 'Developer', 'performance': '4.5'},
            {'position': 'Developer', 'performance': '4.8'},
            {'position': 'Developer', 'performance': '4.6'}
        ]

        for row in rows:
            self.report.process_row(row)

        assert 'Developer' in self.report.data
        assert self.report.data['Developer']['total'] == 4.5 + 4.8 + 4.6

    def test_process_row_different_positions(self):
        """Обработка строк с разными должностями"""
        rows = [
            {'position': 'Developer', 'performance': '4.5'},
            {'position': 'Manager', 'performance': '4.2'},
            {'position': 'QA', 'performance': '4.7'}
        ]

        for row in rows:
            self.report.process_row(row)

        assert len(self.report.data) == 3
        assert 'Developer' in self.report.data
        assert 'Manager' in self.report.data
        assert 'QA' in self.report.data

    def test_process_row_float_conversion(self):
        """Проверка преобразования строки в float"""
        row = {'position': 'Developer', 'performance': '4.75'}

        self.report.process_row(row)

        assert self.report.data['Developer']['total'] == 4.75

    def test_generate_empty(self):
        """Генерация отчета без данных"""
        result = self.report.generate()

        assert result == []

    def test_generate_single_position(self):
        """Генерация отчета с одной должностью"""
        self.report.process_row({'position': 'Developer', 'performance': '4.5'})
        self.report.process_row({'position': 'Developer', 'performance': '4.7'})

        result = self.report.generate()

        assert len(result) == 1
        assert result[0][0] == 1  # №
        assert result[0][1] == 'Developer'  # Position
        assert result[0][2] == '4.60'  # Avg Performance (4.6 = (4.5+4.7)/2)

    def test_generate_sorted_by_performance(self):
        """Проверка сортировки по производительности (от большего к меньшему)"""
        # Developer: 4.5 avg
        self.report.process_row({'position': 'Developer', 'performance': '4.0'})
        self.report.process_row({'position': 'Developer', 'performance': '5.0'})

        # Manager: 4.8 avg
        self.report.process_row({'position': 'Manager', 'performance': '4.8'})

        # QA: 4.6 avg
        self.report.process_row({'position': 'QA', 'performance': '4.6'})

        result = self.report.generate()

        # Проверяем порядок: Manager (4.8) -> QA (4.6) -> Developer (4.5)
        assert len(result) == 3
        assert result[0][1] == 'Manager'  # Первое место
        assert result[0][2] == '4.80'
        assert result[1][1] == 'QA'  # Второе место
        assert result[1][2] == '4.60'
        assert result[2][1] == 'Developer'  # Третье место
        assert result[2][2] == '4.50'

    def test_generate_equal_performance(self):
        """Проверка одинаковой производительности"""
        self.report.process_row({'position': 'Developer', 'performance': '4.5'})
        self.report.process_row({'position': 'Manager', 'performance': '4.5'})

        result = self.report.generate()

        # При одинаковой производительности сохраняется порядок вставки
        assert len(result) == 2
        assert result[0][1] == 'Developer'  # Первым был добавлен Developer
        assert result[1][1] == 'Manager'  # Затем Manager

    def test_get_headers(self):
        """Проверка заголовков отчета"""
        headers = self.report.get_headers()

        assert headers == [" ", "Position", "Performance"]
        assert len(headers) == 3

    def test_get_name(self):
        """Проверка названия отчета"""
        name = self.report.get_name()

        assert name == "Performance Report"


class TestTeamReport:
    """Тесты заглушки для отчета по командам"""

    def setup_method(self):
        self.report = TeamReport()

    def test_process_row_does_nothing(self):
        """Метод process_row ничего не делает (заглушка)"""
        # Не должно вызывать ошибок
        self.report.process_row({'position': 'Developer', 'performance': '4.5'})

    def test_generate_returns_empty_list(self):
        """Метод generate возвращает пустой список"""
        result = self.report.generate()

        assert result == []

    def test_get_headers_returns_empty_list(self):
        """Метод get_headers возвращает пустой список"""
        headers = self.report.get_headers()

        assert headers == []

    def test_get_name(self):
        """Проверка названия отчета"""
        name = self.report.get_name()

        assert name == "Team Report"


class TestSkillsReport:
    """Тесты заглушки для отчета по навыкам"""

    def setup_method(self):
        self.report = SkillsReport()

    def test_process_row_does_nothing(self):
        """Метод process_row ничего не делает (заглушка)"""
        # Не должно вызывать ошибок
        self.report.process_row({'position': 'Developer', 'performance': '4.5'})

    def test_generate_returns_empty_list(self):
        """Метод generate возвращает пустой список"""
        result = self.report.generate()

        assert result == []

    def test_get_headers_returns_empty_list(self):
        """Метод get_headers возвращает пустой список"""
        headers = self.report.get_headers()

        assert headers == []

    def test_get_name(self):
        """Проверка названия отчета"""
        name = self.report.get_name()

        assert name == "Skills Report"


class TestReportProcessor:
    """Тесты обработчика отчетов"""

    def setup_method(self):
        self.processor = ReportProcessor()

    def test_initial_state(self):
        """Проверка начального состояния процессора"""
        # Должен быть активен отчет по производительности
        assert isinstance(self.processor.active_report, PerformanceReport)
        assert 'performance' in self.processor.reports
        assert 'team' in self.processor.reports
        assert 'skills' in self.processor.reports

    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_CSV)
    def test_process_file_success(self, mock_file):
        """Успешная обработка файла"""
        result = self.processor.process_file('test.csv')

        assert result is True
        mock_file.assert_called_once_with('test.csv', 'r', encoding='utf-8')

    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_process_file_not_found(self, mock_file):
        """Обработка несуществующего файла"""
        result = self.processor.process_file('nonexistent.csv')

        assert result is False

    @patch('builtins.open', side_effect=Exception("Some error"))
    def test_process_file_general_error(self, mock_file):
        """Обработка файла с общей ошибкой"""
        result = self.processor.process_file('error.csv')

        assert result is False

    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_CSV)
    def test_process_file_collects_data(self, mock_file):
        """Проверка сбора данных из файла"""
        self.processor.process_file('test.csv')

        # После обработки файла данные должны быть в отчете
        data = self.processor.generate()

        assert len(data) == 5  # 5 позиций в тестовых данных
        assert any(row[1] == 'Backend Developer' for row in data)
        assert any(row[1] == 'Frontend Developer' for row in data)

    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_CSV_TWO_POSITIONS)
    def test_process_file_aggregates_data(self, mock_file):
        """Проверка агрегации данных по должностям"""
        self.processor.process_file('test.csv')

        data = self.processor.generate()

        # Должно быть 2 записи (Backend Developer и Frontend Developer)
        assert len(data) == 2

        # Находим Backend Developer
        backend_row = next(row for row in data if row[1] == 'Backend Developer')
        assert backend_row[2] == '4.85'  # Avg = (4.8 + 4.9) / 2 = 4.85

    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_CSV_EMPTY)
    def test_process_file_empty(self, mock_file):
        """Обработка пустого файла (только заголовки)"""
        result = self.processor.process_file('empty.csv')

        assert result is True
        data = self.processor.generate()
        assert data == []

    def test_generate_without_data(self):
        """Генерация отчета без данных"""
        data = self.processor.generate()

        assert data == []

    def test_generate_with_data(self):
        """Генерация отчета с данными"""
        # Добавляем данные напрямую
        self.processor.active_report.process_row({'position': 'Developer', 'performance': '4.5'})
        self.processor.active_report.process_row({'position': 'Manager', 'performance': '4.8'})

        data = self.processor.generate()

        assert len(data) == 2
        assert data[0][1] == 'Manager'  # Сортировка: Manager (4.8) -> Developer (4.5)
        assert data[1][1] == 'Developer'

    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_CSV_SINGLE)
    def test_print_report_with_data(self, mock_file, capsys):
        """Вывод отчета с данными"""
        self.processor.process_file('test.csv')
        self.processor.print_report()

        captured = capsys.readouterr()
        output = captured.out

        assert "Backend Developer" in output
        assert "4.8" in output

    def test_print_report_empty(self, capsys):
        """Вывод пустого отчета"""
        self.processor.print_report()

        captured = capsys.readouterr()
        output = captured.out

        assert "Нет данных для отображения" in output

    def test_save_to_file_success(self, tmp_path):
        """Успешное сохранение отчета в файл"""
        # Добавляем тестовые данные
        self.processor.active_report.process_row({'position': 'Developer', 'performance': '4.5'})

        test_file = tmp_path / "test_report.txt"
        result = self.processor.save_to_file(str(test_file))

        assert result is True
        assert test_file.exists()

        content = test_file.read_text(encoding='utf-8')
        assert "Developer" in content
        assert "4.5" in content

    def test_save_to_file_empty(self, tmp_path):
        """Сохранение пустого отчета"""
        test_file = tmp_path / "empty_report.txt"
        result = self.processor.save_to_file(str(test_file))

        assert result is True
        assert test_file.exists()

        content = test_file.read_text(encoding='utf-8')
        assert "Нет данных для отчета" in content

    def test_save_to_file_error(self):
        """Ошибка при сохранении отчета"""
        # Пытаемся сохранить в защищенную директорию
        result = self.processor.save_to_file('/root/test.txt')

        assert result is False


class TestIntegration:
    """Интеграционные тесты"""

    def test_full_workflow(self, tmp_path, capsys):
        """Полный рабочий процесс: чтение, обработка, вывод, сохранение"""
        # Создаем тестовый CSV файл
        csv_file = tmp_path / "data.csv"
        csv_file.write_text(SAMPLE_CSV_TWO_POSITIONS)

        # Обрабатываем файл
        processor = ReportProcessor()
        processor.process_file(str(csv_file))

        # Проверяем данные
        data = processor.generate()
        assert len(data) == 2

        # Проверяем сортировку
        assert data[0][1] == 'Backend Developer'  # 4.85 avg
        assert data[1][1] == 'Frontend Developer'  # 4.70 avg

        # Выводим отчет
        processor.print_report()
        captured = capsys.readouterr()
        output = captured.out

        assert "Backend Developer" in output
        assert "4.85" in output

        # Сохраняем отчет
        report_file = tmp_path / "report.txt"
        processor.save_to_file(str(report_file))

        assert report_file.exists()
        content = report_file.read_text(encoding='utf-8')
        assert "Backend Developer" in content
        assert "4.85" in content

    def test_multiple_files_processing(self, tmp_path):
        """Обработка нескольких файлов"""
        # Создаем первый файл
        file1 = tmp_path / "data1.csv"
        file1.write_text("""name,position,completed_tasks,performance,skills,team,experience_years
Alex,Developer,10,4.5,Python,Team A,2""")

        # Создаем второй файл
        file2 = tmp_path / "data2.csv"
        file2.write_text("""name,position,completed_tasks,performance,skills,team,experience_years
Bob,Developer,15,4.8,Python,Team A,3""")

        # Обрабатываем оба файла
        processor = ReportProcessor()
        processor.process_file(str(file1))
        processor.process_file(str(file2))

        data = processor.generate()

        # Должна быть одна запись с агрегированными данными
        assert len(data) == 1
        assert data[0][1] == 'Developer'
        assert data[0][2] == '4.65'  # (4.5 + 4.8) / 2 = 4.65


class TestMainFunction:
    """Тесты основной функции"""

    @patch('sys.argv', ['performance.py', '--files', 'test.csv', '--report', 'output.txt'])
    @patch('performance.ReportProcessor')
    def test_main_with_args(self, MockProcessor, capsys):
        """Запуск main с аргументами"""
        # Настраиваем мок
        mock_instance = MagicMock()
        mock_instance.process_file.return_value = True
        mock_instance.generate.return_value = [['1', 'Developer', '4.50']]
        MockProcessor.return_value = mock_instance

        # Запускаем main
        main()

        # Проверяем вызовы
        MockProcessor.assert_called_once()
        mock_instance.process_file.assert_called_once_with('test.csv')
        mock_instance.print_report.assert_called_once()
        mock_instance.save_to_file.assert_called_once_with('output.txt')

    @patch('sys.argv', ['performance.py', '--files', 'file1.csv', 'file2.csv'])
    @patch('performance.ReportProcessor')
    def test_main_multiple_files(self, MockProcessor):
        """Запуск main с несколькими файлами"""
        mock_instance = MagicMock()
        mock_instance.process_file.return_value = True
        MockProcessor.return_value = mock_instance

        main()

        # Должны быть вызваны для каждого файла
        assert mock_instance.process_file.call_count == 2
        mock_instance.process_file.assert_any_call('file1.csv')
        mock_instance.process_file.assert_any_call('file2.csv')

    @patch('sys.argv', ['performance.py', '--files', 'test.csv'])
    @patch('performance.ReportProcessor')
    def test_main_default_report_name(self, MockProcessor):
        """Проверка имени отчета по умолчанию"""
        mock_instance = MagicMock()
        mock_instance.process_file.return_value = True
        MockProcessor.return_value = mock_instance

        main()

        # По умолчанию должно быть 'report.txt'
        mock_instance.save_to_file.assert_called_once_with('report')

    @patch('sys.argv', ['performance.py'])
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_missing_required_args(self, mock_parse_args):
        """Проверка обязательных аргументов"""
        # Симулируем ошибку argparse при отсутствии обязательных аргументов
        mock_parse_args.side_effect = SystemExit()

        with pytest.raises(SystemExit):
            main()


class TestEdgeCases:
    """Тесты граничных случаев"""

    def test_performance_edge_values(self):
        """Тест граничных значений производительности"""
        report = PerformanceReport()

        # Нулевая производительность
        report.process_row({'position': 'Developer', 'performance': '0.0'})
        data = report.generate()
        assert data[0][2] == '0.00'

        # Отрицательная производительность
        report2 = PerformanceReport()
        report2.process_row({'position': 'Developer', 'performance': '-1.5'})
        report2.process_row({'position': 'Developer', 'performance': '2.5'})
        data2 = report2.generate()
        assert data2[0][2] == '0.50'  # (-1.5 + 2.5) / 2 = 0.50

        # Большие числа
        report3 = PerformanceReport()
        report3.process_row({'position': 'Developer', 'performance': '1000000.5'})
        report3.process_row({'position': 'Developer', 'performance': '2000000.5'})
        data3 = report3.generate()
        assert data3[0][2] == '1500000.50'  # (1000000.5 + 2000000.5) / 2

    def test_position_names_variations(self):
        """Тест различных названий должностей"""
        report = PerformanceReport()

        test_cases = [
            ('Senior Developer', '4.8'),
            ('Junior Developer', '4.2'),
            ('DevOps Engineer', '4.9'),
            ('Data Scientist', '4.7'),
            ('QA Engineer', '4.5'),
            ('', '4.0'),  # Пустая должность
            ('  Developer  ', '4.6'),  # С пробелами
        ]

        for position, performance in test_cases:
            report.process_row({'position': position, 'performance': performance})

        data = report.generate()
        # Все уникальные должности должны быть в отчете
        positions = [row[1] for row in data]
        assert 'Senior Developer' in positions
        assert 'Junior Developer' in positions
        assert '' in positions  # Пустая должность тоже сохраняется
        assert '  Developer  ' in positions  # Сохраняются пробелы

    def test_csv_field_order(self):
        """Тест порядка полей в CSV"""
        # CSV с разным порядком полей
        csv_data = """performance,name,position,skills,completed_tasks,team,experience_years
4.8,Alex,Backend Developer,Python,45,API Team,5"""

        with patch('builtins.open', mock_open(read_data=csv_data)):
            processor = ReportProcessor()
            result = processor.process_file('test.csv')

            # Должен корректно обработать, так как DictReader использует заголовки
            assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])