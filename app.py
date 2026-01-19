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
        df = df_p.merge(df_k, left_on="kategoria", right_on="id", suffixes=('_prod', '_kat'))
        df['wartosc_calkowita'] = df['liczba'] * df['cena']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Suma Towarów", f"{int(df['liczba'].sum())} szt.")
        m2.metric("💰 Wartość", f"{df['wartosc_calkowita'].sum():,.2f} PLN")
        m3.metric("🗂️ Kategorie", len(df_k))
        m4.metric("⚠️ Niski Stan", len(df_p[df_p['liczba'] < 5]))

        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("🔥 Top Produkty wg Wartości")
            fig = px.bar(df.nlargest(10, 'wartosc_calkowita'), x='nazwa_prod', y='wartosc_calkowita', color='nazwa_kat')
            st.plotly_chart(fig, use_container_width=True)
        with col_right:
            st.subheader("🥧 Udział Kategorii")
            fig_pie = px.pie(df, names='nazwa_kat', values='liczba', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Baza jest pusta.")

# --- WIDOK 2: OPERACJE WEJŚCIA ---
elif choice == "📥 Operacje Wejścia":
    st.title("📥 Dodawanie Zasobów")
    tab1, tab2 = st.tabs(["✨ Nowy Produkt", "📁 Nowa Kategoria"])
    
    with tab1:
        df_k = get_categories()
        if df_k.empty:
            st.error("❌ Musisz najpierw dodać kategorię!")
        else:
            opcje_kategorii = {row['nazwa']: row['id'] for _, row in df_k.iterrows()}
            with st.form("new_product_form", clear_on_submit=True):
                nazwa = st.text_input("Nazwa produktu")
                col_a, col_b = st.columns(2)
                ilosc = col_a.number_input("Ilość początkowa", min_value=0, step=1)
                cena = col_b.number_input("Cena", min_value=0.0, format="%.2f")
                kat_nazwa = st.selectbox("Kategoria", options=list(opcje_kategorii.keys()))
                if st.form_submit_button("🚀 Dodaj Produkt"):
                    if nazwa:
                        supabase.table("Produkt").insert({"nazwa": nazwa, "liczba": ilosc, "cena": cena, "kategoria": opcje_kategorii[kat_nazwa]}).execute()
                        st.success(f"Dodano: {nazwa}")
                    else:
                        st.error("Podaj nazwę!")

    with tab2:
        with st.form("new_category_form", clear_on_submit=True):
            k_kod = st.text_input("Kod")
            k_nazwa = st.text_input("Nazwa")
            k_opis = st.text_area("Opis")
            if st.form_submit_button("📁 Zapisz Kategorię"):
                if k_kod and k_nazwa:
                    supabase.table("kategoria").insert({"kod": k_kod, "nazwa": k_nazwa, "opis": k_opis}).execute()
                    st.success("Kategoria dodana!")
                    st.rerun()

# --- WIDOK 3: PRZEGLĄD I ZARZĄDZANIE ILOŚCIĄ ---
elif choice == "🔍 Przegląd i Stan":
    st.title("🔍 Zarządzanie Stanem Magazynowym")
    df_p = get_products()

    if not df_p.empty:
        # Wyświetlanie tabeli
        st.write("### 📦 Aktualne stany")
        st.dataframe(df_p[['nazwa', 'liczba', 'cena']], use_container_width=True)

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📉 Zdejmij ze stanu (Wydanie)")
            with st.form("sub_form"):
                prod_name = st.selectbox("Wybierz produkt", options=df_p['nazwa'].tolist(), key="sub_select")
                ile_odjac = st.number_input("Ile sztuk odebrać?", min_value=1, step=1)
                
                if st.form_submit_button("⬇️ Potwierdź wydanie"):
                    aktualny_stan = df_p[df_p['nazwa'] == prod_name]['liczba'].values[0]
                    nowy_stan = aktualny_stan - ile_odjac
                    
                    if nowy_stan < 0:
                        st.error(f"Nie możesz odjąć {ile_odjac} szt. (Dostępne: {aktualny_stan})")
                    else:
                        prod_id = df_p[df_p['nazwa'] == prod_name]['id'].values[0]
                        supabase.table("Produkt").update({"liczba": nowy_stan}).eq("id", prod_id).execute()
                        st.success(f"Zaktualizowano stan dla {prod_name}. Pozostało: {nowy_stan}")
                        st.rerun()

        with col2:
            st.subheader("🗑️ Usuwanie całkowite")
            with st.form("del_form"):
                prod_to_del = st.selectbox("Produkt do usunięcia z bazy", options=df_p['nazwa'].tolist())
                if st.form_submit_button("🧨 Usuń trwale produkt", type="primary"):
                    p_id = df_p[df_p['nazwa'] == prod_to_del]['id'].values[0]
                    supabase.table("Produkt").delete().eq("id", p_id).execute()
                    st.warning(f"Produkt {prod_to_del} został usunięty z bazy.")
                    st.rerun()
    else:
        st.info("Baza jest pusta.")
