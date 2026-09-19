import streamlit as st
import pandas as pd
import altair as alt
import math

# ==========================================
# KONFIGURASI HALAMAN & WARNA (CSS INJECTION)
# ==========================================
st.set_page_config(page_title="DSS Puskesmas Leuwigoong", layout="wide")

# Menyuntikkan CSS untuk memaksa warna teks hitam pekat dan background putih
st.markdown("""
<style>
    /* Memaksa background menjadi putih */
    .stApp {
        background-color: #FFFFFF;
    }
    /* Memaksa semua teks umum, judul, dan label menjadi hitam pekat */
    html, body, p, div, h1, h2, h3, h4, h5, h6, span, label, li {
        color: #000000 !important;
    }
    /* Memperjelas warna garis pembatas */
    hr {
        border-color: #000000 !important;
        opacity: 0.2;
    }
</style>
""", unsafe_allow_html=True)

st.title("Sistem Pendukung Keputusan (DSS) Kunjungan Pasien")
st.markdown("UPT Puskesmas Leuwigoong - Dashboard Analisis Pola, Tren, dan Prediksi")

# ==========================================
# FUNGSI PEWARNAAN TABEL (TEMA HIJAU)
# ==========================================
def format_tabel_hijau(df):
    """Fungsi untuk merubah warna tabel DataFrame menjadi tema Hijau"""
    return df.style.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#2CA02C'), ('color', 'white'), ('font-weight', 'bold'), ('border', '1px solid #1f77b4')]},
        {'selector': 'td', 'props': [('background-color', '#E8F5E9'), ('color', 'black'), ('border', '1px solid #c3e6cb')]}
    ])

# ==========================================
# 1. MEMUAT 3 FILE EXCEL SEKALIGUS
# ==========================================
@st.cache_data
def load_data():
    df_looker = pd.read_excel('data_untuk_looker_studio6.xlsx')
    df_looker['ds'] = pd.to_datetime(df_looker['ds'])
    df_looker['Tanggal'] = df_looker['ds'].dt.date
    df_looker['Bulan_Tahun'] = df_looker['ds'].dt.to_period('M').astype(str)
    
    df_aktual = pd.read_excel('rata_rata_jam_filterable.xlsx', sheet_name='Aktual_per_Jam')
    df_aktual['Tanggal'] = pd.to_datetime(df_aktual['Tanggal']).dt.date
    df_aktual['Jam_Format'] = df_aktual['Jam'].apply(lambda x: f"{int(x):02d}.00") 
    
    df_prediksi = pd.read_excel('rata_rata_jam_filterable.xlsx', sheet_name='Prediksi_per_Jam')
    df_prediksi['Tanggal'] = pd.to_datetime(df_prediksi['Tanggal']).dt.date
    df_prediksi['Jam_Format'] = df_prediksi['Jam'].apply(lambda x: f"{int(x):02d}.00")
    
    df_eval = pd.read_excel('metrik_evaluasi.xlsx', sheet_name='Metrik_Kumulatif_Bab4')
    
    return df_looker, df_aktual, df_prediksi, df_eval

try:
    df_looker, df_aktual, df_prediksi, df_eval = load_data()
except Exception as e:
    st.error("Gagal memuat file Excel. Pastikan ketiga file berada di folder yang sama dengan app.py!")
    st.stop()

df_looker_hist = df_looker[df_looker['Status_Data'] == 'Historis']

# ==========================================
# 2. FITUR FILTER RENTANG WAKTU (SIDEBAR)
# ==========================================
st.sidebar.header("⚙️ Filter Rentang Waktu")

st.sidebar.subheader("📅 Rentang Data Historis")
min_date_h = df_looker_hist['Tanggal'].min()
max_date_h = df_looker_hist['Tanggal'].max()
rentang_hist = st.sidebar.date_input("Pilih Tanggal Historis:", [min_date_h, max_date_h], min_value=min_date_h, max_value=max_date_h)

st.sidebar.subheader("🔮 Rentang Data Prediksi")
min_date_p = df_prediksi['Tanggal'].min()
max_date_p = df_prediksi['Tanggal'].max()
rentang_pred = st.sidebar.date_input("Pilih Tanggal Prediksi:", [min_date_p, max_date_p], min_value=min_date_p, max_value=max_date_p)

start_h, end_h = rentang_hist if len(rentang_hist) == 2 else (min_date_h, max_date_h)
start_p, end_p = rentang_pred if len(rentang_pred) == 2 else (min_date_p, max_date_p)

df_looker_filtered = df_looker_hist[(df_looker_hist['Tanggal'] >= start_h) & (df_looker_hist['Tanggal'] <= end_h)]
df_aktual_filtered = df_aktual[(df_aktual['Tanggal'] >= start_h) & (df_aktual['Tanggal'] <= end_h)]
df_prediksi_filtered = df_prediksi[(df_prediksi['Tanggal'] >= start_p) & (df_prediksi['Tanggal'] <= end_p)]

# ==========================================
# 3. VISUALISASI TREN KUNJUNGAN
# ==========================================
st.write("---")
st.header("📈 1. Tren Kunjungan Pasien (Bulanan)")
tren_bulanan = df_looker_filtered.groupby('Bulan_Tahun')['y'].sum().reset_index()
chart_tren = alt.Chart(tren_bulanan).mark_line(point=True, color='#2CA02C', strokeWidth=3).encode(
    x=alt.X('Bulan_Tahun:N', title='Bulan', sort=None),
    y=alt.Y('y:Q', title='Total Kunjungan'),
    tooltip=['Bulan_Tahun', 'y']
).properties(height=350)
st.altair_chart(chart_tren, use_container_width=True)

# ==========================================
# 4. VISUALISASI POLA KUNJUNGAN
# ==========================================
st.write("---")
st.header("📊 2. Pola Kunjungan (Berdasarkan Poli & Hari)")
col1, col2 = st.columns(2)

with col1:
    pola_poli = df_looker_filtered.groupby('Poli')['y'].sum().reset_index()
    chart_poli = alt.Chart(pola_poli).mark_bar(color='#1F77B4').encode(
        x=alt.X('Poli:N', title='Poli', sort='-y'),
        y=alt.Y('y:Q', title='Total Kunjungan'),
        tooltip=['Poli', 'y']
    ).properties(height=300, title="Total Kunjungan per Poli")
    st.altair_chart(chart_poli, use_container_width=True)
    
with col2:
    pola_hari = df_looker_filtered.groupby('Nama_Hari')['y'].sum().reset_index()
    urutan_hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    chart_hari = alt.Chart(pola_hari).mark_bar(color='#FF7F0E').encode(
        x=alt.X('Nama_Hari:N', title='Hari', sort=urutan_hari),
        y=alt.Y('y:Q', title='Total Kunjungan'),
        tooltip=['Nama_Hari', 'y']
    ).properties(height=300, title="Akumulasi Kunjungan per Hari")
    st.altair_chart(chart_hari, use_container_width=True)

# ==========================================
# 5. VISUALISASI RATA-RATA JAM
# ==========================================
st.write("---")
st.header("⏰ 3. Rata-Rata Kunjungan per Jam Operasional")

sum_hist_harian = df_aktual_filtered.groupby(['Tanggal', 'Jam_Format'])['Jumlah_Pasien_Aktual'].sum().reset_index()
rata_hist_jam = sum_hist_harian.groupby('Jam_Format')['Jumlah_Pasien_Aktual'].mean().reset_index().round(2)

sum_pred_harian = df_prediksi_filtered.groupby(['Tanggal', 'Jam_Format'])['Jumlah_Pasien_Prediksi'].sum().reset_index()
rata_pred_jam = sum_pred_harian.groupby('Jam_Format')['Jumlah_Pasien_Prediksi'].mean().reset_index().round(2)

col3, col4 = st.columns(2)
with col3:
    chart_rata_hist = alt.Chart(rata_hist_jam).mark_bar(color='#D62728').encode(
        x=alt.X('Jam_Format:O', title='Jam Operasional'),
        y=alt.Y('Jumlah_Pasien_Aktual:Q', title='Rata-Rata Pasien'),
        tooltip=['Jam_Format', 'Jumlah_Pasien_Aktual']
    ).properties(height=300, title=f"Aktual ({start_h} s/d {end_h})")
    st.altair_chart(chart_rata_hist, use_container_width=True)

with col4:
    chart_rata_pred = alt.Chart(rata_pred_jam).mark_bar(color='#9467BD').encode(
        x=alt.X('Jam_Format:O', title='Jam Operasional'),
        y=alt.Y('Jumlah_Pasien_Prediksi:Q', title='Rata-Rata Prediksi Pasien'),
        tooltip=['Jam_Format', 'Jumlah_Pasien_Prediksi']
    ).properties(height=300, title=f"Prediksi ({start_p} s/d {end_p})")
    st.altair_chart(chart_rata_pred, use_container_width=True)

# ==========================================
# 6. EVALUASI MODEL
# ==========================================
st.write("---")
st.header("✅ 4. Evaluasi Performa Model (MAE & RMSE)")

# MENERAPKAN WARNA HIJAU PADA TABEL EVALUASI
df_eval_tampil = df_eval[['Kluster', 'Poli', 'Mode_Seasonality', 'MAE_CrossValidation', 'RMSE_CrossValidation']]
st.table(format_tabel_hijau(df_eval_tampil))

# ==========================================
# 7. KEPUTUSAN DSS (REKOMENDASI KUOTA)
# ==========================================
st.write("---")
st.header("💡 5. Rekomendasi Keputusan Kuota (DSS Output)")
st.markdown("Berdasarkan evaluasi model, tingkat error prediksi (Prophet) memiliki fluktuasi. Oleh karena itu, sesuai pedoman penelitian, rekomendasi penetapan kuota pendaftaran harian didasarkan pada perhitungan **rata-rata beban historis maksimal** pada rentang waktu yang difilter.")

if not df_aktual_filtered.empty:
    df_rekomendasi = df_aktual_filtered.groupby('Jam_Format').agg(
        Rata_Rata_Kunjungan=('Jumlah_Pasien_Aktual', 'mean'),
        Kunjungan_Maksimal_Pernah_Terjadi=('Jumlah_Pasien_Aktual', 'max')
    ).reset_index()
    
    df_rekomendasi['Rata_Rata_Kunjungan'] = df_rekomendasi['Rata_Rata_Kunjungan'].round(2)
    df_rekomendasi['Rekomendasi_Kuota_Pendaftaran'] = df_rekomendasi['Rata_Rata_Kunjungan'].apply(lambda x: math.ceil(x))
    
    # MENERAPKAN WARNA HIJAU PADA TABEL REKOMENDASI DSS
    st.table(format_tabel_hijau(df_rekomendasi))
    
    jam_puncak_hist = df_rekomendasi.loc[df_rekomendasi['Rekomendasi_Kuota_Pendaftaran'].idxmax()]
    
    st.error(f"🚨 **TINDAKAN DSS:** Jam **{jam_puncak_hist['Jam_Format']}** adalah waktu paling kritis. Jika jumlah pendaftar pada jam tersebut sudah mencapai **{jam_puncak_hist['Rekomendasi_Kuota_Pendaftaran']} pasien**, sistem menyarankan staf untuk **menyetop antrean** dan mengarahkan sisa pasien ke jam berikutnya.")
else:
    st.info("Pilih rentang data historis yang valid di sidebar untuk melihat rekomendasi kuota.")
