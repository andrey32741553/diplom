import asyncio
import os
from email.message import EmailMessage
import aiosmtplib


async def send_messages(work_queue):

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


async def email_sender(emails):
    work_queue = asyncio.Queue()
    for data in emails:
        await work_queue.put(data)
    await asyncio.gather(*[(asyncio.create_task(send_messages(work_queue))) for _ in range(6)])

if __name__ == "__main__":
    asyncio.run(email_sender())
