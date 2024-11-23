from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import time


if __name__ == "__main__":

    print('start')
    # Create a SparkSession
    spark = SparkSession.builder \
        .appName("printDataframe") \
        .getOrCreate()

    # Define schema for DataFrame
    schema = StructType([
        StructField("name", StringType(), True),
        StructField("age", IntegerType(), True)
    ])

    # Sample data
    data = [("Alice", 30), ("Bob", 25), ("Charlie", 35)]

    # Create DataFrame
    df = spark.createDataFrame(data, schema)

    # Show contents of DataFrame
    df.show()

    # Sleep for 10 seconds
    time.sleep(10)

    # Stop SparkSession
    spark.stop()
