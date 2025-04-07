import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import chardet
from io import BytesIO

# Конфигурация страницы (должна быть первой!)
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
    
    # Очистка данных
    df = df.rename(columns=lambda x: x.strip())
    if 'Наименование муниципального образования' in df.columns:
        df = df.rename(columns={'Наименование муниципального образования': 'Name'})
    df['Name'] = df['Name'].str.strip()
    return df

# Загрузка всех файлов
try:
    ch_1_6 = load_data('Ch_1_6.csv')      # Дети 1-6 лет
    ch_3_18 = load_data('Ch_3_18.csv')    # Дети 3-18 лет
    ch_5_18 = load_data('Ch_5_18.csv')    # Дети 5-18 лет
    pop_3_79 = load_data('Pop_3_79.csv')  # Население 3-79 лет
    rpop = load_data('RPop.csv')          # Среднегодовая численность
except Exception as e:
    st.error(f"Ошибка загрузки данных: {str(e)}. Проверьте: 1) Наличие файлов 2) Правильность названий")
    st.stop()

# Словарь тем (название: (датафрейм, цвет))
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
    
    # Выбор населенного пункта
    all_locations = ch_1_6['Name'].unique()
    selected_location = st.selectbox("Населённый пункт:", all_locations, index=0)
    
    # Выбор тем (можно несколько)
    selected_topics = st.multiselect(
        "Категории населения:",
        list(data_dict.keys()),
        default=["Дети 1-6 лет", "Среднегодовая численность"]
    )
    
    # Выбор года для Топ-5
    selected_year = st.selectbox(
        "Год для анализа Топ-5:",
        [str(year) for year in range(2019, 2025)],
        index=0
    )

# --- Основной интерфейс ---
st.title(f"Демографические показатели: {selected_location}")

# 1. Линейный график динамики
st.subheader("Динамика численности")
fig, ax = plt.subplots(figsize=(12, 5))
for topic in selected_topics:
    df, color = data_dict[topic]
    location_data = df[df['Name'] == selected_location]
    years = [str(year) for year in range(2019, 2025)]
    ax.plot(years, location_data[years].values.flatten(), 
            label=topic, color=color, marker='o', linewidth=2)
ax.set_xlabel("Год")
ax.set_ylabel("Численность (чел.)")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.7)
st.pyplot(fig)

# 2. Топ-5 населенных пунктов
st.subheader(f"Топ-5 населённых пунктов ({selected_year} год)")
col1, col2 = st.columns(2)
for topic in selected_topics:
    df, color = data_dict[topic]
    top5 = df.nlargest(5, selected_year)[['Name', selected_year]]
    
    with col1:
        st.markdown(f"**{topic}**")
        st.dataframe(top5.set_index('Name'), height=200)
    
    with col2:
        fig_bar = plt.figure(figsize=(8, 4))
        plt.bar(top5['Name'], top5[selected_year], color=color)
        plt.xticks(rotation=45)
        plt.title(f"Топ-5: {topic}")
        st.pyplot(fig_bar)

# 3. Экспорт данных (исправленная версия)
st.subheader("Экспорт данных")
for topic in selected_topics:
    df, _ = data_dict[topic]
    
    # Вариант 1: Экспорт в CSV (работает без доп. библиотек)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"Скачать {topic} (CSV)",
        data=csv,
        file_name=f"{topic.replace(' ', '_')}.csv",
        mime="text/csv"
    )
    
    # Вариант 2: Экспорт в Excel (требует openpyxl)
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=topic[:30])
        st.download_button(
            label=f"Скачать {topic} (Excel)",
            data=output.getvalue(),
            file_name=f"{topic.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.warning(f"Не удалось создать Excel-файл. Убедитесь, что openpyxl установлен")
