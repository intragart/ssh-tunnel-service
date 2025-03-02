# ssh-tunnel-service

This programm uses the built in ssh-command to establish tunnels to the defined remote sites. These
tunnels are also being monitored and restarted once they die or need to be reset for any (known)
reason.

**Please note that the fingerprint of the remote site has to be known in the local system.**

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

`ssh-port`: Optional. Port to be used within the ssh-command.

`password`: Optional. *Not yet implemented.* **If key is not set key `identity-file` is mandatory.**

`identity-file`: Optional. Absolute path to the ssh-keyfile to be used for remote side. The
keyfile musn't have a password. **If key is not set key `password` is mandatory.**

`local-ports`: Optional. List of local sockets to be forwarded with the tunnel. Format is
`bind_address:localport:ip:remoteport`.

**remote-ports**: Optional. List of remote sockets to be forwarded with the tunnel. Format is
`bind_address:localport:ip:remoteport`.

**options**: Optional. *WIP*. List of ssh-command options.

## Adding a Service to Linux

The program can be added as a service within linux. To do so the file `ssh-tunnel-service.service`
can be created with the contents shown below. Please change the path for `ExecStart` to match your
system.

```
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
```

Once the file has been created it can be copied to the correct location:

    cp ssh-tunnel-service.service /etc/systemd/system

To start install the service and to enable it on startup execute these two lines as root user:

    systemctl start ssh-tunnel-service.service
    systemctl enable ssh-tunnel-service.service
