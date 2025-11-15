# **Easy-Split**  
### AI-Powered Receipt Scanner • Smart Bill Splitting

<div align="center">

<img src="./static/img/app_front.png" width="360" />

---

### Tech Stack
![React Native](https://img.shields.io/badge/React%20Native-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Expo](https://img.shields.io/badge/Expo-000000?style=for-the-badge&logo=expo&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-FFFFFF?style=for-the-badge&logo=flask&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=yellow)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=jsonwebtokens)
![OCR](https://img.shields.io/badge/OCR-Image%20Processing-blueviolet?style=for-the-badge)

</div>

---
## App Demo
<p align="center">
<img src="./static/img/app.gif" width="200" height="350" />
</p>
---

# **Project Overview**

**Easy-Split** makes splitting bills painless.  
Just take a picture → AI extracts items → assign friends → done.  

### What the app can do
- Scan receipts automatically  
- Extract totals, items, taxes via OCR  
- Calculate per-person owed amounts  
- Create groups & track shared receipts  
- View spending history  
- Login via Google or email/password  

---

# **Frontend – React Native + TypeScript (Expo)**

Designed mobile-first with soft animations, modern UI, and intuitive flows.

---

## **Mobile UI**
- Minimal, clean, modern design  
- Light + Dark themes  
- Custom tab navigation  
- Reusable components  
- Rounded cards & soft shadows  

---

## **Auth Screens**
- Google OAuth  
- Login / Signup 
- Form validation + errors  

---

## **Receipt Upload Journey**
- Pick or capture a photo  
- Upload to backend  
- Display parsed items + totals  

---

## **Group Management**
- Create groups  
- Shared expense tracking  

---

## **History Page**
- Fetch user receipts via JWT  
- Display previous spending  

---

## **Profile Page**
- User info  
- Theme toggle  
- Logout  

---

# **Backend – Flask API (Python)**

Handles OCR, authentication, and user data.

---

# Authentication API Routes

### **Google OAuth**
- **GET `/api/auth/google/login`** – initiate login  
- **GET `/api/auth/google/auth`** – callback → returns JWT

### **Register**
**POST `/api/auth/register`**

### **Login**
**POST `/api/auth/login`**

### **Me**
**GET `/api/auth/me`** *(JWT required)*

---

# Receipt API Routes

### **Process Receipt**
**POST `/api/process-receipt`**  
Accepts: jpeg, png, webp  
Returns receipt data + receipt_id  

### **Get User Receipts**
**GET `/api/user/receipts`** *(JWT required)*

---

# **Folder Structure**

```
Easy-Split-Gdi-Hackathon-2025/
│
├── frontend/                <-- React Native app 
│   ├── src/
│   ├── screens/
│   ├── components/
│   ├── navigation/
│   └── app.json
│
├── static/img/             <-- README images
├── tests/
├── app.py                  <-- Flask API root
├── models.py
├── bill_splitting_logic.py
├── extensions.py
└── requirements.txt
```

---

# **Running the Project**

## **Backend**
```bash
pip install -r requirements.txt
python app.py
```

## **Frontend (Expo)**
```bash
cd frontend
npm install
npx expo start
```

Scan the QR with your phone to launch the app.

---

# **Team**
Built collaboratively during the GDI 2025 Hackathon.

---
