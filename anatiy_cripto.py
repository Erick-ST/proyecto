import streamlit as st
import pandas as pd
import plotly.express as px
import scipy.stats as stats
from scipy.stats import chi2_contingency, shapiro
import locale

def depuracion(archivo):
    # Lee el archivo CSV separado por ';' y elimina filas con valores faltantes
    bit = pd.read_csv(archivo, sep=';').dropna()
    bit.columns = ['id', 'apertura', 'maximo', 'minimo', 'cierre', 'volumen', 'capitalizacion', 'fecha']
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except:
        pass
    bit['fecha'] = pd.to_datetime(bit['fecha'], format='mixed')
    bit['mes_nombre_es'] = bit['fecha'].dt.strftime('%B')
    bit['mes_anio'] = bit['fecha'].dt.to_period('M')
    cierre_inicio = bit.groupby('mes_anio')['cierre'].first()
    cierre_fin = bit.groupby('mes_anio')['cierre'].last()
    cambio_mes = (cierre_fin - cierre_inicio).apply(lambda x: 'Aumentó' if x > 0 else 'Redujo')
    cambio_mes = cambio_mes.to_dict()
    bit['cambio_mes'] = bit['mes_anio'].map(cambio_mes)
    # Solo elimina 'mes_anio', conserva 'fecha'
    bit = bit.drop(columns=['mes_anio'])
    return bit

# Cargar y depurar los datos
bitcoin = depuracion("Bitcoin.csv")
bitcoin["cripto"] = "Bitcoin"
ethereum = depuracion("Ethereum.csv")
ethereum["cripto"] = "Ethereum"
tether = depuracion("Tether.csv")
tether["cripto"] = "Tether"

# Diccionario para fácil acceso (debe ir antes de usarlo)
criptos = {
    "Bitcoin": bitcoin,
    "Ethereum": ethereum,
    "Tether": tether
}

# --- PRESENTACIÓN DEL PROYECTO Y VISTA PREVIA DE DATOS ---
st.title("Análisis Comparativo de Criptomonedas: Bitcoin, Ethereum y Tether")
st.markdown("""
Este proyecto tiene como objetivo analizar y comparar el comportamiento de las principales criptomonedas: **Bitcoin**, **Ethereum** y **Tether**.  
Se exploran relaciones entre sus precios, volúmenes y tendencias mensuales, utilizando análisis estadísticos y visualizaciones interactivas para comprender mejor su dinámica en el mercado.
""")

# Barra interactiva para mostrar el head de cada cripto (en la barra lateral)
st.header("Vista previa de datos")
cripto_head = st.selectbox(
    "Selecciona la criptomoneda para ver los primeros registros",
    ("Bitcoin", "Ethereum", "Tether")
)
st.write(criptos[cripto_head].head())


# Barra interactiva para seleccionar la criptomoneda
cripto_seleccionada = st.selectbox(
    "Selecciona la criptomoneda",
    ("Bitcoin", "Ethereum", "Tether")
)

df = criptos[cripto_seleccionada]

st.title(f"Análisis de {cripto_seleccionada}")

# Gráfico de línea del cierre a lo largo del tiempo
fig = px.line(df, x="fecha", y="cierre", title=f"Precio de cierre de {cripto_seleccionada} a lo largo del tiempo")
st.plotly_chart(fig)

# Gráfico de barras del volumen mensual
df['mes'] = df['fecha'].dt.to_period('M').astype(str)
volumen_mensual = df.groupby('mes')['volumen'].sum().reset_index()
fig2 = px.bar(volumen_mensual, x="mes", y="volumen", title=f"Volumen mensual de {cripto_seleccionada}")
st.plotly_chart(fig2)

# Gráfico de caja del precio de cierre por mes
fig3 = px.box(df, x="mes_nombre_es", y="cierre", title=f"Distribución del cierre mensual de {cripto_seleccionada}")
st.plotly_chart(fig3)

# Unir los tres dataframes
df_all = pd.concat([bitcoin, ethereum, tether], ignore_index=True)

st.title("Comparativa de Criptomonedas")

# Gráfico de línea: precio de cierre a lo largo del tiempo para las 3 criptos
fig_line = px.line(df_all, x="fecha", y="cierre", color="cripto", title="Precio de cierre a lo largo del tiempo")
st.plotly_chart(fig_line)

# Histograma: distribución de precios de cierre para las 3 criptos
fig_hist = px.histogram(df_all, x="cierre", color="cripto", barmode="overlay", nbins=50, title="Histograma de precios de cierre")
st.plotly_chart(fig_hist)

# Boxplot: distribución de precios de cierre por cripto
fig_box = px.box(df_all, x="cripto", y="cierre", color="cripto", title="Boxplot de precios de cierre por criptomoneda")
st.plotly_chart(fig_box)

st.header("Pruebas estadísticas de correlación entre criptomonedas")

# Unir por fecha para comparar precios de cierre
df_corr = bitcoin[['fecha', 'cierre']].rename(columns={'cierre': 'btc_cierre'})
df_corr = df_corr.merge(ethereum[['fecha', 'cierre']].rename(columns={'cierre': 'eth_cierre'}), on='fecha', how='inner')
df_corr = df_corr.merge(tether[['fecha', 'cierre']].rename(columns={'cierre': 'usdt_cierre'}), on='fecha', how='inner')

# Gráfico de dispersión entre precios de cierre
st.subheader("Gráfico de dispersión entre precios de cierre")
fig_scatter = px.scatter(df_corr, x='btc_cierre', y='eth_cierre', labels={'btc_cierre': 'Bitcoin', 'eth_cierre': 'Ethereum'}, title="Dispersión: Bitcoin vs Ethereum")
st.plotly_chart(fig_scatter)

# Prueba de correlación de Pearson
pearson_btc_eth = stats.pearsonr(df_corr['btc_cierre'], df_corr['eth_cierre'])
pearson_btc_usdt = stats.pearsonr(df_corr['btc_cierre'], df_corr['usdt_cierre'])
pearson_eth_usdt = stats.pearsonr(df_corr['eth_cierre'], df_corr['usdt_cierre'])

st.subheader("Correlación de Pearson (precios de cierre)")
st.write(f"Bitcoin - Ethereum: coef = {pearson_btc_eth[0]:.3f}, p-valor = {pearson_btc_eth[1]:.3g}")
st.write(f"Bitcoin - Tether: coef = {pearson_btc_usdt[0]:.3f}, p-valor = {pearson_btc_usdt[1]:.3g}")
st.write(f"Ethereum - Tether: coef = {pearson_eth_usdt[0]:.3f}, p-valor = {pearson_eth_usdt[1]:.3g}")
st.markdown("""
**Conclusión:**  
No existe una correlación lineal significativa entre los precios de cierre de las criptomonedas analizadas, ya que los coeficientes son bajos y los valores p son mayores a 0.05. Esto indica que los precios de cierre de Bitcoin, Ethereum y Tether no se mueven de manera conjunta de forma lineal.
""")

# Prueba de normalidad Shapiro-Wilk
st.subheader("Prueba de normalidad Shapiro-Wilk (precios de cierre)")
shap_btc = shapiro(df_corr['btc_cierre'])
shap_eth = shapiro(df_corr['eth_cierre'])
shap_usdt = shapiro(df_corr['usdt_cierre'])
st.write(f"Bitcoin: W = {shap_btc[0]:.3f}, p-valor = {shap_btc[1]:.3g}")
st.write(f"Ethereum: W = {shap_eth[0]:.3f}, p-valor = {shap_eth[1]:.3g}")
st.write(f"Tether: W = {shap_usdt[0]:.3f}, p-valor = {shap_usdt[1]:.3g}")
st.markdown("""
**Conclusión:**  
Los precios de cierre de Ethereum siguen una distribución normal, mientras que los de Bitcoin y Tether no. Esto sugiere que para análisis estadísticos más avanzados, se debe tener precaución y considerar métodos no paramétricos para Bitcoin y Tether.
""")

# Prueba de Chi-cuadrado sobre la tendencia de subida/bajada mensual
st.subheader("Chi-cuadrado sobre tendencia de subida/bajada mensual")
# Unir por mes y tendencia
btc_mes = bitcoin[['mes_nombre_es', 'cambio_mes']].rename(columns={'cambio_mes': 'btc_tend'})
eth_mes = ethereum[['mes_nombre_es', 'cambio_mes']].rename(columns={'cambio_mes': 'eth_tend'})
usdt_mes = tether[['mes_nombre_es', 'cambio_mes']].rename(columns={'cambio_mes': 'usdt_tend'})

tendencias = btc_mes.merge(eth_mes, on='mes_nombre_es', how='inner').merge(usdt_mes, on='mes_nombre_es', how='inner')

# Bitcoin vs Ethereum
tabla_btc_eth = pd.crosstab(tendencias['btc_tend'], tendencias['eth_tend'])
chi2_btc_eth, p_btc_eth, _, _ = chi2_contingency(tabla_btc_eth)
st.write("Bitcoin vs Ethereum: Chi2 = {:.3f}, p-valor = {:.3g}".format(chi2_btc_eth, p_btc_eth))

# Bitcoin vs Tether
tabla_btc_usdt = pd.crosstab(tendencias['btc_tend'], tendencias['usdt_tend'])
chi2_btc_usdt, p_btc_usdt, _, _ = chi2_contingency(tabla_btc_usdt)
st.write("Bitcoin vs Tether: Chi2 = {:.3f}, p-valor = {:.3g}".format(chi2_btc_usdt, p_btc_usdt))

# Ethereum vs Tether
tabla_eth_usdt = pd.crosstab(tendencias['eth_tend'], tendencias['usdt_tend'])
chi2_eth_usdt, p_eth_usdt, _, _ = chi2_contingency(tabla_eth_usdt)
st.write("Ethereum vs Tether: Chi2 = {:.3f}, p-valor = {:.3g}".format(chi2_eth_usdt, p_eth_usdt))
st.markdown("""
**Conclusión:**  
Existe una asociación estadísticamente significativa entre las tendencias mensuales de subida o bajada de las criptomonedas. Aunque los precios no están correlacionados linealmente, la tendencia de si suben o bajan en el mes sí está relacionada entre ellas.
""")
st.header("Preguntas y Respuestas")

st.markdown("""
**1. ¿Existe una relación lineal fuerte entre los precios de cierre de Bitcoin, Ethereum y Tether?**  
*No, según la correlación de Pearson, los coeficientes son bajos y los valores p altos, lo que indica que no hay una relación lineal significativa entre los precios de cierre de estas criptomonedas.*

**2. ¿Alguna de las criptomonedas presenta precios de cierre con distribución normal?**  
*Sí, solo Ethereum muestra una distribución normal en sus precios de cierre (p-valor > 0.05 en la prueba de Shapiro-Wilk). Bitcoin y Tether no presentan normalidad.*

**3. ¿Las tendencias mensuales de subida o bajada están asociadas entre las criptomonedas?**  
*Sí, las pruebas de Chi-cuadrado muestran que existe una asociación estadísticamente significativa entre las tendencias mensuales de subida o bajada de las tres criptomonedas.*

**4. ¿Se observan diferencias visuales en la volatilidad o comportamiento de las criptomonedas en los gráficos?**  
*Sí, los boxplots y los histogramas muestran que Bitcoin y Ethereum tienen mayor variabilidad en sus precios de cierre, mientras que Tether es mucho más estable.*

**5. ¿Qué implicaciones tienen estos resultados para el análisis de mercado de criptomonedas?**  
*Los resultados sugieren que, aunque las criptomonedas pueden compartir tendencias generales de mercado (subidas o bajadas mensuales), sus precios de cierre no están fuertemente correlacionados de forma lineal. Además, solo Ethereum puede analizarse con métodos paramétricos clásicos, mientras que para Bitcoin y Tether se recomiendan métodos no paramétricos.*
""")
st.header("Conclusiones")

st.markdown("""
**1. Correlación de Pearson (precios de cierre):**  
No existe una correlación lineal significativa entre los precios de cierre de las criptomonedas analizadas, ya que los coeficientes son bajos y los valores p son mayores a 0.05. Esto indica que los precios de cierre de Bitcoin, Ethereum y Tether no se mueven de manera conjunta de forma lineal.

**2. Prueba de normalidad Shapiro-Wilk (precios de cierre):**  
Los precios de cierre de Ethereum siguen una distribución normal, mientras que los de Bitcoin y Tether no. Esto sugiere que para análisis estadísticos más avanzados, se debe tener precaución y considerar métodos no paramétricos para Bitcoin y Tether.

**3. Chi-cuadrado sobre tendencia de subida/bajada mensual:**  
Existe una asociación estadísticamente significativa entre las tendencias mensuales de subida o bajada de las criptomonedas. Aunque los precios no están correlacionados linealmente, la tendencia de si suben o bajan en el mes sí está relacionada entre ellas.

**Resumen general:**  
- No hay correlación lineal significativa entre los precios de cierre de las criptomonedas.
- Solo Ethereum presenta precios de cierre con distribución normal.
- Las tendencias mensuales de subida o bajada sí están asociadas entre las criptomonedas, lo que sugiere que pueden compartir factores de mercado que afectan su comportamiento mensual.
""")
