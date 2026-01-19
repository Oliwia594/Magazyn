import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# Ustawienia strony
st.set_page_config(page_title="Magazyn Inteligenty v2", layout="wide", page_icon="🏢")

# Połączenie z Supabase
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd połączenia z Supabase. Sprawdź plik .secrets.")
        return None

supabase = init_connection()

# --- FUNKCJE DANYCH ---
def get_products():
    res = supabase.table("Produkt").select("*").execute()
    return pd.DataFrame(res.data)

def get_categories():
    res = supabase.table("kategoria").select("*").execute()
    return pd.DataFrame(res.data)

# --- PANEL BOCZNY ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2271/2271068.png", width=100)
    st.title("Menu Magazynu")
    choice = st.radio("Nawigacja", ["📈 Analiza i Statystyki", "📥 Operacje Wejścia", "🔍 Przegląd i Stan"])
    st.info("System połączony z bazą Supabase ✅")

# --- WIDOK 1: ANALIZA I STATYSTYKI ---
if choice == "📈 Analiza i Statystyki":
    st.title("📊 Inteligentne Statystyki")
    df_p = get_products()
    df_k = get_categories()

    if not df_p.empty and not df_k.empty:
        # Łączenie tabel dla lepszych statystyk
        df = df_p.merge(df_k, left_on="kategoria", right_on="id", suffixes=('_prod', '_kat'))
        df['wartosc_calkowita'] = df['liczba'] * df['cena']
        
        m1, m2, m3, m4 = st.columns(4
