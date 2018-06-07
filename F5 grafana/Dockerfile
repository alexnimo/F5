ARG GRAFANA_VERSION="latest"

FROM grafana/grafana:${GRAFANA_VERSION}

USER grafana

ARG GF_INSTALL_PLUGINS="grafana-piechart-panel,grafana-worldmap-panel,mtanda-histogram-panel"

RUN if [ ! -z "${GF_INSTALL_PLUGINS}" ]; then \
    OLDIFS=$IFS; \
        IFS=','; \
    for plugin in ${GF_INSTALL_PLUGINS}; do \
        IFS=$OLDIFS; \
        grafana-cli --pluginsDir "$GF_PATHS_PLUGINS" plugins install ${plugin}; \
    done; \
fi


#RUN cd /var/lib/grafana/plugins $$ mkdir grafana-admdb-datasource
COPY  grafana_bados_dashboard/data/plugins/grafana-admdb-datasource/ /var/lib/grafana/plugins/grafana-admdb-datasource/
#RUN ls -ls /var/lib/grafana/plugins/grafana-admdb-datasource/
COPY grafana_bados_dashboard/conf /usr/share/grafana/conf/
#RUN ls -ls /var/lib/grafana/
USER root
COPY grafana_bados_dashboard/public/dashboards/*.json /usr/share/grafana/public/dashboards/
RUN  chown grafana:grafana /usr/share/grafana/conf/*
#USER grafana
RUN  chmod 775 /usr/share/grafana/conf/defaults.ini
