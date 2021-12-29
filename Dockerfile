FROM python:3.9

COPY requirements.txt /
WORKDIR /
RUN pip install --no-cache-dir -r requirements.txt

COPY . /

ENTRYPOINT ["python", "scale.py"]
