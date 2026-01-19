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
    choice = st.radio("Nawigacja", ["📈 Analiza i Statystyki", "📥 Operacje Wejścia", "🔍 Przegląd Tabel"])
    st.info("System połączony z bazą Supabase ✅")

# --- WIDOK 1: ANALIZA I STATYSTYKI ---
if choice == "📈 Analiza i Statystyki":
    st.title("📊 Inteligentne Statystyki")
    
    df_p = get_products()
    df_k = get_categories()

    if not df_p.empty and not df_k.empty:
        # Łączenie tabel
        df = df_p.merge(df_k, left_on="kategoria", right_on="id", suffixes=('_prod', '_kat'))
        df['wartosc_calkowita'] = df['liczba'] * df['cena']

        # Wskaźniki
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Suma Towarów", f"{int(df['liczba'].sum())} szt.")
        m2.metric("💰 Wartość", f"{df['wartosc_calkowita'].sum():,.2f} PLN")
        m3.metric("🗂️ Kategorie", len(df_k))
        m4.metric("⚠️ Niski Stan", len(df_p[df_p['liczba'] < 5]))

        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🔥 Top Produkty wg Wartości")
            fig = px.bar(df.nlargest(10, 'wartosc_calkowita'), 
                         x='nazwa_prod', y='wartosc_calkowita', color='nazwa_kat')
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("🥧 Udział Kategorii")
            fig_pie = px.pie(df, names='nazwa_kat', values='liczba', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Baza jest pusta. Dodaj kategorie i produkty!")

# --- WIDOK 2: OPERACJE WEJŚCIA ---
elif choice == "📥 Operacje Wejścia":
    st.title("📥 Dodawanie Zasobów")
    tab1, tab2 = st.tabs(["✨ Nowy Produkt", "📁 Nowa Kategoria"])
    
    with tab1:
        st.subheader("Formularz Produktu")
        df_k = get_categories()
        
        if df_k.empty:
            st.error("❌ Musisz najpierw dodać kategorię!")
        else:
            opcje_kategorii = {row['nazwa']: row['id'] for _, row in df_k.iterrows()}
            with st.form("new_product_form", clear_on_submit=True):
                nazwa = st.text_input("Nazwa produktu")
                col_a, col_b = st.columns(2)
                ilosc = col_a.number_input("Ilość", min_value=0, step=1)
                cena = col_b.number_input("Cena", min_value=0.0, format="%.2f")
                kat_nazwa = st.selectbox("Kategoria", options=list(opcje_kategorii.keys()))
                
                if st.form_submit_button("🚀 Dodaj Produkt"):
                    if nazwa:
                        try:
                            supabase.table("Produkt").insert({
                                "nazwa": nazwa, "liczba": ilosc, "cena": cena, 
                                "kategoria": opcje_kategorii[kat_nazwa]
                            }).execute()
                            st.success(f"Dodano: {nazwa}")
                            # Brak st.balloons() zgodnie z prośbą
                        except Exception as e:
                            st.error(f"Błąd zapisu: {e}")
                    else:
                        st.error("Podaj nazwę produktu!")

    with tab2:
        st.subheader("Nowa Kategoria")
        with st.form("new_category_form", clear_on_submit=True):
            k_kod = st.text_input("Kod (np. KAT-01)")
            k_nazwa = st.text_input("Nazwa")
            k_opis = st.text_area("Opis")
            
            if st.form_submit_button("📁 Zapisz Kategorię"):
                if k_kod and k_nazwa:
                    try:
                        supabase.table("kategoria").insert({
                            "kod": k_kod, "nazwa": k_nazwa, "opis": k_opis
                        }).execute()
                        st.success("Kategoria dodana!")
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Błąd: Kod {k_kod} już istnieje lub brak uprawnień.")
                else:
                    st.error("Wypełnij pola Kod i Nazwa!")

# --- WIDOK 3: PRZEGLĄD I USUWANIE ---
elif choice == "🔍 Przegląd Tabel":
    st.title("🔍 Inspekcja i Zarządzanie")
    
    df_p = get_products()
    df_k = get_categories()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("### 📦 Lista Produktów")
        if not df_p.empty:
            st.dataframe(df_p, use_container_width=True)
        else:
            st.info("Brak produktów.")

    with col2:
        st.write("### 🗑️ Usuń Produkt")
        if not df_p.empty:
            with st.form("delete_form"):
                produkt_do_usuniecia = st.selectbox(
                    "Wybierz produkt", 
                    options=df_p['nazwa'].tolist()
                )
                if st.form_submit_button("Usuń trwale", type="primary"):
                    # Pobranie ID produktu na podstawie nazwy
                    id_to_del = df_p[df_p['nazwa'] == produkt_do_usuniecia]['id'].values[0]
                    supabase.table("Produkt").delete().eq("id", id_to_del).execute()
                    st.warning(f"Usunięto: {produkt_do_usuniecia}")
                    st.rerun()
        else:
            st.write("Brak danych do usunięcia.")

    st.divider()
    st.write("### 📁 Kategorie")
    st.dataframe(df_k, use_container_width=True)
