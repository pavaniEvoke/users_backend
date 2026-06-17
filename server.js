require('dotenv').config();
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Static in-memory users (no MongoDB required)
const users = [
  { _id: '1', name: 'Alice Johnson', email: 'alice@example.com' },
  { _id: '2', name: 'Bob Smith', email: 'bob@example.com' },
  { _id: '3', name: 'Cara Lee', email: 'cara@example.com' }
];

app.get('/api/users', (req, res) => {
  res.json(users);
});

// Seed endpoint for compatibility (returns existing static users)
app.get('/api/seed', (req, res) => {
  res.json({ seeded: true, count: users.length });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
