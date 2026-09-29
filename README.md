# 🍽️ Gastro ERP - Merkezi Mutfak ve Tedarik Yönetim Sistemi

![Odoo](https://img.shields.io/badge/Odoo-19.0-purple?style=flat-square&logo=odoo)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Relational_DB-blue?style=flat-square&logo=postgresql)

Çok şubeli restoran yapıları ve tedarikçiler için tasarlanmış, **rol tabanlı erişim kontrolüne (RBAC)** ve **veri izolasyonuna** sahip kapsamlı bir Odoo ERP modülüdür. Sistem, merkezden yönetilen bir hammadde kataloğu ile restoranların serbest piyasa usulüyle teklifleştiği dinamik bir ihale altyapısını birleştirir.

## 🚀 Öne Çıkan Özellikler ve Mimari

* 🔒 **Rol Tabanlı Katı Veri İzolasyonu (RBAC):** Odoo'nun `ir.model.access` ve `ir.rule` yapıları kullanılarak Admin (Merkez) ve Restoran (Kullanıcı) profilleri arasında kesin veri gizliliği ve işlem kısıtlamaları sağlandı. Miras alma (inheritance) çakışmaları çözümlenerek yetki sızıntıları engellendi.
* 📚 **Merkezi "Evrensel Katalog" Mimarisi:** Veri kirliliğini önlemek amacıyla hammaddeler (gastro.ingredient) sadece sistem yöneticisi tarafından eklenebilir. Restoranlar ise salt okunur (read-only) erişimle bu verileri sadece kendi reçetelerinde görüntüleyip seçebilir.
* 📝 **Reçete Başvuru İş Akışı:** Restoran kullanıcılarının ana üretim reçetelerine doğrudan müdahale etmesi engellenmiş, bunun yerine merkezin onayına sunulan "Reçete Başvuru" mekanizması kurgulanmıştır.
* 🤝 **Dinamik İhale ve Teklif Motoru:** Mutfakların malzeme taleplerine karşılık tedarikçilerin fiyat teklifi sunabildiği, veritabanı ilişkileri (One2many, Many2one) ile birbirine bağlanan onay akışları geliştirilmiştir.

## 📸 Ekran Görüntüleri

**1. Katı Yetki İzolasyonu (Sadece Okuma Yetkisi Olan Restoran Görünümü)**
<img width="1906" height="759" alt="image" src="https://github.com/user-attachments/assets/82f650d4-0764-421a-97b3-dc49b7ffddb2" />



**2. Evrensel Katalog ve Reçete Başvurusu**
<img width="1908" height="708" alt="image" src="https://github.com/user-attachments/assets/fb1cc4c4-3690-48da-b204-c350c2ed8862" />



**3. İhale Merkezi ve Teklif Yönetimi**
<img width="1914" height="564" alt="image" src="https://github.com/user-attachments/assets/693ba606-2e7f-4376-8bd3-6f4d55caae36" />


## 🛠️ Teknik Altyapı
- **Backend:** Python, Odoo ORM (Object-Relational Mapping)
- **Arayüz (Frontend):** Odoo XML (Dinamik formlar, Tree ve Kanban görünümleri)
- **İş Akışları:** TransientModel tabanlı Wizard (Sihirbaz) yapıları
- **Veritabanı:** PostgreSQL

## 👨‍💻 Geliştirici
**Fatih Cemal Yılmaz**  
Bilişim Sistemleri Mühendisi / Yazılım Geliştirici
