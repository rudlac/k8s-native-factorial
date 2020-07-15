FROM python:3-alpine
RUN pip install flask kubernetes
COPY main.py .
RUN chmod +x main.py
ENTRYPOINT ["./main.py"]
