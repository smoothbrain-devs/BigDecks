"""Tournament organization functionality

This module contains the routes and logic for tournament organization.
Includes enhancements for round limits and player records.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import math

from bigdecks.auth import login_required
from bigdecks.database import get_db_connection

# Define the Blueprint first - this was missing in the previous code
bp = Blueprint('tournament', __name__, url_prefix='/tournament')

def get_tournament(id, check_organizer=False):
    """Get a tournament by ID with additional data.
    
    Parameters
    ----------
    id : int
        The tournament ID
    check_organizer : bool
        If True, verify that the current user is the tournament organizer
        
    Returns
    -------
    dict
        The tournament data with added fields:
        - participants_count: Number of participants
        - max_rounds: Maximum number of rounds based on participants
        
    Raises
    ------
    404
        If the tournament doesn't exist
    403
        If check_organizer is True and the current user is not the organizer
    """
    db = get_db_connection('users')
    
    # Get basic tournament info
    tournament = db.execute(
        'SELECT t.id, t.name, t.description, t.format, t.date, '
        't.max_players, t.status, t.organizer_id, u.username as organizer_name '
        'FROM tournament t JOIN user u ON t.organizer_id = u.id '
        'WHERE t.id = ?',
        (id,)
    ).fetchone()
    
    if tournament is None:
        abort(404, f"Tournament id {id} doesn't exist.")
        
    if check_organizer and (g.user is None or g.user['id'] != tournament['organizer_id']):
        abort(403)
    
    # Convert to dictionary so we can add more fields
    tournament = dict(tournament)
    
    # Count participants
    participants_count = db.execute(
        'SELECT COUNT(*) as count FROM participant WHERE tournament_id = ?',
        (id,)
    ).fetchone()['count']
    
    tournament['participants_count'] = participants_count
    
    # Calculate maximum rounds based on Swiss tournament formula
    # Formula: log2(number of players) rounded up
    # For 8 players: 3 rounds, 16 players: 4 rounds, etc.
    if participants_count > 1:
        max_rounds = math.ceil(math.log2(participants_count))
    else:
        max_rounds = 0
        
    tournament['max_rounds'] = max_rounds
    
    # Get current round
    current_round = db.execute(
        'SELECT MAX(round) as max_round FROM match WHERE tournament_id = ?',
        (id,)
    ).fetchone()['max_round']
    
    tournament['current_round'] = current_round if current_round is not None else 0
        
    return tournament

# Function to get player records
def get_player_records(tournament_id):
    """Get win-loss-draw records for all players in a tournament.
    
    Parameters
    ----------
    tournament_id : int
        The tournament ID
        
    Returns
    -------
    dict
        Dictionary mapping participant_id to {wins, losses, draws}
    """
    db = get_db_connection('users')
    records = {}
    
    # Get all participants in this tournament
    participants = db.execute(
        'SELECT id, user_id FROM participant WHERE tournament_id = ?',
        (tournament_id,)
    ).fetchall()
    
    for participant in participants:
        participant_id = participant['id']
        
        # Initialize record
        records[participant_id] = {
            'user_id': participant['user_id'],
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'points': 0  # 3 points for win, 1 for draw
        }
        
        # Get matches where this participant was player 1
        player1_matches = db.execute(
            'SELECT player1_wins, player2_wins, draws, status '
            'FROM match '
            'WHERE tournament_id = ? AND player1_id = ? AND status = "completed"',
            (tournament_id, participant_id)
        ).fetchall()
        
        for match in player1_matches:
            if match['player1_wins'] > match['player2_wins']:
                records[participant_id]['wins'] += 1
                records[participant_id]['points'] += 3
            elif match['player1_wins'] < match['player2_wins']:
                records[participant_id]['losses'] += 1
            else:
                records[participant_id]['draws'] += 1
                records[participant_id]['points'] += 1
                
        # Get matches where this participant was player 2
        player2_matches = db.execute(
            'SELECT player1_wins, player2_wins, draws, status '
            'FROM match '
            'WHERE tournament_id = ? AND player2_id = ? AND status = "completed"',
            (tournament_id, participant_id)
        ).fetchall()
        
        for match in player2_matches:
            if match['player2_wins'] > match['player1_wins']:
                records[participant_id]['wins'] += 1
                records[participant_id]['points'] += 3
            elif match['player2_wins'] < match['player1_wins']:
                records[participant_id]['losses'] += 1
            else:
                records[participant_id]['draws'] += 1
                records[participant_id]['points'] += 1
                
    return records

@bp.route('/')
def index():
    """Display the list of upcoming and past tournaments."""
    db = get_db_connection('users')
    tournaments = db.execute(
        'SELECT t.id, t.name, t.description, t.format, t.date, t.max_players, '
        't.status, t.organizer_id, u.username as organizer_name '
        'FROM tournament t JOIN user u ON t.organizer_id = u.id '
        'ORDER BY t.date DESC'
    ).fetchall()
    return render_template('tournament/index.html', tournaments=tournaments)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new tournament."""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        format = request.form['format']
        date = request.form['date']
        max_players = request.form['max_players']
        error = None

        if not name:
            error = 'Name is required.'
        elif not format:
            error = 'Format is required.'
        elif not date:
            error = 'Date is required.'
        
        try:
            max_players = int(max_players)
            if max_players < 2:
                error = 'Tournament must allow at least 2 players.'
        except ValueError:
            error = 'Maximum players must be a number.'

        if error is not None:
            flash(error)
        else:
            db = get_db_connection('users')
            db.execute(
                'INSERT INTO tournament (name, description, format, date, max_players, status, organizer_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (name, description, format, date, max_players, 'registration', g.user['id'])
            )
            db.commit()
            return redirect(url_for('tournament.index'))

    return render_template('tournament/create.html')

@bp.route('/<int:id>/details')
def details(id):
    """Show tournament details and participants."""
    tournament = get_tournament(id)
    
    db = get_db_connection('users')
    participants = db.execute(
        'SELECT p.id, p.user_id, p.tournament_id, p.registration_date, p.status, u.username '
        'FROM participant p JOIN user u ON p.user_id = u.id '
        'WHERE p.tournament_id = ? '
        'ORDER BY p.registration_date ASC',
        (id,)
    ).fetchall()
    
    # Get player records if tournament is in progress or completed
    records = {}
    if tournament['status'] in ['in_progress', 'completed']:
        records = get_player_records(id)
        
    return render_template('tournament/details.html', 
                          tournament=tournament, 
                          participants=participants,
                          records=records)

@bp.route('/<int:id>/register', methods=('POST',))
@login_required
def register(id):
    """Register current user for a tournament."""
    tournament = get_tournament(id)
    
    db = get_db_connection('users')
    # Check if user is already registered
    already_registered = db.execute(
        'SELECT * FROM participant WHERE tournament_id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()
    
    if already_registered:
        flash('You are already registered for this tournament.')
        return redirect(url_for('tournament.details', id=id))
    
    # Check if tournament is full
    participant_count = db.execute(
        'SELECT COUNT(*) as count FROM participant WHERE tournament_id = ?',
        (id,)
    ).fetchone()['count']
    
    if participant_count >= tournament['max_players']:
        flash('This tournament is already full.')
        return redirect(url_for('tournament.details', id=id))
    
    # Register the user
    db.execute(
        'INSERT INTO participant (tournament_id, user_id, status) '
        'VALUES (?, ?, ?)',
        (id, g.user['id'], 'registered')
    )
    db.commit()
    
    flash('You have successfully registered for the tournament.')
    return redirect(url_for('tournament.details', id=id))

@bp.route('/<int:id>/withdraw', methods=('POST',))
@login_required
def withdraw(id):
    """Withdraw current user from a tournament."""
    tournament = get_tournament(id)
    
    db = get_db_connection('users')
    # Check if user is registered
    participant = db.execute(
        'SELECT * FROM participant WHERE tournament_id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()
    
    if not participant:
        flash('You are not registered for this tournament.')
        return redirect(url_for('tournament.details', id=id))
    
    # Remove the participant
    db.execute(
        'DELETE FROM participant WHERE tournament_id = ? AND user_id = ?',
        (id, g.user['id'])
    )
    db.commit()
    
    flash('You have withdrawn from the tournament.')
    return redirect(url_for('tournament.details', id=id))

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """Update tournament details."""
    tournament = get_tournament(id, check_organizer=True)
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        format = request.form['format']
        date = request.form['date']
        max_players = request.form['max_players']
        status = request.form['status']
        error = None

        if not name:
            error = 'Name is required.'
        elif not format:
            error = 'Format is required.'
        elif not date:
            error = 'Date is required.'
        
        try:
            max_players = int(max_players)
            if max_players < 2:
                error = 'Tournament must allow at least 2 players.'
        except ValueError:
            error = 'Maximum players must be a number.'

        if error is not None:
            flash(error)
        else:
            db = get_db_connection('users')
            db.execute(
                'UPDATE tournament SET name = ?, description = ?, format = ?, '
                'date = ?, max_players = ?, status = ? '
                'WHERE id = ?',
                (name, description, format, date, max_players, status, id)
            )
            db.commit()
            return redirect(url_for('tournament.details', id=id))

    return render_template('tournament/update.html', tournament=tournament)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a tournament."""
    get_tournament(id, check_organizer=True)
    db = get_db_connection('users')
    
    # First delete all participants
    db.execute('DELETE FROM participant WHERE tournament_id = ?', (id,))
    
    # Then delete the tournament
    db.execute('DELETE FROM tournament WHERE id = ?', (id,))
    db.commit()
    
    flash('Tournament deleted successfully.')
    return redirect(url_for('tournament.index'))

@bp.route('/<int:id>/pairings')
@login_required
def pairings(id):
    """Show or generate tournament pairings."""
    tournament = get_tournament(id)
    
    # Check if user is organizer
    is_organizer = g.user and tournament['organizer_id'] == g.user['id']
    
    db = get_db_connection('users')
    
    # Get all matches for this tournament
    matches = db.execute(
        'SELECT m.id, m.round, m.player1_id, m.player2_id, '
        'm.player1_wins, m.player2_wins, m.draws, m.status, '
        'u1.username as player1_name, u2.username as player2_name '
        'FROM match m '
        'JOIN participant p1 ON m.player1_id = p1.id '
        'JOIN participant p2 ON m.player2_id = p2.id '
        'JOIN user u1 ON p1.user_id = u1.id '
        'JOIN user u2 ON p2.user_id = u2.id '
        'WHERE m.tournament_id = ? '
        'ORDER BY m.round ASC, m.id ASC',
        (id,)
    ).fetchall()
    
    return render_template('tournament/pairings.html', 
                          tournament=tournament, 
                          matches=matches,
                          is_organizer=is_organizer)

@bp.route('/<int:id>/generate_pairings', methods=('POST',))
@login_required
def generate_pairings(id):
    """Generate pairings for the next round using Swiss pairing system."""
    tournament = get_tournament(id, check_organizer=True)
    
    db = get_db_connection('users')
    
    # Check if we've reached the maximum number of rounds
    if tournament['current_round'] >= tournament['max_rounds']:
        flash(f'Maximum number of rounds ({tournament["max_rounds"]}) has been reached for this tournament.')
        return redirect(url_for('tournament.pairings', id=id))
    
    # Check if all matches in current round are completed
    if tournament['current_round'] > 0:
        incomplete_matches = db.execute(
            'SELECT COUNT(*) as count FROM match '
            'WHERE tournament_id = ? AND round = ? AND status != "completed"',
            (id, tournament['current_round'])
        ).fetchone()['count']
        
        if incomplete_matches > 0:
            flash('Cannot generate pairings until all matches in the current round are completed.')
            return redirect(url_for('tournament.pairings', id=id))
    
    # Get all active participants
    participants = db.execute(
        'SELECT p.id, p.user_id, u.username '
        'FROM participant p JOIN user u ON p.user_id = u.id '
        'WHERE p.tournament_id = ? AND p.status = "registered"',
        (id,)
    ).fetchall()
    
    # Need an even number of players
    if len(participants) % 2 != 0:
        flash('Cannot generate pairings with an odd number of players. Consider adding a bye.')
        return redirect(url_for('tournament.pairings', id=id))
    
    next_round = tournament['current_round'] + 1
    
    # First round: pair randomly or by registration order
    if next_round == 1:
        # Simple pairing for first round (could be randomized for true Swiss)
        participant_ids = [p['id'] for p in participants]
        
        for i in range(0, len(participant_ids), 2):
            player1_id = participant_ids[i]
            player2_id = participant_ids[i+1]
            
            db.execute(
                'INSERT INTO match (tournament_id, round, player1_id, player2_id, status) '
                'VALUES (?, ?, ?, ?, ?)',
                (id, next_round, player1_id, player2_id, 'in_progress')
            )
    else:
        # Swiss pairing for subsequent rounds
        # Calculate standings based on completed matches
        standings = []
        
        for p in participants:
            # Initialize player record
            points = 0
            wins = 0
            losses = 0
            draws = 0
            opponents = []  # List of opponents this player has faced
            
            # Get matches as player 1
            p1_matches = db.execute(
                'SELECT m.player2_id, m.player1_wins, m.player2_wins, m.draws, m.status '
                'FROM match m '
                'WHERE m.tournament_id = ? AND m.player1_id = ? AND m.status = "completed"',
                (id, p['id'])
            ).fetchall()
            
            for match in p1_matches:
                opponents.append(match['player2_id'])
                if match['player1_wins'] > match['player2_wins']:
                    points += 3
                    wins += 1
                elif match['player1_wins'] < match['player2_wins']:
                    losses += 1
                else:
                    points += 1
                    draws += 1
            
            # Get matches as player 2
            p2_matches = db.execute(
                'SELECT m.player1_id, m.player1_wins, m.player2_wins, m.draws, m.status '
                'FROM match m '
                'WHERE m.tournament_id = ? AND m.player2_id = ? AND m.status = "completed"',
                (id, p['id'])
            ).fetchall()
            
            for match in p2_matches:
                opponents.append(match['player1_id'])
                if match['player2_wins'] > match['player1_wins']:
                    points += 3
                    wins += 1
                elif match['player2_wins'] < match['player1_wins']:
                    losses += 1
                else:
                    points += 1
                    draws += 1
            
            # Add player to standings
            standings.append({
                'id': p['id'],
                'user_id': p['user_id'],
                'username': p['username'],
                'points': points,
                'wins': wins,
                'losses': losses, 
                'draws': draws,
                'opponents': opponents
            })
        
        # Sort standings by points (descending)
        standings.sort(key=lambda x: x['points'], reverse=True)
        
        # Create pairings based on standings
        # Players with similar records play each other
        paired_players = set()
        
        # Try to pair players with similar points who haven't played each other
        for i in range(len(standings)):
            if standings[i]['id'] in paired_players:
                continue
                
            player1_id = standings[i]['id']
            paired_players.add(player1_id)
            
            # Find the highest-ranked player who hasn't played this player
            player2_id = None
            for j in range(i + 1, len(standings)):
                candidate_id = standings[j]['id']
                if candidate_id not in paired_players and candidate_id not in standings[i]['opponents']:
                    player2_id = candidate_id
                    paired_players.add(player2_id)
                    break
            
            # If no eligible opponent found, pair with next available player
            if player2_id is None:
                for j in range(i + 1, len(standings)):
                    candidate_id = standings[j]['id']
                    if candidate_id not in paired_players:
                        player2_id = candidate_id
                        paired_players.add(player2_id)
                        break
            
            # Insert the match if we found a pairing
            if player2_id is not None:
                db.execute(
                    'INSERT INTO match (tournament_id, round, player1_id, player2_id, status) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (id, next_round, player1_id, player2_id, 'in_progress')
                )
            else:
                # This should not happen with even number of players
                flash(f'Warning: Could not find an opponent for player {standings[i]["username"]}')
    
    db.commit()
    flash(f'Pairings for round {next_round} generated successfully using Swiss pairing system.')
    return redirect(url_for('tournament.pairings', id=id))

@bp.route('/match/<int:match_id>/report', methods=('GET', 'POST'))
@login_required
def report_result(match_id):
    """Report match results."""
    db = get_db_connection('users')
    match = db.execute(
        'SELECT m.*, t.organizer_id, '
        'p1.user_id as player1_user_id, p2.user_id as player2_user_id '
        'FROM match m '
        'JOIN tournament t ON m.tournament_id = t.id '
        'JOIN participant p1 ON m.player1_id = p1.id '
        'JOIN participant p2 ON m.player2_id = p2.id '
        'WHERE m.id = ?',
        (match_id,)
    ).fetchone()
    
    if match is None:
        abort(404, f"Match id {match_id} doesn't exist.")
    
    # Check if user is authorized to report
    is_player = (g.user['id'] == match['player1_user_id'] or 
                g.user['id'] == match['player2_user_id'])
    is_organizer = g.user['id'] == match['organizer_id']
    
    if not (is_player or is_organizer):
        abort(403)
    
    if request.method == 'POST':
        player1_wins = int(request.form['player1_wins'])
        player2_wins = int(request.form['player2_wins'])
        draws = int(request.form['draws'])
        
        db.execute(
            'UPDATE match SET player1_wins = ?, player2_wins = ?, draws = ?, status = "completed" '
            'WHERE id = ?',
            (player1_wins, player2_wins, draws, match_id)
        )
        db.commit()
        
        flash('Match result reported successfully.')
        return redirect(url_for('tournament.pairings', id=match['tournament_id']))
    
    # Get player names
    player1 = db.execute(
        'SELECT p.id, u.username '
        'FROM participant p JOIN user u ON p.user_id = u.id '
        'WHERE p.id = ?',
        (match['player1_id'],)
    ).fetchone()
    
    player2 = db.execute(
        'SELECT p.id, u.username '
        'FROM participant p JOIN user u ON p.user_id = u.id '
        'WHERE p.id = ?',
        (match['player2_id'],)
    ).fetchone()
    
    return render_template('tournament/report_result.html', 
                          match=match,
                          player1=player1,
                          player2=player2)

