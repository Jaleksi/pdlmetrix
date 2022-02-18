def expected_result(p1, p2):
    return 1 / (1 + 10 ** ((p2 - p1) / 400))

def result(p1, p2, raw_result=True):
    if p1 == p2:
        return 0.5
    if raw_result:
        return int(p1 > p2)
    return 1 / (p1 + p2) * p1

def modified_elo(player_elo, opponent_elo, p_points, o_points, raw_result=True):
    K = 32
    exp_res = expected_result(player_elo, opponent_elo)
    res = result(p_points, o_points, raw_result=raw_result)
    return int(player_elo + K * (res - exp_res))
