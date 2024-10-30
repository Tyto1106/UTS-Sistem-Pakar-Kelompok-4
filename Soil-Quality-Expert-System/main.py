from flask import Flask
from flask import  render_template
from flask import request
from flask import redirect
from flask import url_for
import os

main = Flask(__name__)

# Fungsi untuk menghitung Certainty Factor (CF)
def hitung_cf(cf_pengguna, cf_pakar):
    
    # Hitung CF
    return cf_pengguna * cf_pakar

def combine_cf(cf_lama, cf_baru):
    
    # Gabungkan 2 nilai CF
    return cf_lama + cf_baru * (1 - cf_lama)

# Fungsi untuk mendapatkan nilai CF dari input user
def get_cf_pengguna(choice):
    return {1: 0.0, 2: 0.2, 3: 0.4, 4: 0.6, 5: 0.8, 6: 1.0}.get(choice, 0.0)

# Fungsi untuk membaca knowledge base dari file di direktori data
def load_knowledge_base_from_file():
    knowledge_base = {}
    
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "knowledge_bases.txt"))
    
    print(f"Mencoba memuat file knowledge base dari path: {file_path}")
    
    try:
        with open(file_path, 'r') as file:
            kode_kerusakan = None
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("K"):  # Baris yang memulai kode penyakit
                    kode_kerusakan, penyakit_name = line.split(" - ")
                    knowledge_base[kode_kerusakan] = {'name': penyakit_name, 'diseases': {}, 'solution': ''}
                elif line.startswith("T"):  # Baris yang memulai kode gejala
                    gejala_code, rest = line.split(": ")
                    gejala_name, berat = rest.split(" - ")
                    knowledge_base[kode_kerusakan]['diseases'][gejala_code] = {'name': gejala_name, 'berat': float(berat)}
                elif line.startswith("Solusi:"):  # Baris solusi
                    solution = line.split("Solusi: ")[1]
                    knowledge_base[kode_kerusakan]['solution'] = solution.strip()
        print("Knowledge base berhasil dimuat.")
    except FileNotFoundError:
        print(f"File {file_path} tidak ditemukan. Pastikan file berada di direktori 'data' dan bernama 'knowledge_bases.txt'.")
    except Exception as e:
        print("Terjadi error saat membaca knowledge base:", e)
    return knowledge_base

# Diagnosa Penyakit dari gejala
def diagnose(gejala_user, knowledge_base):
    hasil_diagnosis = []
    
    for kode_kerusakan, penyakit_data in knowledge_base.items():
        cf_combine = 0.0
        match_found = False
        
        for gejala_code, cf_pakar in penyakit_data['diseases'].items():
           
            cf_pengguna = gejala_user.get(gejala_code, 0.0)
            if cf_pengguna > 0:  # Ada CF User
                match_found = True  # Gejala ditemukan
                cf_current = hitung_cf(cf_pengguna, cf_pakar['berat'])
                cf_combine = combine_cf(cf_combine, cf_current)

        
        if match_found:
            hasil_diagnosis.append((penyakit_data['name'], cf_combine, penyakit_data['solution'] ))

  
    hasil_diagnosis.sort(key=lambda x: x[1], reverse=True)
    return hasil_diagnosis


def process_user_input(form_data):
    gejala_user = {}
    for diseases_code in form_data:
        user_input = int(form_data[diseases_code])
        gejala_user[diseases_code] = get_cf_pengguna(user_input)
    return gejala_user

@main.route('/')
def start():
    return render_template('mulai.html')

@main.route('/diagnosa')
def index():
  
    knowledge_base = load_knowledge_base_from_file()
    if not knowledge_base:
        return "Error: Tidak menemukan file knowledge base."
    
    diseases = {}
    for penyakit_data in knowledge_base.values():
        for gejala_code, gejala_data in penyakit_data['diseases'].items():
            if gejala_code not in diseases:
                diseases[gejala_code] = gejala_data['name']
    return render_template('base.html', diseases=diseases)

@main.route('/diagnose', methods=['POST'])
def diagnose_route():

    knowledge_base = load_knowledge_base_from_file()
    if not knowledge_base:
        return "Error: file knowledge base tidak dimuat."

   
    gejala_user = process_user_input(request.form)

 
    hasil_diagnosis = diagnose(gejala_user, knowledge_base)
 
    diagnosis_akhir = [diagnosis for diagnosis in hasil_diagnosis if diagnosis[1] > 0]

    return render_template('hasil.html', diagnosis_results=diagnosis_akhir)

if __name__ == '__main__':
    main.run(debug=True)
