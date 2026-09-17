# Backend

Express API with MongoDB (Mongoose) for user signup/login and listing users.

Setup:

```bash
cd backend
npm install
cp .env.example .env   # then fill in MONGO_URI, PORT, JWT_SECRET, SENDGRID_API_KEY, FROM_EMAIL
npm start
```

Endpoints:
- `POST /api/auth/signup` - body: `{ name, email, password }` → creates a user, sends a welcome email, returns `{ token, user }`
- `POST /api/auth/login` - body: `{ email, password }` → returns `{ token, user }`
- `GET /api/users` - list all users (passwords excluded)
- `GET /api/users/:id` - get a single user by id
- `POST /api/users` - body: `{ name, email, password }` → creates a user and sends a welcome email
- `PUT /api/users/:id` - body: any of `{ name, email, password }` → updates a user
