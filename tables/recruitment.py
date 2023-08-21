import io

from docx import Document
from docx.shared import RGBColor

from logger import Logger
from tables.Models import Employer
from tables.pdf_blank import Blank_PDF

cls_logger = Logger()
logger = cls_logger.get_logger


class Recruitment(Blank_PDF):
    def __init__(self, employer: Employer = None, document: io.BytesIO = None):
        # self.Employer: Employer = employer
        self.document: Document = None
        self._path = r'.\tables\tmp\recruitment'

        self.replacement_dict = {
            'FOPNAME': {'text': 'ФОП НАГРУЗИЛОВА АННА АКАКИЕВНА'.upper(),
                        'font': 'Times New Roman',
                        'font_size': 14,
                        'text_color': RGBColor(0, 0, 0),
                        'bold': True},
            'ADDRESS': {'text': 'УКРАЇНА, 02160, МІСТО КИЇВ, ДНІПРОВСЬКИЙ Р-Н, ВУЛ. РЕГЕНЕРАТОРНА, БУД. 4, КВ. 165',
                        'font': 'Times New Roman',
                        'font_size': 11,
                        'text_color': RGBColor(70, 70, 70),
                        'bold': False},
            'CODE': {'text': '1010101010010',
                     'font': 'Times New Roman',
                     'font_size': 11,
                     'text_color': RGBColor(70, 70, 70),
                     'bold': False},
            'TELEPHONE': {'text': '+3809965344',
                          'font': 'Times New Roman',
                          'font_size': 11,
                          'text_color': RGBColor(70, 70, 70),
                          'bold': False},
            'DAY': {'text': '01',
                    'font': 'Times New Roman',
                    'font_size': 11,
                    'text_color': RGBColor(0, 0, 0),
                    'bold': False},
            'MONTH': {'text': 'Серпня',
                      'font': 'Times New Roman',
                      'font_size': 12,
                      'text_color': RGBColor(0, 0, 0),
                      'bold': False},
            'YEAR': {'text': '2023',
                     'font': 'Times New Roman',
                     'font_size': 12,
                     'text_color': RGBColor(0, 0, 0),
                     'bold': False},
            'EMPLNAME': {'text': 'EmplName',
                         'font': 'Times New Roman',
                         'font_size': 12,
                         'text_color': RGBColor(0, 0, 0),
                         'bold': False},
            'TITTLE': {'text': 'Tittle',
                       'font': 'Times New Roman',
                       'font_size': 12,
                       'text_color': RGBColor(0, 0, 0),
                       'bold': False},
            'EMPLOYMENT_DATE': {'text': 'EMPL Date',
                                'font': 'Times New Roman',
                                'font_size': 12,
                                'text_color': RGBColor(0, 0, 0),
                                'bold': False},
            'FOPNLASTNAME': {'text': 'Нагрузлова А.'.upper(),
                             'font': 'Roboto',
                             'font_size': 9,
                             'text_color': RGBColor(0, 0, 0),
                             'bold': True},
            'EMPLSHORTNAME': {'text': 'Сотрудникова А.',
                              'font': 'Roboto',
                              'font_size': 12,
                              'text_color': RGBColor(0, 0, 0),
                              'bold': True}

        }


if __name__ == "__main__":
    staff = Recruitment()
    staff.load_document(
        r'./tables/templates/recruitment_blank.docx')
    staff.test_processing()
    staff.save()
    staff.save_as_pdf()
