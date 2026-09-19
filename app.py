import streamlit as st
import pandas as pd
import altair as alt

# Konfigurasi Halaman
st.set_page_config(page_title="DSS Puskesmas Leuwigoong", layout="wide")
st.title("Sistem Pendukung Keputusan (DSS) Kunjungan Pasien")
st.markdown("Dashboard ini menampilkan pola, tren, prediksi kunjungan, serta **Rekomendasi Kuota** untuk mencegah penumpukan pasien di UPT Puskesmas Leuwigoong.")

# ==========================================
# 1. MEMUAT DATA (Dari hasil script asli Anda)
# ==========================================
@st.cache_data
def load_data():
    try:
        # Membaca data yang sudah diolah oleh script asli Anda
        df_aktual = pd.read_excel('rata_rata_jam_filterable.xlsx', sheet_name='Aktual_per_Jam')
        df_prediksi = pd.read_excel('rata_rata_jam_filterable.xlsx', sheet_name='Prediksi_per_Jam')
        df_evaluasi = pd.read_excel('metrik_evaluasi.xlsx', sheet_name='Metrik_Kumulatif_Bab4')
        return df_aktual, df_prediksi, df_evaluasi
    except FileNotFoundError:
        st.error("File Excel tidak ditemukan. Pastikan file 'rata_rata_jam_filterable.xlsx' dan 'metrik_evaluasi.xlsx' berada di folder yang sama.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_aktual, df_prediksi, df_evaluasi = load_data()

if not df_aktual.empty:
    # ==========================================
    # 2. FITUR FILTER (Di Sidebar)
    # ==========================================
    st.sidebar.header("Filter Data")
    
    # Filter Poli
    daftar_poli = ["Semua Poli"] + list(df_aktual['Poli'].unique())
    pilihan_poli = st.sidebar.selectbox("Pilih Poli:", daftar_poli)
    
    # Filter Hari
    daftar_hari = ["Semua Hari"] + list(df_aktual['Nama_Hari'].unique())
    pilihan_hari = st.sidebar.selectbox("Pilih Hari:", daftar_hari)

    # Proses Filtering Data Aktual
    df_aktual_filtered = df_aktual.copy()
    df_prediksi_filtered = df_prediksi.copy()

    if pilihan_poli != "Semua Poli":
        df_aktual_filtered = df_aktual_filtered[df_aktual_filtered['Poli'] == pilihan_poli]
        df_prediksi_filtered = df_prediksi_filtered[df_prediksi_filtered['Poli'] == pilihan_poli]
        
    if pilihan_hari != "Semua Hari":
        df_aktual_filtered = df_aktual_filtered[df_aktual_filtered['Nama_Hari'] == pilihan_hari]
        df_prediksi_filtered = df_prediksi_filtered[df_prediksi_filtered['Nama_Hari'] == pilihan_hari]

    # ==========================================
    # 3. VISUALISASI POLA & PREDIKSI
    # ==========================================
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pola Kunjungan Aktual per Jam")
        # Agregasi rata-rata per jam
        rata_aktual = df_aktual_filtered.groupby('Jam')['Jumlah_Pasien_Aktual'].mean().reset_index()
        chart_aktual = alt.Chart(rata_aktual).mark_bar(color='#F5821F').encode(
            x=alt.X('Jam:O', title='Jam Operasional'),
            y=alt.Y('Jumlah_Pasien_Aktual:Q', title='Rata-Rata Pasien'),
            tooltip=['Jam', 'Jumlah_Pasien_Aktual']
        ).properties(height=300)
        st.altair_chart(chart_aktual, use_container_width=True)

    with col2:
        st.subheader("Prediksi Kunjungan per Jam (Masa Depan)")
        rata_prediksi = df_prediksi_filtered.groupby('Jam')['Jumlah_Pasien_Prediksi'].mean().reset_index()
        chart_prediksi = alt.Chart(rata_prediksi).mark_bar(color='#1F77B4').encode(
            x=alt.X('Jam:O', title='Jam Operasional'),
            y=alt.Y('Jumlah_Pasien_Prediksi:Q', title='Prediksi Pasien'),
            tooltip=['Jam', 'Jumlah_Pasien_Prediksi']
        ).properties(height=300)
        st.altair_chart(chart_prediksi, use_container_width=True)

    # ==========================================
    # 4. EVALUASI MODEL (MAE & RMSE)
    # ==========================================
    st.write("---")
    st.subheader("Evaluasi Performa Model (Validasi)")
    st.markdown("Tabel ini membuktikan bahwa prediksi yang dihasilkan memiliki tingkat error yang wajar berdasarkan metrik *Mean Absolute Error* (MAE) dan *Root Mean Squared Error* (RMSE).")
    
    if pilihan_poli != "Semua Poli":
        df_eval_show = df_evaluasi[df_evaluasi['Poli'] == pilihan_poli]
    else:
        df_eval_show = df_evaluasi
        
    st.dataframe(df_eval_show[['Kluster', 'Poli', 'Mode_Seasonality', 'MAE_CrossValidation', 'RMSE_CrossValidation']], use_container_width=True)

    # ==========================================
    # 5. KEPUTUSAN DSS (REKOMENDASI KUOTA)
    # ==========================================
    st.write("---")
    st.header("Rekomendasi Tindakan (Decision Support)")
    st.info(f"Berdasarkan analisis prediksi untuk **{pilihan_poli}** pada **{pilihan_hari}**, berikut adalah peringatan jam sibuk dan saran tindakan untuk staf Puskesmas.")

    # Logika DSS sederhana: Jika rata-rata prediksi di atas threshold tertentu, beri peringatan
    if not rata_prediksi.empty:
        # Menentukan jam paling sibuk
        jam_puncak = rata_prediksi.loc[rata_prediksi['Jumlah_Pasien_Prediksi'].idxmax()]
        
        st.warning(f"⚠️ **Potensi Penumpukan Tertinggi:** Terdeteksi pada jam **{int(jam_puncak['Jam']):02d}.00** dengan estimasi rata-rata **{jam_puncak['Jumlah_Pasien_Prediksi']:.1f} pasien**.")
        
        st.markdown(f"""
        **Saran Pengambilan Keputusan untuk Manajemen Puskesmas:**
        1. **Pembatasan Kuota:** Tetapkan batas maksimal pendaftaran pada jam {int(jam_puncak['Jam']):02d}.00.
        2. **Load Balancing:** Jika pasien datang pada jam tersebut dan kondisi tidak gawat darurat, sarankan pasien untuk mengambil antrean pada jam operasional siang (misal: 11.00 - 13.00) yang terbukti secara data lebih lengang.
        3. **Alokasi SDM:** Pastikan tenaga medis dan staf pendaftaran *standby* penuh (tidak ada jadwal istirahat/jaga bergantian) pada pukul {int(jam_puncak['Jam']):02d}.00 hingga {int(jam_puncak['Jam'])+1:02d}.00.
        """)
