FROM python:3.13-slim

# set up app environment
LABEL version="0.1.0"
ENV DOCKER_CONTAINER=True
WORKDIR /app

# install additional software
RUN apt-get update
RUN apt-get install -y openssh-client git sshpass
RUN rm -rf /var/lib/apt/lists/*

# install app ssh-tunnel-service
RUN git clone https://github.com/intragart/ssh-tunnel-service .
# TODO: Remove git checkout dev
RUN git checkout dev
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p config
RUN mkdir -p .ssh
RUN chmod 700 .ssh
RUN cp templates/config.example.yml config/config.yml

# run app
CMD ["python", "-u", "main.py"]
