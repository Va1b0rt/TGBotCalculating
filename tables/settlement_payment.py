import datetime
import io

from openpyxl import Workbook
from openpyxl.styles.borders import BORDER_MEDIUM
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Alignment, Font
from openpyxl.styles import Border, Side

from logger import Logger
from tables.Models import Employer, Worker
from XLAssembler import months_names
from .working_hour_sheet import AppearanceOTWHSheet

cls_logger = Logger()
logger = cls_logger.get_logger


class SettlementPayment:
    def __init__(self, employer: Employer):
        self.Employer: Employer = employer
        self.creation_date: datetime = datetime.datetime.now()
        self.start_billing_period: datetime = datetime.date(self.creation_date.year, self.creation_date.month - 1, 1)
        self.end_billing_period: datetime = AppearanceOTWHSheet._get_last_day_of_month(self.creation_date.year,
                                                                                       self.creation_date.month - 1)

        self.workbook: Workbook = Workbook()
        self.sheet: Worksheet = Worksheet('')

        self.__assemble_workbook()

    def _merge(self, cells, cell, text, font=None):

        self.sheet.merge_cells(cells)
        top_left_cell = self.sheet[cell]
        top_left_cell.value = text
        top_left_cell.alignment = Alignment(horizontal='center', vertical='center')
        if font:
            top_left_cell.font = font

    def _billing_period(self) -> str:
        def get_actual_month(_month: int) -> int:
            if _month == 1:
                return 12
            return _month - 1

        month = months_names[get_actual_month(self.creation_date.month)-1]
        year = self.creation_date.year if month != 1 else self.creation_date.year - 1

        return f'{month} {year}'

    def _fill_table(self, num: int, worker: Worker, start_row: int):
        _start_row = start_row

        border = Border(
            left=Side(border_style='thin', color='000000'),
            right=Side(border_style='thin', color='000000'),
            top=Side(border_style='thin', color='000000'),
            bottom=Side(border_style='thin', color='000000')
        )

        self.sheet[f'A{_start_row}'] = f'{num+1}'
        self.sheet[f'B{_start_row}'] = f'{num+1}'
        self.sheet[f'D{_start_row}'] = f'{worker.job_title}'
        employment_date = datetime.datetime.strptime(worker.employment_date, '%d.%m.%Y')
        self.sheet[f'E{_start_row}'] = f'{sum(AppearanceOTWHSheet._get_days_with_eights(self.start_billing_period.year, self.start_billing_period.month, worker.working_hours, employment_date, not_x=True))}'
        self.sheet[f'F{_start_row}'] = f'{worker.salary}'

        for cells in self.sheet.iter_cols(min_col=1, max_col=self.sheet.max_column,
                                          min_row=_start_row, max_row=_start_row):
            for cell in cells:
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = border

        start_column = 7

        for column in range(start_column, self.sheet.max_column+1):
            self.sheet.cell(row=_start_row, column=column).value = '-'

        self.sheet[f'O{_start_row}'] = f'{worker.salary}'
        q21 = float(worker.salary) * 0.18
        self.sheet[f'Q{_start_row}'] = f"{q21}"
        t21 = float(worker.salary) * 0.015
        self.sheet[f'T{_start_row}'] = f"{t21}"
        u21 = q21 + t21
        self.sheet[f'U{_start_row}'] = f"{u21}"
        x21 = float(worker.salary) - u21
        self.sheet[f'X{_start_row}'] = f"{x21}"
        self.sheet[f'Y{_start_row}'] = f'{x21}'
        self.sheet[f'Z{_start_row}'] = f'{x21}'
        self.sheet[f'AA{_start_row}'] = '-'

        def replace_n(string: str) -> str:
            return string.replace('\n', '').replace('\t', '') #.replace(' ', '')

        if '.' in worker.name:
            self.sheet[
                f'AB{_start_row}'] = f'{replace_n(worker.name)}\n{replace_n(worker.ident_IPN)}'
        else:
            self.sheet[f'AB{_start_row}'] = f'{worker.name.split(" ")[0]}\n{worker.name.split(" ")[1]} {replace_n(worker.name.split(" ")[2])} {replace_n(worker.ident_IPN)}'

        self.sheet.row_dimensions[_start_row].height = 36

    @logger.catch
    def __assemble_workbook(self):
        self.sheet = self.workbook.active

        self.sheet['A1'] = f'ФОП {self.Employer.name}'

        self._merge('A2:D2', 'A2', 'Ідентифікаційний код за ЄДРПОУ')
        self._merge('E2:F2', 'E2', f'{self.Employer.ident_EDRPOU}', font=Font(name='Arial', bold=True, size=9))
        self.sheet['E2'].font = Font(bold=True)

        self.sheet['B3'] = 'Цех, відділ'

        self.sheet['C5'] = 'В касу для оплати в строк з _________________________________ '
        self.sheet['H5'] = 'до  ________________________________'
        self.sheet['L5'] = 'року'

        self.sheet['C6'] = 'В сумі'

        self.sheet['C7'] = f'Керівник   {self.Employer.name}'

        self.sheet['C8'] = f'Головний бухгалтер   {self.Employer.name}'

        self._merge('B10:O10', 'B10', f'Розрахунково-платіжна відомість № 7 за {self._billing_period()} р.')
        top_left_cell = self.sheet['B10']
        top_left_cell.font = Font(bold=True)

        self._merge('F12:O12', 'F12', 'Нараховано за видами виплат')
        self._merge('P12:U12', 'P12', 'Утримано та враховано')
        self._merge('X12:Z12', 'X12', 'Сума, грн.')

        self._merge('L13:N13', 'L13', 'Допомога за')
        self.sheet['Q13'] = 'Податок\n на доходи\n фіз. осіб'

        self.sheet['E14'] = 'Відпра-'
        self._merge('F14:J14', 'F14', 'Доплат та надбавок')
        self._merge('L14:N14', 'L14', 'тимчасовою')
        self.sheet['R14'] = 'Єдиний'
        self.sheet['S14'] = 'Проф-'
        self.sheet['V14'] = 'Заборго-'
        self.sheet['W14'] = 'Виплачено'

        self.sheet['A15'] = '№'
        self.sheet['A15'].alignment = Alignment(horizontal='center', vertical='center')
        self.sheet['B15'] = 'Табельний'
        self.sheet['C15'] = 'Категорія'
        self.sheet['D15'] = 'Професія,'
        self.sheet['E15'] = 'цьовано'
        self._merge('L15:N15', 'L15', 'непрацездатністю')
        self.sheet['P15'] = 'виплачено'
        self.sheet['R15'] = 'соціаль-'
        self.sheet['S15'] = 'спілко-'
        self.sheet['T15'] = 'Інші'
        self.sheet['V15'] = 'ваність'
        self.sheet['W15'] = 'за'
        self.sheet['X15'] = 'Заробіт-'
        self.sheet['Y15'] = 'Належить'
        self.sheet['Z15'] = 'Разом'
        self.sheet['AA15'] = 'Розписка'
        self.sheet['AB15'] = 'Прізвище,'

        self.sheet['A16'] = 'з/п'
        self.sheet['B16'] = 'номер'
        self.sheet['C16'] = 'персоналу'
        self.sheet['D16'] = 'посада,'
        self.sheet['E16'] = 'днів,'
        self.sheet['F16'] = 'За тариф.'
        self.sheet['G16'] = 'Благодійна'
        self.sheet['H16'] = 'Обклад.'
        self.sheet['I16'] = 'Обклад.'
        self.sheet['J16'] = 'Індек-'
        self.sheet['K16'] = 'Премія'
        self.sheet['O16'] = 'Разом,'
        self.sheet['P16'] = 'аванса'
        self.sheet['R16'] = 'ний'
        self.sheet['S16'] = 'вий'
        self.sheet['T16'] = 'утри-'
        self.sheet['U16'] = 'ваність'
        self.sheet['V16'] = 'за/перед'
        self.sheet['W16'] = 'попередні'
        self.sheet['X16'] = 'ної'
        self.sheet['Y16'] = 'до'
        self.sheet['Z16'] = 'до'
        self.sheet['AA16'] = 'в'
        self.sheet['AB16'] = 'ім\'я,'

        self.sheet['E17'] = 'годин'
        self.sheet['F17'] = 'ставками'
        self.sheet['G17'] = 'допомога'
        self.sheet['H17'] = 'податками'
        self.sheet['I17'] = 'податками'
        self.sheet['J17'] = 'сація'
        self.sheet['L17'] = 'місяць'
        self.sheet['M17'] = 'дні'
        self.sheet['N17'] = 'сума,'
        self.sheet['O17'] = 'грн.'
        self.sheet['R17'] = 'внесок'
        self.sheet['S17'] = 'внесок'
        self.sheet['T17'] = 'мання'
        self.sheet['V17'] = 'працівни-'
        self.sheet['W17'] = 'періоди'
        self.sheet['X17'] = 'плати'
        self.sheet['Y17'] = 'виплати'
        self.sheet['Z17'] = 'видачі'
        self.sheet['AA17'] = 'отриманні'
        self.sheet['AB17'] = 'по батькові,'

        self.sheet['F18'] = '(посад.'
        self.sheet['H18'] = 'мат.'
        self.sheet['I18'] = 'мат. доп.'
        self.sheet['N18'] = 'грн.'
        self.sheet['V18'] = 'ком'
        self.sheet['AB18'] = 'ІПН'

        self.sheet['F19'] = 'окладами)'
        self.sheet['H19'] = 'допомога'
        self.sheet['I19'] = '(ВВ)'

        start_column = 1

        for row in self.sheet.iter_rows(min_row=12, max_row=20, min_col=1, max_col=self.sheet.max_column):
            for cell in row:
                cell.alignment = Alignment(horizontal='center', vertical='center')

        for column in range(start_column, self.sheet.max_column):
            cell = self.sheet.cell(row=20, column=column)
            cell.value = column - start_column + 1
            cell.alignment = Alignment(horizontal='center', vertical='center')

        last_row = 21


        for num, worker in enumerate(self.Employer.workers):
            self._fill_table(num, worker, last_row)
            last_row += 1

        last_row += 3

        self.sheet[f'A{last_row}'] = 'Начальник підрозділу'
        self.sheet[f'F{last_row}'] = f'{self.Employer.name}'
        self.sheet[f'J{last_row}'] = 'Головний бухгалтер'
        self.sheet[f'N{last_row}'] = f'{self.Employer.name}'

        last_row += 1

        self._merge(f'D{last_row}:G{last_row}', f'D{last_row}', '(підпис, прізвище)')
        self._merge(f'K{last_row}:N{last_row}', f'K{last_row}', '(підпис, прізвище)')

        font = Font(name='Arial', bold=False, italic=False, size=9)
        for col in self.sheet.columns:
            for cell in col:
                cell.font = font

        self.sheet['A1'].font = Font(name='Arial', underline='single', size=10)
        #self.sheet['E2'].font = Font(name='Arial', bold=True)
        self.sheet['B10'].font = Font(name='Arial', bold=True, size=11)

        self.sheet.column_dimensions['A'].width = 4.17
        self.sheet.column_dimensions['B'].width = 11.67
        self.sheet.column_dimensions['C'].width = 10.67
        self.sheet.column_dimensions['D'].width = 22.33
        self.sheet.column_dimensions['E'].width = 8.5
        self.sheet.column_dimensions['F'].width = 9.5
        self.sheet.column_dimensions['G'].width = 9.33
        self.sheet.column_dimensions['H'].width = 9.83
        self.sheet.column_dimensions['I'].width = 10.33
        self.sheet.column_dimensions['J'].width = 6.83
        self.sheet.column_dimensions['K'].width = 7.33
        self.sheet.column_dimensions['L'].width = 6.33
        self.sheet.column_dimensions['M'].width = 3.83
        self.sheet.column_dimensions['N'].width = 10.33
        self.sheet.column_dimensions['O'].width = 11.83
        self.sheet.column_dimensions['P'].width = 9.83
        self.sheet.column_dimensions['Q'].width = 8.67
        self.sheet.column_dimensions['R'].width = 8.83
        self.sheet.column_dimensions['S'].width = 8.17
        self.sheet.column_dimensions['T'].width = 16.83
        self.sheet.column_dimensions['U'].width = 8.67
        self.sheet.column_dimensions['V'].width = 9.33
        self.sheet.column_dimensions['W'].width = 10.67
        self.sheet.column_dimensions['X'].width = 10.67
        self.sheet.column_dimensions['Y'].width = 10.33
        self.sheet.column_dimensions['Z'].width = 10.33
        self.sheet.column_dimensions['AA'].width = 9.33
        self.sheet.column_dimensions['AB'].width = 20.83

        self.sheet.row_dimensions[1].height = 14.25
        self.sheet.row_dimensions[2].height = 15
        self.sheet.row_dimensions[3].height = 16.5
        self.sheet.row_dimensions[4].height = 12
        self.sheet.row_dimensions[5].height = 15
        self.sheet.row_dimensions[6].height = 15
        self.sheet.row_dimensions[7].height = 15
        self.sheet.row_dimensions[8].height = 15
        self.sheet.row_dimensions[9].height = 12
        self.sheet.row_dimensions[10].height = 15
        self.sheet.row_dimensions[11].height = 12
        self.sheet.row_dimensions[12].height = 12
        self.sheet.row_dimensions[13].height = 48
        self.sheet.row_dimensions[14].height = 12
        self.sheet.row_dimensions[15].height = 12
        self.sheet.row_dimensions[16].height = 12
        self.sheet.row_dimensions[17].height = 12
        self.sheet.row_dimensions[18].height = 12
        self.sheet.row_dimensions[19].height = 12
        self.sheet.row_dimensions[20].height = 12
        self.sheet.row_dimensions[21].height = 36

        border = Border(
            left=Side(border_style='thin', color='000000'),
            right=Side(border_style='thin', color='000000'),
            top=Side(border_style='thin', color='000000'),
            bottom=Side(border_style='thin', color='000000')
        )

        left_right_border = Border(
            left=Side(border_style='thin', color='000000'),
            right=Side(border_style='thin', color='000000')
        )

        left_right_top_border = Border(
            left=Side(border_style='thin', color='000000'),
            right=Side(border_style='thin', color='000000'),
            top=Side(border_style='thin', color='000000')
        )

        bottom_border = Border(
            bottom=Side(border_style='thin', color='000000')
        )

        border_2px = Border(
            left=Side(border_style=BORDER_MEDIUM, color='000000'),
            right=Side(border_style=BORDER_MEDIUM, color='000000'),
            top=Side(border_style=BORDER_MEDIUM, color='000000'),
            bottom=Side(border_style=BORDER_MEDIUM, color='000000')
        )

        self.sheet['E2'].border = border_2px
        self.sheet['F2'].border = border_2px
        self.sheet['C3'].border = bottom_border
        self.sheet['D3'].border = bottom_border
        self.sheet['E3'].border = bottom_border
        self.sheet['F3'].border = bottom_border
        self.sheet['V12'].border = left_right_top_border
        self.sheet['W12'].border = left_right_top_border
        self.sheet['X12'].border = border
        self.sheet['Y12'].border = border
        self.sheet['Z12'].border = border
        self.sheet['AA12'].border = left_right_top_border
        self.sheet['AB12'].border = left_right_top_border
        self.sheet['L16'].border = left_right_top_border
        self.sheet['M16'].border = left_right_top_border
        self.sheet['N16'].border = left_right_top_border
        self.sheet[f'D{last_row-1}'].border = bottom_border
        self.sheet[f'E{last_row-1}'].border = bottom_border
        self.sheet[f'F{last_row-1}'].border = bottom_border
        self.sheet[f'G{last_row - 1}'].border = bottom_border
        self.sheet[f'J{last_row - 1}'].border = bottom_border
        self.sheet[f'K{last_row-1}'].border = bottom_border
        self.sheet[f'L{last_row-1}'].border = bottom_border
        self.sheet[f'M{last_row-1}'].border = bottom_border
        self.sheet[f'N{last_row-1}'].border = bottom_border

        for row in self.sheet.iter_rows(min_row=13, max_row=19, min_col=11, max_col=11):
            for cell in row:
                cell.border = left_right_border

        for row in self.sheet.iter_rows(min_row=13, max_row=15, min_col=12, max_col=14):
            for cell in row:
                cell.border = left_right_border

        for row in self.sheet.iter_rows(min_row=13, max_row=19, min_col=15, max_col=16):
            for cell in row:
                cell.border = left_right_border

        for row in self.sheet.iter_rows(min_row=13, max_row=19, min_col=18, max_col=28):
            for cell in row:
                cell.border = left_right_border

        for row in self.sheet.iter_rows(min_row=13, max_row=19, min_col=17, max_col=17):
            for cell in row:
                cell.border = border

        for row in self.sheet.iter_rows(min_row=12, max_row=12, min_col=1, max_col=5):
            for cell in row:
                cell.border = left_right_top_border

        for row in self.sheet.iter_rows(min_row=12, max_row=12, min_col=6, max_col=21):
            for cell in row:
                cell.border = border

        for row in self.sheet.iter_rows(min_row=13, max_row=19, min_col=1, max_col=5):
            for cell in row:
                cell.border = left_right_border

        for row in self.sheet.iter_rows(min_row=16, max_row=16, min_col=6, max_col=10):
            for cell in row:
                cell.border = left_right_top_border

        for row in self.sheet.iter_rows(min_row=17, max_row=19, min_col=6, max_col=10):
            for cell in row:
                cell.border = left_right_border

        for row in self.sheet.iter_rows(min_row=17, max_row=19, min_col=12, max_col=14):
            for cell in row:
                cell.border = left_right_border

        for row in self.sheet.iter_rows(min_row=20, max_row=21, min_col=1, max_col=28):
            for cell in row:
                cell.border = border

    def get_bytes(self) -> io.BytesIO:
        output = io.BytesIO()
        self.workbook.save(output)
        output.seek(0)
        return output

    def save(self):
        self.workbook.save("example.xlsx")


if __name__ == '__main__':
    worker1 = Worker(
        sex="М",
        name="John Doe",
        job_title="Software Engineer",
        salary="5000",
        working_hours="8",
        ident_IPN="1234567890"
    )

    worker2 = Worker(
        sex="Ж",
        name="Jane Smith",
        job_title="Data Scientist",
        salary="6000",
        working_hours="8",
        ident_IPN="0987654321"
    )

    # Создание объекта Employer с несколькими работниками
    employer = Employer(
        name="Acme Corporation",
        ident_EDRPOU="123456789",
        workers=[worker1, worker2]
    )

    sheet = SettlementPayment(employer)
    sheet.save()