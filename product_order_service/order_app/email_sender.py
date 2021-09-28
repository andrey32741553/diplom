import smtplib
import os
import ssl
from email.message import EmailMessage

from order_app.models import Position
from product_order_service import celery_app


@celery_app.task
def send_message_reg_confirm(emails):
    message = EmailMessage()
    message["From"] = os.getenv('MY_EMAIL')
    message["To"] = emails[1]
    message["Subject"] = "Подтверждение о регистрации"
    message.set_content(f"{emails[0]}!\n"
                        "Поздравляем! Вы только что зарегистрировались в нашем сервисе заказов!")
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.mail.ru", port=587) as smtp:
        smtp.starttls(context=context)
        smtp.login(os.getenv('MY_EMAIL'), os.getenv('MY_EMAIL_PASSWORD'))
        smtp.send_message(message)


@celery_app.task
def order_confirm(order_confirm_for_email):
    order_list = []
    user = order_confirm_for_email[0].user
    total = order_confirm_for_email[0].total
    user_email = user.email
    for item in order_confirm_for_email[1]:
        order_dict = {'provider': item.provider, 'product': item.product, 'quantity': item.quantity}
        order_list.append(order_dict)
    message = EmailMessage()
    message["From"] = os.getenv('MY_EMAIL')
    message["To"] = user_email
    message["Subject"] = "Подтверждение заказа"
    message.set_content(f"{str(user).capitalize()}!\nВаш заказ: №: {order_confirm_for_email[0].id} на сумму {total}\n"
                        f"Информация о товаре:\n"
                        f"{order_details(order_list)}")
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.mail.ru", port=587) as smtp:
        smtp.starttls(context=context)
        smtp.login(os.getenv('MY_EMAIL'), os.getenv('MY_EMAIL_PASSWORD'))
        smtp.send_message(message)


def order_details(order_list):
    order_details_list = []
    for position in order_list:
        message = f"поставщик: {position['provider']}, товар: {position['product']}, " \
                  f"количество: {position['quantity']}".replace("\n", "")
        order_details_list.append(message)
    return order_details_list


@celery_app.task
def message_to_provider(order_confirm_for_email):
    user = order_confirm_for_email[0].user
    email_adresses = [data.provider.email for data in order_confirm_for_email[1]]
    message = EmailMessage()
    message["From"] = os.getenv('MY_EMAIL')
    message["To"] = set(email_adresses)
    message["Subject"] = "Новый заказ"
    message.set_content(f"\nЗаказ: №: {order_confirm_for_email[0].id} для {str(user).capitalize()}\n"
                        f"У Вас новый заказ! "
                        f"Просмотрите более подробную информацию на странице: http://127.0.0.1:8000/api/v1/orders/")
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.mail.ru", port=587) as smtp:
        smtp.starttls(context=context)
        smtp.login(os.getenv('MY_EMAIL'), os.getenv('MY_EMAIL_PASSWORD'))
        smtp.send_message(message)


@celery_app.task
def cancelled_status_message(order, user):
    provider_info = Position.objects.filter(order_id=order.id)
    email_adresses = [data.provider.email for data in provider_info]
    message = EmailMessage()
    message["From"] = os.getenv('MY_EMAIL')
    message["To"] = set(email_adresses)
    message["Subject"] = "Статус заказа изменён"
    message.set_content(f"\nПокупатель {str(user).capitalize()} отменил заказ №: {order.id}!\n")
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.mail.ru", port=587) as smtp:
        smtp.starttls(context=context)
        smtp.login(os.getenv('MY_EMAIL'), os.getenv('MY_EMAIL_PASSWORD'))
        smtp.send_message(message)


@celery_app.task
def changed_status_message(order, user):
    message = EmailMessage()
    message["From"] = os.getenv('MY_EMAIL')
    message["To"] = user.email
    message["Subject"] = "Статус заказа изменён"
    message.set_content(f"\n{str(order.user).capitalize()}! Статус Вашего заказа №: {order.id} изменён на {order.status}!\n")
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.mail.ru", port=587) as smtp:
        smtp.starttls(context=context)
        smtp.login(os.getenv('MY_EMAIL'), os.getenv('MY_EMAIL_PASSWORD'))
        smtp.send_message(message)
