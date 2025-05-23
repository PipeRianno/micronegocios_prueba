import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuration ---
CSV_PATH = 'Módulo de emprendimiento.csv' # Make sure this file is in the same directory
APP_TITLE = "Dashboard: Módulo de Emprendimiento de Micronegocios"

# --- Helper Function for Data Preparation ---
@st.cache_data
def load_and_preprocess_data(csv_file_path):
    """Loads, cleans, and preprocesses the data for the Entrepreneurship dashboard."""
    
    st.write(f"Cargando y preprocesando datos desde: {csv_file_path}")

    df = None
    # Use only the specified columns for this dashboard
    required_cols = ['SECUENCIA_P', 'SECUENCIA_ENCUESTA', 'P3050', 'P3051', 'P639', 'P3052', 'CLASE_TE', 'COD_DEPTO', 'AREA', 'F_EXP', 'DIRECTORIO']

    if not os.path.exists(csv_file_path):
        st.error(f"ERROR: El archivo CSV NO se encontró en la ruta: {csv_file_path}")
        st.stop()

    try:
        df_temp = pd.read_csv(csv_file_path, encoding='latin-1', sep=',', low_memory=False)
        found_cols = [col for col in required_cols if col in df_temp.columns]
        if not found_cols:
            raise ValueError("Ninguna de las columnas requeridas se encontró con separador ','.")
        df = df_temp[found_cols].copy()
        st.write(f"Datos cargados con separador ',' y columnas: {df.columns.tolist()}")
    except Exception as e:
        st.warning(f"Error al cargar con separador ',': {e}. Intentando con ';'")
        try:
            df_temp = pd.read_csv(csv_file_path, encoding='latin-1', sep=';', low_memory=False)
            found_cols = [col for col in required_cols if col in df_temp.columns]
            if not found_cols:
                raise ValueError("Ninguna de las columnas requeridas se encontró ni con ',' ni con ';'.")
            df = df_temp[found_cols].copy()
            st.write(f"Datos cargados con separador ';' y columnas: {df.columns.tolist()}")
        except Exception as e_fallback:
            st.error(f"ERROR CRÍTICO: No se pudo cargar el archivo correctamente. Detalle: {e_fallback}")
            st.stop()

    if df is None or df.empty:
        st.error("ERROR: El DataFrame está vacío o no se pudo cargar.")
        st.stop()

    # --- Preprocessing for Entrepreneurship Module ---
    if 'DIRECTORIO' in df.columns:
        df.drop_duplicates(subset=['DIRECTORIO'], keep='first', inplace=True)
    
    # P3050: ¿Quién creó o constituyó el negocio o actividad?
    if 'P3050' in df.columns:
        p3050_map = {
            1: 'Usted solo',
            2: 'Usted y otro(s) familiares',
            3: 'Usted y otra(s) persona(s) no familiar(es)',
            4: 'Otras personas',
            5: 'Un familiar',
            6: 'Otro'
        }
        df['Creador_Negocio'] = pd.to_numeric(df['P3050'], errors='coerce').map(p3050_map)
        df['Creador_Negocio'].fillna('Desconocido', inplace=True)
    else: df['Creador_Negocio'] = 'No Disponible'

    # P3051: ¿Cuál fue el motivo principal por el que usted inició este negocio o actividad económica?
    if 'P3051' in df.columns:
        p3051_map = {
            1: 'No tiene otra alternativa de ingresos',
            2: 'Lo identificó como una oportunidad de negocio en el mercado',
            3: 'Por tradición familiar o lo heredó',
            4: 'Para complementar el ingreso familiar o mejorar el ingreso',
            5: 'Para ejercer su oficio, carrera o profesión',
            6: 'No tenía la experiencia requerida, la escolaridad o capacitación para un empleo',
            7: 'Otro'
        }
        df['Motivo_Inicio'] = pd.to_numeric(df['P3051'], errors='coerce').map(p3051_map)
        df['Motivo_Inicio'].fillna('Desconocido', inplace=True)
    else: df['Motivo_Inicio'] = 'No Disponible'

    # P639: ¿Cuánto tiempo lleva funcionado el negocio o actividad?
    if 'P639' in df.columns:
        p639_map = {
            1: 'Menos de un año',
            2: 'De 1 a menos de 3 años',
            3: 'De 3 a menos de 5 años',
            4: 'De 5 a menos de 10 años',
            5: '10 años y más'
        }
        df['Antiguedad_Negocio_Rango'] = pd.to_numeric(df['P639'], errors='coerce').map(p639_map)
        df['Antiguedad_Negocio_Rango'].fillna('Desconocido', inplace=True)
        # Define explicit order for categorical plots
        antiguedad_order = ['Menos de un año', 'De 1 a menos de 3 años', 'De 3 a menos de 5 años', 
                            'De 5 a menos de 10 años', '10 años y más', 'Desconocido']
        df['Antiguedad_Negocio_Rango'] = pd.Categorical(df['Antiguedad_Negocio_Rango'], categories=antiguedad_order, ordered=True)
    else: df['Antiguedad_Negocio_Rango'] = 'No Disponible'

    # P3052: ¿Cuál fue la mayor fuente de recursos para la creación o constitución de este negocio o actividad?
    if 'P3052' in df.columns:
        p3052_map = {
            1: 'Ahorros personales',
            2: 'Préstamos familiares',
            3: 'Préstamos bancarios',
            4: 'Prestamistas',
            5: 'Capital semilla',
            6: 'No requirió financiación',
            7: 'No sabe',
            8: 'Otro'
        }
        df['Fuente_Recursos'] = pd.to_numeric(df['P3052'], errors='coerce').map(p3052_map)
        df['Fuente_Recursos'].fillna('Desconocido', inplace=True)
    else: df['Fuente_Recursos'] = 'No Disponible'
    
    # CLASE_TE para Entorno (Urbana/Rural)
    if 'CLASE_TE' in df.columns:
        df['CLASE_TE_Label'] = pd.to_numeric(df['CLASE_TE'], errors='coerce')
        df['CLASE_TE_Label'] = df['CLASE_TE_Label'].map({1: 'Urbana', 2: 'Rural'})
        df['CLASE_TE_Label'].fillna('Desconocido', inplace=True)
    else: df['CLASE_TE_Label'] = 'No Disponible'

    # AREA para Ciudades principales y áreas metropolitanas
    if 'AREA' in df.columns:
        df['AREA_Label'] = df['AREA'].fillna('Desconocida').astype(str)
        # Map AREA codes to actual city names if possible (example for Colombia)
        # This requires knowing the codes, let's keep it as is for generic AREA for now.
        # If you have a mapping for COD_DEPTO and AREA, you can add it here.
    else: df['AREA_Label'] = 'No Disponible'
    
    # COD_DEPTO (Department Code) - useful for granular geographical filtering/analysis
    if 'COD_DEPTO' in df.columns:
        df['Departamento'] = df['COD_DEPTO'].astype(str).fillna('Desconocido')
        # You might want to map these codes to actual department names here
        # Example: if 'COD_DEPTO' == 11, then 'Bogotá'
    else: df['Departamento'] = 'No Disponible'

    # Factor de Expansión (F_EXP)
    if 'F_EXP' not in df.columns:
        st.warning("La columna 'F_EXP' no se encontró. Los cálculos de porcentaje no estarán ponderados.")
        df['F_EXP'] = 1 # Default to 1 if not found

    return df

# --- Function to Prepare Data for Plotly (for percentages) ---
def prepare_data_for_plotly_percentage(dataframe, group_col):
    """Prepares data for Plotly charts, calculating ponderated percentages."""
    if group_col not in dataframe.columns:
        st.warning(f"Columna '{group_col}' no encontrada en el DataFrame.")
        return pd.DataFrame()

    temp_df = dataframe.dropna(subset=[group_col])
    if temp_df.empty:
        return pd.DataFrame()

    df_grouped = temp_df.groupby(group_col)['F_EXP'].sum().reset_index()
    df_grouped.columns = [group_col, 'F_EXP_Sum']
    
    total_f_exp = df_grouped['F_EXP_Sum'].sum()
    df_grouped['Porcentaje'] = (df_grouped['F_EXP_Sum'] / total_f_exp) * 100 if total_f_exp > 0 else 0
    
    # Ensure proper sorting for ordered categories 
    if isinstance(df_grouped[group_col].dtype, pd.CategoricalDtype):
        df_grouped = df_grouped.sort_values(group_col)
    else:
        df_grouped = df_grouped.sort_values('Porcentaje', ascending=False)
        
    return df_grouped

# --- Streamlit App Layout ---
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title(APP_TITLE)
st.markdown("Este dashboard se enfoca en el *Módulo de Emprendimiento*, analizando cómo se inician y desarrollan los micronegocios.")

# Load data once
df = load_and_preprocess_data(CSV_PATH)

# Check if data loading was successful
if df.empty:
    st.error("No se pudieron cargar los datos o el DataFrame está vacío después del preprocesamiento.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filtros del Dashboard")

unique_creador = df['Creador_Negocio'].unique().tolist()
selected_creador = st.sidebar.multiselect(
    "Filtrar por Creador del Negocio",
    options=unique_creador,
    default=unique_creador
)

unique_motivo = df['Motivo_Inicio'].unique().tolist()
selected_motivo = st.sidebar.multiselect(
    "Filtrar por Motivo de Inicio",
    options=unique_motivo,
    default=unique_motivo
)

unique_antiguedad_rango = df['Antiguedad_Negocio_Rango'].unique().tolist()
selected_antiguedad_rango = st.sidebar.multiselect(
    "Filtrar por Rango de Antigüedad",
    options=unique_antiguedad_rango,
    default=unique_antiguedad_rango
)

unique_fuente_recursos = df['Fuente_Recursos'].unique().tolist()
selected_fuente_recursos = st.sidebar.multiselect(
    "Filtrar por Fuente de Recursos",
    options=unique_fuente_recursos,
    default=unique_fuente_recursos
)

unique_clase_te = df['CLASE_TE_Label'].unique().tolist()
selected_clase_te = st.sidebar.multiselect(
    "Filtrar por Entorno (Urbana/Rural)",
    options=unique_clase_te,
    default=unique_clase_te
)

unique_area = df['AREA_Label'].unique().tolist()
selected_area = st.sidebar.multiselect(
    "Filtrar por Área Metropolitana",
    options=unique_area,
    default=unique_area
)

# You can add a filter for Department if 'COD_DEPTO' is mapped to names
# unique_deptos = df['Departamento'].unique().tolist()
# selected_deptos = st.sidebar.multiselect(
#     "Filtrar por Departamento",
#     options=unique_deptos,
#     default=unique_deptos
# )


# Apply filters
df_filtered = df[
    (df['Creador_Negocio'].isin(selected_creador)) &
    (df['Motivo_Inicio'].isin(selected_motivo)) &
    (df['Antiguedad_Negocio_Rango'].isin(selected_antiguedad_rango)) &
    (df['Fuente_Recursos'].isin(selected_fuente_recursos)) &
    (df['CLASE_TE_Label'].isin(selected_clase_te)) &
    (df['AREA_Label'].isin(selected_area))
    # Add (df['Departamento'].isin(selected_deptos)) if you implement department filter
]

if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()


# --- Dashboard Sections ---
st.header("Análisis de las Características del Emprendimiento")
st.write(f"*Número total de registros (después de filtros):* {len(df_filtered):,}")

# --- Plot 1: ¿Quién creó el negocio? (P3050) ---
st.subheader("1. Origen de la Creación del Negocio")
df_creador = prepare_data_for_plotly_percentage(df_filtered, 'Creador_Negocio')
if not df_creador.empty:
    fig_creador = px.bar(
        df_creador,
        x='Creador_Negocio',
        y='Porcentaje',
        title='¿Quién creó o constituyó el negocio o actividad?',
        labels={'Creador_Negocio': 'Creador del Negocio', 'Porcentaje': 'Porcentaje de Negocios'},
        hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
    )
    fig_creador.update_yaxes(rangemode="tozero", tickformat=".2f%")
    fig_creador.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    st.plotly_chart(fig_creador, use_container_width=True)
else:
    st.info("No hay datos para mostrar el gráfico de Creador del Negocio.")

st.markdown("---")

# --- Plot 2: Motivo Principal de Inicio (P3051) ---
st.subheader("2. Motivo Principal para Iniciar el Negocio")
df_motivo = prepare_data_for_plotly_percentage(df_filtered, 'Motivo_Inicio')
if not df_motivo.empty:
    fig_motivo = px.bar(
        df_motivo,
        x='Motivo_Inicio',
        y='Porcentaje',
        title='Motivo Principal por el que se Inició el Negocio',
        labels={'Motivo_Inicio': 'Motivo de Inicio', 'Porcentaje': 'Porcentaje de Negocios'},
        hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
    )
    fig_motivo.update_yaxes(rangemode="tozero", tickformat=".2f%")
    fig_motivo.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    st.plotly_chart(fig_motivo, use_container_width=True)
else:
    st.info("No hay datos para mostrar el gráfico de Motivo de Inicio.")

st.markdown("---")

# --- Plot 3: Antigüedad del Negocio (P639) ---
st.subheader("3. Antigüedad del Negocio")
df_antiguedad_rango = prepare_data_for_plotly_percentage(df_filtered, 'Antiguedad_Negocio_Rango')
if not df_antiguedad_rango.empty:
    fig_antiguedad_rango = px.bar(
        df_antiguedad_rango,
        x='Antiguedad_Negocio_Rango',
        y='Porcentaje',
        title='Tiempo de Funcionamiento del Negocio o Actividad',
        labels={'Antiguedad_Negocio_Rango': 'Antigüedad del Negocio', 'Porcentaje': 'Porcentaje de Negocios'},
        hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
    )
    fig_antiguedad_rango.update_yaxes(rangemode="tozero", tickformat=".2f%")
    # Ensure correct order from preprocessing
    fig_antiguedad_rango.update_layout(xaxis={'categoryorder':'array', 'categoryarray':df_antiguedad_rango['Antiguedad_Negocio_Rango'].tolist()}, showlegend=False)
    st.plotly_chart(fig_antiguedad_rango, use_container_width=True)
else:
    st.info("No hay datos para mostrar el gráfico de Antigüedad del Negocio.")

st.markdown("---")

# --- Plot 4: Mayor Fuente de Recursos (P3052) ---
st.subheader("4. Mayor Fuente de Recursos para la Creación del Negocio")
df_fuente_recursos = prepare_data_for_plotly_percentage(df_filtered, 'Fuente_Recursos')
if not df_fuente_recursos.empty:
    fig_fuente_recursos = px.bar(
        df_fuente_recursos,
        x='Fuente_Recursos',
        y='Porcentaje',
        title='Fuente Principal de Recursos para la Creación del Negocio',
        labels={'Fuente_Recursos': 'Fuente de Recursos', 'Porcentaje': 'Porcentaje de Negocios'},
        hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
    )
    fig_fuente_recursos.update_yaxes(rangemode="tozero", tickformat=".2f%")
    fig_fuente_recursos.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    st.plotly_chart(fig_fuente_recursos, use_container_width=True)
else:
    st.info("No hay datos para mostrar el gráfico de Fuente de Recursos.")

st.markdown("---")

# --- Plot 5: Combinación de Antigüedad y Motivo de Inicio (ejemplo de gráfico cruzado) ---
st.subheader("5. Relación entre Motivo de Inicio y Antigüedad")
# Use a smaller subset if this plot becomes too crowded
df_cross_motive_antiguedad = df_filtered.groupby(['Antiguedad_Negocio_Rango', 'Motivo_Inicio'])['F_EXP'].sum().reset_index()
if not df_cross_motive_antiguedad.empty:
    fig_cross_motive_antiguedad = px.bar(
        df_cross_motive_antiguedad,
        x='Antiguedad_Negocio_Rango',
        y='F_EXP',
        color='Motivo_Inicio',
        title='Motivo de Inicio del Negocio por Rango de Antigüedad (Casos Ponderados)',
        labels={'Antiguedad_Negocio_Rango': 'Antigüedad del Negocio', 'F_EXP': 'Casos Ponderados', 'Motivo_Inicio': 'Motivo de Inicio'},
        category_orders={"Antiguedad_Negocio_Rango": df_antiguedad_rango['Antiguedad_Negocio_Rango'].tolist()},
        height=500 # Adjust height for readability
    )
    fig_cross_motive_antiguedad.update_yaxes(rangemode="tozero")
    fig_cross_motive_antiguedad.update_layout(barmode='stack')
    st.plotly_chart(fig_cross_motive_antiguedad, use_container_width=True)
else:
    st.info("No hay datos para mostrar la relación entre Motivo de Inicio y Antigüedad.")


st.markdown("---")

# --- Plot 6 & 7: Impacto Geográfico ---
st.subheader("6. Análisis Geográfico del Emprendimiento")
col_geo1, col_geo2 = st.columns(2)

with col_geo1:
    df_creador_clase_te = df_filtered.groupby(['CLASE_TE_Label', 'Creador_Negocio'])['F_EXP'].sum().reset_index()
    if not df_creador_clase_te.empty:
        fig_creador_clase_te = px.bar(
            df_creador_clase_te,
            x='CLASE_TE_Label',
            y='F_EXP',
            color='Creador_Negocio',
            title='Quién Creó el Negocio por Entorno',
            labels={'CLASE_TE_Label': 'Entorno (Urbana/Rural)', 'F_EXP': 'Casos Ponderados'},
            height=400
        )
        fig_creador_clase_te.update_yaxes(rangemode="tozero")
        st.plotly_chart(fig_creador_clase_te, use_container_width=True)
    else:
        st.info("No hay datos para mostrar quién creó el negocio por entorno.")

with col_geo2:
    # Top 10 Areas by number of businesses for readability
    top_areas = df_filtered.groupby('AREA_Label')['F_EXP'].sum().nlargest(10).index.tolist()
    df_top_areas = df_filtered[df_filtered['AREA_Label'].isin(top_areas)]

    df_motivo_area = df_top_areas.groupby(['AREA_Label', 'Motivo_Inicio'])['F_EXP'].sum().reset_index()
    if not df_motivo_area.empty:
        fig_motivo_area = px.bar(
            df_motivo_area,
            x='AREA_Label',
            y='F_EXP',
            color='Motivo_Inicio',
            title='Motivo de Inicio por Top 10 Áreas Metropolitanas',
            labels={'AREA_Label': 'Área Metropolitana', 'F_EXP': 'Casos Ponderados'},
            height=400
        )
        fig_motivo_area.update_yaxes(rangemode="tozero")
        fig_motivo_area.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_motivo_area, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el motivo de inicio por área metropolitana.")

st.markdown("---")
st.success("Dashboard del Módulo de Emprendimiento generado exitosamente. ¡Explora los datos!")