import datetime

from peewee import (Model, BooleanField, BigIntegerField, DateField, FloatField,
                    TextField, CharField)
from playhouse.signals import pre_save


class Persons(Model):
    Person_ID = BigIntegerField(primary_key=True, verbose_name='ЕГРПОУ')
    Name = CharField(max_length=255, verbose_name='Имя ФОПа')
    Is_FOP = BooleanField(verbose_name='Является ли ФОПом')

    class Meta:
        db_table = 'persons'


class CurrencyRate(Model):
    Date = DateField(primary_key=True)
    EUR = FloatField()
    USD = FloatField()

    class Meta:
        db_table = 'CurrencyRate'


class FormattedDateField(DateField):
    def db_value(self, value):
        return value

    def python_value(self, value):
        if value:
            return datetime.datetime.strptime(f'{value}', "%Y-%m-%d")


class Transaction(Model):
    Transaction_Hash = CharField(primary_key=True, index=True, unique=True, max_length=255)
    Extract_name = CharField(max_length=255, verbose_name='Название выписки')
    Holder_id = BigIntegerField(verbose_name='Holder_ID')
    Date = FormattedDateField()
    Amount = FloatField(verbose_name="Сумма транзакции")
    Purpose = TextField(verbose_name="Назначение платежа")
    EGRPOU = BigIntegerField(verbose_name="ЕГРПОУ код отправителя/получателя")
    Name = CharField(max_length=255, verbose_name="Имя того кто сделал перевод")
    transaction_types = ('extract', 'prro')
    Type = CharField(choices=transaction_types)

    class Meta:
        db_table = 'Transactions'


class FourDF(Model):
    FourDFHash = CharField(primary_key=True, index=True, unique=True, max_length=255)
    ExtractName = CharField(max_length=255, verbose_name='Название выписки')
    Holder_id = BigIntegerField(verbose_name='Holder_ID')
    Date = FormattedDateField()
    Amount = FloatField(verbose_name="Сумма транзакции")
    EntrepreneurID = BigIntegerField(verbose_name='Entrepreneur_ID')
    EntrepreneurName = CharField(max_length=255, verbose_name="Имя того кому сделал перевод")


class User(Model):
    User_ID = BigIntegerField(primary_key=True, unique=True, verbose_name='Telegram ID')
    Username = CharField(max_length=255, verbose_name='Юзернейм в телеграм')
    Name = CharField(max_length=255, verbose_name='Имя в боте')
    isAdmin = BooleanField(verbose_name='Is Admin')
    LastLogged = CharField(max_length=40, verbose_name='Время последнего входа')
    addedByUserID = BigIntegerField(verbose_name='Telegram ID того кто добавил запись', null=True)
    topAdmin = BooleanField(verbose_name='Is TopAdmin')


def copy_username_to_name(sender, instance, created):
    if created:
        instance.Name = instance.Username


# Подключаем сигнал к модели
pre_save.connect(copy_username_to_name, sender=User)
