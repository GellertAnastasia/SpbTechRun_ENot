import requests
import uuid
import json


auth = "ZTRiMjQzOTAtMWE4OS00MWI0LWFkNWEtOWRkODVlNjcwMDJiOmQ5NGU3NGM0LTJmNjAtNGRkNy04YmFiLTNhNjM0YjlkNGVkNg=="
client_secret = "e4b24390-1a89-41b4-ad5a-9dd85e67002b"
client = "d94e74c4-2f60-4dd7-8bab-3a634b9d4ed6"

def get_token(auth_token, scope='GIGACHAT_API_PERS'):
    # Создадим идентификатор UUID (36 знаков)
    rq_uid = str(uuid.uuid4())

    # API URL
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    # Заголовки
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }
    # Тело запроса
    payload = {
        'scope': scope
    }
    try:
        # Делаем POST запрос с отключенной SSL верификацией
        # (можно скачать сертификаты Минцифры, тогда отключать проверку не надо)
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка: {str(e)}")
        return -1






def get_chat_completion(auth_token, user_message):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    # Подготовка данных запроса в формате JSON
    payload = json.dumps({
        "model": "GigaChat",  # Используемая модель
        "messages": [
            {
                "role": "user",  # Роль отправителя (пользователь)
                "content": user_message  # Содержание сообщения
            }
        ],
        "temperature": 1,  # Температура генерации
        "top_p": 0.1,  # Параметр top_p для контроля разнообразия ответов
        "n": 1,  # Количество возвращаемых ответов
        "stream": False,  # Потоковая ли передача ответов
        "max_tokens": 512,  # Максимальное количество токенов в ответе
        "repetition_penalty": 1,  # Штраф за повторения
        "update_interval": 0  # Интервал обновления (для потоковой передачи)
    })

    # Заголовки запроса
    headers = {
        'Content-Type': 'application/json',  # Тип содержимого - JSON
        'Accept': 'application/json',  # Принимаем ответ в формате JSON
        'Authorization': f'Bearer {auth_token}'  # Токен авторизации
    }

    # Выполнение POST-запроса и возвращение ответа
    try:
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        # Обработка исключения в случае ошибки запроса
        print(f"Произошла ошибка: {str(e)}")
        return -1

giga_token = get_token(auth)["access_token"]

answer = get_chat_completion(giga_token, 'Предложи мне рецепт какого-нибудь блюда на основе исключительно следующих продуктов:свинина, помидор, лук, майонез.')
CONTENT = answer.json()['choices'][0]['message']['content']

