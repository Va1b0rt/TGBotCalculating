import subprocess
import time

from docx import Document
from docx.shared import Pt, RGBColor

from logger import Logger

cls_logger = Logger()
logger = cls_logger.get_logger


class Blank_PDF:
    main_font = 'Times New Roman'

    def test_processing(self):
        if not self.document:
            raise DocumentIsEmpty

        for paragraph in self.document.paragraphs:
            for key, value in self.replacement_dict.items():
                runs = paragraph.runs  # Получаем список объектов Run в параграфе
                for run in runs:
                    if key in run.text:
                        # Назначаем стили шрифта из value
                        run.font.name = self.main_font
                        run.font.size = Pt(value['font_size'])
                        run.font.color.rgb = RGBColor(*value['text_color'])
                        run.font.bold = value['bold']
                        run.text = run.text.replace(key, value['text'])

    def load_document(self, file_path: str):
        self.document = Document(file_path)

    def save(self):
        self.document.save(f'{self._path}.docx')

    def save_as_pdf(self):
        if not self.document:
            raise DocumentIsEmpty

        self.save()

        subprocess.run(["lowriter", f"--convert-to pdf {self._path}.docx"], stdout=subprocess.DEVNULL)

        time.sleep(1)


class DocumentIsEmpty(Exception):
    """Document not changed"""
