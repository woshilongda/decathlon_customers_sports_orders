# app.py
# Interaktywny dashboard w Streamlit do analizy danych Decathlon
# Dane: customer_orders.csv, sports.csv, orders.csv

import pandas as pd
import streamlit as st
import altair as alt

# Konfiguracja strony musi być pierwszą komendą Streamlit
st.set_page_config(page_title='Decathlon Dashboard', layout='wide')

# Ścieżki do plików CSV
PATH_CO = r"https://drive.google.com/file/d/1n4fw-_tallj24MXqrSFMY7MWqHdybZen/view?usp=sharing"
PATH_SPORTS = r"https://drive.google.com/file/d/1fagn7etp2eGNU0qzbwS0DUpK4iZcvWmw/view?usp=sharing"
PATH_ORDERS = r"https://drive.google.com/file/d/1n4fw-_tallj24MXqrSFMY7MWqHdybZen/view?usp=sharing"

@st.cache_data
def load_data():
    co = pd.read_csv(PATH_CO, dtype={'customer_id': str, 'order_id': str}).dropna(subset=['customer_id'])
    sp = pd.read_csv(PATH_SPORTS, dtype={'customer_id': str, 'sport': str}).dropna(subset=['customer_id'])
    orders = pd.read_csv(PATH_ORDERS, dtype={'order_id': str}, low_memory=False)

    # Konwersja wartości na numeryczne
    orders['value'] = pd.to_numeric(orders.get('value', []), errors='coerce')
    orders['products'] = pd.to_numeric(orders.get('products', []), errors='coerce')

    # Połączenie tabel
    df = co.merge(orders, on='order_id', how='left')
    return co, sp, orders, df

# Wczytanie danych
tco, sp, orders, df = load_data()

total_customers = tco['customer_id'].nunique()
# Agregacje
sports_per_customer = sp.groupby('customer_id')['sport'].nunique()
orders_per_customer = tco.groupby('customer_id')['order_id'].nunique()
sport_pop = sp.groupby('sport')['customer_id'].nunique().sort_values(ascending=False)

# Tytuł
st.title('Dashboard Decathlon')

# Ogólne metryki
st.header('Ogólne metryki')
st.metric('Klienci uprawiający >2 sporty', int((sports_per_customer > 2).sum()))
top_sport, top_n = sport_pop.index[0], sport_pop.iloc[0]
bot_sport, bot_n = sport_pop.index[-1], sport_pop.iloc[-1]
st.metric('Najpopularniejszy sport', f"{top_sport} ({top_n} klientów)")
st.metric('Najmniej popularny sport', f"{bot_sport} ({bot_n} klientów)")
st.metric('Średnia wartość zamówienia', f"{orders['value'].mean():.2f}")
st.metric('Odsetek klientów z >1 zamówieniem', f"{(orders_per_customer > 1).mean()*100:.2f}%")

# Zwroty i produkty
st.subheader('Zwroty i produkty')
st.metric('% zwrotów wśród zamówień', f"{(orders['value']<0).mean()*100:.2f}%")
st.metric('% klientów ze zwrotem', f"{df.groupby('customer_id')['value'].apply(lambda x: (x<0).any()).mean()*100:.2f}%")
st.metric('Średnia liczba produktów na zamówienie', f"{orders['products'].mean():.2f}")
st.metric('Średnia liczba produktów na klienta', f"{orders['products'].sum()/total_customers:.2f}")

# Segmentacja klientów wg liczby zamówień
df_seg = (orders_per_customer.value_counts().sort_index() / total_customers * 100).reset_index()
df_seg.columns = ['liczba_zamówień','% klientów']
st.subheader('Segmentacja klientów wg liczby zamówień (% klientów)')
chart_seg = alt.Chart(df_seg).mark_bar().encode(
    x=alt.X('liczba_zamówień:O', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('% klientów:Q')
)
st.altair_chart(chart_seg, use_container_width=True)

# Popularność sportów
df_sp = (sport_pop/ total_customers*100).reset_index()
df_sp.columns = ['sport','% klientów']
st.subheader('Popularność sportów (% klientów)')
chart_sp = alt.Chart(df_sp).mark_bar().encode(
    x=alt.X('sport:O', sort='-y', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('% klientów:Q')
)
st.altair_chart(chart_sp, use_container_width=True)

# Profil klienta
st.sidebar.header('Profil klienta')
ids = sorted(tco['customer_id'].unique())
selected = st.sidebar.selectbox('Wybierz customer_id', ids)

st.subheader(f'Sporty klienta {selected}')
sp_sel = sp[sp['customer_id']==selected]['sport'].unique()
st.write(sp_sel if sp_sel.size else 'Brak danych')

st.subheader(f'Zakupy klienta {selected}')
df_sel = df[df['customer_id']==selected]
st.write(f"Łączna wartość: {df_sel['value'].sum():.2f}")
st.write(f"Średnia wartość: {df_sel['value'].mean():.2f}")

# Podsumowanie wszystkich klientów
# Tworzymy podsumowanie wszytkich klientów
# (sporty, zamówienia, łączna wartość)
df_summary = pd.DataFrame({
    'liczba_sportów': sports_per_customer,
    'liczba_zamówień': orders_per_customer,
    'wartość_łączna': df.groupby('customer_id')['value'].sum()
}).reset_index()
st.subheader('Podsumowanie klientów')
st.dataframe(df_summary, use_container_width=True)

# Uruchom: streamlit run app.py 
