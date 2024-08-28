FROM alpine:latest
RUN apk --no-cache add dnsmasq=2.89-r5
VOLUME /etc/dnsmasq
EXPOSE 53 53/udp
ENTRYPOINT ["dnsmasq", "-k"]