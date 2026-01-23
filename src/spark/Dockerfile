FROM apache/spark:3.5.1

ENV SPARK_HOME=/opt/spark
ENV PATH="$SPARK_HOME/bin:$PATH"

ENV SPARK_VERSION=3.5.1
ENV SCALA_BINARY_VERSION=2.12
ENV KAFKA_CLIENTS_VERSION=3.7.0

# JARs do integracji Spark <-> Kafka + Kafka clients (ByteArraySerializer)
RUN set -eux; \
    mkdir -p /opt/spark/jars; \
    curl -fL --retry 5 --retry-delay 2 -o /opt/spark/jars/spark-sql-kafka-0-10_${SCALA_BINARY_VERSION}-${SPARK_VERSION}.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_${SCALA_BINARY_VERSION}/${SPARK_VERSION}/spark-sql-kafka-0-10_${SCALA_BINARY_VERSION}-${SPARK_VERSION}.jar; \
    curl -fL --retry 5 --retry-delay 2 -o /opt/spark/jars/spark-token-provider-kafka-0-10_${SCALA_BINARY_VERSION}-${SPARK_VERSION}.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_${SCALA_BINARY_VERSION}/${SPARK_VERSION}/spark-token-provider-kafka-0-10_${SCALA_BINARY_VERSION}-${SPARK_VERSION}.jar; \
    curl -fL --retry 5 --retry-delay 2 -o /opt/spark/jars/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar \
      https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/${KAFKA_CLIENTS_VERSION}/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar

WORKDIR /opt/spark-app
CMD ["sleep", "infinity"]
