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
    ### LDA to get the topic of the grant

    # Create vectorizer
    custom_sw = ["research", "funding", "data", "study"]
    nltk.download('stopwords')
    sw = stopwords.words("english") + custom_sw
    vec = CountVectorizer(stop_words = sw)

    # Create document-term matrix
    fit_X = vec.fit_transform([grant_text])

    # Create lda
    # Since there is only one document here, there is only 1 topic. We will update this when we have more docs to read in.
    lda = LatentDirichletAllocation(n_components = 1, random_state = 678)

    # Fit lda
    doc_topics = lda.fit_transform(fit_X)
    
    ### Extract top words from the topic

    # Get feature names (vocabulary)
    voc = np.array(vec.get_feature_names_out())

    # Set number of top words you want
    n_words = 5

    # Extract top words from voc
    imp_words = lambda x: [voc[each] for each in np.argsort(x)[:-n_words-1:-1]]

    # Use important words to extract words with the highest weights from the lda model
    words_in_topic = ([imp_words(x) for x in lda.components_])

    return words_in_topic[0]

def get_datalink_acs(identifier, group_name, state):
    if group_name.startswith("S"):
        identifier_clean = identifier[identifier.rfind('/')+1:].replace("ACSSPP1Y", "ACSST1Y")
    elif group_name.startswith("DP"):
        identifier_clean = identifier[identifier.rfind('/')+1:].replace("ACSST1Y", "ACSDP1Y")

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



def main():
    st.markdown("# Grant Application Data Matching")

    link = st.text_input("URL for grant application:")

    state = st.selectbox(label="Retrieve data for state:", options=(list(StateCodes.states_dict.keys())))

    if st.button('Find Data'):
        if not link:
            st.markdown("Please enter a grant url")

        # Create db connection
        database = "census_archive.db"
        conn = create_connection(database)

        # Extract relevant text from provided grant url
        text = read_text(link)

        if not text:
            return

        # Use LDA to get top words of the grant
        top_words = get_top_words(text)
        
        # Create query to return relevant tables
        sql_query = "select distinct table_index, title, is_microdata, variable_link, access_url, identifier from census where is_microdata = 0 and ("
        for word in top_words:
            sql_query += f" title like '%{word}%' or top_words like '%{word}%' or "

        sql_query = sql_query[:-3] + ") limit 5"

        # Use query to get relevant tables from census_archive database table
        relevant_tables = pd.read_sql(sql_query, conn)

        for index, row in relevant_tables.iterrows():
            
            #expander = st.expander(f"[{row['title']}]({api})")
            expander = st.expander(f"{row['title']}")

            group_query = f"""select table_index, group_name, group_desc from groups 
                            where table_index = {row['table_index']} 
                            and group_name not like '%PR'
                            limit 10"""
            table_groups = pd.read_sql(group_query, conn)

            if row['is_microdata'] == 1:
                identifier = row['identifier']
                datalink = f"https://data.census.gov/mdat/#/search?ds={identifier[identifier.rfind('/')+1:]}"
                expander.write(f"[{group_row['group_desc']}]({datalink})")
                continue

            for group_index, group_row in table_groups.iterrows():

                if "/acs/" in row['access_url']:
                    datalink = get_datalink_acs(row['identifier'], group_row['group_name'], StateCodes.states_dict[state])
                    expander.write(f"[{group_row['group_desc']}]({datalink})")
                elif "/absnesd" in row['access_url'] or \
                    "/cre" in row['access_url']:
                    datalink = get_datalink(row['identifier'], group_row['group_name'], StateCodes.states_dict[state])
                    expander.write(f"[{group_row['group_desc']}]({datalink})")
                else:
                    expander.write(f"{group_row['group_name']}")

        # Should we do a matching score??
    st.markdown("# Learn More About Grants")
    powerbi = "https://app.powerbi.com/view?r=eyJrIjoiYWJkNDEzYjctNjJiZC00NmZmLTg1ZmItZDA4MWI1NjViYmI2IiwidCI6ImZkNTcxMTkzLTM4Y2ItNDM3Yi1iYjU1LTYwZjI4ZDY3YjY0MyIsImMiOjF9"
    components.iframe(powerbi, width=900, height=600)

    

if __name__ == '__main__':
    main()
