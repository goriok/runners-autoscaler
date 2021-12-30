FROM python:3.9

COPY requirements.txt /
WORKDIR /
ENV PYTHONPATH /
RUN pip install --no-cache-dir -r requirements.txt

COPY ./apis/ /apis
COPY ./automatic/ /automatic

COPY constants.py \
     exceptions.py \
     helpers.py \
     logger.py \
     runner.py \
     job.yaml.template /

ENTRYPOINT ["python", "automatic/scale.py"]
