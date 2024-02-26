from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import tensorflow as tf
from PIL import Image
import numpy as np

app = Flask(__name__)
application = app

# Cargar el modelo directamente
plastiscan = tf.keras.models.load_model('plastiScan_app.h5')

# Mapeo para la clasificación
mapeo_forma = ['Fibra', 'Fragmento', 'Lámina']
mapeo_color = ['Blanco', 'Negro', 'Azul', 'Marrón', 'Verde', 'Multicolor', 'Rojo', 'Transparente', 'Amarillo']
mapeo_componente = ['No Plástico', 'Nylon', 'PE', 'PET', 'PP', 'PS', 'Otros']
mapeo_categoria = ['Macroplástico', 'Mesoplástico', 'Microplástico']

# Carpeta para almacenar las imágenes cargadas
UPLOAD_FOLDER = 'intranet/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def cargar_y_preprocesar_imagen(imagen_path, target_size=(299, 299)):
    img = Image.open(imagen_path)
    img = img.resize(target_size)
    img_array = np.array(img)
    img_array_expanded = np.expand_dims(img_array, axis=0)
    return img_array_expanded / 255.0

def obtener_etiquetas_salida_con_probabilidad(prediccion, mapeo_forma, mapeo_color, mapeo_componente, mapeo_categoria):
    forma_idx = np.argmax(prediccion[0])
    color_idx = np.argmax(prediccion[1])
    componente_idx = np.argmax(prediccion[2])
    categoria_idx = np.argmax(prediccion[3])

    forma_probabilidad = prediccion[0][0][forma_idx]
    color_probabilidad = prediccion[1][0][color_idx]
    componente_probabilidad = prediccion[2][0][componente_idx]
    categoria_probabilidad = prediccion[3][0][categoria_idx]

    forma = {
        "nombre": mapeo_forma[forma_idx],
        "probabilidad": float(forma_probabilidad)
    }
    color = {
        "nombre": mapeo_color[color_idx],
        "probabilidad": float(color_probabilidad)
    }
    componente = {
        "nombre": mapeo_componente[componente_idx],
        "probabilidad": float(componente_probabilidad)
    }
    categoria = {
        "nombre": mapeo_categoria[categoria_idx],
        "probabilidad": float(categoria_probabilidad)
    }

    return forma, color, componente, categoria

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/volver')
def volver():
    return redirect(url_for('index', _anchor='pruebalo'))

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Verificar si la solicitud tiene la parte del archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró el archivo'})

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'})

        
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif','.svg')):
            return jsonify({'error': 'Extensión de archivo no permitida'})

        # Guardar el archivo en la carpeta de carga
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        
        img_preprocesada = cargar_y_preprocesar_imagen(file_path)
        predicciones = plastiscan.predict(img_preprocesada)
        forma, color, componente, categoria = obtener_etiquetas_salida_con_probabilidad(
            predicciones, mapeo_forma, mapeo_color, mapeo_componente, mapeo_categoria
        )

        # Guardo los resultados 
        resultados_dict = {
            "forma": forma,
            "color": color,
            "componente": componente,
            "categoria": categoria
        }

        # Devolver la predicción como JSON
        return render_template('resultados.html', filename=file.filename, resultados=resultados_dict)

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/clear_memory')
def clear_memory():
    
    global resultados_prediccion
    resultados_prediccion = None
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)


