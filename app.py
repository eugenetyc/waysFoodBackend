from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
model = None

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

    report = initialize_report()

    model_results = predict(user_input) # model.predict(user_input)
    print("model_output: ")
    for res in model_results:
        print(res)

    report = populate_report(report, model_results, user_input)
    print("----------REQ END-----------")

    return jsonify(report)

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
    result = []

    recipe1 = {
        'nameAndLink': "Bacon Cheeseburger,cheeseburger.com",
        'ingredients': ["bread", "cheese", "beef", "bacon", "mustard", "ketchup", "tomato", "onion"]
    }
    recipe2 = {
        'nameAndLink': "Bacon Sandwich,sandwichland.com/bacon",
        'ingredients': ["bread", "bacon", "tomato", "sweet", "chilli", "mayonnaise"]
    }
    recipe3 = {
        'nameAndLink': "Candied Bacon,candiesgalore.net/savoury",
        'ingredients': ["sugar", "bacon", "oil", "mint"]
    }

    result.append(recipe1)
    result.append(recipe2)
    result.append(recipe3)

    return result