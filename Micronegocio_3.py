import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuration ---
CSV_PATH = 'Módulo de ventas.csv' 
APP_TITLE = "Dashboard: Módulo de Ventas e Ingresos (Enfocado en Ingresos y Área)"

# --- Helper Function for Data Preparation ---
@st.cache_data
def load_and_preprocess_data(csv_file_path):
    """Loads, cleans, and preprocesses the data for the Sales & Income dashboard."""
    
    st.write(f"Cargando y preprocesando datos desde: {csv_file_path}")

    df = None
    # Use only the specified columns for this dashboard
    required_cols = [
        'DIRECTORIO', 'F_EXP', 'AREA', 
        'P3057', 'P3061', 'P3064', 'P3072' 
    ]

    if not os.path.exists(csv_file_path):
        st.error(f"ERROR: El archivo CSV NO se encontró en la ruta: {csv_file_path}")
        st.stop()

    try:
        df_temp = pd.read_csv(csv_file_path, encoding='latin-1', sep=',', low_memory=False)
        found_cols = [col for col in required_cols if col in df_temp.columns]
        if not found_cols:
            raise ValueError(f"Ninguna de las columnas requeridas ({', '.join(required_cols)}) se encontró con separador ','.")
        df = df_temp[found_cols].copy()
        st.write(f"Columnas encontradas y cargadas: {df.columns.tolist()}")
    except Exception as e:
        st.warning(f"Error al cargar con separador ',': {e}. Intentando con ';'")
        try:
            df_temp = pd.read_csv(csv_file_path, encoding='latin-1', sep=';', low_memory=False)
            found_cols = [col for col in required_cols if col in df_temp.columns]
            if not found_cols:
                raise ValueError(f"Ninguna de las columnas requeridas ({', '.join(required_cols)}) se encontró ni con ',' ni con ';'.")
            df = df_temp[found_cols].copy()
            st.write(f"Columnas encontradas y cargadas: {df.columns.tolist()}")
        except Exception as e_fallback:
            st.error(f"ERROR CRÍTICO: No se pudo cargar el archivo correctamente. Detalle: {e_fallback}")
            st.stop()

    if df is None or df.empty:
        st.error("ERROR: El DataFrame está vacío o no se pudo cargar.")
        st.stop()

    # Drop duplicates based on DIRECTORIO if present
    if 'DIRECTORIO' in df.columns:
        df.drop_duplicates(subset=['DIRECTORIO'], keep='first', inplace=True)
    
    # Ensure F_EXP exists and is numeric
    if 'F_EXP' in df.columns:
        df['F_EXP'] = pd.to_numeric(df['F_EXP'], errors='coerce').fillna(1)
    else:
        st.warning("La columna 'F_EXP' no se encontró. Los cálculos no estarán ponderados.")
        df['F_EXP'] = 1 # Default to 1 if not found

    # AREA for Metropolitan Areas
    if 'AREA' in df.columns:
        df['AREA_Label'] = df['AREA'].fillna('Desconocida').astype(str)
    else: 
        df['AREA_Label'] = 'No Disponible'

    # Convert income/sales columns to numeric, filling NaNs with 0 for summation
    income_cols_to_process = ['P3057', 'P3061', 'P3064', 'P3072']
    for col in income_cols_to_process:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0 # Ensure column exists if not in original data, set to 0

    # Calculate Total Monthly Income from primary sources for composition
    df['Total_Ingresos_Categorizados'] = df['P3057'] + df['P3061'] + df['P3064']
    
    return df

# --- Streamlit App Layout ---
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title(APP_TITLE)
st.markdown("Este dashboard se enfoca en el *Módulo de Ventas e Ingresos, analizando las fuentes de ingresos y el desempeño económico de los micronegocios, usando **tus datos reales y columnas especificadas*.")

# Load data once
df = load_and_preprocess_data(CSV_PATH)

# Check if data loading was successful
if df.empty:
    st.error("No se pudieron cargar los datos o el DataFrame está vacío después del preprocesamiento.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filtros del Dashboard")

# Filter for P3072 (Average Monthly Income)
st.sidebar.subheader("Filtrar por Ingreso Promedio Mensual")
if not df['P3072'].dropna().empty:
    min_income_p3072, max_income_p3072 = float(df['P3072'].min()), float(df['P3072'].max())
    selected_income_p3072_range = st.sidebar.slider(
        "Rango de Ingreso Promedio Mensual ($)",
        min_value=min_income_p3072,
        max_value=max_income_p3072 if max_income_p3072 > min_income_p3072 else min_income_p3072 + 1, # Avoid error if min=max
        value=(min_income_p3072, max_income_p3072 if max_income_p3072 > min_income_p3072 else min_income_p3072 + 1),
        step=1000.0,
        format="$%,.0f"
    )
else:
    st.sidebar.info("No hay datos válidos para filtrar por Ingreso Promedio Mensual.")
    selected_income_p3072_range = (0, 0) # Default to avoid errors

# Filter for AREA
st.sidebar.subheader("Filtrar por Área Metropolitana")
unique_area = df['AREA_Label'].unique().tolist()
selected_area = st.sidebar.multiselect(
    "Selecciona Área(s)",
    options=unique_area,
    default=unique_area
)

# Apply filters
df_filtered = df[
    (df['AREA_Label'].isin(selected_area))
]

# Apply P3072 filter only if valid range is available
if selected_income_p3072_range[0] != 0 or selected_income_p3072_range[1] != 0:
     df_filtered = df_filtered[
        (df_filtered['P3072'] >= selected_income_p3072_range[0]) & (df_filtered['P3072'] <= selected_income_p3072_range[1])
    ]


if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()


# --- Dashboard Sections ---
st.header("Análisis de las Ventas e Ingresos de los Micronegocios")
st.write(f"*Número total de registros (después de filtros):* {len(df_filtered):,}")

# --- Plot 1: Distribución del Ingreso Promedio Mensual (P3072) ---
st.subheader("1. Distribución del Ingreso Promedio Mensual (P3072)")
if df_filtered['P3072'].sum() > 0:
    fig_p3072_dist = px.histogram(
        df_filtered,
        x='P3072',
        nbins=50,
        title='Distribución de Micronegocios por Ingreso Promedio Mensual',
        labels={'P3072': 'Ingreso Promedio Mensual ($)', 'count': 'Número de Negocios'},
        hover_data={'P3072': '$,.0f'},
        log_y=True # Log scale because income data is often skewed
    )
    fig_p3072_dist.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig_p3072_dist, use_container_width=True)
else:
    st.info("No hay datos válidos para mostrar la distribución de Ingreso Promedio Mensual con los filtros actuales.")

---

# --- Plot 2: Composición de Ingresos por Tipo de Venta/Servicio ---
st.subheader("2. Composición de Ingresos por Tipo de Venta/Servicio")
# Sum of weighted income types
df_income_types = df_filtered[['P3057', 'P3061', 'P3064', 'F_EXP']].copy()
df_income_types['P3057_Weighted'] = df_income_types['P3057'] * df_income_types['F_EXP']
df_income_types['P3061_Weighted'] = df_income_types['P3061'] * df_income_types['F_EXP']
df_income_types['P3064_Weighted'] = df_income_types['P3064'] * df_income_types['F_EXP']

total_p3057 = df_income_types['P3057_Weighted'].sum()
total_p3061 = df_income_types['P3061_Weighted'].sum()
total_p3064 = df_income_types['P3064_Weighted'].sum()

total_income_weighted_overall = total_p3057 + total_p3061 + total_p3064

if total_income_weighted_overall > 0:
    df_income_composition = pd.DataFrame({
        'Tipo de Ingreso': ['Productos Elaborados (P3057)', 'Venta de Mercancía (P3061)', 'Servicios Ofrecidos (P3064)'],
        'Valor Ponderado': [total_p3057, total_p3061, total_p3064]
    })
    
    fig_income_composition = px.pie(
        df_income_composition,
        names='Tipo de Ingreso',
        values='Valor Ponderado',
        title='Proporción de Ingresos por Tipo de Venta/Servicio (Casos Ponderados)',
        hover_data={'Valor Ponderado': '$,.0f'}
    )
    fig_income_composition.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
    st.plotly_chart(fig_income_composition, use_container_width=True)
else:
    st.info("No hay datos de ingresos válidos para mostrar la composición por tipo de venta con los filtros actuales.")

---

# --- Plot 3: Ingreso Promedio Mensual por Área Metropolitana ---
st.subheader("3. Ingreso Promedio Mensual por Área Metropolitana (AREA_Label)")

# Calculate average P3072 per Area
df_income_by_area = df_filtered.groupby('AREA_Label')['P3072'].mean().reset_index()

if not df_income_by_area.empty and df_income_by_area['P3072'].sum() > 0:
    fig_income_by_area = px.bar(
        df_income_by_area.sort_values('P3072', ascending=False), # Sort for better visualization
        x='AREA_Label',
        y='P3072',
        title='Ingreso Promedio Mensual por Área Metropolitana',
        labels={'AREA_Label': 'Área Metropolitana', 'P3072': 'Ingreso Promedio Mensual ($)'},
        hover_data={'P3072': '$,.0f'}
    )
    fig_income_by_area.update_yaxes(rangemode="tozero", tickprefix="$", tickformat=",.0f")
    fig_income_by_area.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_income_by_area, use_container_width=True)
else:
    st.info("No hay datos para mostrar el ingreso promedio por área metropolitana con los filtros actuales.")

---
st.success("¡Dashboard del Módulo de Ventas e Ingresos generado exitosamente con TUS datos reales y columnas seleccionadas!")