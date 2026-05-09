import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(page_title="Job Lakehouse Query", page_icon="📊", layout="wide")

DB_PATH = "dbt/job_lakehouse.duckdb"

st.title("📊 Job Lakehouse Query Tool")

if 'conn' not in st.session_state:
    st.session_state.conn = duckdb.connect(DB_PATH, read_only=True)

conn = st.session_state.conn

# Sidebar
st.sidebar.header("Database")
tables = [t[0] for t in conn.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
).fetchall()]

st.sidebar.subheader("Tables")
for t in tables:
    cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    st.sidebar.write(f"• {t} ({cnt})")

# Quick queries
st.sidebar.subheader("Quick Queries")
queries = {
    "Top Companies": "SELECT * FROM dim_company LIMIT 20",
    "Job Count": "SELECT COUNT(*) as total_jobs FROM fact_job_posting",
    "Sample Jobs": "SELECT * FROM fact_job_posting LIMIT 10",
}
selected_query = st.sidebar.selectbox("Select Query", list(queries.keys()))

# Main area
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_area("SQL Query", queries[selected_query], height=80)
    
    if st.button("Run Query", type="primary"):
        try:
            result = conn.execute(query).fetchdf()
            st.success(f"Returned {len(result)} rows")
            st.dataframe(result, use_container_width=True, height=400)
            
            # Show schema
            with st.expander("Column Types"):
                st.table(result.dtypes.apply(lambda x: pd.Series({'Column': x.name, 'Type': str(x.dtype)})))
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.subheader("Sample Queries")
    st.code("SELECT * FROM dim_company LIMIT 10", language="sql")
    st.code("SELECT COUNT(*) FROM dim_company", language="sql")
    st.code("SELECT * FROM fact_job_posting LIMIT 5", language="sql")

conn.close()