from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
import json

def database_viewer(request):
    """Main database viewer page"""
    cursor = connection.cursor()
    
    # Get all tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
    tables = [row[0] for row in cursor.fetchall()]
    
    table_data = {}
    
    for table in tables:
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        
        # Get sample data (first 10 rows)
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 10;")
            rows = cursor.fetchall()
            # Get column names
            column_names = [col[1] for col in columns]
            
            table_data[table] = {
                'columns': columns,
                'row_count': count,
                'sample_data': rows,
                'column_names': column_names
            }
        else:
            table_data[table] = {
                'columns': columns,
                'row_count': 0,
                'sample_data': [],
                'column_names': [col[1] for col in columns]
            }
    
    context = {
        'tables': tables,
        'table_data': table_data,
        'total_tables': len(tables)
    }
    
    return render(request, 'database_viewer.html', context)

def table_data_api(request, table_name):
    """API to get full table data"""
    cursor = connection.cursor()
    
    # Validate table name to prevent SQL injection
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?;', [table_name])
    if not cursor.fetchone():
        return JsonResponse({'error': 'Table not found'}, status=404)
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Get all data with pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    offset = (page - 1) * per_page
    
    cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?;", [per_page, offset])
    rows = cursor.fetchall()
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    total_count = cursor.fetchone()[0]
    
    data = []
    for row in rows:
        row_dict = {}
        for i, value in enumerate(row):
            if i < len(column_names):
                row_dict[column_names[i]] = str(value) if value is not None else 'NULL'
        data.append(row_dict)
    
    return JsonResponse({
        'data': data,
        'columns': column_names,
        'total_count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page
    })
