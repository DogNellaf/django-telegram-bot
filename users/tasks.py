"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from typing import Union, List, Optional, Dict
from datetime import datetime

import telegram

from dtb.celery import app
from celery.utils.log import get_task_logger
from celery import shared_task
from tgbot.handlers.broadcast_message.utils import send_one_message, from_celery_entities_to_entities, \
    from_celery_markup_to_markup

from users.models import User, Event

logger = get_task_logger(__name__)


@shared_task
def send_daily_reminders():
    today = datetime.today()
    events = Event.objects.filter(date=today).all()

    for event in events:
        users = User.objects.filter(company=event.company).all()

        for user in users:
            send_one_message(
                user_id=user.user_id,
                text=f"Напоминание: Сегодня запланировано событие:\n'{event.text}'."
            )
            logger.info(f"Уведомление отправлено пользователю {user.user_id}")

    print(f"Уведомления за {today} отправлены")

@app.task(ignore_result=True)
def broadcast_message(
    user_ids: List[Union[str, int]],
    text: str,
    entities: Optional[List[Dict]] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ It's used to broadcast message to big amount of users """
    logger.info(f"Going to send message: '{text}' to {len(user_ids)} users")

    entities_ = from_celery_entities_to_entities(entities)
    reply_markup_ = from_celery_markup_to_markup(reply_markup)
    for user_id in user_ids:
        try:
            send_one_message(
                user_id=user_id,
                text=text,
                entities=entities_,
                parse_mode=parse_mode,
                reply_markup=reply_markup_,
            )
            logger.info(f"Broadcast message was sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}, reason: {e}")
        time.sleep(max(sleep_between, 0.1))

    logger.info("Broadcast finished!")