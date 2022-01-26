FROM python:3.9

COPY requirements.txt /
WORKDIR /
ENV PYTHONPATH /
RUN pip install --no-cache-dir -r requirements.txt

COPY ./autoscaler /autoscaler

ENTRYPOINT ["python3", "autoscaler", "start"]
