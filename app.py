import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# Konfiguracja strony
st.set_page_config(page_title="Magazyn Pro", layout="wide")

# Połączenie z Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNKCJE POMOCNICZE ---
def get_data(table_name):
    res = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(res.data)

# --- SIDEBAR / NAWIGACJA ---
st.sidebar.title("🎮 Panel Sterowania")
page = st.sidebar.radio("Przejdź do:", ["Dashboard i Wykresy", "Dodaj Produkty/Kategorie", "Zarządzaj Bazą"])

# --- WIDOK 1: DASHBOARD ---
if page == "Dashboard i Wykresy":
    st.title("📊 Analityka Magazynu")
    
    # Pobieranie danych
    df_prod = get_data("Produkt")
    df_kat = get_data("kategoria")
    
    if not df_prod.empty:
        # Połączenie danych (Merge), aby mieć nazwy kategorii zamiast ID
        df_full = df_prod.merge(df_kat, left_on="kategoria", right_on="id", suffixes=('_prod', '_kat'))
        
        # Wskaźniki KPI
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Łączna liczba produktów", int(df_full["liczba"].sum()))
        with col2:
            wartosc_magazynu = (df_full["liczba"] * df_full["cena"]).sum()
            st.metric("Wartość magazynu", f"{wartosc_magazynu:,.2f} PLN")
        with col3:
            st.metric("Liczba kategorii", len(df_kat))

        st.divider()

        # WYKRESY
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Ilość produktów w kategoriach")
            fig_bar = px.bar(df_full, x="nazwa_kat", y="liczba", color="nazwa_prod", 
                             title="Stan ilościowy", barmode="group",
                             labels={"nazwa_kat": "Kategoria", "liczba": "Sztuki"})
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            st.subheader("Udział wartościowy kategorii")
            df_full["total_val"] = df_full["liczba"] * df_full["cena"]
            fig_pie = px.pie(df_full, values="total_val", names="nazwa_kat", 
                             title="Rozkład wartości (PLN)", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Baza jest pusta. Dodaj pierwsze produkty, aby zobaczyć wykresy.")

# --- WIDOK 2: DODAWANIE ---
elif page == "Dodaj Produkty/Kategorie":
    st.title("➕ Dodawanie do bazy")
    
    tab1, tab2 = st.tabs(["📦 Nowy Produkt", "📁 Nowa Kategoria"])
    
    with tab1:
        kategorie_data = supabase.table("kategoria").select("id, nazwa").execute()
        opcje_kategorii = {item['nazwa']: item['id'] for item in kategorie_data.data}
        
        with st.form("form_prod"):
            n = st.text_input("Nazwa produktu")
            l = st.number_input("Ilość", min_value=0)
            c = st.number_input("Cena (PLN)", min_value=0.0)
            k = st.selectbox("Kategoria", options=list(opcje_kategorii.keys()))
            if st.form_submit_button("Dodaj produkt"):
                supabase.table("Produkt").insert({"nazwa": n, "liczba": l, "cena": c, "kategoria": opcje_kategorii[k]}).execute()
                st.success("Dodano!")

    with tab2:
        with st.form("form_kat"):
            k_kod = st.text_input("Kod (np. ABC)")
            k_nazwa = st.text_input("Nazwa")
            k_opis = st.text_area("Opis")
            if st.form_submit_button("Dodaj kategorię"):
                supabase.table("kategoria").insert({"kod": k_kod, "nazwa": k_nazwa, "opis": k_opis}).execute()
                st.success("Kategoria zapisana!")

# --- WIDOK 3: ZARZĄDZANIE ---
elif page == "Zarządzaj Bazą":
    st.title("🔍 Przegląd tabel")
    
    st.subheader("Tabela Produkty")
    st.dataframe(get_data("Produkt"), use_container_width=True)
    
    st.subheader("Tabela Kategorie")
    st.dataframe(get_data("kategoria"), use_container_width=True)
