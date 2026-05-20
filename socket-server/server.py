# # socket-server/server.py - COMPLETE WORKING VERSION
# import socketio
# import eventlet
# import json
# from eventlet import wsgi

# # Create Socket.IO server with CORS enabled
# sio = socketio.Server(
#     cors_allowed_origins='*',
#     async_mode='eventlet'
# )

# # Create WSGI app
# app = socketio.WSGIApp(sio)


# @sio.event
# def connect(sid, environ):
#     print(f'✅ Client connected: {sid}')
#     sio.emit('connected', {'status': 'ok'}, room=sid)


# @sio.event
# def authenticate(sid, data):
#     """Handle admin authentication"""
#     print(f'🔐 Admin authenticated: {data.get("userName", "Unknown")}')
#     sio.save_session(sid, {'role': 'admin'})
#     sio.emit('admin:connected', {
#         'message': 'Admin dashboard connected',
#         'activeUsers': 0
#     }, room=sid)
#     sio.enter_room(sid, 'admin_room')
#     print(f'👑 Admin joined admin_room')


# @sio.event
# def disconnect(sid):
#     print(f'🔴 Client disconnected: {sid}')


# # Custom WSGI middleware to handle CORS
# class CORSMiddleware:
#     def __init__(self, app):
#         self.app = app

#     def __call__(self, environ, start_response):
#         def custom_start_response(status, headers, exc_info=None):
#             # Add CORS headers
#             headers.append(('Access-Control-Allow-Origin', '*'))
#             headers.append(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'))
#             headers.append(('Access-Control-Allow-Headers', 'Content-Type, Authorization'))
#             headers.append(('Access-Control-Max-Age', '86400'))
#             return start_response(status, headers, exc_info)
        
#         # Handle preflight OPTIONS request
#         if environ['REQUEST_METHOD'] == 'OPTIONS':
#             custom_start_response('204 No Content', [])
#             return [b'']
        
#         return self.app(environ, custom_start_response)


# # Create a simple WSGI app for HTTP endpoints
# def http_app(environ, start_response):
#     path = environ.get('PATH_INFO', '')
    
#     # Handle CORS preflight
#     if environ['REQUEST_METHOD'] == 'OPTIONS':
#         start_response('204 No Content', [
#             ('Access-Control-Allow-Origin', '*'),
#             ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
#             ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
#             ('Access-Control-Max-Age', '86400'),
#         ])
#         return [b'']
    
#     # Health check endpoint
#     if path == '/health' and environ['REQUEST_METHOD'] == 'GET':
#         start_response('200 OK', [
#             ('Content-Type', 'application/json'),
#             ('Access-Control-Allow-Origin', '*'),
#         ])
#         return [b'{"status": "healthy", "server": "python"}']
    
#     # Notification endpoint
#     if path == '/emit' and environ['REQUEST_METHOD'] == 'POST':
#         try:
#             content_length = int(environ.get('CONTENT_LENGTH', 0))
#             body = environ['wsgi.input'].read(content_length)
#             data = json.loads(body)
            
#             event = data.get('event')
#             notification_data = data.get('data', {})
            
#             print(f"📨 Received notification: {event}")
            
#             if event == 'new_order':
#                 # Broadcast to all admins
#                 sio.emit('new_order', notification_data, room='admin_room')
#                 sio.emit('admin:newNotification', {
#                     'title': '🛒 New Order!',
#                     'message': f"Order #{notification_data.get('order_id', 'N/A')} - ₹{notification_data.get('total', 0)}",
#                     'data': notification_data,
#                     'notificationType': 'order'
#                 }, room='admin_room')
#                 print(f"✅ Broadcast new order: {notification_data}")
            
#             start_response('200 OK', [
#                 ('Content-Type', 'application/json'),
#                 ('Access-Control-Allow-Origin', '*'),
#             ])
#             return [b'{"status": "sent"}']
            
#         except Exception as e:
#             print(f"❌ Error: {e}")
#             start_response('500 Internal Error', [
#                 ('Content-Type', 'application/json'),
#                 ('Access-Control-Allow-Origin', '*'),
#             ])
#             return [b'{"error": "failed"}']
    
#     # 404 for other paths
#     start_response('404 Not Found', [
#         ('Content-Type', 'application/json'),
#         ('Access-Control-Allow-Origin', '*'),
#     ])
#     return [b'{"error": "not found"}']


# # Wrap the socket app with CORS middleware
# wrapped_app = CORSMiddleware(app)

# # Create a combined app that routes to socket or HTTP
# def combined_app(environ, start_response):
#     path = environ.get('PATH_INFO', '')
    
#     # Socket.IO paths go to the socket app
#     if path.startswith('/socket.io/'):
#         return wrapped_app(environ, start_response)
    
#     # HTTP endpoints go to http_app
#     return http_app(environ, start_response)


# if __name__ == '__main__':
#     PORT = 5000
#     print(f"🚀 Socket.IO server running on http://localhost:{PORT}")
#     print(f"📊 Health check: http://localhost:{PORT}/health")
#     print(f"📨 Notification endpoint: http://localhost:{PORT}/emit")
#     print(f"🔌 WebSocket endpoint: ws://localhost:{PORT}/socket.io/")
#     print("\n✅ CORS enabled for all origins")
#     print("✅ Ready to receive notifications\n")
    
#     # Run the server
#     wsgi.server(eventlet.listen(('0.0.0.0', PORT)), combined_app)