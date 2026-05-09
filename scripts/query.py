#!/usr/bin/env python3
import duckdb
import sys

DB_PATH = 'dbt/job_lakehouse.duckdb'

def main():
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # Get tables
    tables = [t[0] for t in conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()]
    
    if len(sys.argv) > 1:
        # Run custom query
        query = ' '.join(sys.argv[1:])
        try:
            result = conn.execute(query).fetchall()
            if result:
                # Print headers
                cols = [d[0] for d in conn.description]
                print(' | '.join(cols))
                print('-' * 80)
                # Print rows
                for row in result[:100]:
                    print(' | '.join(str(x) for x in row))
                if len(result) > 100:
                    print(f"... {len(result)-100} more rows")
            else:
                print("No results")
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Show tables
        print("Available tables:")
        for t in tables:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  - {t} ({cnt} rows)")
        
        print("\nExample queries:")
        print("  python scripts/query.py 'SELECT * FROM dim_company LIMIT 5'")
        print("  python scripts/query.py 'SELECT COUNT(*) as total, company FROM stg_jobs GROUP BY company ORDER BY total DESC LIMIT 10'")
    
    conn.close()

if __name__ == '__main__':
    main()