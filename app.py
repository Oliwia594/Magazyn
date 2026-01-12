import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Najlepiej ustawić te dane w "Secrets" na Streamlit Cloud lub GitHubie
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 System Zarządzania Magazynem")

# --- SEKCJA: DODAWANIE KATEGORII ---
st.header("Dodaj nową kategorię")
with st.form("form_kategoria", clear_on_submit=True):
    kod_kat = st.text_input("Kod kategorii (np. ELE-01)")
    nazwa_kat = st.text_input("Nazwa kategorii")
    opis_kat = st.text_area("Opis")
    
    submit_kat = st.form_submit_button("Zapisz kategorię")
    
    if submit_kat:
        data = {"kod": kod_kat, "nazwa": nazwa_kat, "opis": opis_kat}
        response = supabase.table("kategoria").insert(data).execute()
        st.success(f"Dodano kategorię: {nazwa_kat}")

st.divider()

# --- SEKCJA: DODAWANIE PRODUKTU ---
st.header("Dodaj nowy produkt")

# Pobieranie kategorii do listy rozwijanej
kategorie_data = supabase.table("kategoria").select("id, nazwa").execute()
opcje_kategorii = {item['nazwa']: item['id'] for item in kategorie_data.data}

with st.form("form_produkt", clear_on_submit=True):
    nazwa_prod = st.text_input("Nazwa produktu")
    liczba_prod = st.number_input("Liczba (ilość)", min_value=0, step=1)
    cena_prod = st.number_input("Cena", min_value=0.0, format="%.2f")
    wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(opcje_kategorii.keys()))
    
    submit_prod = st.form_submit_button("Dodaj produkt do magazynu")
    
    if submit_prod:
        produkt = {
            "nazwa": nazwa_prod,
            "liczba": liczba_prod,
            "cena": cena_prod,
            "kategoria": opcje_kategorii[wybrana_kat_nazwa]
        }
        supabase.table("Produkt").insert(produkt).execute()
        st.success(f"Produkt {nazwa_prod} został dodany!")
