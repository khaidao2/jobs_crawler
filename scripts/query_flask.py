from flask import Flask, render_template_string, request, jsonify
import duckdb

app = Flask(__name__)

import os
DB_PATH = os.environ.get('DB_PATH', 'dbt/job_lakehouse.duckdb')

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Job Lakehouse Query</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        textarea { width: 100%; height: 80px; font-family: monospace; padding: 10px; }
        button { background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; margin: 10px 0; }
        button:hover { background: #45a049; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #4CAF50; color: white; }
        tr:nth-child(even) { background: #f2f2f2; }
        .error { color: red; background: #ffe6e6; padding: 10px; border-radius: 4px; }
        .success { color: green; background: #e6ffe6; padding: 10px; border-radius: 4px; }
        select { padding: 8px; margin: 5px; }
        .tables { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        a { color: #1976D2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Job Lakehouse Query Tool</h1>
        
        <div class="tables">
            <h3>Available Tables:</h3>
            {% for table in tables %}
                <a href="#" onclick="setQuery('SELECT * FROM {{ table }} LIMIT 100')">{{ table }}</a>{% if not loop.last %}, {% endif %}
            {% endfor %}
        </div>
        
        <form method="post">
            <textarea name="query" placeholder="Enter SQL query...">{{ query }}</textarea><br>
            <button type="submit">Run Query</button>
        </form>
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if results %}
            <div class="success">Returned {{ results|length }} rows</div>
            <div style="overflow-x: auto;">
                <table>
                    <tr>
                        {% for col in columns %}
                            <th>{{ col }}</th>
                        {% endfor %}
                    </tr>
                    {% for row in results %}
                        <tr>
                            {% for cell in row %}
                                <td>{{ cell }}</td>
                            {% endfor %}
                        </tr>
                    {% endfor %}
                </table>
            </div>
        {% endif %}
    </div>
    
    <script>
        function setQuery(q) {
            document.querySelector('textarea[name="query"]').value = q;
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # Get tables
    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
    table_names = [t[0] for t in tables]
    
    query = ''
    results = None
    columns = None
    error = None
    
    if request.method == 'POST':
        query = request.form.get('query', '')
        try:
            result = conn.execute(query).fetchall()
            if result:
                columns = [desc[0] for desc in conn.description]
                results = result[:1000]  # Limit to 1000 rows
            else:
                results = []
        except Exception as e:
            error = str(e)
    
    conn.close()
    return render_template_string(HTML, tables=table_names, query=query, results=results, columns=columns, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)