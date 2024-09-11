from datetime import timedelta, datetime, date

from django.utils.timezone import now
from django.db.transaction import commit
from telegram import ParseMode, Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from asgiref.sync import sync_to_async
from tgbot.handlers.admin import static_text
from tgbot.handlers.admin.utils import _get_csv_from_qs_values
from tgbot.handlers.utils.decorators import admin_only, send_typing_action
from users.models import User, Role, Company


@admin_only
def admin(update: Update, context: CallbackContext) -> None:
    """ Show help info about all secret admins commands """
    update.message.reply_text(static_text.secret_admin_commands)


@admin_only
def stats(update: Update, context: CallbackContext) -> None:
    """ Show help info about all secret admins commands """
    text = static_text.users_amount_stat.format(
        user_count=User.objects.count(),  # count may be ineffective if there are a lot of users.
        active_24=User.objects.filter(updated_at__gte=now() - timedelta(hours=24)).count()
    )

    update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@admin_only
@send_typing_action
def export_users(update: Update, context: CallbackContext) -> None:
    # in values argument you can specify which fields should be returned in output csv
    users = User.objects.all().values()
    csv_users = _get_csv_from_qs_values(users)
    update.message.reply_document(csv_users)

COMPANIES = ['Folk', 'Amber', 'Padron', 'ENO']

SELECT_COMPANY, ENTER_NAME = range(2)  # Определяем состояния

def save_user_company(user_id, company_name) -> bool:
    user_with_id_exists = User.objects.filter(user_id=user_id).exists()
    company_with_name_exists = Company.objects.filter(name=company_name).exists()

    if not company_with_name_exists:
        print(f"Компания {company_name} не найдена")
        return False

    company = Company.objects.get(name=company_name)
    if user_with_id_exists:
        user_profile = User.objects.get(user_id=user_id)
        user_profile.company = company
        user_profile.save()
        return True
    else:
        guest_role = Role.objects.get(name="Гость")
        User.objects.create(
            user_id = user_id,
            username = "",
            first_name = "",
            company = company,
            role = guest_role
        )
        return True

def save_user_name(user_id, name):
    user_profile = User.objects.get(user_id=user_id)
    user_profile.username = name
    user_profile.save()

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[company.name] for company in list(Company.objects.all())]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Выберите компанию:', reply_markup=reply_markup)

    context.user_data['state'] = SELECT_COMPANY  # Устанавливаем состояние

def select_company(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('state') == SELECT_COMPANY:
        user = update.message.from_user
        company = update.message.text

        does_user_save = save_user_company(user.id, company)
        if not does_user_save:
            update.message.reply_text('Возникла ошибка - компания не найдена. Обратитесь к администратору')
            return

        update.message.reply_text(f'Вы выбрали {company}. Теперь введите свое имя:')

        context.user_data['state'] = ENTER_NAME  # Переходим к следующему состоянию

def get_name(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('state') == ENTER_NAME:
        user = update.message.from_user
        name = update.message.text

        save_user_name(user.id, name)
        update.message.reply_text(f'Спасибо, {name}. Мы будем уведомлять вас о событиях.')

        context.user_data['state'] = None  # Сбрасываем состояние после завершения

def handle_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('state') == SELECT_COMPANY:
        select_company(update, context)
    elif context.user_data.get('state') == ENTER_NAME:
        get_name(update, context)
    else:
        update.message.reply_text('Нажмите /start для начала.')

