# Required libraries
pip install flask

# Setup Instructions

## Use of virtual environments
- Remember to use virtualenv or conda environment # see below
- Remember to activate the environment # see below
- Set the following environment variables (in command line / terminal) so that the environment can detect and run flask properly
    > set FLASK_APP=app.py  
  
    > set FLASK_ENV=development  
  
    > flask run  
  
    > note that you can use control-c to stop the server
- If you run into any issues (e.g. entered command line command(s) but only shown a blank line and awaits next command)
you'll most likely need to set the environmental variables again (i.e. run all 3 commands after activating environment)
- After you "run flask", any changes are automatically effected, allowing us to interactively test (e.g. via Postman)
- In Postman, use Body > Raw > { 'ingredients': ["bacon", "cheese"] } as an example for sending POST data to the endpoint

### Some possible commands you may find useful
"virtualenv ." --> activate; "deactivate" --> deactivate to exit environment once done
OR (if you use conda) "conda activate"
flask run