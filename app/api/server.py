"""
HTTP API server for receiving user data from node_workers.
Includes WebSocket support for real-time updates.
"""

import logging
from typing import List, Dict, Optional
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.db.session import db_session
from app.db.models import RawPlayer, IdentityMatch
from app.db.repositories import RawPlayerRepository

log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO
try:
    import eventlet
    async_mode = 'eventlet'
except ImportError:
    async_mode = 'threading'

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode=async_mode,
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    allow_upgrades=True,
    transports=['websocket', 'polling']
)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'enrichment-api'})


@app.route('/api/raw-players', methods=['POST'])
def receive_raw_players():
    """
    Receive array of user data from node_workers and save to PostgreSQL.
    
    Expected JSON body:
    {
        "players": [
            {"username": "player1", "site": "stake", "rank": 1, "metric_value": 100.5, "source_url": "https://..."},
            {"username": "player2", "site": "roobet", "rank": 2}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        players = data.get('players', [])
        if not players:
            return jsonify({
                'success': False,
                'error': 'No players provided in request'
            }), 400
        
        inserted = 0
        skipped = 0
        errors = 0
        
        with db_session() as session:
            for player_data in players:
                try:
                    username = player_data.get('username')
                    site = player_data.get('site') or player_data.get('platform')  # Support both
                    
                    if not username or not site:
                        errors += 1
                        continue
                    
                    # Check if already exists (site + username combination)
                    existing = session.query(RawPlayer).filter(
                        RawPlayer.site == site,
                        RawPlayer.username == username
                    ).first()
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    # Create new raw player
                    raw_player = RawPlayer(
                        site=site,
                        username=username,
                        rank=player_data.get('rank'),
                        metric_value=player_data.get('metric_value'),
                        source_url=player_data.get('source_url'),
                        captured_at=datetime.fromisoformat(player_data['timestamp'].replace('Z', '+00:00')) if player_data.get('timestamp') else None,
                    )
                    session.add(raw_player)
                    inserted += 1
                    
                except Exception as e:
                    log.error(f"Error processing player data: {e}")
                    errors += 1
                    continue
            
            session.commit()
            
            # Emit WebSocket events for new players
            if inserted > 0:
                new_players = session.query(RawPlayer).order_by(
                    RawPlayer.captured_at.desc()
                ).limit(inserted).all()
                
                for player in new_players:
                    socketio.emit('raw_player_added', {
                        'id': str(player.id),
                        'site': player.site,
                        'username': player.username,
                        'rank': player.rank,
                        'metric_value': float(player.metric_value) if player.metric_value else None,
                        'source_url': player.source_url,
                        'captured_at': player.captured_at.isoformat() if player.captured_at else None,
                    })
                
                _emit_stats_update()
        
        return jsonify({
            'success': True,
            'inserted': inserted,
            'skipped': skipped,
            'errors': errors
        })
        
    except Exception as e:
        log.error(f"Error receiving raw players: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/raw-players', methods=['GET'])
def get_raw_players():
    """Get raw players with pagination."""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        site = request.args.get('site')
        
        with db_session() as session:
            query = session.query(RawPlayer)
            
            if site:
                query = query.filter(RawPlayer.site == site)
            
            total = query.count()
            players = query.order_by(
                RawPlayer.captured_at.desc()
            ).limit(limit).offset(offset).all()
            
            return jsonify({
                'success': True,
                'data': [{
                    'id': str(p.id),
                    'site': p.site,
                    'username': p.username,
                    'rank': p.rank,
                    'metric_value': float(p.metric_value) if p.metric_value else None,
                    'source_url': p.source_url,
                    'captured_at': p.captured_at.isoformat() if p.captured_at else None,
                } for p in players],
                'total': total,
                'limit': limit,
                'offset': offset
            })
    except Exception as e:
        log.error(f"Error fetching raw players: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/identity-matches', methods=['GET'])
def get_identity_matches():
    """Get identity matches with pagination."""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        raw_player_id = request.args.get('raw_player_id')
        
        with db_session() as session:
            query = session.query(IdentityMatch).join(RawPlayer)
            
            if raw_player_id:
                query = query.filter(IdentityMatch.raw_player_id == raw_player_id)
            
            total = query.count()
            matches = query.order_by(
                IdentityMatch.total_score.desc(),
                IdentityMatch.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return jsonify({
                'success': True,
                'data': [{
                    'id': str(m.id),
                    'raw_player_id': str(m.raw_player_id),
                    'username': m.raw_player.username,
                    'site': m.raw_player.site,
                    'telegram_url': m.telegram_url,
                    'instagram_url': m.instagram_url,
                    'x_url': m.x_url,
                    'youtube_url': m.youtube_url,
                    'telegram_score': m.telegram_score,
                    'instagram_score': m.instagram_score,
                    'x_score': m.x_score,
                    'youtube_score': m.youtube_score,
                    'total_score': m.total_score,
                    'created_at': m.created_at.isoformat() if m.created_at else None,
                } for m in matches],
                'total': total,
                'limit': limit,
                'offset': offset
            })
    except Exception as e:
        log.error(f"Error fetching identity matches: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics."""
    try:
        with db_session() as session:
            total_raw_players = session.query(RawPlayer).count()
            total_identity_matches = session.query(IdentityMatch).count()
            
            site_counts = session.query(
                RawPlayer.site,
                func.count(RawPlayer.id).label('count')
            ).group_by(RawPlayer.site).all()
            
            return jsonify({
                'success': True,
                'total_raw_players': total_raw_players,
                'total_identity_matches': total_identity_matches,
                'by_site': {site: count for site, count in site_counts if site}
            })
    except Exception as e:
        log.error(f"Error fetching stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _emit_stats_update():
    """Emit stats update via WebSocket."""
    try:
        with db_session() as session:
            total_raw_players = session.query(RawPlayer).count()
            total_identity_matches = session.query(IdentityMatch).count()
            
            site_counts = session.query(
                RawPlayer.site,
                func.count(RawPlayer.id).label('count')
            ).group_by(RawPlayer.site).all()
            
            stats = {
                'total_raw_players': total_raw_players,
                'total_identity_matches': total_identity_matches,
                'by_site': {site: count for site, count in site_counts if site}
            }
            
            socketio.emit('stats_updated', stats)
    except Exception as e:
        log.error(f"Error emitting stats update: {e}")


# WebSocket events
@socketio.on('connect')
def handle_connect(auth):
    """Handle WebSocket connection."""
    log.info(f'WebSocket client connected from {request.remote_addr}')
    emit('connected', {'status': 'connected', 'message': 'Successfully connected to WebSocket'})
    _emit_stats_update()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    log.info(f'WebSocket client disconnected from {request.remote_addr}')


def create_app():
    """Create and return Flask app instance."""
    return app, socketio
