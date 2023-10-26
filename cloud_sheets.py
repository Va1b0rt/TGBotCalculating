import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import (keyfile, sheet_url, worksheet as worksheet_name, workers_sheet, workers_worksheet,
                    statement_columns, statement_worksheet)
from tables.Models import Employer, Worker

IGNORE_LIST = ['Рахуємо суми з + (ігнор рядків із найменуванням нижче) "ПРИВАТ"',
               'Рахуємо суми з - (тільки перелік рядків із найменуванням нижче)',
               'Призначення платежу +',
               'Призначення платежу -',
               ]

scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']


class Patterns:

    def __init__(self):
        # TIMESHEET
        self.column_A: list[str] = []  # blacklist TIMESHEET
        self.column_B: list[str] = []  # blacklist negatives
        self.column_C: list[str] = []  # bank fee

        self.whitelist: list[str] = []
        self.whitelist_minus: list[str] = []
        self.blacklist: list[str] = []

        self.__feel_lists()

    def __feel_lists(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
        client = gspread.authorize(credentials)
        sheet = client.open_by_url(sheet_url)
        worksheet = sheet.worksheet(worksheet_name)
        data = worksheet.get_all_values()

        for row in data:
            if row[0]:
                if row[0] not in IGNORE_LIST:
                    self.column_A.append(row[0])
            if row[1]:
                if row[1] not in IGNORE_LIST:
                    self.column_B.append(row[1])
            if row[2]:
                if row[2] not in IGNORE_LIST:
                    self.column_C.append(row[2])


class Employers:
    def __init__(self):
        self.employers: list[Employer] = []

        self.data = []

        self._fill_employers()

    def _get_employers_row_ids(self) -> list[list[int]]:
        result: list[list[int]] = []
        first_row = True

        for num, row in enumerate(self.data):
            if first_row:
                first_row = False
                continue

            if len(row[0]) > 0:
                result.append([num])
            else:
                result[len(result)-1].append(num)

        return result

    def _get_workers(self, row_ids: list[int]) -> list[Worker]:
        workers: list[Worker] = []
        for id_row in row_ids:
            if len(self.data[id_row][16]) > 5:
                workers.append(Worker(sex=self.data[id_row][17],
                                      name=self.data[id_row][16],
                                      job_title=self.data[id_row][19],
                                      salary=self.data[id_row][20],
                                      working_hours=self.data[id_row][21],
                                      ident_IPN=self.data[id_row][25],
                                      employment_date=self.data[id_row][26],
                                      birthday=self.data[id_row][22],
                                      dismissal=self.data[id_row][27]
                                      )
                               )
        return workers

    def _fill_employers(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
        client = gspread.authorize(credentials)
        sheet = client.open_by_url(workers_sheet)
        worksheet = sheet.worksheet(workers_worksheet)
        self.data = worksheet.get_all_values()

        employers_row_id = self._get_employers_row_ids()

        for rows in employers_row_id:
            workers = self._get_workers(rows)
            self.employers.append(Employer(name=self.data[rows[0]][0],
                                           ident_EDRPOU=self.data[rows[0]][4],
                                           residence=self.data[rows[0]][7],
                                           phone=self.data[rows[0]][9],
                                           workers=workers))

    def get_employers(self) -> list[Employer]:
        return self.employers


class Columns:
    def __init__(self):
        self.columns = {"date": [],
                        "sum": [],
                        "purpose": [],
                        "egrpou": [],
                        "name": [],
                        "currency": []}

        self._feel_colum_names()

    def _feel_colum_names(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
        client = gspread.authorize(credentials)
        sheet = client.open_by_url(statement_columns)
        worksheet = sheet.worksheet(statement_worksheet)
        data = worksheet.get_all_values()

        for row in data:
            if row[0]:
                self.columns['date'].append(row[0])
            if row[1]:
                self.columns['sum'].append(row[1])
            if row[2]:
                self.columns['purpose'].append(row[2])
            if row[3]:
                self.columns['egrpou'].append(row[3])
            if row[4]:
                self.columns['name'].append(row[4])
            if row[5]:
                self.columns['currency'].append(row[5])


if __name__ == '__main__':
    #ptrns = Patterns()
#
    #for black in ptrns.blacklist:
    #    print(f'black: {black}')
#
    #for white_min in ptrns.whitelist_minus:
    #    print(f'minus: {white_min}')
#
    #for white in ptrns.whitelist:
    #    print(f'white: {white}')
#
#    emp = Employers()
#    for employer in emp.get_employers():
#        print(employer.model_dump_json())
    col = Columns()
    print(col.columns)
