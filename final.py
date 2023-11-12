import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from sqlite3 import Error
import sqlite3 as sql
import sys


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

def write_grants_database(conn, xml_string):
    """
    Load grants data and store in SQLite database of conn
    """

    # Read grants data
    grants = grants_xml_to_df(xml_string) 

    # Write data to sql table called grants
    # if_exists='replace': Drop the table before inserting new values.
    # index=False: Don't Write DataFrame index as a column, we already have OpportunityID as unique identifier (I think it's unique?)
    grants.to_sql('grants', conn, if_exists='replace',index=False)

def sql_to_dataframe(conn, sql):
    """
    Returns sql query data as pandas dataframe
    """
    
    return pd.read_sql(sql, conn)

st.markdown("# Hoya 1 - Capstone")

text_input = st.text_input("URL for grant application:")

powerbi = "https://app.powerbi.com/view?r=eyJrIjoiYzkyNGUyYmItNjFjNi00Njg1LThmNjgtNTNiMWNmN2QwZWQyIiwidCI6ImZkNTcxMTkzLTM4Y2ItNDM3Yi1iYjU1LTYwZjI4ZDY3YjY0MyIsImMiOjF9"
components.iframe(powerbi, width=900, height=600)



