import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

KAFKA_BOOTSTRAP = "kafka:29092"
TOPIC = "olist.public.orders"

# Debezium JSON (minimalnie: payload.op + payload.after)
schema_after = StructType([
    StructField("order_id", StringType(), True),
    StructField("order_status", StringType(), True),
])

schema_payload = StructType([
    StructField("op", StringType(), True),
    StructField("after", schema_after, True),
])

schema_root = StructType([
    StructField("payload", schema_payload, True),
])

spark = SparkSession.builder.appName("orders_stream").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

# bytes -> string
json_str = raw.selectExpr("CAST(value AS STRING) AS json")

parsed = (
    json_str
    .select(F.from_json(F.col("json"), schema_root).alias("data"))
    .select("data.*")
)

events = (
    parsed
    .select(
        F.col("payload.op").alias("op"),
        F.col("payload.after.order_id").alias("order_id"),
        F.col("payload.after.order_status").alias("order_status"),
    )
    .where(F.col("order_id").isNotNull())
    .where(F.col("order_status").isNotNull())
)

agg = events.groupBy("order_status").count()

query = (
    agg.writeStream
    .outputMode("complete")
    .format("console")
    .option("truncate", "false")
    .option("checkpointLocation", "/opt/spark-app/checkpoints/orders_stream")
    .start()
)

query.awaitTermination()