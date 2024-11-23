from pyspark.sql import SparkSession
import boto3

s3_client = boto3.client('s3')
credentials = s3_client._request_signer._credentials
access_key = credentials.access_key
secret_key = credentials.secret_key
token = credentials.get_frozen_credentials().token

# Initialize Spark session
spark = SparkSession.builder \
    .appName("MyApp") \
    .config("spark.executor.memory", "8g") \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.cores", "4") \
    .config("spark.driver.cores", "4") \
    .config("spark.sql.execution.ui.retainedExecutions", "1000") \
    .config("spark.ui.showConsoleProgress", "true") \
    .config("spark.driver.port", "4040") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.2,io.delta:delta-spark_2.12:3.1.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.hadoop.fs.s3a.access.key", access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", secret_key) \
    .config("spark.hadoop.fs.s3a.session.token", token) \
    .getOrCreate()

spark.read.format("parquet").load("s3a://data/some_data1").createOrReplaceTempView("some_data1")
spark.read.format("parquet").load("s3a://data/some_data2").createOrReplaceTempView("some_data2")


query_result = spark.sql("""
SELECT * from some_data1
UNION ALL
SELECT * from some_data2
""")

query_result.write.format('parquet').save("s3a://data/some_data_u_l2")
spark.stop()

