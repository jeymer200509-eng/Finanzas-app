import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from database import init_db, add_transaction, get_all_transactions, delete_transaction

# Initial configuration of the site
st.set_page_config(page_title="Gestión de Finanzas", page_icon="💰", layout="wide")

# Initialize SQLite database
init_db()

# Initialize last date used in session state, defaults to today
if 'last_date' not in st.session_state:
    st.session_state.last_date = datetime.date.today()

# Custom Styling (Dark/Rich Aesthetics)
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #f0f2f6;
    }
    .metric-container {
        display: flex;
        justify-content: center;
        text-align: center;
        padding: 20px;
        background-color: #1e2129;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #a0aabf;
    }
    .positive { color: #2ecc71; }
    .negative { color: #e74c3c; }
    .neutral { color: #3498db; }
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135673.png", width=80)
    st.title("Nuevo Registro")
    
    t_type = st.radio("Tipo de Movimiento", ["Ingreso", "Gasto"], horizontal=True)

    with st.form("transaction_form", clear_on_submit=True):
        t_date = st.date_input("Fecha", st.session_state.last_date)
        t_amount = st.number_input(
            "Monto (COP)", 
            min_value=0.0, 
            format="%.2f",
            help="Digita el número sin puntos ni comas de miles. Por ejemplo, para un millón escribe 1000000. Usa el punto (.) solo si necesitas separar decimales."
        )
        
        if t_type == "Gasto":
            t_category = st.selectbox("Categoría", [
                "Alimentación", "Domicilios", "Café", "Servicio de tostión",
                "Servicios (Agua/Luz/Internet)", "Inventario / Mercadería", 
                "Nómina / Salarios", "Alquiler", "Marketing", "Mantenimiento", "Otros"
            ])
        else:
            t_category = st.selectbox("Categoría", [
                "Efectivo", "Transferencias"
            ])
            
        submitted = st.form_submit_button("Guardar Movimiento", use_container_width=True)
        
        if submitted:
            add_transaction(t_date.strftime("%Y-%m-%d"), t_amount, t_category, t_type)
            # Update session state date so the next form uses this date
            st.session_state.last_date = t_date
            st.success("✅ ¡Movimiento registrado con éxito!")
            # Retain a small delay or just let the app rerun to show updated data

# ----------------- MAIN VIEW -----------------
st.title("📊 Panel de Control Financiero")
st.markdown("Visualiza y administra los ingresos y gastos de tu negocio de forma centralizada.")

# Load Data
df = get_all_transactions()

if df.empty:
    st.info("👋 ¡Bienvenido! Aún no hay transacciones registradas. Usa el menú de la izquierda para agregar tu primer ingreso o gasto.")
    st.image("https://illustrations.popsy.co/amber/surreal-hourglass.svg", width=300)
else:
    # Preprocess Data
    df['date'] = pd.to_datetime(df['date'])
    
    # KPIs Calculation
    total_ingresos = df[df['type'] == 'Ingreso']['amount'].sum()
    total_gastos = df[df['type'] == 'Gasto']['amount'].sum()
    balance_actual = total_ingresos - total_gastos
    
    # Render Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Balance Actual", value=f"COP {balance_actual:,.2f}", 
                  delta="Rendimiento Total", delta_color="normal" if balance_actual >= 0 else "inverse")
    with col2:
        st.metric(label="Total Ingresos 📈", value=f"COP {total_ingresos:,.2f}")
    with col3:
        st.metric(label="Total Gastos 📉", value=f"COP {total_gastos:,.2f}")

    st.markdown("---")

    # Tabs for Reports
    tab_dashboard, tab_weekly, tab_monthly, tab_data = st.tabs([
        "📈 Dashboard General", 
        "📅 Reporte Semanal", 
        "🗓️ Reporte Mensual", 
        "🗃️ Historial de Datos"
    ])
    
    # 1. DASHBOARD GENERAL (Pie chart & Daily chart)
    with tab_dashboard:
        colA, colB = st.columns(2)
        
        with colA:
            st.subheader("Distribución de Movimientos")
            if total_ingresos > 0 or total_gastos > 0:
                fig_pie = px.pie(
                    values=[total_ingresos, total_gastos], 
                    names=['Ingresos', 'Gastos'], 
                    color=['Ingresos', 'Gastos'],
                    color_discrete_map={'Ingresos':'#2ecc71', 'Gastos':'#e74c3c'},
                    hole=0.45
                )
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("No hay datos suficientes para el gráfico.")
                
        with colB:
            st.subheader("Gastos por Categoría")
            gastos_df = df[df['type'] == 'Gasto']
            if not gastos_df.empty:
                gastos_cat = gastos_df.groupby('category')['amount'].sum().sort_values(ascending=True).reset_index()
                fig_bar = px.bar(
                    gastos_cat, 
                    x='amount', 
                    y='category', 
                    orientation='h',
                    color='amount',
                    color_continuous_scale="Reds"
                )
                fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No hay gastos registrados para analizar categorías.")

    # 2. WEEKLY REPORT
    with tab_weekly:
        st.subheader("Resumen Semanal de Flujo de Caja")
        # Prepare weekly data
        df['year_week'] = df['date'].dt.strftime('%Y-W%V')
        weekly_summary = df.groupby(['year_week', 'type'])['amount'].sum().reset_index()
        
        if not weekly_summary.empty:
            fig_weekly = px.bar(
                weekly_summary, 
                x='year_week', 
                y='amount', 
                color='type', 
                barmode='group',
                color_discrete_map={'Ingreso':'#2ecc71', 'Gasto':'#e74c3c'},
                labels={'year_week': 'Semana del Año', 'amount': 'Monto (COP)', 'type': 'Movimiento'}
            )
            st.plotly_chart(fig_weekly, use_container_width=True)

    # 3. MONTHLY REPORT
    with tab_monthly:
        st.subheader("Evolución Mensual")
        # Prepare monthly data
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        monthly_summary = df.groupby(['year_month', 'type'])['amount'].sum().reset_index()
        
        if not monthly_summary.empty:
            # Line chart or area chart
            fig_monthly = px.area(
                monthly_summary, 
                x='year_month', 
                y='amount', 
                color='type',
                color_discrete_map={'Ingreso':'#2ecc71', 'Gasto':'#e74c3c'},
                labels={'year_month': 'Mes', 'amount': 'Monto (COP)', 'type': 'Movimiento'}
            )
            st.plotly_chart(fig_monthly, use_container_width=True)

    # 4. DATA HISTORY (Table and Delete feature simulation)
    with tab_data:
        st.subheader("Registro Completo de Transacciones")
        
        # We can format the dataframe for better display
        display_df = df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        # Sort descending
        display_df = display_df.sort_values(by='date', ascending=False)
        
        # Insert a selection checkbox column
        display_df.insert(0, "Seleccionar", False)
        
        # Show interactive dataframe
        edited_df = st.data_editor(
            display_df[['Seleccionar', 'id', 'date', 'type', 'category', 'amount']], 
            use_container_width=True,
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn("Seleccionar", default=False),
                "id": st.column_config.NumberColumn("ID", format="%d"),
                "date": "Fecha",
                "type": "Tipo",
                "category": "Categoría",
                "amount": st.column_config.NumberColumn("Monto (COP)", format="COP %.2f")
            },
            hide_index=True,
            disabled=["id", "date", "type", "category", "amount"]
        )
        
        # Get selected rows
        selected_ids = edited_df[edited_df["Seleccionar"]]["id"].tolist()
        
        # Expander to delete multiple records
        with st.expander("🗑️ Eliminar registros seleccionados"):
            st.write(f"Has seleccionado **{len(selected_ids)}** registro(s).")
            if st.button("Eliminar Seleccionados", type="primary", disabled=len(selected_ids) == 0):
                for del_id in selected_ids:
                    delete_transaction(del_id)
                st.success(f"¡Se han eliminado {len(selected_ids)} registro(s) con éxito!")
                st.rerun()

