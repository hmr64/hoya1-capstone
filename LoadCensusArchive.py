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

	# url = "https://api.census.gov/data/2019.json"  
	# response = requests.get(url)

	# # Read data from census archive
	# if response.status_code == 200:
	#     # Parse the JSON content from the response
	#     json_data = json.loads(response.text)
	# else:
	#     print(f"Failed to retrieve data. Status code: {response.status_code}")

    # Create dataframe for all relevant info from census archive
	columns = ['table_index', 'title', 'year', 'description', 'groups_link', 'is_microdata', 'top_words', 'access_url', 'identifier']
	df = pd.DataFrame(columns=columns)

	# Cast coltype to bool
	df['is_microdata'] = df['is_microdata'].astype(bool)

	table_index = 1


	years = ['2019', '2020', '2021', '2022']
	for year in years:
		url = f"https://api.census.gov/data/{year}.json"  
		response = requests.get(url)

		# Read data from census archive
		if response.status_code == 200:
		    # Parse the JSON content from the response
		    json_data = json.loads(response.text)
		else:
		    print(f"Failed to retrieve data. Status code: {response.status_code}")
		    continue

		for sd in json_data['dataset']:
			title = sd.get('title')
			year = sd.get('c_vintage')
			description = sd.get('description')
			groups_link = sd.get('c_groupsLink')
			is_microdata = sd.get('c_isMicrodata', False)
			desc_top_words = " ".join(top_words(description))
			access_url = sd['distribution'][0]['accessURL']
			identifier = sd['identifier']

		    # For monthly surveys, only store december
			months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov']
			pattern_months = re.compile('|'.join(months), re.IGNORECASE)
			if "basic monthly" in title.lower() and pattern_months.search(groups_link):
				continue

			# Remove years from titles to help filter out duplicates
			pattern_years = re.compile('|'.join(map(re.escape, years)))
			title = pattern_years.sub('', title)

			row2 = [table_index, title, year, description, groups_link, is_microdata, desc_top_words, access_url, identifier]
			df = pd.concat([df, pd.DataFrame([row2], columns=columns)], ignore_index=True)
			table_index += 1


	### Create table to store groups for each dataset    
	columns_groups = ['table_index', 'group_name', 'group_desc']
	df3 = pd.DataFrame(columns=columns_groups)

	# Iterate through all the grants and get a list of groups to store in the groups table
	for index, row in df.iterrows():

		groups_link = row['groups_link']
		response_groups = requests.get(groups_link)

		if response_groups.status_code == 200:
			# Parse the JSON content from the response
			json_groups = json.loads(response_groups.text)
			for key in json_groups['groups']:
				groups_row = [row['table_index'], key['name'], key['description']]
				df3 = pd.concat([df3, pd.DataFrame([groups_row], columns=columns_groups)], ignore_index=True)


	# Write data to sql database
	df.to_sql('census', conn, if_exists='replace',index=False)
	df3.to_sql('groups', conn, if_exists='replace',index=False)



if __name__ == '__main__':
    main()
    

