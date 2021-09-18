import asyncio
import os
from email.message import EmailMessage
import aiosmtplib


async def send_message_reg_confirm(work_queue):

    while not work_queue.empty():
        data = await work_queue.get()
        message = EmailMessage()
        message["From"] = os.getenv('MY_EMAIL')
        message["To"] = data[1]
        message["Subject"] = "Подтверждение о регистрации"
        message.set_content(f"{data[0]}!\n"
                            "Поздравляем! Вы только что зарегистрировались в нашем сервисе заказов!")
        try:
            await aiosmtplib.send(message,
                                  hostname="smtp.mail.ru",
                                  port=465, use_tls=True,
                                  password=os.getenv('MY_EMAIL_PASSWORD'),
                                  username=os.getenv('MY_EMAIL'))
        except:
            pass


async def registration_confirm(emails):
    work_queue = asyncio.Queue()
    for data in emails:
        await work_queue.put(data)
    await asyncio.gather(*[(asyncio.create_task(send_message_reg_confirm(work_queue))) for _ in range(6)])


async def send_message_order_confirm(work_queue):
    order_list = []
    order_dict = {}
    while not work_queue.empty():
        data = await work_queue.get()
        user = data[0].user
        user_email = user.email
        for i in data[1]:
            order_dict['provider'] = i.provider
            order_dict['product'] = i.product
            order_dict['quantity'] = i.quantity
            order_list.append(order_dict)
        message = EmailMessage()
        message["From"] = os.getenv('MY_EMAIL')
        message["To"] = user_email
        message["Subject"] = "Подтверждение заказа"
        message.set_content(f"""{str(user).capitalize()}!
                                Ваш заказ: №: {data[0].id}
                                Информация о товаре:"""
                                                f"""поставщик: {provider},
                                                    товар: {product},
                                                    количество: {quantity}""")
        try:
            await aiosmtplib.send(message,
                                  hostname="smtp.mail.ru",
                                  port=465, use_tls=True,
                                  password=os.getenv('MY_EMAIL_PASSWORD'),
                                  username=os.getenv('MY_EMAIL'))
        except:
            pass


async def order_confirm(order_confirm_for_email):
    work_queue = asyncio.Queue()
    await work_queue.put(order_confirm_for_email)
    await asyncio.gather(*[(asyncio.create_task(send_message_order_confirm(work_queue))) for _ in range(6)])


if __name__ == "__main__":
    asyncio.run(order_confirm())
