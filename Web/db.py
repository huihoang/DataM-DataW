import psycopg2
import pandas as pd
import streamlit as st

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="fraud_detection_dw",
        user="dwuser",
        password="123456"
    )

@st.cache_data
def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)
