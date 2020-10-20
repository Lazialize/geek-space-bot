FROM python:3.8

RUN pip install pipenv

COPY Pipfile Pipfile.lock *.py ./
COPY ./extensions ./extensions

RUN pipenv install --system --deploy

ENTRYPOINT ["python3", "launcher.py"]