from bs4 import BeautifulSoup
import pandas as pd
import pathlib
import re
import requests
import sqlite3 as sql
from sqlite3 import Error
import sys
import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

def create_connection(db_file):
    """
    Create databse connection to a SQLite database
    Returns connection status
    """
    
    conn = None
    try:
        conn = sql.connect(db_file)
    except Error as e:
        print(e)

    return conn

def top_words(description):
    
    default_stop_words = list(CountVectorizer(stop_words="english").get_stop_words())
    
    # Add custom stop words
    custom_stop_words = ["research","funding","selec","american","attitudes","changes","nih", "use", "program", "programs", "award", "application", "interventions", "data", "census", "acs","survey", "annual", "estimates","year","2010"]  # Add your own words here
    all_stop_words = default_stop_words + custom_stop_words
    
    # Initialize the CountVectorizer
    vectorizer = CountVectorizer(stop_words=all_stop_words)

    # Fit and transform the data
    X = vectorizer.fit_transform([description])
    
    # Summing the occurrences of each word
    word_counts = X.sum(axis=0)
    
    # Get the feature names
    words = vectorizer.get_feature_names_out()
    
    # Combine words with their counts
    word_counts = list(zip(words, word_counts.flat))
    
    # Sort words by counts in descending order
    word_counts.sort(key=lambda x: x[1], reverse=True)
        
    # Get top 3 words
    words = [word for word, count in word_counts[:3]]
    
    # If there are less than 3 words, fill the list with 'N/A'
    words += ['N/A'] * (3 - len(words))
    
    return words

def main():
	# Create database
	database = "census_archive.db"
	conn = create_connection(database)

	url = "https://api.census.gov/data/2019.json"  
	response = requests.get(url)

	# Read data from census archive
	if response.status_code == 200:
	    # Parse the JSON content from the response
	    json_data = json.loads(response.text)
	else:
	    print(f"Failed to retrieve data. Status code: {response.status_code}")

    # Create dataframe for all relevant info from census archive
	columns = ['table_index', 'title', 'year', 'description', 'variable_link', 'is_microdata', 'top_words', 'access_url']
	df = pd.DataFrame(columns=columns)

	# Cast coltype to bool
	df['is_microdata'] = df['is_microdata'].astype(bool)

	table_index = 1
	for sd in json_data['dataset']:
		title = sd.get('title')
		year = sd.get('c_vintage')
		description = sd.get('description')
		variables_link = sd.get('c_variablesLink')
		is_microdata = sd.get('c_isMicrodata', False)
		desc_top_words = " ".join(top_words(description))
		access_url = sd['distribution'][0]['accessURL']

		row2 = [table_index, title, year, description, variables_link, is_microdata, desc_top_words, access_url]
		df = pd.concat([df, pd.DataFrame([row2], columns=columns)], ignore_index=True)
		table_index += 1
	    
	columns_vars = ['table_index', 'variable_name', 'variable_desc']
	df2 = pd.DataFrame(columns=columns_vars)

	# Iterate through all the grants and get a list of variables to store in the variable table
	for index, row in df.iterrows():
		is_microdata = row['is_microdata']

        # We don't want to load the variables for microdata tables because there are too many
		if not is_microdata:
			vars_link = row['variable_link']
			response_vars = requests.get(vars_link)

			if response_vars.status_code == 200:
				# Parse the JSON content from the response
				json_vars = json.loads(response_vars.text)
				for key in json_vars['variables']:
					vars_row = [row['table_index'], key, json_vars['variables'][key]['label']]
					df2 = pd.concat([df2, pd.DataFrame([vars_row], columns=columns_vars)], ignore_index=True)

	# Write data to sql database
	df.to_sql('census', conn, if_exists='replace',index=False)
	df2.to_sql('variables', conn, if_exists='replace',index=False)



if __name__ == '__main__':
    main()
    

