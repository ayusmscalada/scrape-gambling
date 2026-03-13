#!/usr/bin/env python3
"""
Simple test script to verify WebSocket connection works.
"""
import socketio
import time

# Create a Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print('✅ Connected to server!')
    print(f'   Session ID: {sio.sid}')

@sio.event
def disconnect():
    print('❌ Disconnected from server')

@sio.event
def connected(data):
    print(f'📡 Server confirmed connection: {data}')

@sio.event
def stats_updated(data):
    print(f'📊 Stats updated: {data}')

if __name__ == '__main__':
    try:
        print('🔌 Connecting to http://localhost:5000...')
        sio.connect('http://localhost:5000')
        print('✅ Connection established!')
        print('   Waiting for events (press Ctrl+C to exit)...')
        
        # Keep the connection alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n👋 Disconnecting...')
        sio.disconnect()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
