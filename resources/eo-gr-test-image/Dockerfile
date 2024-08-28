# Dockerfile that contains Python 3.12.2 and Docker for testing purposes of the project 'eo-gr-testing'

FROM python:3.12.2-alpine3.19

# Set PYTHONUNBUFFERED to non-zero value for unbuffered Python output
ENV PYTHONUNBUFFERED 1

# Install the packages required to install the dependencies of the 'eo-gr-testing' project
RUN apk update && apk add docker bash gcc python3-dev libc-dev linux-headers curl && apk add --no-cache git

CMD ["python", "-V"]
