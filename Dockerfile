FROM python:3.9-alpine
RUN pip install flask requests docker
COPY src/*.py /app/
WORKDIR /app
ENTRYPOINT ["python","main.py"]