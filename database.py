from supabase import create_client
import streamlit as st

# =====================================================
# CONNECT SUPABASE (KUNCI UTAMA VALID & DIUTAMAKAN)
# =====================================================

# Kita langsung pasang URL dan Anon Key terbaru yang valid di sini agar pasti terbaca
url_pasti = "https://dzwfjzsvpmaxjmwptvau.supabase.co"
key_pasti = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6d2ZqenN2cG1heGptd3B0dmF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg4MTAyOTAsImV4cCI6MjA5NDM4NjI5MH0.-dPJaHCUOYeAJvI74z8Fjxnw1HuYmMR23fqzn3weO4s"

try:
    # Mencoba menggunakan kunci pasti yang sudah terbukti valid
    supabase = create_client(url_pasti, key_pasti)
except Exception:
    # Jalur cadangan terakhir jika ada kendala sistem lokal
    url_backup = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    key_backup = st.secrets["SUPABASE_KEY"].strip()
    supabase = create_client(url_backup, key_backup)

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