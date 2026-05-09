import streamlit as st
import duckdb

st.set_page_config(page_title="Job Lakehouse Query", layout="wide")
st.title("📊 Job Lakehouse Query Tool")

# Connect to DuckDB
conn = duckdb.connect('/app/dbt/job_lakehouse.duckdb', read_only=True)

# Get tables
tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
table_names = [t[0] for t in tables]

# Sidebar - table selector
st.sidebar.header("Select Table")
selected_table = st.sidebar.selectbox("Tables", table_names)

if selected_table:
    # Get table schema
    st.subheader(f"Schema: {selected_table}")
    schema = conn.execute(f"DESCRIBE {selected_table}").fetchall()
    st.table([{"Column": s[0], "Type": s[1]} for s in schema])
    
    # Query input
    st.subheader("Query")
    default_query = f"SELECT * FROM {selected_table} LIMIT 100"
    query = st.text_area("SQL Query", default_query, height=100)
    
    if st.button("Run Query"):
        try:
            result = conn.execute(query).fetchdf()
            st.success(f"Returned {len(result)} rows")
            st.dataframe(result, use_container_width=True)
            
            # Export option
            csv = result.to_csv(index=False)
            st.download_button("Download CSV", csv, f"{selected_table}.csv", "text/csv")
        except Exception as e:
            st.error(f"Error: {e}")

conn.close()