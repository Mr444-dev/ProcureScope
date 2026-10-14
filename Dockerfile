FROM apache/airflow:2.10.5-python3.11

USER root
RUN mkdir -p /opt/airflow/app && chown airflow:root /opt/airflow/app
USER airflow
WORKDIR /opt/airflow/app

COPY --chown=airflow:root requirements.txt pyproject.toml README.md LICENSE ./
COPY --chown=airflow:root src ./src
COPY --chown=airflow:root dbt ./dbt
COPY --chown=airflow:root airflow/dags /opt/airflow/dags

RUN pip install --no-cache-dir \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt" \
      "apache-airflow-providers-postgres==5.14.0" \
      "dbt-postgres==1.9.0" \
      -r requirements.txt \
      .

ENV PYTHONPATH=/opt/airflow/app/src \
    DBT_PROFILES_DIR=/opt/airflow/app/dbt \
    DBT_PROJECT_DIR=/opt/airflow/app/dbt
