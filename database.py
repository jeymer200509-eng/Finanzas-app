import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Inicializar conexión a Supabase usando los secretos de Streamlit
@st.cache_resource
def init_db() -> Client:
    url = st.secrets["supabase"]["URL"]
    key = st.secrets["supabase"]["KEY"]
    return create_client(url, key)

supabase = init_db()

def add_transaction(date, amount, category, t_type):
    # La API de Supabase requiere un diccionario con los nombres de las columnas
    data = {
        "date": date,
        "amount": amount,
        "category": category,
        "type": t_type
    }
    supabase.table("transactions").insert(data).execute()

def get_all_transactions():
    response = supabase.table("transactions").select("*").execute()
    data = response.data
    
    if data:
        df = pd.DataFrame(data)
        return df
    else:
        # Retorna un DataFrame vacío con las columnas esperadas en caso de no haber datos en la nube
        return pd.DataFrame(columns=['id', 'date', 'amount', 'category', 'type'])

def delete_transaction(transaction_id):
    supabase.table("transactions").delete().eq("id", transaction_id).execute()
