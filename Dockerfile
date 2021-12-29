FROM python:3.9

COPY requirements.txt /
WORKDIR /
ENV PYTHONPATH /
RUN pip install --no-cache-dir -r requirements.txt

COPY . /

ENTRYPOINT ["python", "automatic/scale.py"]
