import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuration ---
CSV_PATH = 'Módulo de identificación.csv' # Make sure this file is in the same directory
APP_TITLE = "Dashboard Interactivo de Micronegocios"

# --- Helper Function for Data Preparation ---
@st.cache_data # Cache data to avoid reloading on every rerun
def load_and_preprocess_data(csv_file_path):
    """Loads, cleans, and preprocesses the data for the dashboard."""
   
    st.write(f"Cargando y preprocesando datos desde: {csv_file_path}")

    df = None
    required_cols = ['P35', 'GRUPOS12', 'P241', 'P3034', 'P3031', 'AREA', 'CLASE_TE', 'F_EXP', 'DIRECTORIO']

    if not os.path.exists(csv_file_path):
        st.error(f"ERROR: El archivo CSV NO se encontró en la ruta: {csv_file_path}")
        st.stop() # Stop the app if file is not found

    try:
        # Try reading with comma separator first
        df_temp = pd.read_csv(csv_file_path, encoding='latin-1', sep=',', low_memory=False)
        found_cols = [col for col in required_cols if col in df_temp.columns]
        if not found_cols:
            raise ValueError("Ninguna de las columnas requeridas se encontró con separador ','.")
        df = df_temp[found_cols].copy()
        st.write(f"Datos cargados con separador ',' y columnas: {df.columns.tolist()}")
    except Exception as e:
        st.warning(f"Error al cargar con separador ',': {e}. Intentando con ';'")
        try:
            # Fallback to semicolon separator
            df_temp = pd.read_csv(csv_file_path, encoding='latin-1', sep=';', low_memory=False)
            found_cols = [col for col in required_cols if col in df_temp.columns]
            if not found_cols:
                raise ValueError("Ninguna de las columnas requeridas se encontró ni con ',' ni con ';'.")
            df = df_temp[found_cols].copy()
            st.write(f"Datos cargados con separador ';' y columnas: {df.columns.tolist()}")
        except Exception as e_fallback:
            st.error(f"ERROR CRÍTICO: No se pudo cargar el archivo correctamente. Detalle: {e_fallback}")
            st.stop() # Stop the app if data loading fails

    if df is None or df.empty:
        st.error("ERROR: El DataFrame está vacío o no se pudo cargar.")
        st.stop()

    # --- Preprocessing ---
    if 'DIRECTORIO' in df.columns:
        rows_before_dedup = df.shape[0]
        df.drop_duplicates(subset=['DIRECTORIO'], keep='first', inplace=True)
        rows_after_dedup = df.shape[0]
        if rows_before_dedup > rows_after_dedup:
            st.info(f"Se eliminaron {rows_before_dedup - rows_after_dedup} filas duplicadas en 'DIRECTORIO'.")

    # Mapeo y limpieza de P35 (Sexo del propietario)
    if 'P35' in df.columns:
        df['Género'] = pd.to_numeric(df['P35'], errors='coerce')
        df['Género'] = df['Género'].map({1: 'Hombre', 2: 'Mujer'})
        df['Género'].fillna('Desconocido', inplace=True)
    else: df['Género'] = 'No Disponible'

    # Mapeo y limpieza de GRUPOS12 (Rama de actividad)
    if 'GRUPOS12' in df.columns:
        grupos12_map = {
            1: 'Agricultura, Ganadería, Caza y Silvicultura', 2: 'Explotación de Minas y Canteras',
            3: 'Industrias Manufactureras', 4: 'Suministro de Electricidad, Gas y Agua',
            5: 'Construcción', 6: 'Comercio al por mayor y al por menor',
            7: 'Hoteles y Restaurantes', 8: 'Transporte, Almacenamiento y Comunicaciones',
            9: 'Intermediación Financiera y Seguros', 10: 'Actividades Inmobiliarias, Empresariales y de Alquiler',
            11: 'Administración Pública y Defensa; Educación; Servicios Sociales y de Salud',
            12: 'Otras Actividades de Servicios Comunitarias, Sociales y Personales'
        }
        df['Industria_Label'] = pd.to_numeric(df['GRUPOS12'], errors='coerce')
        df['Industria_Label'] = df['Industria_Label'].map(grupos12_map)
        df['Industria_Label'].fillna('Desconocido', inplace=True)
    else: df['Industria_Label'] = 'No Disponible'

    # Edad del propietario (P241) y creación de grupos de edad
    if 'P241' in df.columns:
        df['Edad'] = pd.to_numeric(df['P241'], errors='coerce')
        df.dropna(subset=['Edad'], inplace=True)
        bins_edad = [0, 25, 35, 45, 55, 65, df['Edad'].max() + 10 if df['Edad'].max() > 0 else 100]
        labels_edad = ['<25', '25-34', '35-44', '45-54', '55-64', '65+']
        df['Edad_Grupo'] = pd.cut(df['Edad'], bins=bins_edad, labels=labels_edad, right=False, include_lowest=True)
        # Ensure categories are explicitly set for correct ordering in plots
        df['Edad_Grupo'] = pd.Categorical(df['Edad_Grupo'], categories=labels_edad, ordered=True)
    else:
        df['Edad'] = None
        df['Edad_Grupo'] = 'No Disponible'

    # Meses de operación del negocio (P3034) y creación de grupos de antigüedad
    if 'P3034' in df.columns:
        df['Antiguedad_Meses'] = pd.to_numeric(df['P3034'], errors='coerce')
        df.dropna(subset=['Antiguedad_Meses'], inplace=True)
        bins_antiguedad = [0, 12, 36, 60, 120, 240, df['Antiguedad_Meses'].max() + 10 if df['Antiguedad_Meses'].max() > 0 else 250]
        labels_antiguedad = ['<1 año', '1-3 años', '3-5 años', '5-10 años', '10-20 años', '20+ años']
        df['Antiguedad_Negocio_Grupo'] = pd.cut(df['Antiguedad_Meses'], bins=bins_antiguedad, labels=labels_antiguedad, right=False, include_lowest=True)
        # Ensure categories are explicitly set for correct ordering in plots
        df['Antiguedad_Negocio_Grupo'] = pd.Categorical(df['Antiguedad_Negocio_Grupo'], categories=labels_antiguedad, ordered=True)
    else:
        df['Antiguedad_Meses'] = None
        df['Antiguedad_Negocio_Grupo'] = 'No Disponible'

    # P3031 (Tiene ayuda)
    if 'P3031' in df.columns:
        df['Tiene_Ayuda'] = pd.to_numeric(df['P3031'], errors='coerce')
        df['Tiene_Ayuda'] = df['Tiene_Ayuda'].map({1: 'Sí', 2: 'No'})
        df['Tiene_Ayuda'].fillna('Desconocido', inplace=True)
    else: df['Tiene_Ayuda'] = 'No Disponible'

    # AREA y CLASE_TE para Ubicación
    if 'AREA' in df.columns:
        df['AREA_Label'] = df['AREA'].fillna('Desconocida').astype(str)
    else: df['AREA_Label'] = 'No Disponible'

    if 'CLASE_TE' in df.columns:
        df['CLASE_TE_Label'] = pd.to_numeric(df['CLASE_TE'], errors='coerce')
        df['CLASE_TE_Label'] = df['CLASE_TE_Label'].map({1: 'Urbana', 2: 'Rural'})
        df['CLASE_TE_Label'].fillna('Desconocido', inplace=True)
    else: df['CLASE_TE_Label'] = 'No Disponible'

    # Factor de Expansión (F_EXP)
    if 'F_EXP' not in df.columns:
        st.warning("La columna 'F_EXP' no se encontró. Los cálculos de porcentaje no estarán ponderados.")
        df['F_EXP'] = 1 # Default to 1 if not found

    return df

# --- Function to Prepare Data for Plotly ---
def prepare_data_for_plotly(dataframe, group_col):
    """Prepares data for Plotly charts, calculating ponderated percentages."""
    if group_col not in dataframe.columns:
        st.warning(f"Columna '{group_col}' no encontrada en el DataFrame.")
        return pd.DataFrame() # Return empty DataFrame

    temp_df = dataframe.dropna(subset=[group_col])
    if temp_df.empty:
        return pd.DataFrame()

    df_grouped = temp_df.groupby(group_col)['F_EXP'].sum().reset_index()
    df_grouped.columns = [group_col, 'F_EXP_Sum']

    total_f_exp = df_grouped['F_EXP_Sum'].sum()
    df_grouped['Porcentaje'] = (df_grouped['F_EXP_Sum'] / total_f_exp) * 100 if total_f_exp > 0 else 0
   
    # Ensure proper sorting for ordered categories like age/antiquity
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

# Load data once
df = load_and_preprocess_data(CSV_PATH)

# Check if data loading was successful
if df.empty:
    st.error("No se pudieron cargar los datos o el DataFrame está vacío después del preprocesamiento.")
    st.stop()

# --- Sidebar Filters (Optional but Recommended) ---
st.sidebar.header("Filtros del Dashboard")

# Example Filter: Filter by Gender
unique_genders = df['Género'].unique().tolist()
selected_genders = st.sidebar.multiselect(
    "Filtrar por Género del Propietario",
    options=unique_genders,
    default=unique_genders
)

# Example Filter: Filter by Industry
unique_industries = df['Industria_Label'].unique().tolist()
selected_industries = st.sidebar.multiselect(
    "Filtrar por Industria",
    options=unique_industries,
    default=unique_industries
)

# Apply filters
df_filtered = df[
    (df['Género'].isin(selected_genders)) &
    (df['Industria_Label'].isin(selected_industries))
]

if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
    st.stop()


# --- Dashboard Pages/Sections ---

st.header("Análisis General")
st.write(f"**Número total de registros (después de duplicados y filtros):** {len(df_filtered):,}")

# --- Plot 1: Industria (GRUPOS12) ---
st.subheader("Distribución de Negocios por Industria")
df_industria = prepare_data_for_plotly(df_filtered, 'Industria_Label')
if not df_industria.empty:
    fig_industria = px.bar(
        df_industria,
        x='Industria_Label',
        y='Porcentaje',
        title='Porcentaje de Negocios por Industria',
        labels={'Industria_Label': 'Grupo de Industria', 'Porcentaje': 'Porcentaje de Negocios'},
        hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'} # Show weighted count and percentage on hover
    )
    fig_industria.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    fig_industria.update_yaxes(rangemode="tozero", tickformat=".2f%")
    st.plotly_chart(fig_industria, use_container_width=True)
else:
    st.info("No hay datos para mostrar el gráfico de Industria con los filtros actuales.")

st.markdown("---")

# --- Plot 2 & 3: Género (P35) and Edad (P241) ---
st.subheader("Análisis Demográfico de Propietarios")
col1, col2 = st.columns(2)

with col1:
    df_genero = prepare_data_for_plotly(df_filtered, 'Género')
    if not df_genero.empty:
        fig_genero = px.bar(
            df_genero,
            x='Género',
            y='Porcentaje',
            title='Porcentaje de Propietarios por Género',
            labels={'Género': 'Género', 'Porcentaje': 'Porcentaje de Propietarios'},
            hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
        )
        fig_genero.update_yaxes(rangemode="tozero", tickformat=".2f%")
        fig_genero.update_layout(showlegend=False)
        st.plotly_chart(fig_genero, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el gráfico de Género con los filtros actuales.")

with col2:
    df_edad = prepare_data_for_plotly(df_filtered, 'Edad_Grupo')
    if not df_edad.empty:
        fig_edad = px.bar(
            df_edad,
            x='Edad_Grupo',
            y='Porcentaje',
            title='Porcentaje de Propietarios por Edad',
            labels={'Edad_Grupo': 'Grupo de Edad', 'Porcentaje': 'Porcentaje de Propietarios'},
            hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
        )
        fig_edad.update_yaxes(rangemode="tozero", tickformat=".2f%")
        fig_edad.update_layout(xaxis={'categoryorder':'array', 'categoryarray':df_edad['Edad_Grupo'].tolist()}, showlegend=False) # Keep original order
        st.plotly_chart(fig_edad, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el gráfico de Edad con los filtros actuales.")

st.markdown("---")

# --- Plot 4 & 5: Antigüedad del Negocio (P3034) and Tiene Ayuda (P3031) ---
st.subheader("Características del Negocio")
col3, col4 = st.columns(2)

with col3:
    df_antiguedad = prepare_data_for_plotly(df_filtered, 'Antiguedad_Negocio_Grupo')
    if not df_antiguedad.empty:
        fig_antiguedad = px.bar(
            df_antiguedad,
            x='Antiguedad_Negocio_Grupo',
            y='Porcentaje',
            title='Porcentaje de Negocios por Antigüedad',
            labels={'Antiguedad_Negocio_Grupo': 'Antigüedad (Años)', 'Porcentaje': 'Porcentaje de Negocios'},
            hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
        )
        fig_antiguedad.update_yaxes(rangemode="tozero", tickformat=".2f%")
        fig_antiguedad.update_layout(xaxis={'categoryorder':'array', 'categoryarray':df_antiguedad['Antiguedad_Negocio_Grupo'].tolist()}, showlegend=False) # Keep original order
        st.plotly_chart(fig_antiguedad, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el gráfico de Antigüedad del Negocio con los filtros actuales.")

with col4:
    df_ayuda = prepare_data_for_plotly(df_filtered, 'Tiene_Ayuda')
    if not df_ayuda.empty:
        fig_ayuda = px.bar(
            df_ayuda,
            x='Tiene_Ayuda',
            y='Porcentaje',
            title='Porcentaje de Negocios con Personal de Ayuda',
            labels={'Tiene_Ayuda': '¿Tiene Personal de Ayuda?', 'Porcentaje': 'Porcentaje de Negocios'},
            hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
        )
        fig_ayuda.update_yaxes(rangemode="tozero", tickformat=".2f%")
        fig_ayuda.update_layout(showlegend=False)
        st.plotly_chart(fig_ayuda, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el gráfico de Personal de Ayuda con los filtros actuales.")

st.markdown("---")

# --- Plot 6 & 7: Área Geográfica (AREA) and Clase_TE (Urbana/Rural) ---
st.subheader("Ubicación Geográfica de Negocios")
col5, col6 = st.columns(2)

with col5:
    df_area = prepare_data_for_plotly(df_filtered, 'AREA_Label')
    if not df_area.empty:
        fig_area = px.bar(
            df_area,
            x='AREA_Label',
            y='Porcentaje',
            title='Porcentaje de Negocios por Área Geográfica',
            labels={'AREA_Label': 'Área Geográfica', 'Porcentaje': 'Porcentaje de Negocios'},
            hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
        )
        fig_area.update_yaxes(rangemode="tozero", tickformat=".2f%")
        fig_area.update_layout(showlegend=False)
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el gráfico de Área Geográfica con los filtros actuales.")

with col6:
    df_clase_te = prepare_data_for_plotly(df_filtered, 'CLASE_TE_Label')
    if not df_clase_te.empty:
        fig_clase_te = px.bar(
            df_clase_te,
            x='CLASE_TE_Label',
            y='Porcentaje',
            title='Porcentaje de Negocios por Entorno',
            labels={'CLASE_TE_Label': 'Entorno (Urbana/Rural)', 'Porcentaje': 'Porcentaje de Negocios'},
            hover_data={'F_EXP_Sum': True, 'Porcentaje': ':.2f'}
        )
        fig_clase_te.update_yaxes(rangemode="tozero", tickformat=".2f%")
        fig_clase_te.update_layout(showlegend=False)
        st.plotly_chart(fig_clase_te, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el gráfico de Entorno (Urbana/Rural) con los filtros actuales.")

st.markdown("---")
st.success("Dashboard cargado y listo para interactuar.")