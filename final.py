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

# powerbi = "https://app.powerbi.com/view?r=eyJrIjoiYzA2OGVmZWUtY2U4Ny00MWUzLWEyOTMtMmUyZDgxYTExYmExIiwidCI6ImZkNTcxMTkzLTM4Y2ItNDM3Yi1iYjU1LTYwZjI4ZDY3YjY0MyIsImMiOjF9"
# components.iframe(powerbi, width=900, height=600)

# Open up connection to database
database = "capstone.db"
conn = create_connection(database)

data = {'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 22],
        'City': ['New York', 'San Francisco', 'Los Angeles']}

df = pd.DataFrame(data)

df.to_sql('data', conn, if_exists='replace',index=False)

df2 = sql_to_dataframe(conn, "select * from data")
st.markdown(df2.shape)

str = ""
for index, row in df2.iterrows():
    str += f"Index: {index}, Name: {row['Name']}, Age: {row['Age']}, City: {row['City']}"
    str += "\n\r\n"

st.markdown(str)

