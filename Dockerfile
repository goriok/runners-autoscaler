FROM python:3.10-slim

WORKDIR /home/bitbucket
ENV PYTHONPATH /home/bitbucket

COPY requirements.txt setup.py CHANGELOG.md README.md LICENSE.txt /home/bitbucket/
COPY autoscaler/ /home/bitbucket/autoscaler

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "autoscaler/start.py"]
