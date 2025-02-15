FROM python:3.11

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY appBackend /app/appBackend
WORKDIR /app/appBackend

WORKDIR /app
CMD ["uvicorn", "appBackend.main:app", "--host", "0.0.0.0", "--port", "8001"]