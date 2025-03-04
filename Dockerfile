FROM python:3.9-slim

ENV DOCKER_CONTAINER=True

WORKDIR /app

RUN apt-get update
RUN apt-get install -y openssh-client git sshpass
RUN rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/intragart/ssh-tunnel-service .
# TODO: Remove git checkout dev
RUN git checkout dev
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p config
RUN mkdir -p .ssh
RUN chmod 700 .ssh

COPY templates/config.example.yml config/config.yml

CMD ["python", "main.py"]
