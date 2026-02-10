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

Bucket: datalake
Zawiera pliki Delta
