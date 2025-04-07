import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import chardet
from io import BytesIO

# Конфигурация страницы
st.set_page_config(layout="wide")

# --- Загрузка данных ---
@st.cache_data
def load_data(file_name):
    with open(file_name, 'rb') as f:
        result = chardet.detect(f.read(10000))
    try:
        df = pd.read_csv(file_name, sep=';', encoding=result['encoding'])
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_name, sep=';', encoding='utf-8')
        except:
            df = pd.read_csv(file_name, sep=';', encoding='cp1251')
    
    df = df.rename(columns=lambda x: x.strip())
    if 'Наименование муниципального образования' in df.columns:
        df = df.rename(columns={'Наименование муниципального образования': 'Name'})
    df['Name'] = df['Name'].str.strip()
    return df

# Загрузка файлов
try:
    ch_1_6 = load_data('Ch_1_6.csv')      # Дети 1-6 лет
    ch_3_18 = load_data('Ch_3_18.csv')    # Дети 3-18 лет
    ch_5_18 = load_data('Ch-5-18.csv')    # Дети 5-18 лет
    pop_3_79 = load_data('Pop_3_79.csv')  # Население 3-79 лет
    rpop = load_data('RPop.csv')          # Среднегодовая численность
except Exception as e:
    st.error(f"Ошибка загрузки данных: {str(e)}. Проверьте названия файлов!")
    st.stop()

data_dict = {
    "Дети 1-6 лет": (ch_1_6, "skyblue"),
    "Дети 3-18 лет": (ch_3_18, "salmon"),
    "Дети 5-18 лет": (ch_5_18, "gold"),
    "Население 3-79 лет": (pop_3_79, "lightgreen"),
    "Среднегодовая численность": (rpop, "violet")
}

# --- Боковая панель ---
with st.sidebar:
    st.title("Настройки анализа")
    selected_location = st.selectbox("Населённый пункт:", ch_1_6['Name'].unique(), index=0)
    selected_topics = st.multiselect("Категории:", list(data_dict.keys()), default=list(data_dict.keys())[:2])
    selected_year = st.selectbox("Год для Топ-5:", [str(year) for year in range(2019, 2025)], index=0)

# --- Основной интерфейс ---
st.title(f"Демография Орловской области: {selected_location}")

# 1. Графики динамики
st.subheader("Динамика численности")
fig, ax = plt.subplots(figsize=(12, 5))
for topic in selected_topics:
    df, color = data_dict[topic]
    data = df[df['Name'] == selected_location]
    years = [str(year) for year in range(2019, 2025)]
    ax.plot(years, data[years].values.flatten(), label=topic, color=color, marker='o')
ax.legend()
st.pyplot(fig)

# 2. Топ-5 населённых пунктов
st.subheader(f"Топ-5 по категории ({selected_year} год)")
col1, col2 = st.columns(2)
for topic in selected_topics:
    df, _ = data_dict[topic]
    top5 = df.nlargest(5, selected_year)[['Name', selected_year]]
    with col1:
        st.markdown(f"**{topic}**")
        st.dataframe(top5.set_index('Name'), height=200)
    with col2:
        st.bar_chart(top5.set_index('Name'))

# 3. Скачивание данных
st.subheader("Экспорт данных")
for topic in selected_topics:
    df, _ = data_dict[topic]
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label=f"Скачать {topic} (Excel)",
        data=output.getvalue(),
        file_name=f"{topic.replace(' ', '_')}.xlsx",
        mime="application/vnd.ms-excel"
    )
