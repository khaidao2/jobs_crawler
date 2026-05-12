import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(
    page_title="Job Crawler Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = os.environ.get('DB_PATH', 'dbt/job_lakehouse.duckdb')
S3_ENDPOINT = os.environ.get('AWS_S3_ENDPOINT', 'http://minio:9000')
S3_KEY = os.environ.get('AWS_ACCESS_KEY_ID', 'admin')
S3_SECRET = os.environ.get('AWS_SECRET_ACCESS_KEY', 'changeme123')

st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .metric-label { font-size: 14px; color: #666; }
    .metric-value { font-size: 24px; font-weight: bold; color: #1f77b4; }
</style>
""", unsafe_allow_html=True)

# Database connection function
def get_connection():
    conn = duckdb.connect(DB_PATH, read_only=True)
    # Configure S3/MinIO access using parameterized settings
    try:
        conn.execute("SET s3_access_key_id = ?", [S3_KEY])
        conn.execute("SET s3_secret_access_key = ?", [S3_SECRET])
        conn.execute("SET s3_endpoint = ?", [S3_ENDPOINT])
        conn.execute("SET s3_url_style = 'path'")
        conn.execute("SET s3_use_ssl = 'false'")
    except Exception:
        pass
    return conn

def get_table_counts(conn):
    tables = {}
    for t in ['dim_company', 'dim_job', 'fact_job_posting', 'stg_jobs', 'int_jobs_dedup']:
        try:
            tables[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except:
            tables[t] = 0
    return tables

# Sidebar
st.sidebar.title("📊 Job Crawler Monitor")
st.sidebar.markdown("---")

# Menu
menu = st.sidebar.radio(
    "Navigation",
    ["📈 Overview", "💼 Jobs", "🏢 Companies", "📊 Analytics", "🔍 Query Tool"]
)

# ==================== OVERVIEW ====================
if menu == "📈 Overview":
    st.title("📈 System Overview")
    
    try:
        conn = get_connection()
        counts = get_table_counts(conn)
        conn.close()
    except Exception as e:
        st.error(f"Cannot connect to database: {e}")
        counts = {'dim_company': 0, 'fact_job_posting': 0, 'stg_jobs': 0, 'int_jobs_dedup': 0}
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jobs", counts.get('fact_job_posting', 0))
    with col2:
        st.metric("Unique Companies", counts.get('dim_company', 0))
    with col3:
        st.metric("Staging Records", counts.get('stg_jobs', 0))
    with col4:
        st.metric("Deduplicated", counts.get('int_jobs_dedup', 0))
    
    st.markdown("---")
    
    # Quick Stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Data Distribution")
        if counts['dim_company'] > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Companies', 'Jobs', 'Staging'],
                values=[counts['dim_company'], counts['fact_job_posting'], counts['stg_jobs']],
                hole=0.4
            )])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🔗 Table Health")
        for table, count in counts.items():
            status = "✅" if count > 0 else "❌"
            st.write(f"{status} **{table}**: {count:,} rows")

# ==================== JOBS ====================
elif menu == "💼 Jobs":
    st.title("💼 Job Postings")
    
    conn = None
    try:
        conn = get_connection()
        df = conn.execute("SELECT * FROM fact_job_posting ORDER BY crawled_at DESC").fetchdf()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Jobs", len(df))
        with col2:
            st.metric("Unique Job IDs", df['job_id'].nunique())
        
        st.subheader("Sample Data")
        st.dataframe(df, height=400)
        
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        if conn:
            conn.close()

# ==================== COMPANIES ====================
elif menu == "🏢 Companies":
    st.title("🏢 Companies")
    
    conn = get_connection()
    try:
        df = conn.execute("SELECT * FROM dim_company").fetchdf()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Companies", len(df))
        with col2:
            empty_companies = df[df['company_name'] == ''].shape[0]
            st.metric("Empty Company Names", empty_companies)
        
        # Search
        search = st.text_input("Search Company", "")
        if search:
            df = df[df['company_name'].str.contains(search, case=False, na=False)]
        
        st.dataframe(df, height=400)
        
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()

# ==================== ANALYTICS ====================
elif menu == "📊 Analytics":
    st.title("📊 Data Analytics")
    
    try:
        conn = get_connection()
        df = conn.execute("SELECT * FROM fact_job_posting").fetchdf()
        conn.close()
        
        if len(df) > 0:
            tab1, tab2, tab3 = st.tabs(["💰 Salary", "⏳ Experience", "🏢 Companies"])
            
            with tab1:
                st.subheader("💰 Salary Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Filter out nulls for distribution
                    salary_df = df[df['salary_min'].notnull()]
                    if not salary_df.empty:
                        fig = px.histogram(salary_df, x="salary_min", nbins=20, 
                                         title="Salary Min Distribution (VND)",
                                         labels={'salary_min': 'Min Salary'},
                                         color_discrete_sequence=['#2ecc71'])
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    salary_max_df = df[df['salary_max'].notnull()]
                    if not salary_max_df.empty:
                        fig = px.box(salary_max_df, x="source", y="salary_max", 
                                   title="Salary Max by Platform",
                                   color="source")
                        st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"Jobs with negotiable salary: {df[df['deal_salary'] == True].shape[0]}")

            with tab2:
                st.subheader("⏳ Experience Requirements")
                exp_df = df[df['experience_min'].notnull()]
                if not exp_df.empty:
                    fig = px.bar(exp_df.groupby('experience_min').size().reset_index(name='count'), 
                               x='experience_min', y='count',
                               title="Jobs by Minimum Experience (Years)",
                               labels={'experience_min': 'Years', 'count': 'Number of Jobs'})
                    st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"Jobs with no experience mentioned: {df[df['experience_not_mentioned'] == True].shape[0]}")

            with tab3:
                st.subheader("🏢 Top Companies")
                top_cos = df['company'].value_counts().head(15).reset_index()
                top_cos.columns = ['company', 'count']
                fig = px.bar(top_cos, x='count', y='company', orientation='h', 
                           title="Top 15 Hiring Companies",
                           color='count', color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for analytics. Run the crawler first!")
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
    finally:
        if 'conn' in locals(): conn.close()

# ==================== QUERY TOOL ====================
elif menu == "🔍 Query Tool":
    st.title("🔍 SQL Query Tool")
    
    conn = get_connection()
    
    # Get tables
    try:
        tables = [t[0] for t in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()]
    except Exception as e:
        st.error(f"Error getting tables: {e}")
        tables = []
        conn.close()
    
    # Sidebar with table info
    st.sidebar.subheader("📋 Table Reference")
    for t in tables:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            st.sidebar.write(f"**{t}**: {cnt:,} rows")
            
            # Show schema
            schema = conn.execute(f"DESCRIBE {t}").fetchall()
            with st.sidebar.expander(f"Schema: {t}"):
                for col, typ in schema:
                    st.sidebar.write(f"  `{col}`: {typ}")
        except:
            pass
    
    # Query input
    query = st.text_area("Enter SQL Query", "SELECT * FROM dim_company LIMIT 10", height=100)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        run_btn = st.button("Run Query", type="primary")
    with col2:
        st.write("")
        st.write("")
        st.write("💡 Tip: Click table names in sidebar to see their data")
    
    if run_btn:
        try:
            result = conn.execute(query).fetchdf()
            st.success(f"✅ Query returned {len(result)} rows")
            
            # Show data
            st.dataframe(result, height=400)
            
            # Export
            csv = result.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                "query_results.csv",
                "text/csv"
            )
            
            # Schema
            with st.expander("📋 Result Schema"):
                st.table(pd.DataFrame({
                    'Column': result.dtypes.index,
                    'Type': result.dtypes.astype(str)
                }))
                
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    conn.close()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.sidebar.markdown("**Database**: `dbt/job_lakehouse.duckdb`")