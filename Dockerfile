FROM python:3.12-alpine

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

ENV PYTHONPATH=/code


RUN chmod +x /code/entrypoint.sh

ENTRYPOINT ["/code/entrypoint.sh"]

CMD ["uvicorn", "entrypoints.main:app", "--host", "0.0.0.0", "--port", "8000"]