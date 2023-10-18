class NotExistsPerson(Exception):
    def __str__(self):
        return 'The record is missing from the database'


class NotHaveTemplate(Exception):
    def __str__(self):
        return 'We do not have a suitable template'


class NotHaveTemplatePRRO(Exception):
    def __str__(self):
        return 'We do not have a suitable PRRO template'


class TemplateDoesNotFit(Exception):
    def __str__(self):
        return 'The keys dont fit. Most likely, this template is in our database, but most likely it was changed by the bank.'


class UnknownEncoding(Exception):
    def __str__(self):
        return 'We were unable to determine the encoding in your file. Most likely the file is damaged.'
