import string
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import pickle

# import findspark
# findspark.init()

from pyspark.context import SparkContext
from recipe_predictor import RecipePredictor

"""
nltk required as a dependency
workaround try-except needed to setup lemmatizer and avoid errors
"""
import nltk
nltk.download('omw-1.4')
from pattern import en
try:
  en.lemma("workaround")
except:
  pass

"""
Actual backend application starts below
"""

app = Flask(__name__)
CORS(app)
model = None
sc = SparkContext.getOrCreate() 

@app.route('/', methods=["GET"])
def hello_world():
    return 'The service is up and running!'


@app.route('/', methods=["POST"])
def basic_check():

    # read in input, should just be 'ingredients',
    # which is an array of Strings
    input_json = request.get_json(force=True)
    print("----------REQ START---------")
    print("input received: ")
    print(input_json)
    print("------------------------")
    user_input = input_json['ingredients']
    user_input_processed = clean_user_input(user_input)

    report = initialize_report()

    model_results = predict(user_input_processed) # model.predict(user_input_processed)
    print("model_output: ")
    for res in model_results:
        print(res)

    report = populate_report(report, model_results, user_input_processed)
    print("----------REQ END-----------")

    return jsonify(report)

def clean_user_input(user_input):
    """
    Cleans the user input to follow the same as the model.
    1. Remove whitespaces (trailing/leading)
    2. Remove punctuations
    3. Casefold to lowercase
    4. Lemmatize via en.lemma(word)
    5. Filter check for consistency with model and to reduce dimensions
    :param user_input: the array of strings to clean
    :return: the cleaned array of strings
    """
    print("cleaning started")
    result = []
    for input in user_input:
        splitted_inputs = input.split()
        for splitted_input in splitted_inputs:
            current_string = splitted_input.strip()
            current_string = current_string.translate(str.maketrans('', '', string.punctuation)).lower()
            current_string = en.lemma(current_string)
            if all(x.isalpha() or x.isspace() for x in current_string) and len(current_string) > 1 and not current_string.isspace():
                result.append(current_string)
    print("cleaning results: " + str(result))
    print("cleaning ended")
    return result

def populate_report(report, model_results, user_input):
    """
    Fills up the report response with the results from the model
    :param report: the skeleton json response
    :param model_results: the content to fill up in the json
    :param user_input: the list of ingredients from the user
    :return: the json response filled up with the content

    Note that model_results is [ {nameAndLink: String, ingredients: String[]} ]
    """

    for recipe in model_results:

        current_recipe_result = {}

        try:
            recipe_name_and_Link = recipe['nameAndLink'].split(",")
            recipe_name = recipe_name_and_Link[0]
            recipe_link = recipe_name_and_Link[1]
        except:
            recipe_name = recipe['nameAndLink'] # preserve as much data as possible
            recipe_link = recipe['nameAndLink'] # preserve as much data as possible

        recipe_ingredients = recipe['ingredients']
        matching = find_matching(recipe_ingredients, user_input)
        missing = find_difference_A_minus_B(recipe_ingredients, user_input)
        additional = find_difference_A_minus_B(user_input, recipe_ingredients)

        current_recipe_result["name"] = recipe_name
        current_recipe_result["link"] = recipe_link
        current_recipe_result["matching"] = matching
        current_recipe_result["missing"] = missing
        current_recipe_result["additional"] = additional

        report['recipes'].append(current_recipe_result)

    return report

def initialize_report():
    # note that 'recipes' is a length 3 array of recipe objects
    # recipe object is as follows (5 members):
    # {name: String, link: String, matching: String[], missing: String[], additional: String[]}
    report = {
        'recipes': [],
        'created_at': datetime.datetime.now().replace(microsecond=0).isoformat()
    }
    return report

def find_matching(recipe_ingredients, user_ingredients):
    """
    Finds the intersection of the 2 list inputs
    :param recipe_ingredients: the first list of Strings
    :param user_ingredients: the second list of Strings
    :return: the common elements in both lists
    """
    return list(set(recipe_ingredients).intersection(user_ingredients))

def find_difference_A_minus_B(A, B):
    """
    Finds the elements in A which do not appear in B.
    Note that B can have elements that do not exist in A,
    but these will not appear in the final result.
    :param A: the base list to remove elements from
    :param B: the list of elements to remove
    :return: the remaining elements of A which do not appear in B
    """
    return list(set(A)-set(B))

def predict(user_input):

    """
    Dummy data generator; can ignore if unneeded
    """
    # pickle_file = open('predictor', 'rb')
    # predictor = pickle.load(pickle_file)
    # pickle_file.close()
    predictor = RecipePredictor()
    ingredient_input = ["milk", "sugar", "salt", "weewoo"]
    res = predictor.get_top_3_recipes(sc, ingredient_input)
    print(*res, sep='\n')

    return res