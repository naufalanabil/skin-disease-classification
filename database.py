from supabase import create_client
import streamlit as st

# =====================================================
# CONNECT SUPABASE
# =====================================================

url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
key = st.secrets["SUPABASE_KEY"].strip()

supabase = create_client(url, key)

# =====================================================
# SAVE PREDICTION
# =====================================================

def save_prediction(image_name, prediction, confidence):
    try:
        data = {
            "image_name": image_name,
            "prediction": prediction,
            "confidence": confidence
        }
        
        # JIKA NAMA TABEL DI BROWSER BERBEDA, GANTI TEKS "predictions" DI BAWAH INI
        response = supabase.table("predictions").insert(data).execute()
        return response
        
    except Exception as e:
        print(f"Error saat menyimpan data: {e}")
        raise e

# =====================================================
# GET HISTORY
# =====================================================

def get_history():
    try:
        # Kita pakai query paling dasar dan polosan tanpa .order() dulu untuk test jalur
        # JIKA NAMA TABEL DI BROWSER BERBEDA, GANTI TEKS "predictions" DI BAWAH INI
        response = supabase.table("predictions").select("*").execute()
        
        return response.data
        
    except Exception as e:
        print(f"Error saat mengambil data: {e}")
        raise e