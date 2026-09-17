const express = require('express');
const { getAllUsers, getUserById, createUser, updateUser } = require('../controllers/userController');

const router = express.Router();

router.get('/', getAllUsers);
router.get('/:id', getUserById);
router.post('/', createUser);
router.put('/:id', updateUser);

module.exports = router;
