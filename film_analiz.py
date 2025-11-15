import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path  # Dosya yolları için modern ve güçlü bir kütüphane
import datetime
import warnings

# Uyarıları (örn: eski kütüphane sürümleri) gizle
warnings.filterwarnings('ignore')

# --- GÖRSELLEŞTİRME FONKSİYONLARI ---
# Script'i modüler ve GitHub'a uygun hale getirmek için 
# her grafiği kendi fonksiyonuna ayırıyoruz.

def plot_rating_distribution(df, save_path):
    """IMDb Puanlarının dağılımını gösteren bir histogram kaydeder."""
    plt.figure(figsize=(12, 7))
    sns.histplot(df['imdbRating'], bins=40, kde=True, color='blue')
    plt.title('Film Puanlarının Dağılımı (imdbRating)', fontsize=16)
    plt.xlabel('IMDb Puanı', fontsize=12)
    plt.ylabel('Film Sayısı', fontsize=12)
    plt.axvline(df['imdbRating'].mean(), color='red', linestyle='--', label=f'Ortalama: {df["imdbRating"].mean():.2f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path / '1_puan_dagilimi.png')
    plt.close()

def plot_runtime_distribution(df, save_path):
    """Film sürelerinin dağılımını gösteren bir histogram kaydeder."""
    # 240 dakikadan (4 saat) uzun filmler grafiği bozmasın diye filtreliyoruz
    filtered_runtime_df = df[(df['runtime'] > 0) & (df['runtime'] < 240)]
    
    if filtered_runtime_df.empty:
        print("Uyarı: Süre dağılımı için 0-240 dk arası uygun veri bulunamadı.")
        return
        
    plt.figure(figsize=(12, 7))
    sns.histplot(filtered_runtime_df['runtime'], bins=50, kde=True, color='green')
    plt.title('Film Sürelerinin Dağılımı (0-240 Dakika)', fontsize=16)
    plt.xlabel('Süre (Dakika)', fontsize=12)
    plt.ylabel('Film Sayısı', fontsize=12)
    plt.axvline(filtered_runtime_df['runtime'].mean(), color='red', linestyle='--', label=f'Ortalama: {filtered_runtime_df["runtime"].mean():.2f} dk')
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path / '2_sure_dagilimi.png')
    plt.close()

def plot_top_genres_by_rating(df, save_path):
    """Türlerin ortalama puanlarını gösteren bir bar grafiği kaydeder."""
    # Tür başına film sayılarını hesapla
    genre_counts = df['genre'].value_counts()
    # Sadece en az 100 filme sahip olan "popüler" türleri seç
    popular_genres = genre_counts[genre_counts >= 100].index
    
    if popular_genres.empty:
        print("Uyarı: En az 100 filme sahip popüler tür bulunamadı. Bu grafik atlanıyor.")
        return pd.Series(dtype=object).to_string() # Rapor için boş tablo döndür

    df_popular_genres = df[df['genre'].isin(popular_genres)]
    
    # Ortalama puanı hesapla ve sırala
    genre_avg_rating = df_popular_genres.groupby('genre')['imdbRating'].mean().sort_values(ascending=False).head(15)
    
    plt.figure(figsize=(14, 9))
    sns.barplot(x=genre_avg_rating.values, y=genre_avg_rating.index, palette='viridis')
    plt.title('En Yüksek Puanlı Film Türleri (En az 100 film)', fontsize=16)
    plt.xlabel('Ortalama IMDb Puanı', fontsize=12)
    plt.ylabel('Ana Film Türü', fontsize=12)
    plt.tight_layout()
    plt.savefig(save_path / '3_tur_puan_ortalamasi.png')
    plt.close()
    
    # Rapor için en popüler türlerin (film sayısına göre) listesini döndür
    return genre_counts.head(10).to_string()

def plot_top_directors(df, save_path):
    """En başarılı (8.0+ puan) yönetmenleri gösteren bir bar grafiği kaydeder."""
    high_rated_movies = df[df['imdbRating'] >= 8.0]
    
    if high_rated_movies.empty:
        print("Uyarı: 8.0+ puanlı film bulunamadı. Yönetmen grafiği atlanıyor.")
        return

    # Yönetmen başına film sayılarını hesapla
    director_counts = df['director'].value_counts()
    # Sadece en az 10 film çekmiş yönetmenleri dikkate al
    prolific_directors = director_counts[director_counts >= 10].index
    
    if prolific_directors.empty:
        print("Uyarı: En az 10 film çekmiş üretken yönetmen bulunamadı. Grafik atlanıyor.")
        return

    # Bu "üretken" yönetmenlerin 8.0+ puanlı filmlerini say
    top_directors = high_rated_movies[high_rated_movies['director'].isin(prolific_directors)]['director'].value_counts().head(15)

    if top_directors.empty:
        print("Uyarı: Üretken yönetmenler arasında 8.0+ puanlı film bulunamadı. Grafik atlanıyor.")
        return

    plt.figure(figsize=(14, 9))
    sns.barplot(x=top_directors.values, y=top_directors.index, palette='plasma')
    plt.title('En Başarılı Yönetmenler (8.0+ Puanlı Film Sayısı)', fontsize=16)
    plt.xlabel('Yüksek Puanlı (8.0+) Film Sayısı', fontsize=12)
    plt.ylabel('Yönetmen (En az 10 film yönetmiş)', fontsize=12)
    plt.tight_layout()
    plt.savefig(save_path / '4_en_basarili_yonetmenler.png')
    plt.close()

def plot_runtime_vs_rating(df, save_path):
    """Süre ve Puan ilişkisini gösteren bir yoğunluk grafiği (hexbin) kaydeder."""
    # Aykırı süreleri filtrele
    df_filtered = df[(df['runtime'] > 0) & (df['runtime'] < 240)]

    if df_filtered.empty:
        print("Uyarı: Süre-puan ilişkisi için uygun veri yok.")
        return 0.0 # Korelasyon 0 döndür

    # Performans için 10.000 rastgele örnek al
    df_sample = df_filtered.sample(n=min(10000, len(df_filtered)), random_state=42)
    
    g = sns.jointplot(data=df_sample, x='runtime', y='imdbRating', kind='hex', height=10, cmap='inferno')
    g.set_axis_labels('Süre (Dakika)', 'IMDb Puanı', fontsize=12)
    g.fig.suptitle('Film Süresi vs. IMDb Puanı İlişkisi (Yoğunluk Haritası)', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(save_path / '5_sure_puan_iliskisi.png')
    plt.close()
    
    # Rapor için korelasyon katsayısını hesapla
    correlation = df_filtered['runtime'].corr(df_filtered['imdbRating'])
    return correlation

def plot_rating_over_time(df, save_path):
    """Yıllara göre ortalama puan değişimini gösteren bir çizgi grafiği kaydeder."""
    # 1920 öncesi film sayısı az olduğu için 1920 sonrası veriyi al
    yearly_data = df[df['year'] >= 1920].groupby('year')['imdbRating'].mean().reset_index()
    
    if yearly_data.empty:
        print("Uyarı: 1920 sonrası yıllara göre puan verisi bulunamadı. Grafik atlanıyor.")
        return

    plt.figure(figsize=(14, 7))
    sns.lineplot(data=yearly_data, x='year', y='imdbRating', color='purple', label='Yıllık Ortalama')
    # Trendi daha iyi görmek için 10 yıllık hareketli ortalama ekleyelim
    yearly_data['rolling_avg_10y'] = yearly_data['imdbRating'].rolling(window=10).mean()
    sns.lineplot(data=yearly_data, x='year', y='rolling_avg_10y', color='orange', linestyle='--', label='10 Yıllık Hareketli Ortalama')
    
    plt.title('Yıllara Göre Ortalama IMDb Puanı (1920 Sonrası)', fontsize=16)
    plt.xlabel('Yıl', fontsize=12)
    plt.ylabel('Ortalama Puan', fontsize=12)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path / '6_yillara_gore_puan.png')
    plt.close()


# --- ANA İŞLEVLER (Temizleme, Raporlama, Ana Akış) ---

def load_and_clean_data(csv_path):
    """
    Veriyi yükler, temizler ve hem temiz DataFrame'i hem de 
    temizlik işlemlerinin bir özetini (rapor için) döndürür.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"HATA: '{csv_path}' dosyası bulunamadı.")
        return None, "Dosya bulunamadı."
    except Exception as e:
        print(f"HATA: Dosya okunurken bir hata oluştu: {e}")
        return None, f"Dosya okuma hatası: {e}"

    initial_rows = len(df)
    report_log = [f"\n1. Ham Veri Yüklendi: '{Path(csv_path).name}' dosyasından {initial_rows:,} kayıt okundu."]
    
    # Adım 1: Sadece analiz için gerekli sütunları seç
    columns_to_keep = ['title', 'year', 'runtime', 'genre', 'director', 'imdbRating']
    
    # 'type' sütunu varsa onu da alıp sadece 'movie' olanları filtreleyelim
    if 'type' in df.columns:
        columns_to_keep.append('type')
    
    # Var olmayan sütunları isteme hatasını engelle
    actual_columns = [col for col in columns_to_keep if col in df.columns]
    df_clean = df[actual_columns].copy()

    # Adım 2: Sadece 'movie' tipindekileri tut (eğer 'type' sütunu varsa)
    if 'type' in df_clean.columns:
        movie_rows_mask = (df_clean['type'] == 'movie')
        movie_rows_count = movie_rows_mask.sum()
        df_clean = df_clean[movie_rows_mask].copy()
        report_log.append(f"2. Filtreleme: Sadece 'movie' tipindeki {movie_rows_count:,} kayıt tutuldu. Diğer tipler (örn: 'series') analiz dışı bırakıldı.")

    # Adım 3: Kritik sütunlarda eksik veri olanları at
    # 'director' ve 'genre' olmasa da analiz yapılabilir, ama puan/süre/yıl kritik
    critical_subset_cols = ['imdbRating', 'runtime', 'year']
    
    # Eğer 'director' ve 'genre' varsa onları da temizliğe dahil et
    if 'director' in df_clean.columns:
        critical_subset_cols.append('director')
    if 'genre' in df_clean.columns:
        critical_subset_cols.append('genre')

    rows_before_na = len(df_clean)
    df_clean.dropna(subset=critical_subset_cols, inplace=True)
    rows_after_na = len(df_clean)
    report_log.append(f"3. Eksik Veri Temizliği: Kritik bilgi (puan, süre, yıl vb.) eksik olan {rows_before_na - rows_after_na:,} kayıt silindi.")

    # Adım 4: 'runtime' (Süre) sütununu temizle
    if 'runtime' in df_clean.columns:
        df_clean['runtime'] = df_clean['runtime'].astype(str).str.replace(r'\s*min', '', regex=True)
        df_clean['runtime'] = pd.to_numeric(df_clean['runtime'], errors='coerce')
        df_clean.dropna(subset=['runtime'], inplace=True)
        df_clean['runtime'] = df_clean['runtime'].astype(int)
        report_log.append("4. 'runtime' Sütunu Temizlendi: Metin formatı (örn: '120 min') sayısal (120) tamsayıya dönüştürüldü.")

    # Adım 5: 'year' (Yıl) sütununu temizle
    if 'year' in df_clean.columns:
        df_clean['year'] = df_clean['year'].astype(str).str.slice(0, 4)
        df_clean['year'] = pd.to_numeric(df_clean['year'], errors='coerce')
        df_clean.dropna(subset=['year'], inplace=True)
        df_clean['year'] = df_clean['year'].astype(int)
        report_log.append("5. 'year' Sütunu Temizlendi: Metin formatı (örn: '1990-1991') sayısal (1990) tamsayıya dönüştürüldü.")

    # Adım 6: 'genre' (Tür) sütununu temizle
    if 'genre' in df_clean.columns:
        df_clean['genre'] = df_clean['genre'].astype(str).str.split(',').str[0].str.strip()
        report_log.append("6. 'genre' Sütunu Temizlendi: Birden fazla tür (örn: 'Comedy, Drama') ana türe ('Comedy') indirgendi.")

    final_rows = len(df_clean)
    report_log.append(f"\nTEMİZLİK SONUCU: {initial_rows:,} ham kayıttan, analiz için uygun {final_rows:,} temiz film verisi elde edildi.")
    
    return df_clean, "\n".join(report_log)

def generate_report(cleaning_log, analysis_findings, save_path, csv_name):
    """
    Tüm bulguları DİNAMİK olarak birleştirip 'analiz_raporu.txt' dosyasına yazar.
    Bu versiyon, veriye dair önceden-yazılmış (hard-coded) hiçbir yorum içermez.
    """
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""
IMDb FİLM ANALİZİ - OTOMATİK RAPOR
===================================================
Rapor Oluşturma Tarihi: {now}
Analiz Edilen Dosya: {csv_name}
===================================================

GİRİŞ
---------------------------------------------------
Bu rapor, '{csv_name}' adlı veri setinin otomatik analizini sunmaktadır.
Rapor, uygulanan veri temizleme adımlarını ve keşifsel veri analizi (EDA)
sonucunda elde edilen temel bulguları içermektedir.

Tüm destekleyici grafikler bu raporla aynı klasörde ('.png' formatında)
kayıtlıdır ve bulguların görsel yorumlaması için kullanılmalıdır.


AŞAMA 1: VERİ TEMİZLEME VE HAZIRLIK RAPORU
---------------------------------------------------
Analiz için ham veri seti üzerinde aşağıdaki adımlar uygulanmıştır:
(Not: Temizlenmiş ara veri dosyası diske kaydedilmemiştir.)
{cleaning_log}


AŞAMA 2: KEŞİFSEL VERİ ANALİZİ (EDA) - DİNAMİK BULGULAR
---------------------------------------------------
Temizlenmiş veri seti (Toplam {analysis_findings.get('final_rows', 0):,} film) üzerinden 
elde edilen bulgular aşağıdadır:

1. GENEL BAKIŞ VE PUAN DAĞILIMI
   - Analiz edilen filmlerin ortalama IMDb puanı: {analysis_findings.get('mean_rating', 0.0):.2f}
   - Medyan (Orta Değer) Puan: {analysis_findings.get('median_rating', 0.0):.2f}
   - Standart Sapma (Puan Dağılımı): {analysis_findings.get('std_rating', 0.0):.2f}
   - (Detaylı dağılım için bkz: 1_puan_dagilimi.png)

2. FİLM SÜRESİ ANALİZİ (0-240 Dk Arası Filmler)
   - Ortalama film süresi: {analysis_findings.get('mean_runtime', 0.0):.2f} dakika
   - Medyan (Orta Değer) Süre: {analysis_findings.get('median_runtime', 0.0):.0f} dakika
   - (Detaylı dağılım için bkz: 2_sure_dagilimi.png)

3. SÜRE-PUAN İLİŞKİSİ (0-240 Dk Arası Filmler)
   - Süre ve Puan arasındaki (Pearson) Korelasyon Katsayısı: {analysis_findings.get('correlation', 0.0):.4f}
   - (Korelasyon -1 ile 1 arasındadır. 0'a yakın olması zayıf ilişki, 1'e yakın 
     olması güçlü pozitif ilişki anlamına gelir.)
   - (İlişkinin yoğunluk haritası için bkz: 5_sure_puan_iliskisi.png)

4. TÜR ANALİZİ
   - Veri setindeki en popüler (en çok filme sahip) 10 tür:
{analysis_findings.get('popular_genres_table', 'Tür verisi bulunamadı.')}

   - PUAN BAŞARISI (En az 100 filme sahip türler):
     (Ortalama puana göre sıralanmış türlerin grafiği için bkz: 3_tur_puan_ortalamasi.png)

5. YÖNETMEN ANALİZİ
   - En başarılı yönetmenler (8.0+ Puanlı Film Sayısına Göre, en az 10 film yönetenler):
     (Yönetmen başarı sıralaması için bkz: 4_en_basarili_yonetmenler.png)

6. YILLARA GÖRE TRENDLER
   - Yıllara göre ortalama puan değişimleri için (bkz: 6_yillara_gore_puan.png).
   - Trend analizi (10 yıllık hareketli ortalama) grafiğe eklenmiştir.


SONUÇ
---------------------------------------------------
Rapor tamamlanmıştır. Tüm bulgular, {csv_name} dosyasından elde edilen
verilere dayanmaktadır ve 'analiz' klasöründeki grafiklerle desteklenmektedir.

*** Rapor Sonu ***
"""
    
    try:
        report_file_path = save_path / 'analiz_raporu.txt'
        with open(report_file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        return True
    except Exception as e:
        print(f"HATA: Rapor dosyası yazılırken bir hata oluştu: {e}")
        return False

# --- ANA SCRIPT AKIŞI ---

def main():
    """
    Ana script fonksiyonu: Kullanıcıdan yolu alır, 
    analiz klasörünü oluşturur ve tüm süreci yönetir.
    """
    print("🎬 IMDb FİLM ANALİZ VE RAPORLAMA SCRIPT'İ 🎬")
    print("=" * 40)
    
    # Adım 1: Kullanıcıdan CSV dosya yolunu al
    csv_file_path_str = input("Lütfen analiz edilecek .csv dosyasının tam yolunu girin:")
    
    csv_file_path = Path(csv_file_path_str)
    
    if not csv_file_path.is_file():
        print(f"HATA: Girdiğiniz yolda dosya bulunamadı: {csv_file_path}")
        return

    # Adım 2: Çıktı klasörünü ayarla ('analiz' klasörü)
    base_dir = csv_file_path.parent 
    analiz_dir = base_dir / 'analiz'
    
    try:
        analiz_dir.mkdir(exist_ok=True)
        print(f"\n📁 Analiz klasörü hazırlandı: {analiz_dir}")
    except Exception as e:
        print(f"HATA: Analiz klasörü oluşturulamadı: {e}")
        return

    # Adım 3: Veriyi Yükle ve Temizle
    print("⏳ Veri yükleniyor ve temizleniyor... (Bu işlem biraz sürebilir)")
    df_clean, cleaning_report = load_and_clean_data(csv_file_path)
    
    if df_clean is None or df_clean.empty:
        print("\nVeri temizleme başarısız oldu veya analiz edilecek veri kalmadı. Script durduruluyor.")
        print(f"Temizlik Raporu:\n{cleaning_report}")
        return
        
    print("✅ Veri temizleme tamamlandı.")
    print(f"   {len(df_clean):,} adet film analize hazır.")

    # Adım 4: Analizleri Yap ve Görselleri Oluştur
    print("📊 Analizler yapılıyor ve grafikler oluşturuluyor...")
    
    try:
        # Rapor için temel istatistikleri bir sözlükte toplayalım
        analysis_findings = {}
        analysis_findings['final_rows'] = len(df_clean)
        
        # Grafikleri oluştur ve bulguları topla
        
        # Puan istatistikleri
        if 'imdbRating' in df_clean.columns:
            plot_rating_distribution(df_clean, analiz_dir)
            analysis_findings['mean_rating'] = df_clean['imdbRating'].mean()
            analysis_findings['median_rating'] = df_clean['imdbRating'].median()
            analysis_findings['std_rating'] = df_clean['imdbRating'].std()
        
        # Süre istatistikleri
        if 'runtime' in df_clean.columns:
            plot_runtime_distribution(df_clean, analiz_dir)
            # Rapor için istatistikleri de aynı filtrelenmiş veriden al
            filtered_runtime_df = df_clean[(df_clean['runtime'] > 0) & (df_clean['runtime'] < 240)]
            if not filtered_runtime_df.empty:
                analysis_findings['mean_runtime'] = filtered_runtime_df['runtime'].mean()
                analysis_findings['median_runtime'] = filtered_runtime_df['runtime'].median()
            
            # Korelasyon
            correlation = plot_runtime_vs_rating(df_clean, analiz_dir)
            analysis_findings['correlation'] = correlation

        # Tür istatistikleri
        if 'genre' in df_clean.columns:
            popular_genres_table = plot_top_genres_by_rating(df_clean, analiz_dir)
            analysis_findings['popular_genres_table'] = popular_genres_table

        # Yönetmen istatistikleri
        if 'director' in df_clean.columns:
            plot_top_directors(df_clean, analiz_dir)
        
        # Yıl istatistikleri
        if 'year' in df_clean.columns:
            plot_rating_over_time(df_clean, analiz_dir)

        print("✅ Tüm grafikler 'analiz' klasörüne başarıyla kaydedildi.")
    
    except Exception as e:
        print(f"HATA: Görselleştirme sırasında bir hata oluştu: {e}")
        import traceback
        traceback.print_exc() # Hatanın detayını görmek için
        return

    # Adım 5: Yönetici Raporunu Oluştur
    print("📝 Otomatik rapor oluşturuluyor...")
    
    report_success = generate_report(
        cleaning_report, 
        analysis_findings, 
        analiz_dir,
        csv_file_path.name
    )
    
    if report_success:
        print(f"✅ Rapor başarıyla 'analiz_raporu.txt' olarak kaydedildi.")
        print("\n🎉 Tüm işlemler tamamlandı! 'analiz' klasörünü kontrol edebilirsiniz.")
    else:
        print("\n❌ Rapor oluşturulurken bir hata meydana geldi.")


if __name__ == "__main__":
    # Gerekli kütüphanelerin yüklü olduğundan emin olun
    # Terminale: pip install pandas numpy matplotlib seaborn
    sns.set_theme(style="whitegrid", palette="muted") # Grafikler için güzel bir tema ayarla
    main()
