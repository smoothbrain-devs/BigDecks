"""Tournament organization functionality

This module contains the routes and logic for tournament organization.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from bigdecks.auth import login_required
from bigdecks.database import get_db_connection

bp = Blueprint('tournament', __name__, url_prefix='/tournament')

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
    
    return render_template('tournament/details.html', tournament=tournament, participants=participants)

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
    """Generate pairings for the next round."""
    tournament = get_tournament(id, check_organizer=True)
    
    db = get_db_connection('users')
    # TODO: Implement proper Swiss pairing algorithm
    # For now, just pair players randomly for the first round
    
    # Check if pairings already exist
    current_round = db.execute(
        'SELECT MAX(round) as max_round FROM match WHERE tournament_id = ?',
        (id,)
    ).fetchone()['max_round']
    
    if current_round is None:
        current_round = 0
    
    # Check if all matches in current round are completed
    if current_round > 0:
        incomplete_matches = db.execute(
            'SELECT COUNT(*) as count FROM match '
            'WHERE tournament_id = ? AND round = ? AND status != "completed"',
            (id, current_round)
        ).fetchone()['count']
        
        if incomplete_matches > 0:
            flash('Cannot generate pairings until all matches in the current round are completed.')
            return redirect(url_for('tournament.pairings', id=id))
    
    # Get all participants
    participants = db.execute(
        'SELECT p.id FROM participant p '
        'WHERE p.tournament_id = ? AND p.status = "registered"',
        (id,)
    ).fetchall()
    
    participant_ids = [p['id'] for p in participants]
    
    # Need an even number of players
    if len(participant_ids) % 2 != 0:
        flash('Cannot generate pairings with an odd number of players. Consider adding a bye.')
        return redirect(url_for('tournament.pairings', id=id))
    
    # Simple pairing: just match players sequentially for now
    next_round = current_round + 1
    
    for i in range(0, len(participant_ids), 2):
        player1_id = participant_ids[i]
        player2_id = participant_ids[i+1]
        
        db.execute(
            'INSERT INTO match (tournament_id, round, player1_id, player2_id, status) '
            'VALUES (?, ?, ?, ?, ?)',
            (id, next_round, player1_id, player2_id, 'in_progress')
        )
    
    db.commit()
    flash(f'Pairings for round {next_round} generated successfully.')
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

def get_tournament(id, check_organizer=False):
    """Get a tournament by ID.
    
    Parameters
    ----------
    id : int
        The tournament ID
    check_organizer : bool
        If True, verify that the current user is the tournament organizer
        
    Returns
    -------
    dict
        The tournament data
        
    Raises
    ------
    404
        If the tournament doesn't exist
    403
        If check_organizer is True and the current user is not the organizer
    """
    tournament = get_db_connection('users').execute(
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
        
    return tournament