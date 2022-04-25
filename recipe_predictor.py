from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.ml.linalg import Vectors
from pyspark.ml.clustering import KMeans
from pyspark.ml.clustering import KMeansModel

from math import sqrt
from pyspark.sql.functions import udf, col
from pyspark.sql.types import ArrayType, FloatType

class RecipePredictor:

  def get_top_3_recipes(self, sc, ingredient_input):
    spark = SparkSession(sc)
    
    # 1. Load model
    filename = 'finalized_model'
    model = KMeansModel.load(filename)
    
    # 2. Load dataframes that need to be used later
    filename = "ingredient_mapping"
    pickleRdd = sc.pickleFile(filename).collect()
    ingredients_mapping = spark.createDataFrame(pickleRdd)
    ingredients_mapping.show(10, False)

    filename = "ingredient_agg"
    pickleRdd = sc.pickleFile(filename).collect()
    ingredient_agg = spark.createDataFrame(pickleRdd)
    ingredient_agg.show(10, False)

    filename = "predictions"
    pickleRdd = sc.pickleFile(filename).collect()
    predictions = spark.createDataFrame(pickleRdd)
    predictions.show(10, False)
    
    # 3. Load and predict
    # transform into id array. ie ["milk"] -> [12]
    input_ids = []
    for ingredient in ingredient_input:
      result_row = ingredients_mapping.filter(ingredients_mapping.single_ingredient == ingredient).collect()
      if len(result_row) == 0: # ignore ingredient if not in our known list
        continue
      input_ids.append(result_row[0]["id"])

    # transform into feature vector and make prediction. ie [12] -> [0.0 ... 1.0 ...]
    def get_feature_vector(member_list):
      result = [0.0 for i in range(ingredients_mapping.count() + 1)]
      for member in member_list:
        result[member] = 1.0
      return result
    get_feature_vector_udf = udf(get_feature_vector,ArrayType(FloatType(), containsNull=False))

    input_feature_vector = get_feature_vector(input_ids)
    predicted_cluster = model.predict(Vectors.dense(input_feature_vector))
    print(input_ids)
    print("predicted cluster: " + str(predicted_cluster))

    def ingredients_to_jaccard(ingredients):
      A = set(ingredients)
      B = set(input_ids)
      numerator = A.intersection(B)
      denominator = A.union(B)
      similarity = len(numerator) / len(denominator)
      return similarity
    ingredients_to_jaccard_udf = udf(ingredients_to_jaccard, FloatType())

    def feature_to_distance(point):
      ans = Vectors.dense(point).squared_distance(Vectors.dense(input_feature_vector))
      return float(ans)
    feature_to_distance_udf = udf(feature_to_distance, FloatType())

    top_3 = predictions.filter(predictions.prediction == predicted_cluster)
    top_3 = top_3.withColumn('jacc_similarity',ingredients_to_jaccard_udf(col('ingredients')))
    top_3 = top_3.withColumn('distance',feature_to_distance_udf(col('features')))
    top_3 = top_3.orderBy(col('jacc_similarity').desc(), col('distance').asc())
    top_3 = top_3.select('nameAndLink', 'ingredients', 'jacc_similarity', 'distance')
    top_3.show(20, False)
    top_3 = top_3.take(3)

    top_3_arr = []
    for recipe in top_3:
      recipe_dict = {"nameAndLink": recipe.nameAndLink}
      result_row = ingredient_agg.filter(ingredient_agg.nameAndLink == recipe.nameAndLink).collect()
      recipe_dict["ingredients"] = result_row[0]["ingredients"]
      top_3_arr.append(recipe_dict)

    return top_3_arr