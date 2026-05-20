// socket-server/server.js - ADD /emit-event endpoint
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
const server = http.createServer(app);

// Enable CORS
app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:3000', 'http://localhost:8000'],
  credentials: true
}));
app.use(express.json());

// Socket.IO with proper CORS
const io = new Server(server, {
  cors: {
    origin: ['http://localhost:5173', 'http://localhost:3000', 'http://localhost:8000'],
    methods: ['GET', 'POST'],
    credentials: true
  }
});

// Store connected admins
const adminSockets = new Set();

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    admins: adminSockets.size,
    timestamp: new Date()
  });
});

// ✅ NEW: Endpoint for Django to emit events
app.post('/emit-event', (req, res) => {
  const { event, data } = req.body;
  console.log(`📨 Received event: ${event}`, data);

  if (event === 'new_order') {
    // Broadcast to all connected admins
    io.to('admin_room').emit('new_order', data);
    io.to('admin_room').emit('admin:newNotification', {
      title: '🛒 New Order!',
      message: `Order #${data.order_id} - ₹${data.total_amount} from ${data.customer_name}`,
      data: data,
      notificationType: 'order',
      timestamp: new Date()
    });
    console.log(`✅ Broadcast new order to ${adminSockets.size} admins`);
  }

  res.json({ status: 'sent', event: event });
});

// Keep the old endpoint for compatibility
app.post('/emit', (req, res) => {
  const { event, data } = req.body;
  console.log(`📨 Received (legacy): ${event}`, data);

  if (event === 'new_order') {
    io.to('admin_room').emit('new_order', data);
    io.to('admin_room').emit('admin:newNotification', {
      title: '🛒 New Order!',
      message: `Order #${data.order_id} - ₹${data.total} from ${data.username}`,
      data: data,
      notificationType: 'order'
    });
  }

  res.json({ status: 'sent' });
});

// Socket connection handling
io.on('connection', (socket) => {
  console.log('🟢 Client connected:', socket.id);

  socket.on('authenticate', (data) => {
    console.log('🔐 Authenticating:', data);

    if (data.userType === 'admin') {
      adminSockets.add(socket.id);
      socket.join('admin_room');
      socket.emit('admin:connected', {
        message: 'Connected to admin panel',
        activeUsers: adminSockets.size
      });
      console.log(`👑 Admin authenticated. Total admins: ${adminSockets.size}`);
    }
  });

  socket.on('user:sendNotification', (data) => {
    console.log('📢 User notification:', data);
    io.to('admin_room').emit('admin:newNotification', data);
  });

  socket.on('disconnect', () => {
    console.log('🔴 Client disconnected:', socket.id);
    adminSockets.delete(socket.id);
  });
});

const PORT = 5000;
server.listen(PORT, () => {
  console.log(`\n🚀 Socket server running on http://localhost:${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`📨 POST endpoint: http://localhost:${PORT}/emit-event`);
  console.log(`✅ CORS enabled for http://localhost:5173, http://localhost:8000\n`);
});