FROM joyzoursky/python-chromedriver:3.9

WORKDIR /src

COPY requirements.txt /src
COPY main.py /src
COPY habr.csv /src

RUN pip install -r requirements.txt

CMD ["python", "main.py"]