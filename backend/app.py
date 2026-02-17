#!/usr/bin/env python3
"""
RiccScanner Backend v3.0
Run di HP lo (Termux/Proot)
"""

import io
import base64
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
import cv2
import pytesseract
import sympy as sp

app = Flask(__name__)
CORS(app)

def solve_math(expression):
    try:
        if '=' in expression:
            left, right = expression.split('=', 1)
            eq = sp.Eq(sp.sympify(left.strip()), sp.sympify(right.strip()))
            sol = sp.solve(eq)
            return f"Persamaan: {expression}\nSolusi: {sol}"
        
        expr = sp.sympify(expression)
        simplified = sp.simplify(expr)
        numeric = float(expr.evalf())
        return f"Ekspresi: {expression}\nSimplifikasi: {simplified}\nNumerik: {numeric}"
    except Exception as e:
        return f"Error solve: {str(e)}"

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        image = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(image)
        
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789+-*/=().xXyYzZabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ^{}√∫∑∏'
        text = pytesseract.image_to_string(thresh, config=config)
        text = text.strip().replace('\n', ' ').replace('  ', ' ')
        
        reps = {'x':'*', 'X':'*', '×':'*', '⋅':'*', '÷':'/', ':':'/',
                '√':'sqrt', '²':'**2', '³':'**3', '^':'**', '{':'(', '}':')',
                'π':'pi', 'sin':'sp.sin', 'cos':'sp.cos', 'tan':'sp.tan',
                'log':'sp.log', 'ln':'sp.ln'}
        for old, new in reps.items():
            text = text.replace(old, new)
        
        if not text:
            result = "❌ Tidak mendeteksi teks\n\nTips:\n- Pastikan pencahayaan cukup\n- Soal di tengah frame\n- Hindari background berantakan"
        else:
            solution = solve_math(text)
            result = f"✅ BERHASIL!\n\n{solution}"
        
        return jsonify({'result': result})
    
    except Exception as e:
        return jsonify({'result': f'❌ Server Error: {str(e)}'})

@app.route('/')
def health():
    return jsonify({'status': 'RiccScanner Backend Online', 'version': '3.0'})

if __name__ == '__main__':
    print("🔥 RiccScanner Backend v3.0 — Mr.X Edition")
    print("=" * 50)
    print("Server jalan di http://0.0.0.0:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
