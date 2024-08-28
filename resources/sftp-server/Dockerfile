# The Dockerfile for an SFTP (SSH File Transfer Protocol) server sets up a
# lightweight container environment and grantes necessary permissions for user operations
FROM alpine:latest
# Alpine version of the current image - 3.19.1

RUN apk add --no-cache bash shadow openssh-server-pam openssh-sftp-server iperf3 && \
    ln -s /usr/sbin/sshd.pam /usr/sbin/sshd && \
    mkdir -p /var/run/sshd && \
    rm -f /etc/ssh/ssh_host_*key*

COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint /
RUN chmod +x /entrypoint

VOLUME /home/ericsson

EXPOSE 22

ENTRYPOINT ["/entrypoint"]
