# Easy-Split-
take a picture of the receipt and have the app tell you how much each person owes, then connects you with mobile banking so you can split evenly. Keeps track of spending for others. 

![Alt text describing the image](./static/images/app_front.png)


## Authentication API Routes

### 1. Google OAuth

- **GET `/api/auth/google/login`**  
  Redirects the user to Google’s OAuth consent screen to initiate login.

- **GET `/api/auth/google/auth`**  
  Callback endpoint for Google OAuth. Retrieves user info, registers new users if needed, and returns a JWT access token.  

---

### 2. User Registration

- **POST `/api/auth/register`**  
  Registers a new user with the following fields:  
  - `username` (required, unique)  
  - `email` (required, unique)  
  - `password` (required)  
  - `name` (optional)  
  - `birthdate` (optional, format: YYYY-MM-DD)  
  - `phone_number` (optional)  

**Responses:**  
- `201 Created` – User successfully registered  
- `400 Bad Request` – Validation errors (duplicate username/email, missing password, invalid birthdate)

---

### 3. User Login

- **POST `/api/auth/login`**  
  Logs in a user using **username or email** and password. Returns a JWT access token.  

**Responses:**  
- `200 OK` – Login successful, returns JWT  
- `401 Unauthorized` – Invalid credentials or OAuth-only user attempting password login  

---

### 4. Protected User Info

- **GET `/api/auth/me`**  
  Requires a valid JWT. Returns the current user’s information:  
  - `id`  
  - `username`  
  - `email`  
  - `phone_number` 

## Receipt Processing API Routes

### 5. Process Receipt Image

- **POST `/api/process-receipt`**  
  Uploads a receipt image, validates the file type, processes it, and returns structured receipt data.

**Accepted File Types:**  
- `image/jpeg`  
- `image/png`  
- `image/webp`

**Responses:**  
- `200 OK` – Receipt processed successfully  
  - Returns:  
    - `success` (boolean)  
    - `data` (parsed receipt information)  
    - `receipt_id` (database ID)

- `400 Bad Request` – Missing image or empty filename  
  - `{ "error": "No image file provided" }`  
  - `{ "error": "No file selected" }`

- `415 Unsupported Media Type` – File is not an allowed image type  
  - `{ "error": "Unsupported file type: text/plain. Must be an image." }`

- `500 Internal Server Error` – Failure during image processing  
  - `{ "success": false, "error": "Internal Server Error during image processing." }`

---
### 6. Get All User Receipts

**GET `/api/user/receipts`** *(JWT required)*  
  Returns all receipts for the authenticated user. 

---

**Notes:**  
- All JWTs use `user.id` as the identity (string).  
- OAuth users cannot login with a password.  
- Registration handles birthdate conversion.  
