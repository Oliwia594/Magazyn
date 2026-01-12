
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ustawienia strony z ikoną magazynu
st.set_page_config(page_title="Magazyn Inteligenty v2", layout="wide", page_icon="🏢")

# Połączenie z Supabase (pobierane z st.secrets)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

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
    choice = st.radio("Nawigacja", ["📈 Analiza i Statystyki", "📥 Operacje Wejścia", "🔍 Przegląd Tabel"])
    st.info("System połączony z bazą Supabase ✅")

# --- WIDOK 1: ANALIZA I STATYSTYKI ---
if choice == "📈 Analiza i Statystyki":
    st.title("📊 Inteligentne Statystyki")
    
    df_p = get_products()
    df_k = get_categories()

    if not df_p.empty and not df_k.empty:
        # Łączenie tabel dla lepszej analizy
        df = df_p.merge(df_k, left_on="kategoria", right_on="id", suffixes=('_prod', '_kat'))
        df['wartosc_calkowita'] = df['liczba'] * df['cena']

        # Wskaźniki na górze
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Suma Towarów", f"{int(df['liczba'].sum())} szt.")
        m2.metric("💰 Wartość", f"{df['wartosc_calkowita'].sum():,.2f} PLN")
        m3.metric("🗂️ Kategorie", len(df_k))
        m4.metric("⚠️ Niski Stan", len(df_p[df_p['liczba'] < 5]))

        st.divider()

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🔥 Top Produkty wg Wartości")
            fig = px.bar(df.nlargest(10, 'wartosc_calkowita'), 
                         x='nazwa_prod', y='wartosc_calkowita', 
                         color='nazwa_kat', text_auto='.2s',
                         labels={'nazwa_prod': 'Produkt', 'wartosc_calkowita': 'Wartość (PLN)'})
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("🥧 Udział Kategorii w Magazynie")
            fig_pie = px.sunburst(df, path=['nazwa_kat', 'nazwa_prod'], values='liczba',
                                  color='nazwa_kat', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Dodaj najpierw kategorie i produkty, aby zobaczyć wykresy!")

# --- WIDOK 2: OPERACJE WEJŚCIA ---
elif choice == "📥 Operacje Wejścia":
    st.title("📥 Dodawanie Zasobów")
    
    tab1, tab2 = st.tabs(["✨ Nowy Produkt", "📁 Nowa Kategoria"])
    
    with tab1:
        st.subheader("Formularz Produktu")
        df_k = get_categories()
        
        if df_k.empty:
            st.error("❌ Błąd: Nie możesz dodać produktu, bo nie masz żadnej kategorii! Przejdź do zakładki 'Nowa Kategoria'.")
        else:
            opcje_kategorii = {row['nazwa']: row['id'] for _, row in df_k.iterrows()}
            
            with st.form("new_product_form"):
                nazwa = st.text_input("Nazwa produktu", placeholder="np. Mleko 1L")
                col_a, col_b = st.columns(2)
                ilosc = col_a.number_input("Ilość (szt)", min_value=0, step=1)
                cena = col_b.number_input("Cena jednostkowa (PLN)", min_value=0.0, format="%.2f")
                kat_nazwa = st.selectbox("Wybierz kategorię", options=list(opcje_kategorii.keys()))
                
                if st.form_submit_button("🚀 Dodaj do bazy"):
                    if nazwa:
                        new_prod = {
                            "nazwa": nazwa,
                            "liczba": ilosc,
                            "cena": cena,
                            "kategoria": opcje_kategorii[kat_nazwa]
                        }
                        supabase.table("Produkt").insert(new_prod).execute()
                        st.success(f"Dodano produkt: {nazwa}")
                        st.balloons()
                    else:
                        st.error("Nazwa nie może być pusta!")

    with tab2:
        st.subheader("Utwórz nową grupę produktów")
        with st.form("new_category_form"):
            k_kod = st.text_input("Kod systemowy", placeholder="np. SPO-01")
            k_nazwa = st.text_input("Nazwa wyświetlana", placeholder="np. Spożywcze")
            k_opis = st.text_area("Opis kategorii")
            
            if st.form_submit_button("📁 Zapisz Kategorię"):
                if k_kod and k_nazwa:
                    supabase.table("kategoria").insert({"kod": k_kod, "nazwa": k_nazwa, "opis": k_opis}).execute()
                    st.success("Kategoria dodana pomyślnie!")
                else:
                    st.error("Wypełnij wymagane pola (Kod i Nazwa)!")

# --- WIDOK 3: ZARZĄDZANIE ---
elif choice == "🔍 Przegląd Tabel":
    st.title("🔍 Inspekcja Bazy Danych")
    
    st.write("### 📦 Wszystkie Produkty")
    st.dataframe(get_products(), use_container_width=True)
    
    st.write("### 📁 Wszystkie Kategorie")
    st.dataframe(get_categories(), use_container_width=True)
