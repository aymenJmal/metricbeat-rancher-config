FROM frolvlad/alpine-python3

RUN pip install urllib3
RUN pip install pyyaml
RUN apk add --no-cache shadow

RUN mkdir /metricbeat-rancher-data

RUN groupadd --gid 1000 metricbeat && \useradd  --uid 1000 --gid 1000 metricbeat

COPY metricbeat-rancher.py /
RUN chmod 755 /metricbeat-rancher.py && \
    chown metricbeat.metricbeat /metricbeat-rancher-data

USER metricbeat

RUN mkdir /metricbeat-rancher-data/modules.d

ADD modules.d /metricbeat-rancher-data/modules.d

VOLUME /metricbeat-rancher-data

CMD ["/metricbeat-rancher.py"]
