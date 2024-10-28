const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mongoose = require('mongoose');

// Define the MongoDB schema and model
const messageSchema = new mongoose.Schema({
    time: String,
    job_id: String,
    content_id: String,
    content_type: String,
    file_name: String,
    status: String,
    message: String
}, { timestamps: true });

const Message = mongoose.model('Message', messageSchema);

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

const PORT = process.env.PORT || 5001;

// Connect to MongoDB without deprecated options
mongoose.connect('mongodb://localhost:27017/dashboard_db')
    .then(() => console.log('Connected to MongoDB'))
    .catch(err => console.error('MongoDB connection error:', err));

// WebSocket connection
io.on('connection', (socket) => {
    console.log('New client connected');

    // Fetch all messages from the database on client connection
    Message.find({})
        .sort({ createdAt: -1 }) // Sort by creation time (newest first)
        .limit(100) // Limit to the most recent 100 messages (adjust as needed)
        .then((messages) => {
            socket.emit('initialMessages', messages);
        })
        .catch((err) => console.error('Error fetching messages:', err));

    // Listen for new messages
    socket.on('newMessage', (msg) => {
        const newMessage = new Message(msg);
        newMessage.save()
            .then(() => {
                io.emit('newMessage', msg); // Broadcast the new message to all clients
                console.log('New message saved and broadcasted');
            })
            .catch((err) => console.error('Error saving new message:', err));
    });

    // Handle client disconnect
    socket.on('disconnect', () => {
        console.log('Client disconnected');
    });
});

server.listen(PORT, () => console.log(`Server running on port ${PORT}`));
