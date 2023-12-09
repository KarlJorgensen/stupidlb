FROM debian:12-slim

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get --yes --no-install-recommends install python3-minimal python3-pip

RUN pip install --break-system-packages kopf kubernetes
CMD /entrypoint
ADD entrypoint /entrypoint
ADD stupidlb.py /stupidlb.py

