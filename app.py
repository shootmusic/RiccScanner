#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io, base64, numpy as np, cv2, pytesseract, sympy as sp

app = Flask(__name__)
# CORS untuk semua domain (GitHub Pages lo)
CORS(app, resources={r"/*": {"origins": "*"}})

def solve(expr):
    try:
        if '=' in expr:
            l, r = expr.split('=', 1)
            return f"Solusi: {sp.solve(sp.Eq(sp.sympify(l.strip()), sp.sympify(r.strip())))}"
        return f"Hasil: {sp.sympify(expr).evalf()}"
    except: 
        return f"Error parsing: {expr}"

@app.route('/')
def health():
    return jsonify({'status': 'RiccScanner Online', 'version': '3.0'})

@app.route('/solve', methods=['POST'])
def scan():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'result': 'Error: No image data'}), 400
            
        img_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(img_data)
        
        img = Image.open(io.BytesIO(img_bytes))
        gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789+-*/=().xX^sqrt'
        text = pytesseract.image_to_string(thresh, config=config).strip()
        
        # Replace symbols
        for old, new in {'x':'*','X':'*','×':'*','÷':'/','^':'**','√':'sqrt'}.items():
            text = text.replace(old, new)
            
        if not text:
            return jsonify({'result': '❌ No math detected. Try better lighting.'})
            
        result = solve(text)
        return jsonify({'result': f"📸 Detected: {text}\n\n🧠 {result}"})
        
    except Exception as e:
        return jsonify({'result': f'❌ Error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🔥 RiccScanner Online - Port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
