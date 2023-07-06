import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import keyfile, sheet_url, worksheet as worksheet_name

IGNORE_LIST = ['Рахуємо суми з + (ігнор рядків із найменуванням нижче) "ПРИВАТ"',
               'Рахуємо суми з - (тільки перелік рядків із найменуванням нижче)',
               'Призначення платежу +',
               'Призначення платежу -',
               ]


class Patterns:
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    def __init__(self):
        # TIMESHEET
        self.column_A: list[str] = []  # blacklist TIMESHEET
        self.column_C: list[str] = []  # bank fee

        self.whitelist: list[str] = []
        self.whitelist_minus: list[str] = []
        self.blacklist: list[str] = []

        self.__feel_lists()

    def __feel_lists(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, self.scope)
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
                    self.whitelist_minus.append(row[1])
            if row[2]:
                if row[2] not in IGNORE_LIST:
                    self.column_C.append(row[2])


if __name__ == '__main__':
    ptrns = Patterns()

    for black in ptrns.blacklist:
        print(f'black: {black}')

    for white_min in ptrns.whitelist_minus:
        print(f'minus: {white_min}')

    for white in ptrns.whitelist:
        print(f'white: {white}')
