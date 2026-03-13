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

from app.db.session import db_session
from app.db.models import RawPlayer, QualifiedLead, IdentityMatch
from app.db.repositories import RawPlayerRepository

log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow CORS for React frontend
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


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
            {"username": "player1", "platform": "stake", "timestamp": "2026-03-13T10:30:00Z"},
            {"username": "player2", "platform": "roobet", "timestamp": "2026-03-13T10:29:00Z"}
        ]
    }
    
    Returns:
        {
            "success": true,
            "inserted": 2,
            "skipped": 1,
            "errors": 0
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Accept both "players" and "usernames" for backward compatibility
        players = data.get('players') or data.get('usernames', [])
        
        if not isinstance(players, list):
            return jsonify({
                'success': False,
                'error': 'Expected "players" or "usernames" to be an array'
            }), 400
        
        if len(players) == 0:
            return jsonify({
                'success': True,
                'inserted': 0,
                'skipped': 0,
                'errors': 0,
                'message': 'No players provided'
            })
        
        # Process players
        inserted = 0
        skipped = 0
        errors = 0
        
        with db_session() as session:
            from datetime import datetime
            from sqlalchemy.exc import IntegrityError
            
            for player_data in players:
                try:
                    username = player_data.get('username') or player_data.get('user')
                    platform = player_data.get('platform') or player_data.get('source_site')
                    
                    if not username:
                        log.warning(f"Skipping player with no username: {player_data}")
                        skipped += 1
                        continue
                    
                    # Check if already exists (uniqueness check by username + platform)
                    existing = RawPlayerRepository.get_by_username(
                        db=session,
                        username=username,
                        source_site=platform
                    )
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    # Parse timestamp if provided
                    captured_at = None
                    if 'timestamp' in player_data:
                        try:
                            timestamp_str = player_data['timestamp']
                            # Handle ISO format with or without Z
                            if timestamp_str.endswith('Z'):
                                timestamp_str = timestamp_str[:-1] + '+00:00'
                            captured_at = datetime.fromisoformat(timestamp_str)
                        except Exception as e:
                            log.warning(f"Failed to parse timestamp {player_data.get('timestamp')}: {e}")
                    
                    # Create new raw player
                    RawPlayerRepository.create(
                        db=session,
                        username=username,
                        source_site=platform,
                        captured_at=captured_at
                    )
                    inserted += 1
                    
                except IntegrityError as e:
                    # Handle unique constraint violation (race condition or constraint exists)
                    if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                        skipped += 1
                    else:
                        log.error(f"Integrity error processing player {player_data}: {e}")
                        errors += 1
                        session.rollback()
                except Exception as e:
                    log.error(f"Error processing player {player_data}: {e}")
                    errors += 1
                    session.rollback()
                    continue
            
            # Commit all inserts
            try:
                session.commit()
            except Exception as e:
                log.error(f"Error committing transaction: {e}")
                session.rollback()
                # Count remaining as errors
                remaining = len(players) - inserted - skipped
                errors += remaining
        
        log.info(f"Received {len(players)} players: {inserted} inserted, {skipped} skipped, {errors} errors")
        
        # Emit WebSocket event for new raw players
        if inserted > 0:
            # Fetch the newly inserted players to send via WebSocket
            with db_session() as session:
                new_players = session.query(RawPlayer).order_by(
                    RawPlayer.created_at.desc()
                ).limit(inserted).all()
                
                for player in new_players:
                    socketio.emit('raw_player_added', {
                        'id': player.id,
                        'username': player.username,
                        'source_site': player.source_site,
                        'captured_at': player.captured_at.isoformat() if player.captured_at else None,
                        'created_at': player.created_at.isoformat() if player.created_at else None,
                    })
            
            # Emit stats update
            _emit_stats_update()
        
        return jsonify({
            'success': True,
            'inserted': inserted,
            'skipped': skipped,
            'errors': errors,
            'total': len(players)
        })
        
    except Exception as e:
        log.error(f"Error in /api/raw-players endpoint: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _emit_stats_update():
    """Emit updated statistics via WebSocket."""
    try:
        with db_session() as session:
            total_raw_players = session.query(RawPlayer).count()
            total_qualified_leads = session.query(QualifiedLead).count()
            total_identity_matches = session.query(IdentityMatch).count()
            
            # Count by platform
            from sqlalchemy import func
            platform_counts = session.query(
                RawPlayer.source_site,
                func.count(RawPlayer.id).label('count')
            ).group_by(RawPlayer.source_site).all()
            
            stats = {
                'total_raw_players': total_raw_players,
                'total_qualified_leads': total_qualified_leads,
                'total_identity_matches': total_identity_matches,
                'by_platform': {platform: count for platform, count in platform_counts if platform}
            }
            
            socketio.emit('stats_updated', stats)
    except Exception as e:
        log.error(f"Error emitting stats update: {e}")


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    log.info('WebSocket client connected')
    emit('connected', {'status': 'connected'})
    _emit_stats_update()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    log.info('WebSocket client disconnected')


# API endpoints for fetching data
@app.route('/api/raw-players', methods=['GET'])
def get_raw_players():
    """Get raw players with pagination."""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        platform = request.args.get('platform')
        
        with db_session() as session:
            query = session.query(RawPlayer)
            
            if platform:
                query = query.filter(RawPlayer.source_site == platform)
            
            total = query.count()
            players = query.order_by(
                RawPlayer.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return jsonify({
                'success': True,
                'data': [{
                    'id': p.id,
                    'username': p.username,
                    'source_site': p.source_site,
                    'captured_at': p.captured_at.isoformat() if p.captured_at else None,
                    'created_at': p.created_at.isoformat() if p.created_at else None,
                } for p in players],
                'total': total,
                'limit': limit,
                'offset': offset
            })
    except Exception as e:
        log.error(f"Error fetching raw players: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qualified-leads', methods=['GET'])
def get_qualified_leads():
    """Get qualified leads with pagination."""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        confidence_label = request.args.get('confidence_label')
        
        with db_session() as session:
            query = session.query(QualifiedLead).join(RawPlayer)
            
            if confidence_label:
                query = query.filter(QualifiedLead.confidence_label == confidence_label)
            
            total = query.count()
            leads = query.order_by(
                QualifiedLead.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return jsonify({
                'success': True,
                'data': [{
                    'id': l.id,
                    'raw_player_id': l.raw_player_id,
                    'username': l.raw_player.username,
                    'source_site': l.raw_player.source_site,
                    'best_contact_type': l.best_contact_type,
                    'best_contact_value': l.best_contact_value,
                    'confidence': l.confidence,
                    'confidence_label': l.confidence_label,
                    'notes': l.notes,
                    'created_at': l.created_at.isoformat() if l.created_at else None,
                } for l in leads],
                'total': total,
                'limit': limit,
                'offset': offset
            })
    except Exception as e:
        log.error(f"Error fetching qualified leads: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/identity-matches', methods=['GET'])
def get_identity_matches():
    """Get identity matches with pagination."""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        raw_player_id = request.args.get('raw_player_id')
        platform = request.args.get('platform')
        
        with db_session() as session:
            query = session.query(IdentityMatch).join(RawPlayer)
            
            if raw_player_id:
                query = query.filter(IdentityMatch.raw_player_id == raw_player_id)
            if platform:
                query = query.filter(IdentityMatch.platform == platform)
            
            total = query.count()
            matches = query.order_by(
                IdentityMatch.match_score.desc(),
                IdentityMatch.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return jsonify({
                'success': True,
                'data': [{
                    'id': m.id,
                    'raw_player_id': m.raw_player_id,
                    'username': m.raw_player.username,
                    'source_site': m.raw_player.source_site,
                    'platform': m.platform,
                    'social_handle': m.social_handle,
                    'social_url': m.social_url,
                    'display_name': m.display_name,
                    'avatar_url': m.avatar_url,
                    'public_contact_type': m.public_contact_type,
                    'public_contact_value': m.public_contact_value,
                    'match_score': m.match_score,
                    'confidence_label': m.confidence_label,
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
            from sqlalchemy import func
            
            total_raw_players = session.query(RawPlayer).count()
            total_qualified_leads = session.query(QualifiedLead).count()
            total_identity_matches = session.query(IdentityMatch).count()
            
            # Count by platform
            platform_counts = session.query(
                RawPlayer.source_site,
                func.count(RawPlayer.id).label('count')
            ).group_by(RawPlayer.source_site).all()
            
            # Count by confidence label
            confidence_counts = session.query(
                QualifiedLead.confidence_label,
                func.count(QualifiedLead.id).label('count')
            ).group_by(QualifiedLead.confidence_label).all()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_raw_players': total_raw_players,
                    'total_qualified_leads': total_qualified_leads,
                    'total_identity_matches': total_identity_matches,
                    'by_platform': {platform: count for platform, count in platform_counts if platform},
                    'by_confidence': {label: count for label, count in confidence_counts}
                }
            })
    except Exception as e:
        log.error(f"Error fetching stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def create_app():
    """Create and configure Flask app."""
    return app, socketio


if __name__ == '__main__':
    # For development only
    app.run(host='0.0.0.0', port=5000, debug=True)
