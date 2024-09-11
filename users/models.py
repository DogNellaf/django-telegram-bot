from __future__ import annotations

from typing import Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, GetOrNoneManager


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class Company(models.Model):
    '''Определение компании'''
    name = models.CharField("Название", max_length=100)

    class Meta:
        verbose_name = "компанию"
        verbose_name_plural = "компании"

    def __str__(self):
        return self.name


class Role(models.Model):
    '''Определение роли пользователя'''
    name = models.CharField("Название", max_length=100)

    class Meta:
        verbose_name = "роль"
        verbose_name_plural = "роли"

    def __str__(self):
        return self.name


class Event(models.Model):
    '''Определение события'''
    title = models.CharField("Заголовок", max_length=255)
    text = models.TextField("Текст события")
    date = models.DateField("Дата события")
    company = models.ForeignKey(Company, verbose_name="Компания", on_delete=models.CASCADE)
    roles = models.ManyToManyField(Role, verbose_name="Роли, которым отображается")

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

    def __str__(self):
        return f"{self.title} - {self.date}"


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(
        verbose_name='Telegram ID',
        primary_key=True
    )

    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=32,
        **nb
    )

    # first_name = models.CharField(max_length=256)
    # last_name = models.CharField(max_length=256, **nb)
    # language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    # deep_link = models.CharField(max_length=64, **nb)
    role = models.ForeignKey(Role, verbose_name="Роль", on_delete=models.CASCADE)
    company = models.ForeignKey(Company, verbose_name="Компания", on_delete=models.CASCADE)

    is_blocked_bot = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    # u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        return f'@{self.username}'

