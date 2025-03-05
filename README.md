# ssh-tunnel-service

This programm uses the built in ssh-command to establish tunnels to the defined remote sites. These
tunnels are also being monitored and restarted once they die or need to be reset for any (known)
reason.

**Please note that the fingerprint of the remote site has to be known in the local system.**

Contents of README.md:

- [Installation](#installation)
- [Configuration](#configuration)
- [Adding a Service to Linux](#adding-a-service-to-linux)
- [Docker Container](#docker-container)

## Installation

To use this program on your local machine Python needs to be installed. All neccessary non-standard
libraries are listed in `requirements.txt` and can be installed with the following command:

    python -m pip install -r requirements.txt

Once all requirements are installed copy `templates/config.example.yml` to `config/config.yml` and
also copy `templates/siteconfig.example.yml` to `config/config.yml`. Both files are needed for
execution.

## Configuration

### config/config.yml

**log-path**: Relative or absolute path to the directory where all logfiles should be stored.
The program will generate a main file for the parent process and one logfile per site defined in
`siteconfig.yml`.

**siteconfig**: Relative or absolute path to the yaml-file where all tunnel endpoints are defined.

### config/siteconfig.yml

*Name and path for this file might differ, depending on your configuration in `config/config.yml`.*

Each site has a uniqe sitename. These sitenames can be configured using the keys defined below.

`active`: Mandatory. Used to indicate if a tunnel should be established for this site. Sites not
in use can be turned off using this setting. Possible values are `True` or `False`.

`fqdn`: Mandatory. Fully-Qualified-Domain-Name or IP-Address of the remote site.

`user`: Mandatory. Username to be used at the remote site.

`hostkey`: Optional. `known_hosts` entry of remote host. This key is needed to verify the identity
of the remote system. If host key verification shall not be executed add
`UserKnownHostsFile: /dev/null` and `StrictHostKeyChecking: no` to options list of yml file.

`ssh-port`: Optional. Port to be used within the ssh-command.

`password`: Optional, not recommended. Password to be used for user authentication at the remote
host. The programm `sshpass` needs to be installed on the local system.
**If key is not set key `identity-file` is mandatory.**

`identity-file`: Optional. Absolute path to the ssh-keyfile to be used for remote side. The
keyfile musn't have a password. **If key is not set key `password` is mandatory.**

`local-ports`: Optional. List of local sockets to be forwarded with the tunnel. Format is
`bind_address:localport:ip:remoteport`.

`remote-ports`: Optional. List of remote sockets to be forwarded with the tunnel. Format is
`bind_address:localport:ip:remoteport`.

`options`: Optional. List of ssh options that will be added to the ssh command with the `-o` option.

## Adding a Service to Linux

The program can be added as a service within linux. To do so the file `ssh-tunnel-service.service`
can be created with the contents shown below. Please change the path for `ExecStart` to match your
system.

    [Unit]
    Description=ssh-tunnel-service
    After=network.target
    
    [Service]
    Type=simple
    ExecStart=/usr/bin/python3 /path/to/ssh-tunnel-service/main.py
    User=test
    Restart=always
    RestartSec=1
    
    [Install]
    WantedBy=multi-user.target

Once the file has been created it can be copied to the correct location:

    cp ssh-tunnel-service.service /etc/systemd/system

To start install the service and to enable it on startup execute these two lines as root user:

    systemctl start ssh-tunnel-service.service
    systemctl enable ssh-tunnel-service.service

## Docker Container

### Build an image

To use this program inside a docker container an image file needs to be build first. Currently
there's no image available on docker hub. Use this command to create a docker image:

    docker build -t ssh-tunnel-service .

### Run Container via siteconfig.yml

The Container needs a `siteconfig.yml` to run. Since the docker container doesn't know any remote
hosts key `hostkey` should be set accordingly. A not recommended alternative to `hostkey` is
disabling host key verification with options `UserKnownHostsFile: /dev/null` and
`StrictHostKeyChecking: no`. `siteconfig.yml` can simply be mounted using `-v`. Therefore, a run
command could look like this:

    docker run -dt \
    -v /local/path/to/siteconfig.yml:/app/config/siteconfig.yml:ro \
    ssh-tunnel-service

If you're using an identity-file for authentification there's the directory `/app/.ssh` that can be
used. The correct location must be referenced in `siteconfig.yml`. One or more identity-file(s) can
simply be mounted as well:

    docker run -dt \
    -v /local/path/to/siteconfig.yml:/app/config/siteconfig.yml:ro \
    -v /local/path/to/identity-file:/app/.ssh/identity-file \
    ssh-tunnel-service

### Run Container using environment variables

The `siteconfig.yml` can be replaced by environment variables when using a docker container. When
environment variables are being used the `siteconfig.yml` inside the docker container is being
rebuild using the values from the environment variables. The names for the variables are almost the
same as described in [config/siteconfig.yml](#configsiteconfigyml). The only differences are:

- environment variables are capslocked and `-` becomes `_`. For example `identity-file` becomes
`IDENTITY_FILE`
- lists are comma seperated values with no spaces between keys and values. For example
`OPTIONS=TCPKeepAlive:yes,GatewayPorts:no`
- For `OPTIONS` character `:` seperates key and value

**Please note that this option only supports one site.**

A command using environment variables could look like this:

    docker run -dt \
    -v /local/path/to/identity-file:/app/.ssh/identity-file \
    -e FQDN=example.com \
    -e SSH_PORT=22 \
    -e USER=test \
    -e IDENTITY_FILE=/app/.ssh/identity-file \
    -e HOSTKEY="ssh-ed25519 AAAAC123456" \
    -e LOCAL_PORTS=bind_address:localport:ip:remoteport,bind_address:localport:ip:remoteport \
    -e REMOTE_PORTS=bind_address:localport:ip:remoteport \
    -e OPTIONS=TCPKeepAlive:yes \
    ssh-tunnel-service

### Docker Compose

A working docker compose file using environment variables could look like this:

    ---
    services:
      ssh-tunnel-service:
        container_name: ssh-tunnel-service
        image: ssh-tunnel-service
        restart: unless-stopped
        volumes:
          - /local/path/to/identity-file:/app/.ssh/identity-file
        environment:
          - FQDN=example.com
          - SSH_PORT=22
          - USER=test
          - IDENTITY_FILE=/app/.ssh/identity-file
          - HOSTKEY="ssh-ed25519 AAAAC123456"
          - LOCAL_PORTS=bind_address:localport:ip:remoteport,bind_address:localport:ip:remoteport
          - REMOTE_PORTS=bind_address:localport:ip:remoteport
          - OPTIONS=TCPKeepAlive:yes
