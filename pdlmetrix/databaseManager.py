import time
import hashlib
from typing import List, Union
from . import db
from .models import Player, Game, RatingHistory, User
from .elo_utils import modified_elo


def verify_password(username, password: str) -> bool:
    user = User.query.filter(User.username == username).first()
    if user is None:
        return False
    given_hash = hashlib.md5(password.encode()).hexdigest()
    return user.password == given_hash

def add_player(player_name: str) -> None:
    new_player = Player(
        name=player_name,
        rating=1000,
        rating_by_rounds=1000,
    )
    db.session.add(new_player)
    db.session.commit()


def add_game(
    team1_ids: List[int],
    team2_ids: List[int],
    scores: List[int],
    datetime: str = None
) -> None:
    new_game = Game(
        team1=','.join([str(i) for i in team1_ids]),
        team2=','.join([str(i) for i in team2_ids]),
        score=','.join([str(s) for s in scores]),
        datetime=str(int(time.time())) if datetime is None else datetime
    )
    db.session.add(new_game)
    db.session.commit()
    update_player_ratings(new_game)


def update_player_ratings(game: Game) -> None:
    team1_ids = [int(p_id) for p_id in game.team1.split(',')]
    team2_ids = [int(p_id) for p_id in game.team2.split(',')]
    team1_players = [get_player_by_id(p_id) for p_id in team1_ids]
    team2_players = [get_player_by_id(p_id) for p_id in team2_ids]

    team1_rating = sum([p.rating for p in team1_players]) / 2
    team2_rating = sum([p.rating for p in team2_players]) / 2

    team1_round_rating = sum([p.rating_by_rounds for p in team1_players]) / 2
    team2_round_rating = sum([p.rating_by_rounds for p in team2_players]) / 2

    team1_score, team2_score = [int(s) for s in game.score.split(',')]

    for player in team1_players + team2_players:
        player_in_team1 = player in team1_players
        opponent_rating = team2_rating if player_in_team1 else team1_rating
        opponent_round_rating = team2_round_rating if player_in_team1 else team1_round_rating
        opponent_score = team2_score if player_in_team1 else team1_score
        own_score = team1_score if player_in_team1 else team2_score

        new_rating = modified_elo(
            player.rating,
            opponent_rating,
            own_score,
            opponent_score,
            raw_result=True
        )

        new_rating_by_rounds = modified_elo(
            player.rating_by_rounds,
            opponent_round_rating,
            own_score,
            opponent_score,
            raw_result=False
        )
        rating_diff = new_rating - player.rating
        rounds_rating_diff = new_rating_by_rounds - player.rating_by_rounds
        player.rating = new_rating
        player.rating_by_rounds = new_rating_by_rounds

        set_rating_checkpoint(player, game, rating_diff, rounds_rating_diff)
        db.session.commit()


def set_rating_checkpoint(
    player: Player,
    game: Game,
    rating_diff: int,
    rounds_rating_diff: int
) -> None:
    existing_checkpoint = get_history_entry_by_player_and_game(
        player.id,
        game.id
    )
    if existing_checkpoint is None:
        new_history = RatingHistory(
            player_id=player.id,
            game_id=game.id,
            rating=player.rating,
            rating_by_rounds=player.rating_by_rounds,
            rating_diff=rating_diff,
            rounds_rating_diff=rounds_rating_diff,
            datetime=game.datetime
        )
        db.session.add(new_history)
        db.session.commit()
    else:
        existing_checkpoint.rating = player.rating
        existing_checkpoint.rating_by_rounds = player.rating_by_rounds
        existing_checkpoint.rating_diff = rating_diff
        existing_checkpoint.rounds_rating_diff = rating_diff
        db.session.commit()


def remove_game(game_id: int) -> None:
    game_to_remove = get_game_by_id(game_id)
    assert game_to_remove is not None, f'Game to remove id no match found {game_id}'
    removed_game_datetime = int(game_to_remove.datetime)

    for entry in get_history_entries_by_game_id(game_id):
        db.session.delete(entry)
    db.session.delete(game_to_remove)
    db.session.commit()
    reset_all_player_ratings()

    games = sorted(get_all_games(), key=lambda h: h.datetime)
    for game in games:
        if int(game.datetime) < removed_game_datetime:
            game_history_entries = get_history_entries_by_game_id(game.id)
            for entry in game_history_entries:
                set_rating_from_checkpoint(entry)
            continue
        update_player_ratings(game)


def reset_all_player_ratings() -> None:
    players = get_all_players()
    for player in players:
        player.rating = 1000
        player.rating_by_rounds = 1000
    db.session.commit()


def set_rating_from_checkpoint(checkpoint: RatingHistory):
    player = get_player_by_id(checkpoint.player_id)
    assert player is not None, f'No player found for history, id: {checkpoint.id}'
    player.rating = checkpoint.rating
    player.rating_by_rounds = checkpoint.rating_by_rounds
    db.session.commit()


def get_game_by_id(game_id: int) -> Union[Game, None]:
    return Game.query.filter(Game.id == game_id).first()


def get_player_by_id(player_id: int) -> Union[Player, None]:
    return Player.query.filter(Player.id == player_id).first()


def get_player_by_name(player_name: str) -> Union[Player, None]:
    return Player.query.filter(Player.name == player_name).first()


def get_history_entries_by_game_id(game_id: int) -> Union[Game, None]:
    return RatingHistory.query.filter(RatingHistory.game_id == game_id)


def get_history_entry_by_player_and_game(
    player_id: int,
    game_id: int
) -> Union[RatingHistory, None]:
    player_history_entries = RatingHistory.query.filter(RatingHistory.player_id == player_id)
    return player_history_entries.filter(RatingHistory.game_id == game_id).first()


def get_all_players() -> List[Player]:
    return Player.query.all()


def get_all_games() -> List[Game]:
    return Game.query.all()


def get_all_rating_history() -> List[RatingHistory]:
    return RatingHistory.query.all()


def get_games_by_player(player: Player) -> List[Game]:
    return Game.query.filter((Game.team1 + Game.team2).contains(str(player.id)))

def get_player_stats(player: Player) -> dict:
    stats = {
        'won_games': 0,
        'lost_games': 0,
        'total_games': 0,
        'won_rounds': 0,
        'lost_rounds': 0,
        'total_rounds': 0,
        'win_perc': 0,
        'round_win_perc': 0,
    }

    player_games = get_games_by_player(player)

    for game in player_games:
        player_in_team1 = str(player.id) in game.team1
        team1_score, team2_score = [int(s) for s in game.score.split(',')]
        team1_won = team1_score > team2_score

        stats['won_rounds'] += team1_score if player_in_team1 else team2_score
        stats['lost_rounds'] += team2_score if player_in_team1 else team1_score
        stats['total_games'] += 1
        stats['total_rounds'] += team1_score + team2_score

        if team1_won:
            stats['won_games'] += int(player_in_team1)
            stats['lost_games'] += int(not player_in_team1)
        else:
            stats['won_games'] += int(not player_in_team1)
            stats['lost_games'] += int(player_in_team1)

    try:
        stats['win_perc'] = stats['won_games'] / stats['total_games'] * 100
        stats['round_win_perc'] = stats['won_rounds'] / stats['total_rounds'] * 100
    except ZeroDivisionError:
        stats['win_perc'] = 0
        stats['round_win_perc'] = 0

    return stats


def games_table_data() -> dict:
    table_data = []
    games = sorted(get_all_games(), key=lambda g: int(g.datetime), reverse=True)

    for game in games:
        readable_datetime = time.strftime('%d.%m.%Y', time.localtime(int(game.datetime)))
        t1score, t2score = game.score.split(',')

        game_data = {
            'datetime': readable_datetime,
            'team1score': t1score,
            'team2score': t2score,
            'id': game.id,
            'players': [],
        }

        player_ids_str = game.team1.split(',') + game.team2.split(',')
        player_ids = [int(p_id) for p_id in player_ids_str]
        players = [get_player_by_id(p_id) for p_id in player_ids]

        for player in players:
            player_history_entry = get_history_entry_by_player_and_game(
                player.id,
                game.id
            )
            game_data['players'].append({
                'name': player.name,
                'rating_diff': f'{player_history_entry.rating_diff:+g}',
                'rounds_rating_diff': f'{player_history_entry.rounds_rating_diff:+g}'
            })

        table_data.append(game_data)

    return table_data


def players_table_data() -> dict:
    table_data = []
    players = sorted(get_all_players(), key=lambda p: p.rating, reverse=True)

    for player in players:
        player_stats = get_player_stats(player)
        table_data.append({
            'name': player.name,
            'rating': player.rating,
            'rounds_rating': player.rating_by_rounds,
            'win_perc': int(player_stats['win_perc']),
            'round_win_perc': int(player_stats['round_win_perc'])
        })

    return table_data


def create_backup() -> str:
    games_text = ''
    games = get_all_games()
    for game in games:
        p1, p2 = [get_player_by_id(int(p)).name for p in game.team1.split(',')]
        p3, p4 = [get_player_by_id(int(p)).name for p in game.team2.split(',')]
        t1score, t2score = game.score.split(',')
        games_text += f'{p1},{p2},{p3},{p4},{t1score},{t2score},{game.datetime}\n'
    return games_text


def load_from_backup(backup_data) -> None:
    game_strings = backup_data.read().decode('UTF-8').split('\n')
    games = [game.split(',') for game in game_strings if game != '']
    for game_data in games:
        # format: ['Aleksi', 'Aki', 'Saku', 'Repa', '5', '6', '1643569200']
        assert len(game_data) == 7, 'Bad game data'
        team1 = game_data[0:2]
        team2 = game_data[2:4]
        for player_name in team1 + team2:
            if get_player_by_name(player_name) is not None:
                continue
            add_player(player_name)

        score = [int(game_data[4]), int(game_data[5])]
        team1_ids = [get_player_by_name(p).id for p in team1]
        team2_ids = [get_player_by_name(p).id for p in team2]
        add_game(team1_ids, team2_ids, score, datetime=game_data[6])


def clear_database() -> None:
    Game.query.delete()
    Player.query.delete()
    RatingHistory.query.delete()
    db.session.commit()
