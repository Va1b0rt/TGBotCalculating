import io

from openpyxl.styles import Alignment
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import Workbook
from tables.Models import Employer, Worker


class Table:
    def __init__(self, employer: Employer):
        self.Employer: Employer = employer

        self.workbook: Workbook = Workbook()
        self.sheet: Worksheet = Worksheet('')

    @property
    def file(self) -> io.BytesIO:
        output = io.BytesIO()
        self.workbook.save(output)
        output.seek(0)
        return output

    def __assemble_workbook(self):
        """
        В этом методе заполняем таблицу.
        :return: None
        """
        pass

    def _merge(self, cells, cell, text, font=None):
        self.sheet.merge_cells(cells)
        top_left_cell = self.sheet[cell]
        top_left_cell.value = text
        top_left_cell.alignment = Alignment(horizontal='center', vertical='center')
        if font:
            top_left_cell.font = font

    def get_bytes(self) -> io.BytesIO:
        output = io.BytesIO()
        self.workbook.save(output)
        output.seek(0)
        return output

    def save(self, name):
        self.workbook.save(f"{name}.xlsx")
