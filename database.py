from supabase import create_client
import streamlit as st

# =====================================================
# CONNECT SUPABASE (DENGAN SISTEM CADANGAN AMAN)
# =====================================================

try:
    # Jalur utama: Membaca dari secrets cloud/lokal (.streamlit/secrets.toml)
    url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    key = st.secrets["SUPABASE_KEY"].strip()
except Exception:
    # Jalur cadangan: Jika secrets di Streamlit Cloud mendadak macet / tidak terbaca
    url = "https://dzwfjzsvpmaxjmwptvau.supabase.co"
    # ⚠️ GANTI teks di bawah ini dengan anon public key asli dari dashboard Supabase kamu
    key = "MASUKKAN_ANON_PUBLIC_KEY_PROJECT_SUPABASE_KAMU_DI_SINI"

# Inisialisasi client Supabase menggunakan url dan key yang aktif
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
        
        # Menyimpan data hasil prediksi ke tabel 'predictions'
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
        # Mengambil data dari tabel 'predictions' menggunakan pengurutan 'desc=True' yang valid
        response = supabase.table("predictions").select("*").order("id", desc=True).execute()
        
        return response.data
        
    except Exception as e:
        # Jika query .order() di atas memicu error baru (misal karena kolom id tidak ada),
        # maka otomatis pakai query polosan sebagai backup agar aplikasi tidak crash
        try:
            response = supabase.table("predictions").select("*").execute()
            return response.data
        except Exception as final_err:
            print(f"Error saat mengambil data: {final_err}")
            raise final_err