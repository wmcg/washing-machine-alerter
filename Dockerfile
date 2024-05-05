FROM python:3.11-alpine

RUN apk update && apk add poetry python3-dev libffi-dev musl-dev gcc

COPY poetry.lock pyproject.toml README.md /app/
RUN cd /app && poetry install --no-root

COPY ./washing_machine_alerter/ /app/

WORKDIR /app

CMD ["poetry", "run", "python", "/app/main.py"]