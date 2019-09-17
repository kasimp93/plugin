# import the classes for accessing DSS objects from the recipe
import dataiku
from dataiku.customrecipe import *
from dataiku import pandasutils as pdu
import pandas as pd
import json
import time
import dataikuapi
from dataikuapi import JoinRecipeCreator
from dataiku import api_client as client
from dataiku.sql import Column, Constant, Expression, Interval, SelectQuery, Window, TimeUnit, JoinTypes, ColumnType, toSQL
from dataiku.core.sql import SQLExecutor2, HiveExecutor

# Inputs and outputs are defined by roles. In the recipe's I/O tab, the user can associate one
# or more dataset to each input and output role.
# Roles need to be defined in recipe.json, in the inputRoles and outputRoles fields.

# To  retrieve the datasets of an input role named 'input_A' as an array of dataset names:
input_A_names = get_input_names_for_role('input_A_role')
# The dataset objects themselves can then be created like this:
input_A_datasets = [dataiku.Dataset(name) for name in input_A_names]
input_B_names = get_input_names_for_role('input_B_role')
input_B_datasets = [dataiku.Dataset(name) for name in input_B_names]


# For outputs, the process is the same:
output_A_names = get_output_names_for_role('left_output')
output_A_datasets = [dataiku.Dataset(name) for name in output_A_names]
output_B_names = get_output_names_for_role('right_output')
output_B_datasets = [dataiku.Dataset(name) for name in output_B_names]

output_C_names = get_output_names_for_role('inner_output')
output_C_datasets = [dataiku.Dataset(name) for name in output_C_names]

# The configuration consists of the parameters set up by the user in the recipe Settings tab.

# Parameters must be added to the recipe.json file so that DSS can prompt the user for values in
# the Settings tab of the recipe. The field "params" holds a list of all the params for wich the
# user will be prompted for values.

# The configuration is simply a map of parameters, and retrieving the value of one of them is simply:
#my_variable = get_recipe_config()['parameter_name']
key_a = get_recipe_config()['key_1']
key_b = get_recipe_config()['key_2']
operator = get_recipe_config()['operator']

columns_left = get_recipe_config()['columns_1']
columns_right = get_recipe_config()['columns_2']
# For optional parameters, you should provide a default value in case the parameter is not present:
#my_variable = get_recipe_config().get('parameter_name', None)

# Note about typing:
# The configuration of the recipe is passed through a JSON object
# As such, INT parameters of the recipe are received in the get_recipe_config() dict as a Python float.
# If you absolutely require a Python int, use int(get_recipe_config()["my_int_param"])


#############################
# Your original recipe
#############################

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: MARKDOWN
# ## DS Pluginathon - Create an advanced join plugin
# 
# ### Objectives
# 
# The goals is to take two datasets in input and output three different datasets:
# 
# - The result of the inner join
# - The rows that were present only on the left
# - The rows that were present only on the right

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE


####################################
####################################
####################################
#define the connection and put it as parameter 
# -------------------------------------------------------------------------------- NOTEBOOK-CELL: MARKDOWN

#Start the loop
joins = ['LEFT', 'RIGHT', 'INNER']
join_conds = []

for key in range(len(key_a)):
    join_cond = Expression()
    globals()['join_cond_'+str(key)] = join_cond.and_(Column(key_a[key], input_A_names[0]).eq_null_unsafe(Column(key_b[key], input_B_names[0])))
    join_conds.append(globals()['join_cond_'+str(key)])  
    
for i in joins:
    query = SelectQuery()
    query.select_from(input_A_datasets[0], alias = input_A_names[0])
    for j in columns_left:
        query.select(Column(j, input_A_names[0]),alias = j)
    for k in columns_right:
        query.select(Column(k, input_B_names[0]),alias = k) 
    query.join(input_B_datasets[0], i, join_conds, operatorBetweenConditions = operator , alias= input_B_names[0])
    globals()['sql_'+str(i)] = toSQL(query, input_A_datasets[0])


e = SQLExecutor2()
e.exec_recipe_fragment(output_A_datasets[0], sql_LEFT)
e.exec_recipe_fragment(output_B_datasets[0], sql_RIGHT)
e.exec_recipe_fragment(output_C_datasets[0], sql_INNER)