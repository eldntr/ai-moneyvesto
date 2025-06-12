# ai-moneyvesto

## 1. Arsitektur & Alur Sistem

### Endpoint: `/chat`

```mermaid
sequenceDiagram
    participant Klien as Pengguna/Frontend
    participant Docker as Kontainer Docker
    participant Flask as Aplikasi Flask
    participant Service as OpenRouter Service
    participant OpenRouter as OpenRouter API

    Klien->>+Docker: POST /chat (JSON)
    Docker->>+Flask: Meneruskan request ke /chat
    Flask->>+Service: get_chat_response(pesan, previous_chats)
    Service->>+OpenRouter: POST /v1/chat/completions (text)
    OpenRouter-->>-Service: Respons Teks
    Service-->>-Flask: Kembalikan teks
    Flask-->>-Docker: Respons JSON
    Docker-->>-Klien: {"response": "..."} 
```

Endpoint utama untuk interaksi berbasis teks.

- **URL**: `/chat`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`
- **Request Body (JSON)**:
  ```json
  {
    "message": "Apa kabar hari ini?",
    "previous_chats": [
      "Halo, siapa namamu?",
      "Namaku AI Moneyvesto. Bagaimana saya bisa membantu?"
    ]
  }
  ```
- **Respons Sukses (200 OK)**:
  Mengembalikan respons teks dari model AI.
  ```json
  {
    "response": "Saya baik-baik saja, terima kasih. Ada yang bisa saya bantu?"
  }
  ```
- **Contoh Pengujian dengan cURL**:
  ```bash
  curl -X POST http://localhost:{PORT}/chat \
       -H "Content-Type: application/json" \
       -d '{
            "message": "Apa kabar hari ini?",
            "previous_chats": [
              "Halo, siapa namamu?",
              "Namaku AI Moneyvesto. Bagaimana saya bisa membantu?"
            ]
          }'
  ```

--- 

### Endpoint: `/vision`

```mermaid
sequenceDiagram
    participant Klien as Pengguna/Frontend
    participant Docker as Kontainer Docker
    participant Flask as Aplikasi Flask
    participant Service as OpenRouter Service
    participant OpenRouter as OpenRouter API

    Klien->>+Docker: POST /vision (multipart/form-data)
    Docker->>+Flask: Meneruskan request ke /vision
    Flask->>+Service: get_vision_response(pesan, gambar)
    Note over Service: Encode gambar ke Base64
    Service->>+OpenRouter: POST /v1/chat/completions (text+image)
    OpenRouter-->>-Service: Respons Teks dari VLM
    Service-->>-Flask: Kembalikan teks
    Flask-->>-Docker: Respons JSON
    Docker-->>-Klien: {"response": "..."} 
```

Endpoint untuk interaksi yang melibatkan gambar dan teks.

- **URL**: `/vision`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: multipart/form-data`
- **Request Body (Form Data)**:

| Key       | Type   | Description                   | Wajib |
| :-------- | :----- | :---------------------------- | :---- |
| `message` | string | Pesan teks dari pengguna. Tambahkan konteks seperti "foto nota", "foto barang", atau "aktivitas rekening". | Ya    |
| `image`   | file   | File gambar (jpg, png, webp). | Ya    |

- **Respons Sukses (200 OK)**:
  Mengembalikan objek JSON dengan deskripsi atau jawaban dari model AI berdasarkan gambar dan teks.
  ```json
  {
    "response": "Nota ini mencatat pembelian 2 barang: 1 galon air mineral seharga 22000 dan 1 bungkus roti seharga 15000."
  }
  ```
- **Contoh Pengujian dengan cURL**:
  Ganti `path/to/your/image.jpg` dengan path file gambar Anda.
  ```bash
  curl -X POST http://localhost:{PORT}/vision -F "image=@path/to/your/image.jpg"
  ```

--- 

### Endpoint: `/record`

```mermaid
sequenceDiagram
    participant Klien as Pengguna/Frontend
    participant Docker as Kontainer Docker
    participant Flask as Aplikasi Flask
    participant Service as OpenRouter Service
    participant OpenRouter as OpenRouter API

    Klien->>+Docker: POST /record (JSON)
    Docker->>+Flask: Meneruskan request ke /record
    Flask->>+Service: record_finance(pesan)
    Service->>+OpenRouter: POST /v1/chat/completions (text)
    OpenRouter-->>-Service: Respons JSON
    Service-->>-Flask: Kembalikan JSON transaksi
    Flask-->>-Docker: Respons JSON
    Docker-->>-Klien: [{"description": "...", ...}]
```

Endpoint untuk mencatat transaksi keuangan dari pesan teks.

- **URL**: `/record`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`
- **Request Body (JSON)**:
  ```json
  {
    "message": "hari ini beli 2 porsi nasi goreng 15rb dan es teh manis 5000"
  }
  ```
- **Respons Sukses (200 OK)**:
  Mengembalikan daftar transaksi dalam format JSON.
  ```json
  [
    {
      "description": "Nasi Goreng",
      "transaction_type": "withdrawal",
      "amount": 2,
      "total_price": 30000
    },
    {
      "description": "Es Teh Manis",
      "transaction_type": "withdrawal",
      "amount": 1,
      "total_price": 5000
    }
  ]
  ```
- **Contoh Pengujian dengan cURL**:
  ```bash
  curl -X POST http://localhost:{PORT}/record \
       -H "Content-Type: application/json" \
       -d '{ "message": "hari ini beli 2 porsi nasi goreng 15rb dan es teh manis 5000" }'
  ```

--- 

### Endpoint: `/transaction`

```mermaid
sequenceDiagram
    participant Klien as Pengguna/Frontend
    participant Docker as Kontainer Docker
    participant Flask as Aplikasi Flask
    participant Service as OpenRouter Service
    participant OpenRouter as OpenRouter API

    Klien->>+Docker: POST /transaction (multipart/form-data)
    Docker->>+Flask: Meneruskan request ke /transaction
    Flask->>+Service: get_vision_response(prompt, gambar)
    Note over Service: Encode gambar ke Base64
    Service->>+OpenRouter: POST /v1/chat/completions (text+image)
    OpenRouter-->>-Service: Respons Teks dari VLM
    Service->>+Service: record_finance(vision_response)
    Service->>+OpenRouter: POST /v1/chat/completions (text)
    OpenRouter-->>-Service: Respons JSON transaksi
    Service->>+Service: get_tone_responses(vision_response)
    Service->>+OpenRouter: POST /v1/chat/completions (3x untuk setiap nada)
    OpenRouter-->>-Service: 3 Respons dengan nada berbeda
    Service-->>-Flask: Kembalikan analisis + transaksi + respons nada
    Flask-->>-Docker: Respons JSON
    Docker-->>-Klien: {"vision_analysis": "...", "transactions": [...], "responses": {...}}
```

Endpoint untuk memproses gambar nota/struk menjadi data transaksi terstruktur dengan respons AI dalam 3 nada berbeda. Menggabungkan analisis gambar, pencatatan keuangan, dan respons berkarakter.

- **URL**: `/transaction`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: multipart/form-data`
- **Request Body (Form Data)**:

| Key         | Type   | Description                              | Wajib |
| :---------- | :----- | :--------------------------------------- | :---- |
| `image`     | file   | File gambar nota/struk (jpg, png, webp). | Ya    |
| `tone_type` | string | Jenis nada respons: `supportive_cheerleader`, `angry_mom`, `wise_mentor`, atau `all` (default: `all`) | Tidak |

- **Respons Sukses (200 OK)**:
  Mengembalikan objek JSON dengan analisis gambar, daftar transaksi terstruktur, dan respons AI sesuai tone yang diminta.
  
  **Jika tone_type="all" atau tidak diisi:**
  ```json
  {
    "vision_analysis": "Nota ini mencatat pembelian beberapa item: beli nasi goreng 2 porsi dengan harga 30000, beli es teh manis 1 gelas dengan harga 5000.",
    "transactions": [
      {
        "description": "Nasi Goreng",
        "transaction_type": "withdrawal",
        "amount": 2,
        "total_price": 30000
      },
      {
        "description": "Es Teh Manis",
        "transaction_type": "withdrawal",
        "amount": 1,
        "total_price": 5000
      }
    ],
    "responses": {
      "supportive_cheerleader": "Great job mencatat pengeluaran! Rp 35.000 untuk makanan masih wajar kok. Keep it up!",
      "angry_mom": "Duh, jajan lagi! 35 ribu buat makan siang doang. Coba deh masak sendiri, lebih hemat!",
      "wise_mentor": "Pengeluaran Rp 35.000 per hari = Rp 1 juta per bulan untuk makan. Pertimbangkan meal prep untuk efisiensi budget."
    }
  }
  ```
  
  **Jika tone_type="supportive_cheerleader":**
  ```json
  {
    "vision_analysis": "Nota ini mencatat pembelian beberapa item...",
    "transactions": [...],
    "responses": {
      "supportive_cheerleader": "Great job mencatat pengeluaran! Rp 35.000 untuk makanan masih wajar kok. Keep it up!"
    }
  }
  ```

- **Contoh Pengujian dengan cURL**:
  ```bash
  # Semua tone (default)
  curl -X POST http://localhost:{PORT}/transaction \
       -F "image=@path/to/your/receipt.jpg"
  
  # Tone tertentu
  curl -X POST http://localhost:{PORT}/transaction \
       -F "image=@path/to/your/receipt.jpg" \
       -F "tone_type=supportive_cheerleader"
  ```

---