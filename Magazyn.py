import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("Zarządzanie Produktami i Kategoriami")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
st.header("Dodaj Nową Kategorię")
with st.form("form_kategorie", clear_on_submit=True):
    kat_nazwa = st.text_input("Nazwa kategorii")
    kat_opis = st.text_area("Opis kategorii")
    submit_kat = st.form_submit_button("Zapisz kategorię")

    if submit_kat:
        if kat_nazwa:
            data = {"nazwa": kat_nazwa, "opis": kat_opis}
            response = supabase.table("kategorie").insert(data).execute()
            st.success(f"Dodano kategorię: {kat_nazwa}")
            # st.rerun() # Opcjonalnie odśwież, by kategoria była od razu widoczna w formularzu produktu
        else:
            st.error("Nazwa kategorii jest wymagana!")

# --- SEKCJA 2: DODAWANIE PRODUKTU ---
st.header("Dodaj Nowy Produkt")

# Pobranie aktualnych kategorii do listy rozwijanej
categories_query = supabase.table("kategorie").select("id, nazwa").execute()
categories_list = categories_query.data
cat_options = {c['nazwa']: c['id'] for c in categories_list}

with st.form("form_produkty", clear_on_submit=True):
    prod_nazwa = st.text_input("Nazwa produktu")
    prod_liczba = st.number_input("Liczba (szt.)", min_value=0, step=1)
    prod_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    
    selected_cat_name = st.selectbox("Wybierz kategorię", options=list(cat_options.keys()))
    submit_prod = st.form_submit_button("Zapisz produkt")

    if submit_prod:
        if prod_nazwa and selected_cat_name:
            product_data = {
                "nazwa": prod_nazwa,
                "liczba": prod_liczba,
                "cena": prod_cena,
                "kategoria_id": cat_options[selected_cat_name]
            }
            response = supabase.table("produkty").insert(product_data).execute()
            st.success(f"Dodano produkt: {prod_nazwa}")
            st.rerun() # Odświeżamy aplikację, aby lista produktów poniżej się zaktualizowała
        else:
            st.error("Wypełnij wymagane pola!")

# --- SEKCJA 3: PODGLĄD I USUWANIE DANYCH ---
st.divider()
st.header("Lista Produktów i Usuwanie")

# Pobranie produktów
res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
produkty_dane = res.data

if produkty_dane:
    # Wyświetlenie tabeli
    # Przygotowanie danych do ładnego wyświetlenia (spłaszczenie nazwy kategorii)
    display_data = []
    for p in produkty_dane:
        display_data.append({
            "ID": p['id'],
            "Nazwa": p['nazwa'],
            "Liczba": p['liczba'],
            "Cena": p['cena'],
            "Kategoria": p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
        })
    
    st.table(display_data)

    # Formularz usuwania produktu
    st.subheader("Usuń produkt")
    lista_nazw = [p['nazwa'] for p in produkty_dane]
    produkt_do_usuniecia = st.selectbox("Wybierz produkt do usunięcia", options=lista_nazw)
    
    if st.button("Usuń zaznaczony produkt", type="primary"):
        # Znalezienie ID po nazwie
        item_id = next(item['id'] for item in produkty_dane if item['nazwa'] == produkt_do_usuniecia)
        
        # Usunięcie z Supabase
        supabase.table("produkty").delete().eq("id", item_id).execute()
        
        st.warning(f"Produkt '{produkt_do_usuniecia}' został usunięty.")
        st.rerun() # Odświeżamy widok po usunięciu
else:
    st.info("Brak produktów w bazie danych.")
