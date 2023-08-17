import io

from docx import Document

from logger import Logger
from tables.Models import Employer

cls_logger = Logger()
logger = cls_logger.get_logger


class StaffingOrder:
    def __init__(self, employer: Employer = None, document: io.BytesIO = None):
        #self.Employer: Employer = employer
        self.document: Document = None

    def test_processing(self):
        if not self.document:
            raise DocumentIsEmpty

        for paragraph in self.document.paragraphs:
            if 'FOPNAME' in paragraph.text:
                paragraph.text = paragraph.text.replace('FOPNAME', 'ФОП НАГРУЗИЛОВА АННА АКАКИЕВНА')
            if 'ADDRESS' in paragraph.text:
                paragraph.text = paragraph.text.replace('ADDRESS', 'УКРАЇНА, 02160, МІСТО КИЇВ, ДНІПРОВСЬКИЙ Р-Н, ВУЛ. РЕГЕНЕРАТОРНА, БУД. 4, КВ. 165')
            if 'CODE' in paragraph.text:
                paragraph.text = paragraph.text.replace('CODE', '1010101010010')
            if 'TELEFON' in paragraph.text:
                paragraph.text = paragraph.text.replace('TELEFON', '+3809965344')
            if 'DAY' in paragraph.text:
                paragraph.text = paragraph.text.replace('DAY', '01')
            if 'MONTH' in paragraph.text:
                paragraph.text = paragraph.text.replace('MONTH', 'Серпня')
            if 'YEAR' in paragraph.text:
                paragraph.text = paragraph.text.replace('YEAR', '2023')
            if 'SALARY' in paragraph.text:
                paragraph.text = paragraph.text.replace('SALARY', '25 000.00')
            if 'FOPNLASTNAME' in paragraph.text:
                paragraph.text = paragraph.text.replace('FOPNLASTNAME', 'НАГРУЗИЛОВА А.')

    def load_document(self, file_path: str):
        self.document = Document(file_path)

    def save(self):
        self.document.save(r'C:\Users\valbo\Downloads\Telegram Desktop\Для книги\NEW_FORMS\прием на работу\test.docx')



class DocumentIsEmpty(Exception):
    """Document not changed"""


if __name__ == "__main__":
    staff = StaffingOrder()
    staff.load_document(r'C:\Users\valbo\Downloads\Telegram Desktop\Для книги\NEW_FORMS\прием на работу\№1 штатн розпис (1).docx')
    staff.test_processing()
    staff.save()

