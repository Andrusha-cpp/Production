import json
import sys

# читаем JSON из запроса
data = json.loads(sys.stdin.read())

email = data.get("email")
password = data.get("password")

# ПРИМЕР ПРОВЕРКИ (замени на БД)
if email == "test@mail.com" and password == "1234":
    result = {"success": True}
else:
    result = {"success": False}

# отдаем JSON обратно
print("Content-Type: application/json\n")
print(json.dumps(result))