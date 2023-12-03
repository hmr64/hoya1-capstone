import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from sqlite3 import Error
import sqlite3 as sql
import sys
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
from nltk.corpus import stopwords
import numpy as np
import requests
import json
import time

from FileReader.BjaGrantReader import BjaGrantReader
from FileReader.NihGrantReader import NihGrantReader
from FileReader.BasePdfReader import BasePdfReader
from FileReader.BaseHtmlReader import BaseHtmlReader
from FileReader.BaseHtmlReader import BaseHtmlReader
import StateCodes


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

def read_text(link):
    reader = None
    if 'bja.ojp.gov' in link:
        reader = BjaGrantReader(link)
    elif 'grants.nih.gov' in link:
        reader = NihGrantReader(link)
    elif link.endswith('pdf'):
        reader = BasePdfReader(link)
    elif link.endswith('html'):
        reader = BaseHtmlReader(link)

    if not reader or not reader.url:
        return ""

    # Extract sentences from the grant
    return reader.extract_text(False)

def get_top_words(grant_text):

    # Create vectorizer
    custom_sw = ["research", "funding", "data", "study", "use"]
    nltk.download('stopwords')
    sw = stopwords.words("english") + custom_sw
    vec = CountVectorizer(stop_words = sw)

    # Fit and transform the data
    X = vec.fit_transform([grant_text])
    
    # Summing the occurrences of each word
    word_counts = X.sum(axis=0)
    
    # Get the feature names
    words = vec.get_feature_names_out()
    
    # Combine words with their counts
    word_counts = list(zip(words, word_counts.flat))
    
    # Sort words by counts in descending order
    word_counts.sort(key=lambda x: x[1], reverse=True)

    # Select number of words we want
    num_words = 5
        
    # Get top n words
    words = [word for word, count in word_counts[:num_words]]
    
    return words

def get_datalink_acs(identifier, group_name, state):
    if group_name.startswith("S"):
        identifier_clean = identifier[identifier.rfind('/')+1:].replace("ACSSPP1Y", "ACSST1Y")
    elif group_name.startswith("DP"):
        identifier_clean = identifier[identifier.rfind('/')+1:].replace("ACSST1Y", "ACSDP1Y")
    else:
        identifier_clean = identifier[identifier.rfind('/')+1:]

    datalink = f"https://data.census.gov/table/{identifier_clean}.{group_name}"
    
    if state != "00":
        datalink += f"?g=040XX00US{state}"

    return datalink

def get_datalink(identifier, group_name, state):
    identifier_clean = identifier[identifier.rfind('/')+1:]
    datalink = f"https://data.census.gov/table/{identifier_clean}.{group_name}"
    
    if state != "00":
        datalink += f"?g=040XX00US{state}"

    return datalink

def get_matched_words(dataset_top_words, dataset_title, grant_top_words):
    top_words_dataset = dataset_top_words.split() + dataset_title.lower().split()
    matched_words = list(set(grant_top_words).intersection(top_words_dataset))
    return ', '.join(matched_words)

def load_dataset_expanders(conn, relevant_tables, top_words, state):

    for index, row in relevant_tables.iterrows():
        
        expander = st.expander(f"{row['year']}: {row['title']}")

        sql_group_matches = ""
        for word in top_words:
            sql_group_matches += f" group_desc like '%{word}%' or "

        group_query = f"""select table_index, group_name, group_desc from groups 
                        where table_index = {row['table_index']} 
                        and group_name not like '%PR'
                        and ({sql_group_matches[:-3]}) 
                        limit 10"""
        table_groups_match = pd.read_sql(group_query, conn)

        group_query = f"""select table_index, group_name, group_desc from groups 
                        where table_index = {row['table_index']} 
                        and group_name not like '%PR'
                        limit {10 - table_groups_match.shape[0]}"""
        table_groups_filler = pd.read_sql(group_query, conn)

        table_groups = pd.concat([table_groups_match, table_groups_filler], ignore_index=True, axis=0)
        table_groups = table_groups.drop_duplicates()

        if row['is_microdata'] == 1:
            identifier = row['identifier']
            datalink = f"https://data.census.gov/mdat/#/search?ds={identifier[identifier.rfind('/')+1:]}"

            selected_state = StateCodes.states_dict[state]
            if selected_state != "00":
                datalink += f"&rv=ucgid&g=0400000US{selected_state}"

            expander.write(f"[{row['year']}- {row['title']}]({datalink})")
            matches = get_matched_words(row['top_words'], row["title"], top_words)
            if len(matches) > 0:
                expander.write(f"Matched words: {matches}")
            continue

        for group_index, group_row in table_groups.iterrows():

            if "/acs/" in row['access_url']:
                datalink = get_datalink_acs(row['identifier'], group_row['group_name'], StateCodes.states_dict[state])
                expander.write(f"[{group_row['group_desc']}]({datalink})")
            elif "/absnesd" in row['access_url'] or \
                "/cre" in row['access_url'] or \
                "/pep/population" in row['access_url'] or \
                "/nonemp" in row['access_url']:
                datalink = get_datalink(row['identifier'], group_row['group_name'], StateCodes.states_dict[state])
                expander.write(f"[{group_row['group_desc']}]({datalink})")
            else:
                expander.write(f"{group_row['group_name']}")

        if table_groups.shape[0] == 10:
            expander.write(f"See all tables: {row['groups_link']}")

        if table_groups.shape[0] > 0:
            #expander.write(f"Top words grant: {top_words}")
            #expander.write(f"Top words dataset: {top_words_dataset}")
            matches = get_matched_words(row['top_words'], row["title"], top_words)
            if len(matches) > 0:
                expander.write(f"Matched words: {matches}")

    return relevant_tables.shape[0]


def perform_matching(link, state):
    if not link:
        st.error('Please enter a link to the grant application')
        return

    # Create db connection
    database = "census_archive.db"
    conn = create_connection(database)

    # Extract relevant text from provided grant url
    text = read_text(link)

    if not text:
        st.error('Unable to read grant text, please verify format is .pdf or .html')
        return

    # Get top words of the grant
    top_words = get_top_words(text)

    sql_matches = ""
    for word in top_words:
            sql_matches += f" title like '%{word}%' or top_words like '%{word}%' or "

    sql_query = f"""select distinct table_index, title, year, is_microdata, access_url, identifier, top_words, groups_link  
                from census 
                where ({sql_matches[:-3]}) 
                and title not like '%Puerto Rico%'
                order by year desc"""

    relevant_tables = pd.read_sql(sql_query, conn)
    df_no_duplicates = relevant_tables.drop_duplicates(subset='title', keep='first')

    num_datasets = load_dataset_expanders(conn, df_no_duplicates.head(15), top_words, state)

    # If we can't find any matching census datasets, display generic ones
    if num_datasets == 0:
        st.warning('No matching datasets found, please explore these common tables')
        sql_query = f"""select distinct table_index, title, year, is_microdata, access_url, identifier, top_words, groups_link 
                from census 
                where (title = 'American Community Survey: 1-Year Estimates: Detailed Tables 1-Year' 
                or title = 'Population Estimates: Population Estimates' 
                or title = 'Current Population Survey: Basic Monthly')
                order by year desc"""

        standard_tables = pd.read_sql(sql_query, conn)
        df_no_duplicates = standard_tables.drop_duplicates(subset='title', keep='first')
        load_dataset_expanders(conn, df_no_duplicates, top_words, state)



def main():
    st.markdown("# Grant Application Data Matching")

    link = st.text_input("URL for grant application:")

    state = st.selectbox(label="Filter data for state:", options=(list(StateCodes.states_dict.keys())))

    if st.button('Find Data'):
        perform_matching(link, state)
        
    st.markdown("## Learn More About Grants")
    powerbi = "https://app.powerbi.com/view?r=eyJrIjoiYzJkZDJiOGQtMjFmNS00MTBjLThjODgtOGMzMzI2OTU3Mjg5IiwidCI6ImZkNTcxMTkzLTM4Y2ItNDM3Yi1iYjU1LTYwZjI4ZDY3YjY0MyIsImMiOjF9"
    components.iframe(powerbi, width=900, height=600)

    

if __name__ == '__main__':
    main()
