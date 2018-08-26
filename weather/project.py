from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import udf

if __name__=="__main__":
    spark=SparkSession.builder.appName('project').getOrCreate()
    df2017=spark.read.format('csv')\
        .option("header","true")\
        .option("inferSchema","true")\
        .load('file:///home/sam/Documents/spark/data/Beijing_2017_HourlyPM25_created20170803.csv')\
        .select("Year","Month","Day","Hour","Value","Qc Name")
    df2016=spark.read.format('csv')\
        .option('header','true')\
        .option('inferSchema','true')\
        .load('file:///home/sam/Documents/spark/data/Beijing_2016_HourlyPM25_created20170201.csv')\
        .select('Year','Month','Day','Hour','Value','Qc Name')
    df2015=spark.read.format('csv')\
        .option('header','true')\
        .option('inferSchema','true')\
        .load('file:///home/sam/Documents/spark/data/Beijing_2015_HourlyPM25_created20160201.csv')\
        .select('Year','Month','Day','Hour','Value','Qc Name')


    def get_grade(value):
        if value>=0 and value<=50:
            return '健康'
        elif  value<=100:
            return '中等'
        elif value<=150:
            return '导致敏感的人群过敏'
        elif  value<=200:
            return "不健康"
        elif  value<=300:
            return '非常不健康'
        elif  value<=500:
            return '危险'
        elif value>500:
            return '极度危险'
        else:
            return None

    grade_function_udf=udf(get_grade,StringType())


    group2015=df2015.withColumn("Grade",grade_function_udf(df2015['Value']))\
        .groupBy('Grade')\
        .count()
    group2016=df2016.withColumn("Grade", grade_function_udf(df2016['Value']))\
        .groupBy('Grade')\
        .count()
    group2017=df2017.withColumn("Grade", grade_function_udf(df2017['Value']))\
        .groupBy('Grade')\
        .count()

    group2015=group2015.select('Grade','count',group2015['count']/df2015.count())
    group2016 = group2016.select('Grade', 'count', group2016['count'] / df2016.count())
    group2017 = group2017.select('Grade', 'count', group2017['count'] / df2017.count())

    result2015=group2015.withColumn("percent",group2015['count']/df2015.count()*100)\
        .select('Grade','count','percent')\
        .selectExpr("Grade as grade",'count','percent')

    result2016 = group2016.withColumn("percent", group2016['count'] / df2016.count()*100) \
        .select('Grade', 'count', 'percent')\
        .selectExpr('Grade as grade','count','percent')

    result2017 = group2017.withColumn("percent", group2017['count'] / df2017.count()*100) \
        .select('Grade', 'count', 'percent')\
        .selectExpr('Grade as grade','count','percent')






    result2015.write.format("org.elasticsearch.spark.sql").option("es.nodes","192.168.1.4:9200").mode("overwrite").save("weather2015/pm")
    result2016.write.format("org.elasticsearch.spark.sql").option("es.nodes","192.168.1.4:9200").mode("overwrite").save("weather2016/pm")
    result2017.write.format("org.elasticsearch.spark.sql").option("es.nodes","192.168.1.4:9200").mode("overwrite").save("weather2017/pm")

    spark.stop()