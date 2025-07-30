## Локальный запуск

Клонируйте репозиторий

```bash
  git clone https://github.com/ArtemRuslanovich/wildberries.git
```

Перейдите в репозиторий :)

```bash
  cd wildberries
```

Создайте виртуальное окружение

```bash
  python3 -m venv venv
```

Активируйте виртуальное окружение

```bash
  source venv/bin/activate
```

Установите зависимости

```bash
  pip3 install -r requirements.txt
```

Запустите программу

```bash
  python3 parser.py
```

## Важно

У меня мак и команды подходят для маков и линукса, если вы используете windows, то:

```bash
  Вместо pip3 используем pip
  Вместо python3 используем python
  Вместо source venv/bin/activate используем venv\\Scripts\\activate
```