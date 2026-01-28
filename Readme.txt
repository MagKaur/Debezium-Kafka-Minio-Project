--------------------------------------------------------------Opis projektu---------------------------------------------------------------------------

Projekt prezentuje kompletny pipeline przetwarzania danych w czasie zbliżonym do rzeczywistego, oparty o technologie Big Data.
Dane są ładowane do relacyjnej bazy danych (PostgreSQL), następnie zmiany w tabelach są przechwytywane przez Debezium (CDC) i publikowane do Apache Kafka.
Strumień danych jest przetwarzany w Apache Spark Structured Streaming, a wyniki zapisywane są do Delta Lake na obiekcie storage (MinIO).

Projekt realizuje wymagania zadań 1–5 kursu WPBD.




---------------------------------------------------------.Architektura (High-Level)-------------------------------------------------------------------

CSV → PostgreSQL → Debezium → Kafka → Spark Structured Streaming → Delta Lake (MinIO)


===========================================URUCHOMIENIE================================================

z path katalogu projektu uruchom docker-compose.yml 
-------> command: docker-compose up -d

Uruchomione zostaną m.in.:

PostgreSQL

Kafka

Kafka Connect (Debezium)

Schema Registry

Spark

MinIO

-----------------Dostęp przez MinIO UI (opcjonalnie)

URL: http://localhost:9001

login: minioadmin

hasło: minioadmin

Bucket: datalake
Zawiera pliki Delta


------Test------------

---> docker exec -it kafka bash -lc "/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --list | head"

---> docker exec -it olist-postgres psql -U debezium -d olist -c "SHOW wal_level;"

---> docker exec -it olist-postgres psql -U debezium -d olist -c "UPDATE public.orders SET order_status='delivered' WHERE order_id IN (SELECT order_id FROM public.orders LIMIT 1);"

---> docker exec -it kafka bash -lc "/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --list | grep -E '^olist\.' || echo 'NO OLIST TOPICS'"

---> docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:29092 --topic olist.public.orders --max-messages 1

---> docker logs -f spark-job

---> docker attach spark-shell

---> docker exec -it spark-shell /opt/spark/bin/spark-shell --packages io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 --conf spark.hadoop.fs.s3a.access.key=minioadmin --conf spark.hadoop.fs.s3a.secret.key=minioadmin --conf spark.hadoop.fs.s3a.path.style.access=true --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false --conf spark.jars.ivy=/tmp/.ivy2

---> import org.apache.hadoop.fs.{FileSystem, Path}
import java.net.URI

val fs = FileSystem.get(new URI("s3a://datalake"), spark.sparkContext.hadoopConfiguration)
fs.listStatus(new Path("s3a://datalake/")).map(_.getPath.toString).foreach(println)

---> val df=spark.read.format("delta").load("s3a://datalake/delta/orders_status_counts") df.show(false)

