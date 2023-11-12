import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from sqlite3 import Error
import sqlite3 as sql
import sys

st.markdown("# Hoya 1 - Capstone")

text_input = st.text_input("URL for grant application:")

powerbi = "https://app.powerbi.com/view?r=eyJrIjoiYzkyNGUyYmItNjFjNi00Njg1LThmNjgtNTNiMWNmN2QwZWQyIiwidCI6ImZkNTcxMTkzLTM4Y2ItNDM3Yi1iYjU1LTYwZjI4ZDY3YjY0MyIsImMiOjF9"
components.iframe(powerbi, width=900, height=600)

