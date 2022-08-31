import time
from flask import current_app as app
from flask import render_template, request, redirect, url_for, Response, abort
from .elo_utils import modified_elo
from . import databaseManager as DbManager
from . import auth


@auth.verify_password
def verify_password(username, password):
    return DbManager.verify_password(username, password)


@app.route('/')
def index():
    return render_template(
        'index.html',
        players=DbManager.players_table_data(),
        games=DbManager.games_table_data(),
    )


@app.route('/player/<player_name>')
def player(player_name):
    player = DbManager.get_player_by_name(player_name)
    if not player:
        abort(404)
    return render_template(
        'player.html',
        player=player,
        data=DbManager.get_player_stats(player),
        games=DbManager.get_games_by_player_formatted(player),
        others=DbManager.get_player_partner_enemy(player),
    )

@app.route('/admin')
@auth.login_required
def admin():
    return render_template(
        'admin.html',
        players=DbManager.get_all_players(),
        games=DbManager.games_table_data(),
    )


@app.route('/new_player', methods=['POST'])
@auth.login_required
def new_player():
    pname = request.form.get('pname')
    name_taken = DbManager.get_player_by_name(pname) is not None
    if name_taken or pname is None:
        return redirect(url_for('admin'))

    DbManager.add_player(pname)
    return redirect(url_for('index'))


@app.route('/new_game', methods=['POST'])
@auth.login_required
def new_game():
    t1p1_id = int(request.form.get('t1p1')) # Team 1, Player 1
    t1p2_id = int(request.form.get('t1p2'))
    t2p1_id = int(request.form.get('t2p1'))
    t2p2_id = int(request.form.get('t2p2'))

    t1score = request.form.get('t1score')
    t2score = request.form.get('t2score')

    all_player_ids = [t1p1_id, t1p2_id, t2p1_id, t2p2_id]
    has_duplicates = len(set(all_player_ids)) != len(all_player_ids)

    if has_duplicates or None in [t1score, t2score]:
        return redirect(url_for('admin'))

    DbManager.add_game(
        team1_ids=[t1p1_id, t1p2_id],
        team2_ids=[t2p1_id, t2p2_id],
        scores=[t1score, t2score]
    )
    return redirect(url_for('index'))


@app.route('/delete_game', methods=['POST'])
@auth.login_required
def delete_game():
    game_id = int(request.form.get('game_id'))
    if game_id is not None:
        DbManager.remove_game(game_id)
    return redirect(url_for('index'))


@app.route('/download_games', methods=['GET'])
@auth.login_required
def download_games():
    time_now = int(time.time())
    return Response(
        DbManager.create_backup(),
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment;filename=games_backup_{time_now}.txt'
        }
    )

@app.route('/load_from_backup', methods=['POST'])
@auth.login_required
def load_from_backup():
    backup_file = request.files['backup_file']
    DbManager.load_from_backup(backup_file)
    return redirect(url_for('index'))


@app.route('/clear_database')
@auth.login_required
def clear_database():
    DbManager.clear_database()
    return redirect(url_for('index'))
