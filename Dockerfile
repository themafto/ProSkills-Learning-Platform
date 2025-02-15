FROM python:3.11

COPY appBackend /app/appBackend
WORKDIR /app/appBackend

RUN pip install --upgrade pip
RUN pip install .       # setup.py found в /app/appBackend

WORKDIR /app
CMD ["uvicorn", "appBackend.main:app", "--host", "0.0.0.0", "--port", "8001"]