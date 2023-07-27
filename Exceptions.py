class NotExistsPerson(Exception):
    def __str__(self):
        return 'The record is missing from the database'
