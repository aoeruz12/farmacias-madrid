import os
import re
import json
import unicodedata
import sqlite3
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
DATABASE = 'productos.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def normalizar_texto(s):
    if not s:
        return ''
    s = s.lower()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

# Carpetas donde buscar fotos
CARPETAS_FOTOS = [
    'imagenes_medicamentos',
    'MEDICAMENTOS',
    'FOTOS_MEDICAMENTOS_FINAL',
    'MEDICAMENTOS_LIMPIOS',
    'farmacias_madrid_backend-v01/static/importaciones',
    'static/importaciones',
]

def buscar_imagen(nombre_producto, ruta_guardada):
    """
    1. PRIMERO: buscar en TODAS las carpetas de fotos (LOCAL)
    2. Si no, usar URL externa
    3. Si no, devolver None
    """
    # ========== CASO 1: BUSCAR EN TODAS LAS CARPETAS (LOCAL) ==========
    palabras = [p.lower() for p in re.findall(r'[A-Za-z0-9.]+', nombre_producto)]
    palabras = [p for p in palabras if len(p) >= 2]
    palabras_norm = [normalizar_texto(p) for p in palabras if normalizar_texto(p)]
    
    # Si no hay palabras clave, usar las primeras 2 palabras
    if not palabras_norm:
        palabras_norm = [normalizar_texto(p) for p in re.findall(r'[A-Za-z0-9]+', nombre_producto)[:2]]
    
    if palabras_norm:
        mejor_match = None
        mejor_score = 0
        mejor_carpeta = None
        
        for carpeta_base in CARPETAS_FOTOS:
            if not os.path.exists(carpeta_base):
                continue
            
            for carpeta in os.listdir(carpeta_base):
                carpeta_path = os.path.join(carpeta_base, carpeta)
                if not os.path.isdir(carpeta_path):
                    continue
                
                carpeta_norm = normalizar_texto(carpeta)
                carpeta_norm = normalizar_texto(carpeta)
                # Solo contar si la carpeta tiene archivos
                tiene_archivos = any(f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) for f in os.listdir(carpeta_path))
                if not tiene_archivos:
                    continue
                score = sum(1 for p in palabras_norm if p in carpeta_norm)
                
                if score > mejor_score:
                    mejor_score = score
                    mejor_match = carpeta
                    mejor_carpeta = carpeta_base
                
                if score > mejor_score:
                    mejor_score = score
                    mejor_match = carpeta
                    mejor_carpeta = carpeta_base
        
        # Match con al menos 2 palabras clave (o 1 si el nombre es corto)
        umbral = 2 if len(palabras_norm) >= 3 else 1
        
        if mejor_match and mejor_score >= umbral:
            carpeta_path = os.path.join(mejor_carpeta, mejor_match)
            archivos = sorted([f for f in os.listdir(carpeta_path)
                              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
            if archivos:
                return f'/{mejor_carpeta}/{mejor_match}/{archivos[0]}'
    
    # ========== CASO 2: URL EXTERNA ==========
    if ruta_guardada and ruta_guardada.startswith('http'):
        # Si es placeholder, intentar buscar de nuevo (sin suerte)
        if 'placehold' in ruta_guardada or 'countryicon' in ruta_guardada:
            return ruta_guardada  # Placeholder
        return ruta_guardada
    
    # ========== CASO 3: ruta local explícita ==========
    if ruta_guardada and not ruta_guardada.startswith('http'):
        if os.path.exists(ruta_guardada):
            return '/' + ruta_guardada
        for carpeta_base in CARPETAS_FOTOS:
            ruta_alt = os.path.join(carpeta_base, ruta_guardada)
            if os.path.exists(ruta_alt):
                return '/' + ruta_alt
    
    return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    # Buscar en todas las carpetas de fotos primero
    for carpeta_base in CARPETAS_FOTOS:
        ruta = os.path.join(carpeta_base, filename)
        if os.path.exists(ruta):
            return send_from_directory(carpeta_base, filename)
    return send_from_directory('.', filename)

@app.route('/imagenes_medicamentos/<path:filename>')
def imagenes_medicamentos(filename):
    return send_from_directory('imagenes_medicamentos', filename)

@app.route('/MEDICAMENTOS/<path:filename>')
def medicamentos(filename):
    return send_from_directory('MEDICAMENTOS', filename)

@app.route('/FOTOS_MEDICAMENTOS_FINAL/<path:filename>')
def fotos_medicamentos(filename):
    return send_from_directory('FOTOS_MEDICAMENTOS_FINAL', filename)

@app.route('/api/productos', methods=['GET'])
def get_productos():
    categoria = request.args.get('categoria', '')
    search = request.args.get('search', '')
    pais = request.args.get('pais', '')
    destacados = request.args.get('destacados', '')
    limit = int(request.args.get('limit', 12))
    offset = int(request.args.get('offset', 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''SELECT * FROM productos WHERE 1=1 
        AND NOT (
            categoria = 'Importación' 
            AND nombre LIKE '%Mounjaro%'
            AND id_producto NOT IN (
                SELECT MIN(id_producto) FROM productos 
                WHERE categoria = 'Importación' AND nombre LIKE '%Mounjaro%'
                GROUP BY nombre
            )
        )'''
    params = []

    if categoria and categoria.lower() != 'todas':
        query += ' AND categoria LIKE ?'
        params.append(f'%{categoria}%')

    if search:
        query += ' AND (nombre LIKE ? OR principio_activo LIKE ? OR CAST(id_producto AS TEXT) LIKE ?)'
        like = f'%{search}%'
        params.extend([like, like, like])

    if pais:
        if pais.lower() in ('méxico', 'mexico'):
            query += ' AND categoria = ?'
            params.append('Nacional')
            query += ' ORDER BY prioridad DESC, id_producto ASC'
            query += ' ORDER BY prioridad DESC, id_producto ASC'
        else:
            query += ' AND categoria = ?'
            params.append('Importación')





    
    if destacados == 'nacionales':
        mas_vendidos = [
            'RoActemra', 'Tocilizumab', 'Simponi', 'Golimumab',
            'Tagrisso', 'Osimertinib', 'Xeljanz', 'Tofacitinib',
            'Actilyse', 'Alteplasa', 'Hemlibra', 'Emicizumab',
            'Higlobin', 'Inmonuglobulina', 'Lilemidol', 'Lenalidomida',
            'Metalyse', 'Tenecteplasa', 'Mozobil', 'Plerixafor',
            'Renegy', 'Carboximaltosa Ferrica', 'Revolade', 'Eltrombopag'
        ]
        condiciones = ' OR '.join(['nombre LIKE ?' for _ in mas_vendidos])
        query += f' AND categoria = ? AND ({condiciones})'
        params.append('Nacional')
        params.extend([f'%{m}%' for m in mas_vendidos])

    if destacados == 'importados':
        mas_vendidos = [
            'Keytruda', 'Ozempic', 'Humira', 'Enbrel', 'Remicade',
            'Orencia', 'Actemra', 'Cimzia', 'Simponi', 'Xeljanz'
        ]
        condiciones = ' OR '.join(['nombre LIKE ?' for _ in mas_vendidos])
        query += f' AND categoria = ? AND ({condiciones})'
        params.append('Importación')
        params.extend([f'%{m}%' for m in mas_vendidos])

    count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    cursor.execute(query, params)
    productos = cursor.fetchall()
    conn.close()

    productos_list = []
    for p in productos:
        productos_list.append({
            'id_producto': p['id_producto'],
            'nombre': p['nombre'],
            'principio_activo': p['principio_activo'],
            'categoria': p['categoria'],
            'presentacion': p['presentacion'],
            'precio_venta_mxn': p['precio_venta_mxn'],
            'requiere_receta': bool(p['requiere_receta']),
            'imagen_principal': buscar_imagen(p['nombre'], p['imagen_principal']),
            'disponibilidad': p['disponibilidad'],
            'tiempo_entrega': p['tiempo_entrega'],
            'pais_origen': 'México' if p['categoria'] == 'Nacional' else 'Importación',
            'proveedor': '',
            'descripcion': '',
            'variantes': []
        })

    return jsonify({
        'productos': productos_list,
        'total': total,
        'limit': limit,
        'offset': offset
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
