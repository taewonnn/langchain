import os
import time
import pandas as pd
from pprint import pprint
import streamlit as st
from dotenv import load_dotenv

# import
from functions.run_query import run_query


st.title("ADN QnA Test")
query = st.text_input('query 입력')

if query:
    try:
        result = run_query(query)
        st.write('결과', result)
    except Exception as e:
        st.error(f"Error : {e}")



