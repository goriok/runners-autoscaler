FROM python:3.9-slim

WORKDIR /home/bitbucket

COPY requirements.txt setup.py CHANGELOG.md README.md LICENSE.txt /home/bitbucket/
COPY autoscaler/ /home/bitbucket/autoscaler

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

CMD ["start"]
ENTRYPOINT ["bitbucket-runner-autoscaler"]
