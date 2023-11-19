import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from sqlite3 import Error
import sqlite3 as sql
import sys
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from nltk.corpus import stopwords
import numpy as np

from FileReader.BjaGrantReader import BjaGrantReader
from FileReader.NihGrantReader import NihGrantReader
from FileReader.BasePdfReader import BasePdfReader
from FileReader.BaseHtmlReader import BaseHtmlReader
from FileReader.BaseHtmlReader import BaseHtmlReader

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
    n_words = 3

    # Extract top words from voc
    imp_words = lambda x: [voc[each] for each in np.argsort(x)[:-n_words-1:-1]]

    # Use important words to extract words with the highest weights from the lda model
    words_in_topic = ([imp_words(x) for x in lda.components_])

    return words_in_topic[0]


def main():
    st.markdown("# Hoya 1 - Capstone")

    link = st.text_input("URL for grant application:")

    grants_link = 'https://api.census.gov/data/2019.html'

    if st.button('Find Data'):
        # Extract relevant text from provided grant url
        text = read_text(link)

        # Use LDA to get top words of the grant
        top_words = get_top_words(text)
        
        f'Top words in grant={top_words}'

    if st.toggle('View Dashboard'):
        powerbi = "https://app.powerbi.com/view?r=eyJrIjoiYWU3NTY5NjAtMWEzYi00Y2MzLWJlMzMtMjFlOGVkMDE2YTU2IiwidCI6ImZkNTcxMTkzLTM4Y2ItNDM3Yi1iYjU1LTYwZjI4ZDY3YjY0MyIsImMiOjF9"
        components.iframe(powerbi, width=900, height=600)

    

if __name__ == '__main__':
    main()