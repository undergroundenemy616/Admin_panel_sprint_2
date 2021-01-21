def generate_html(body: str, office: str, account):
    return f"""<h2>Новая заявка по офису "{office}".</h2>
                <h3>Содержание заявки:</h3>
                <p style="text-indent:20px;">"{body}"</p>
                <h3>Данные пользователя:</h3>
        <p style="text-indent:20px;">Имя: {account.first_name + ' ' + account.last_name if account.last_name else account.first_name}</p>
        <p style="text-indent:20px;">Телефон: {account.phone_number if account.phone_number else 'Отсутствует'}</p>
        <p style="text-indent:20px;">Почтовый адрес: {account.email if account.email else 'Отсутствует'}</p>"""


def generate_attach(body: str, attachments: list = None):
    if attachments:
        count = len(attachments)
        body += "<h3>Вложения:</h3>"
        for url in attachments:
            body = body + '<p style="text-indent:10px;"> Изображение {0}:</p>'.format(
                count
            )
            body = body + '<img alt="Изображение {0}" src={1}><br>'.format(count, url)
            body = body + "<a href = {0}>Прямая ссылка</a><br>".format(url)
            count -= 1
    return body
