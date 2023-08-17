import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import keyfile, sheet_url, worksheet as worksheet_name, workers_sheet, workers_worksheet
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
            if len(self.data[id_row][17]) > 5:
                workers.append(Worker(sex=self.data[id_row][18],
                                      name=self.data[id_row][17],
                                      job_title=self.data[id_row][20],
                                      salary=self.data[id_row][21],
                                      working_hours=self.data[id_row][22],
                                      ident_IPN=self.data[id_row][26],
                                      employment_date=self.data[id_row][27]
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
                                           workers=workers))

    def get_employers(self) -> list[Employer]:
        return self.employers

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
    emp = Employers()
    for employer in emp.get_employers():
        print(employer.model_dump_json())
