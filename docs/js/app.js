// Data Science & Data Analyst Roadmap Application Logic

const modulesData = [
  // --- DATA ANALYST TRACK ---
  {
    id: "da-1",
    track: "analyst",
    number: "MOD-01",
    title: "İş Problemleri & KPI Tanımlama",
    category: "kpi",
    desc: "İş hedeflerini analitik metriklere dönüştürme, Kuzey Yıldızı (North Star) metriği ve KPI ağaçları oluşturma.",
    syllabus: [
      "İş Problemlerini Analiz Etme ve Hipotez Kurma",
      "KPI & OKR Kavramları ve Metrik Mimarisi",
      "North Star Metric ve Funnel Analiz Temelleri"
    ],
    chips: ["Business", "KPI", "Metrics", "Strategy"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_1_Is_Problemi_KPI.pdf"
  },
  {
    id: "da-2",
    track: "analyst",
    number: "MOD-02",
    title: "İleri Excel & Finansal Veri Modelleme",
    category: "excel",
    desc: "Karmaşık Excel formülleri, XLOOKUP, INDEX/MATCH, Pivot Table ve Senaryo Analizleri.",
    syllabus: [
      "Dinamik Dizi Formülleri ve Mantıksal Fonksiyonlar",
      "Özet Tablolar (Pivot Table) ve Veri Dilimleyiciler",
      "What-If Analizi ve Finansal Modelleme"
    ],
    chips: ["Excel", "Pivot", "Modeling", "Spreadsheets"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_2_Excel_Ayrintili.pdf"
  },
  {
    id: "da-3",
    track: "analyst",
    number: "MOD-03",
    title: "Veri Temelleri, Kalitesi & ETL Giriş",
    category: "data-eng",
    desc: "Ham verinin alınması, temizlenmesi, doğruluk ve tutarlılık kontrollerinin gerçekleştirilmesi.",
    syllabus: [
      "Veri Kalitesi (Data Quality) Boyutları",
      "Eksik ve Aykırı Değer Yönetimi",
      "ETL İşlem Adımları ve Veri Dönüştürme"
    ],
    chips: ["Data Quality", "ETL", "Cleansing", "Fundamentals"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_3_Veri_Temelleri_Ayrintili.pdf"
  },
  {
    id: "da-4",
    track: "analyst",
    number: "MOD-04",
    title: "İlişkisel Veritabanı Tasarımı & ERD",
    category: "sql",
    desc: "Varlık-İlişki Diyagramları (ERD), Birincil ve Yabancı Anahtarlar, Normalizasyon kuralları.",
    syllabus: [
      "ERD (Entity Relationship Diagram) Çizimi",
      "1NF, 2NF, 3NF Normalizasyon Teknikleri",
      "Veritabanı Şeması ve Veri Tipleri Tasarımı"
    ],
    chips: ["Database", "ERD", "Normalization", "Architecture"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_4_Iliskisel_Veritabanlari_Ayrintili.pdf"
  },
  {
    id: "da-5",
    track: "analyst",
    number: "MOD-05",
    title: "SQL Temel: Sorgulama & Filtreleme",
    category: "sql",
    desc: "SELECT, WHERE, ORDER BY, GROUP BY ve temel mantıksal operatörler ile veritabanı sorgulama.",
    syllabus: [
      "SELECT, WHERE, BETWEEN, IN Kullanımı",
      "GROUP BY ve Toplulaştırma (COUNT, SUM, AVG)",
      "ORDER BY ve LIMIT ile Veri Sıralama"
    ],
    chips: ["SQL", "Queries", "Filtering", "Aggregations"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_5_SQL_Temel_Ayrintili.pdf"
  },
  {
    id: "da-6",
    track: "analyst",
    number: "MOD-06",
    title: "SQL Orta Seviye: Tablo Birleştirme & Alt Sorgular",
    category: "sql",
    desc: "INNER JOIN, LEFT JOIN, FULL JOIN, Subqueries ve Karmaşık Mantıksal Koşullar.",
    syllabus: [
      "Tüm JOIN Türlerinin Derinlemesine İncelenmesi",
      "Correlated & Uncorrelated Subquery Mantığı",
      "HAVING vs WHERE Farkı ve Mantıksal Yapılar"
    ],
    chips: ["SQL", "Joins", "Subqueries", "Relational"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_6_SQL_Orta_Ayrintili.pdf"
  },
  {
    id: "da-7",
    track: "analyst",
    number: "MOD-07",
    title: "SQL İleri: Window Functions & Performans Tuning",
    category: "sql",
    desc: "Pencereli Fonksiyonlar (ROW_NUMBER, LAG/LEAD), CTE'ler, İndeksleme ve Sorgu Optimizasyonu.",
    syllabus: [
      "OVER(), PARTITION BY, RANK, DENSE_RANK",
      "CTE (Common Table Expressions) & Özyinelemeli Sorgular",
      "Index Optimizasyonu ve Query Execution Plan"
    ],
    chips: ["SQL", "Window Functions", "CTE", "Performance"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_7_SQL_Ileri_Ayrintili.pdf"
  },
  {
    id: "da-8",
    track: "analyst",
    number: "MOD-08",
    title: "İstatistik & Olasılık Analizi",
    category: "stats",
    desc: "Betimsel istatistikler, Olasılık Dağılımları, Hipotez Testleri ve Güven Aralıkları.",
    syllabus: [
      "Ortalama, Medyan, Standart Sapma, Skewness",
      "Normal Dağılım, Binom ve Poisson Dağılımı",
      "p-value, t-testi, Z-testi ve Hipotez Testi"
    ],
    chips: ["Statistics", "Probability", "Hypothesis", "Math"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_8_Istatistik_Ayrintili.pdf"
  },
  {
    id: "da-9",
    track: "analyst",
    number: "MOD-09",
    title: "Python ile Veri Analizi (Pandas & NumPy)",
    category: "python",
    desc: "Pandas DataFrame işlemleri, NumPy vektörel matris hesaplamaları ve Keşifçi Veri Analizi (EDA).",
    syllabus: [
      "NumPy Dizileri ve Vektörel Operasyonlar",
      "Pandas DataFrame Temizleme, Groupby ve Merge",
      "Kapsamlı Exploratory Data Analysis (EDA) Süreçleri"
    ],
    chips: ["Python", "Pandas", "NumPy", "EDA"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_9_Python_Ayrintili.pdf"
  },
  {
    id: "da-10",
    track: "analyst",
    number: "MOD-10",
    title: "Veri Görselleştirme (Seaborn & Plotly)",
    category: "python",
    desc: "Matplotlib, Seaborn ve Etkileşimli Plotly grafikleri ile görsel veri hikayeleştirme.",
    syllabus: [
      "Görsel Tasarım İlkeleri (Color Palette & Layout)",
      "Seaborn ile İstatistiksel Grafikler (Heatmap, Violin)",
      "Plotly ile Etkileşimli Dashboard ve Grafikler"
    ],
    chips: ["Visualization", "Plotly", "Seaborn", "Charts"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_10_Gorsellestirme_Ayrintili.pdf"
  },
  {
    id: "da-11",
    track: "analyst",
    number: "MOD-11",
    title: "Power BI & Business Intelligence (DAX)",
    category: "bi",
    desc: "Power BI Data Model, Star Schema, DAX Metrikleri ve Etkileşimli İş Raporları.",
    syllabus: [
      "Power Query ile Veri Dönüştürme",
      "Star Schema & Snowflake Şema Modelleme",
      "İleri DAX (CALCULATE, ALL, FILTER, Time Intelligence)"
    ],
    chips: ["Power BI", "DAX", "Business Intelligence", "Dashboards"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_11_Power_BI_Ayrintili.pdf"
  },
  {
    id: "da-12",
    track: "analyst",
    number: "MOD-12",
    title: "İleri Analitik Teknikler: RFM, Cohort & Churn",
    category: "kpi",
    desc: "RFM Müşteri Segmentasyonu, Cohort Elde Tutma Analizi, Funnel Analizi ve Churn Tahmini.",
    syllabus: [
      "RFM (Recency, Frequency, Monetary) Analizi",
      "Cohort Retention Matrix ve Yaşam Boyu Değer (CLV)",
      "Dönüşüm Hunisi (Funnel) ve Kayıp Müşteri (Churn) Analizi"
    ],
    chips: ["RFM", "Cohort", "Churn", "Customer Analytics"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_12_Analitik_Teknikler_Ayrintili.pdf"
  },
  {
    id: "da-13",
    track: "analyst",
    number: "MOD-13",
    title: "AI Destekli Veri Analizi & Otomasyon",
    category: "python",
    desc: "LLM ve AI araçları ile SQL sorgusu üretme, kod tamamlama ve analitik otomasyon.",
    syllabus: [
      "Prompt Engineering ile Analiz Hızlandırma",
      "AI ile Otomatik Rapor ve SQL Üretimi",
      "Python Script Otomasyonu ve İş Akışları"
    ],
    chips: ["AI Analytics", "LLM", "Automation", "Prompting"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_13_AI_Destekli_Analiz_Ayrintili.pdf"
  },
  {
    id: "da-14",
    track: "analyst",
    number: "MOD-14",
    title: "İş İletişimi & Data Storytelling",
    category: "career",
    desc: "Analiz sonuçlarını karar vericilere sunma, Data Storytelling ve Sunum Becerileri.",
    syllabus: [
      "Veri Odaklı Hikaye Anlatıcılığı (Data Storytelling)",
      "Executive Dashboard ve Özet Rapor Sunumları",
      "Kelimelerle ve Görsellerle Etkili İletişim"
    ],
    chips: ["Storytelling", "Communication", "Executive", "Soft Skills"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_14_Iletisim_Ayrintili.pdf"
  },
  {
    id: "da-15",
    track: "analyst",
    number: "MOD-15",
    title: "Portföy Oluşturma & Mülakat Hazırlığı",
    category: "career",
    desc: "GitHub Portföyü hazırlama, Case Study çözümleri ve Veri Analisti teknik mülakatları.",
    syllabus: [
      "Uçtan Uca Portföy Projesi Mimarisi",
      "GitHub Repository Düzenleme & README Hazırlama",
      "SQL & Analitik Case Study Mülakat Stratejileri"
    ],
    chips: ["Portfolio", "Career", "Interview", "GitHub"],
    pdfPath: "../data-analyst/Veri_Analisti_Modul_15_Portfolio_Mulakat_Ayrintili.pdf"
  },

  // --- DATA SCIENTIST TRACK ---
  {
    id: "ds-1",
    track: "scientist",
    number: "DS-01",
    title: "İş Problemi & KPI Tanımlama (DS Perspektifi)",
    category: "kpi",
    desc: "Makine Öğrenmesi projelerinde iş problemini optimizasyon ve hedef fonksiyona çevirme.",
    syllabus: [
      "ML Projelerinde Problem Tanımlama (Classification vs Regression)",
      "İş KPI'ları ile ML Metriklerinin (Precision, Recall, ROC-AUC) Eşlenmesi",
      "Baseline Model ve ROI Hesaplama"
    ],
    chips: ["Business Problem", "ML Metrics", "Problem Formulation"],
    pdfPath: "../data-scientist/01_Is_Problemi_KPI_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-2",
    track: "scientist",
    number: "DS-02",
    title: "Python Temelleri & Nesne Yönelimli Programlama",
    category: "python",
    desc: "Veri bilimi için gelişmiş Python syntax, Veri Yapıları, OOP ve Modüler Kod Mimarisi.",
    syllabus: [
      "List Comprehension, Generators ve Decorators",
      "Object-Oriented Programming (OOP) ve Sınıf Tasarımı",
      "Modüler Python Kütüphane Yapısı Oluşturma"
    ],
    chips: ["Python", "OOP", "Software Engineering", "Algorithms"],
    pdfPath: "../data-scientist/02_Python_Temelleri_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-3",
    track: "scientist",
    number: "DS-03",
    title: "NumPy & Vektörel Hesaplama Teknikleri",
    category: "python",
    desc: "Çok boyutlu diziler (N-D Arrays), Matrix Algebra, Broad-casting ve Vektörel Performans Optimizasyonu.",
    syllabus: [
      "Broadcasting Kuralları ve Vectorized Operations",
      "Lineer Cebir Operasyonları (Dot Product, Matrix Multiplications)",
      "High-Performance Computation & Memory Layout"
    ],
    chips: ["NumPy", "Linear Algebra", "Vectorization", "Performance"],
    pdfPath: "../data-scientist/03_NumPy_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-4",
    track: "scientist",
    number: "DS-11",
    title: "A/B Testing & Deneysel Tasarım",
    category: "stats",
    desc: "Ürün değişikliklerini doğrulamak için A/B Testleri, Örneklem Boyutu ve İstatistiki Anlamlılık.",
    syllabus: [
      "Hipotez Oluşturma ve Variance Reduction (CUPED)",
      "Sample Size (Örneklem Büyüklüğü) ve Power Analysis",
      "Minimum Detectable Effect (MDE) ve Novelty Effect"
    ],
    chips: ["A/B Testing", "Experimentation", "Statistics", "Product"],
    pdfPath: "../data-scientist/11_AB_Testing_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-5",
    track: "scientist",
    number: "DS-14",
    title: "Machine Learning Temelleri & Modelleme",
    category: "ml",
    desc: "Gözetimli ve Gözetimsiz Öğrenme, Cross-Validation, Bias-Variance Tradeoff ve Feature Engineering.",
    syllabus: [
      "Linear/Logistic Regression, Decision Trees, XGBoost/LightGBM",
      "K-Means, PCA, Hierarchical Clustering",
      "Overfitting, Regularization (L1/L2) ve Hyperparameter Tuning"
    ],
    chips: ["Machine Learning", "Scikit-Learn", "XGBoost", "Algorithms"],
    pdfPath: "../data-scientist/14_Machine_Learning_Temelleri_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-6",
    track: "scientist",
    number: "DS-44",
    title: "Data Ethics, Governance & Privacy",
    category: "career",
    desc: "Model adilliği (Fairness), Yapay Zeka Etiği, Algoritma Yanlılığı (Bias) ve KVKK/GDPR uyumu.",
    syllabus: [
      "Model Algoritma Yanlılığı (Fairness & Bias Audit)",
      "Explainable AI (SHAP, LIME)",
      "Veri Gizliliği (GDPR, KVKK, Anonymization)"
    ],
    chips: ["Data Ethics", "Governance", "SHAP", "Privacy"],
    pdfPath: "../data-scientist/44_Data_Ethics_Governance_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-7",
    track: "scientist",
    number: "DS-46",
    title: "Portfolio & GitHub Stratejisi",
    category: "career",
    desc: "Üst düzey Veri Bilimi projelerini GitHub üzerinde standartlara uygun yayınlama rehberi.",
    syllabus: [
      "Clean Code & PEP8 Standartları",
      "Virtual Environments (Conda/Pipenv) & Dockerfile Giriş",
      "README, Dokümantasyon ve Proje Sergileme"
    ],
    chips: ["GitHub", "Portfolio", "Clean Code", "Docker"],
    pdfPath: "../data-scientist/46_Portfolio_GitHub_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-8",
    track: "scientist",
    number: "DS-47",
    title: "Data Science Interview Preparation",
    category: "career",
    desc: "Kapsamlı Veri Bilimi Mülakat Rehberi: Algoritma, ML Teorisi, Coding ve System Case.",
    syllabus: [
      "ML Teori Soru Bankası & Çözümleri",
      "Live Coding ve Algoritma Mülakatı Taktikleri",
      "Behavioral & Problem Solving Case Study Mülakatları"
    ],
    chips: ["Interview", "Career", "Live Coding", "Problem Solving"],
    pdfPath: "../data-scientist/47_Data_Science_Interview_Ayrintili_Konu_Anlatimi.pdf"
  },
  {
    id: "ds-9",
    track: "scientist",
    number: "DS-48",
    title: "System Design for ML (MLSys Mimarisi)",
    category: "ml",
    desc: "Üretim ortamında ML modellerini ölçekleme, Real-Time Inference, Feature Store ve Monitoring.",
    syllabus: [
      "Batch vs Real-Time Inference Architecture",
      "Feature Store, Model Registry (MLflow) ve CI/CD Pipelines",
      "Data Drift, Concept Drift ve Model Monitoring"
    ],
    chips: ["System Design", "MLSys", "MLOps", "Architecture"],
    pdfPath: "../data-scientist/48_System_Design_for_ML_Ayrintili_Konu_Anlatimi.pdf"
  }
];

// Local Storage Progress Management
const STORAGE_KEY = 'ds_roadmap_completed_modules_v1';

function getCompletedModules() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch (e) {
    return [];
  }
}

function setCompletedModule(id, isCompleted) {
  let completed = getCompletedModules();
  if (isCompleted) {
    if (!completed.includes(id)) completed.push(id);
  } else {
    completed = completed.filter(item => item !== id);
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(completed));
  } catch (e) {}
  updateProgressUI();
}

// App State
let currentTrack = 'all';
let currentCategory = 'all';
let searchQuery = '';

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

function initApp() {
  renderModules();
  updateProgressUI();
  setupEventListeners();
}

function setupEventListeners() {
  // Track selector tabs
  const tabs = document.querySelectorAll('.track-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentTrack = tab.dataset.track;
      renderModules();
    });
  });

  // Category filter tags
  const tagBtns = document.querySelectorAll('.tag-btn');
  tagBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tagBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = btn.dataset.category;
      renderModules();
    });
  });

  // Search input
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderModules();
    });
  }

  // Modal elements
  const modalBackdrop = document.getElementById('modalBackdrop');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closeModal);
  }

  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) closeModal();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });
}

function renderModules() {
  const container = document.getElementById('moduleGrid');
  if (!container) return;

  const completedList = getCompletedModules();

  const filtered = modulesData.filter(mod => {
    // Filter track
    if (currentTrack !== 'all' && mod.track !== currentTrack) return false;
    
    // Filter category
    if (currentCategory !== 'all' && mod.category !== currentCategory) return false;

    // Filter search
    if (searchQuery) {
      const inTitle = mod.title.toLowerCase().includes(searchQuery);
      const inDesc = mod.desc.toLowerCase().includes(searchQuery);
      const inNum = mod.number.toLowerCase().includes(searchQuery);
      const inChips = mod.chips.some(c => c.toLowerCase().includes(searchQuery));
      return inTitle || inDesc || inNum || inChips;
    }

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
        <p style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">Aradığınız kriterlere uygun modül bulunamadı.</p>
        <p style="font-size: 0.9rem;">Filtreleri veya arama terimini değiştirmeyi deneyebilirsiniz.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(mod => {
    const isDone = completedList.includes(mod.id);
    const trackLabel = mod.track === 'analyst' ? 'Data Analyst' : 'Data Scientist';

    return `
      <div class="module-card ${isDone ? 'completed' : ''}" id="card-${mod.id}">
        <div>
          <div class="module-header">
            <div class="module-tag-row">
              <span class="track-badge ${mod.track}">${trackLabel}</span>
              <span class="mod-number">${mod.number}</span>
            </div>
            <button class="toggle-complete-btn" onclick="toggleComplete('${mod.id}')" title="${isDone ? 'Tamamlandı olarak işaretlendi' : 'Tamamlandı olarak işaretle'}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </button>
          </div>

          <h3 class="module-title">${mod.title}</h3>
          <p class="module-desc">${mod.desc}</p>

          <ul class="syllabus-list">
            ${mod.syllabus.map(item => `<li class="syllabus-item">${item}</li>`).join('')}
          </ul>

          <div class="topics-chips">
            ${mod.chips.map(chip => `<span class="chip">#${chip}</span>`).join('')}
          </div>
        </div>

        <div class="module-footer">
          <button class="btn-card-primary" onclick="openPdfModal('${mod.pdfPath}', '${mod.number}: ${mod.title}')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
            İncele (PDF)
          </button>
          <a class="btn-card-download" href="${mod.pdfPath}" download title="PDF İndir">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </a>
        </div>
      </div>
    `;
  }).join('');
}

function toggleComplete(id) {
  const completed = getCompletedModules();
  const isDone = completed.includes(id);
  setCompletedModule(id, !isDone);
  renderModules();
}

function updateProgressUI() {
  const completed = getCompletedModules();
  const total = modulesData.length;
  const count = completed.length;
  const percentage = Math.round((count / total) * 100);

  const fill = document.getElementById('globalProgressBar');
  const countText = document.getElementById('completedCountText');
  const pillText = document.getElementById('navProgressText');

  if (fill) fill.style.width = `${percentage}%`;
  if (countText) countText.textContent = `${count} / ${total} Modül (${percentage}%)`;
  if (pillText) pillText.textContent = `%${percentage} İlerleme`;
}

function openPdfModal(pdfUrl, title) {
  const backdrop = document.getElementById('modalBackdrop');
  const iframe = document.getElementById('modalIframe');
  const modalTitle = document.getElementById('modalTitle');

  if (!backdrop || !iframe) return;

  modalTitle.textContent = title;
  iframe.src = pdfUrl;
  backdrop.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const backdrop = document.getElementById('modalBackdrop');
  const iframe = document.getElementById('modalIframe');

  if (!backdrop) return;

  backdrop.classList.remove('active');
  if (iframe) iframe.src = 'about:blank';
  document.body.style.overflow = '';
}
