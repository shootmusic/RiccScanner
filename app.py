#!/usr/bin/env python3
"""
RiccScanner Backend
Clean OCR + Math Solver
"""

import os
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
CORS(app, resources={r"/*": {"origins": "*"}})

def preprocess_image(img_array):
    """Preprocessing agar OCR lebih akurat"""
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Resize besar untuk OCR lebih baik
    height, width = gray.shape
    if width < 1000:
        scale = 1000 / width
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Threshold adaptif
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Morphological ops untuk bersihin noise
    kernel = np.ones((2,2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return thresh

def clean_text(text):
    """Bersihin hasil OCR dari karakter aneh"""
    # Hapus newline jadi space
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Hapus multiple spaces
    text = ' '.join(text.split())
    
    # Hapus karakter aneh, sisain cuma yang penting
    allowed = "0123456789+-*/=().xX^sqrtSQRTrt "
    cleaned = ""
    for char in text:
        if char in allowed:
            cleaned += char
    
    return cleaned.strip()

def normalize_math(text):
    """Normalisasi simbol matematika"""
    # Lowercase dulu
    text = text.lower()
    
    # Ganti variasi simbol
    replacements = {
        'x': '*',
        '×': '*',
        '·': '*',
        '÷': '/',
        ':': '/',
        '^': '**',
        'sqrt': 'sqrt',
        'sqr': 'sqrt',
        'sq': 'sqrt',
        'rt': 'sqrt',
        '{': '(',
        '}': ')',
        '[': '(',
        ']': ')',
        'pi': '3.14159',
        ' ': ''  # Hapus semua space
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def solve_expression(expr):
    """Solve ekspresi matematika"""
    try:
        # Cek kalau ada = (persamaan)
        if '=' in expr:
            left, right = expr.split('=', 1)
            left = left.strip()
            right = right.strip()
            
            if not left or not right:
                return "Error: Invalid equation format"
            
            eq = sp.Eq(sp.sympify(left), sp.sympify(right))
            solution = sp.solve(eq)
            return f"Equation: {left} = {right}\nSolution: {solution}"
        
        # Ekspresi biasa
        result = sp.sympify(expr)
        simplified = sp.simplify(result)
        numeric = float(result.evalf())
        
        return f"Expression: {expr}\nSimplified: {simplified}\nResult: {numeric}"
        
    except Exception as e:
        return f"Error parsing: {expr}\nDetails: {str(e)}"

@app.route('/')
def health():
    return jsonify({
        'status': 'RiccScanner Online',
        'version': '3.0'
    })

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'result': 'Error: No image data provided'}), 400
        
        # Decode image
        img_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(img_data)
        
        # Open dan preprocess
        image = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(image)
        
        # Preprocess
        processed = preprocess_image(img_array)
        
        # OCR dengan config ketat
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789+-*/=().xX^sqrtSQRT '
        raw_text = pytesseract.image_to_string(processed, config=custom_config)
        
        # Clean dan normalize
        cleaned = clean_text(raw_text)
        normalized = normalize_math(cleaned)
        
        if not normalized:
            return jsonify({
                'result': 'No math expression detected.\n\nTips:\n- Write clearly with dark ink\n- Ensure good lighting\n- Keep math centered in frame\n- Avoid cluttered background'
            })
        
        # Solve
        solution = solve_expression(normalized)
        
        return jsonify({
            'result': f"Detected: {normalized}\n\n{solution}"
        })
        
    except Exception as e:
        return jsonify({
            'result': f'Server Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"RiccScanner Backend - Port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
