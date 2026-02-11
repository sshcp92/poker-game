import streamlit as st
import random
import time

# ==========================================
# 1. 설정 및 초기화
# ==========================================
st.set_page_config(layout="wide", page_title="AI 몬스터 토너먼트", page_icon="🦁")

# 블라인드 구조
BLIND_STRUCTURE = [
    (100, 200, 0), (200, 400, 0), (300, 600, 600), (400, 800, 800),
    (500, 1000, 1000), (1000, 2000, 2000), (2000, 4000, 4000), (5000, 10000, 10000)
]
LEVEL_DURATION = 600
RANKS = '23456789TJQKA'
SUITS = ['\u2660', '\u2665', '\u2666', '\u2663']
DISPLAY_MAP = {'T': '10', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}

if 'init_done' not in st.session_state:
    st.session_state['init_done'] = True
    st.session_state['start_time'] = time.time()
    st.session_state['hero_turn_start'] = 0
    st.session_state['game_round'] = 0
    st.session_state['message'] = ""
    st.session_state['dealer_idx'] = 8 
    st.session_state['showdown_phase'] = False
    st.session_state['hero_show_flags'] = [False, False]
    st.session_state['show_bb'] = False 
    st.session_state['wait_for_next_hand'] = False 
    
    start_stack = 60000
    st.session_state['players'] = [
        {'name': 'Bot 1', 'seat': 1, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Tight'},
        {'name': 'Bot 2', 'seat': 2, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Aggressive'},
        {'name': 'Bot 3', 'seat': 3, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Normal'},
        {'name': 'Bot 4', 'seat': 4, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Tight'},
        {'name': '👑 형님', 'seat': 5, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'hero'},
        {'name': 'Bot 5', 'seat': 6, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Normal'},
        {'name': 'Bot 6', 'seat': 7, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Aggressive'},
        {'name': 'Bot 7', 'seat': 8, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Tight'},
        {'name': 'Bot 8', 'seat': 9, 'stack': start_stack, 'hand': [], 'status': 'alive', 'bet': 0, 'total_bet_hand': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1, 'style': 'Normal'},
    ]
    st.session_state['pot'] = 0
    st.session_state['deck'] = []
    st.session_state['community'] = []
    st.session_state['phase'] = 'PREFLOP'
    st.session_state['current_bet'] = 0
    st.session_state['turn_idx'] = 0
    st.session_state['sb_amount'] = 100
    st.session_state['bb_amount'] = 200
    st.session_state['ante_amount'] = 0
    st.session_state['level'] = 1

# ==========================================
# 2. 유틸리티 함수
# ==========================================
def new_deck():
    deck = [r+s for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck

def get_current_info():
    elapsed = time.time() - st.session_state['start_time']
    lvl_idx = int(elapsed // LEVEL_DURATION)
    if lvl_idx >= len(BLIND_STRUCTURE): lvl_idx = len(BLIND_STRUCTURE) - 1
    sb, bb, ante = BLIND_STRUCTURE[lvl_idx]
    next_level_time = (lvl_idx + 1) * LEVEL_DURATION
    time_left = max(0, int(next_level_time - elapsed))
    mins, secs = divmod(time_left, 60)
    timer_str = f"{mins:02d}:{secs:02d}"
    active_players = [p for p in st.session_state['players'] if p['status'] != 'spectator']
    total_chips = sum(p['stack'] for p in st.session_state['players'])
    avg_stack = total_chips // len(active_players) if active_players else 0
    return sb, bb, ante, lvl_idx + 1, timer_str, avg_stack

def r_str(rank_idx): return DISPLAY_MAP.get(RANKS[rank_idx], RANKS[rank_idx])

def make_card(card):
    if not card: return "🂠"
    color = "red" if card[1] in ['\u2665', '\u2666'] else "black"
    return f"<span class='card-span' style='color:{color}'>{card}</span>"

def get_hand_strength(hand):
    if not hand: return (-1, [])
    ranks = sorted([RANKS.index(c[0]) for c in hand], reverse=True)
    suits = [c[1] for c in hand]
    suit_counts = {s: suits.count(s) for s in set(suits)}
    flush_suit = next((s for s, c in suit_counts.items() if c >= 5), None)
    is_flush = (flush_suit is not None)
    unique_ranks = sorted(list(set(ranks)), reverse=True)
    is_straight = False; straight_high = -1
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i] - unique_ranks[i+4] == 4:
            is_straight = True; straight_high = unique_ranks[i]; break
    if not is_straight and set([12, 3, 2, 1, 0]).issubset(set(ranks)):
        is_straight = True; straight_high = 3
    counts = {r: ranks.count(r) for r in ranks}
    sorted_groups = sorted([(c, r) for r, c in counts.items()], reverse=True)
    
    if is_flush and is_straight:
        flush_cards = sorted([RANKS.index(c[0]) for c in hand if c[1] == flush_suit], reverse=True)
        f_unique = sorted(list(set(flush_cards)), reverse=True)
        sf_high = -1; found_sf = False
        for i in range(len(f_unique) - 4):
            if f_unique[i] - f_unique[i+4] == 4:
                sf_high = f_unique[i]; found_sf = True; break
        if not found_sf and set([12, 3, 2, 1, 0]).issubset(set(f_unique)):
            sf_high = 3; found_sf = True
        if found_sf:
            if sf_high == 12: return (9, [12], "로얄 스트레이트 플러시")
            return (8, [sf_high], f"{r_str(sf_high)} 스트레이트 플러시")
    if sorted_groups[0][0] == 4:
        quad = sorted_groups[0][1]
        kicker = sorted([r for r in ranks if r != quad], reverse=True)[0]
        return (7, [quad, kicker], f"{r_str(quad)} 포카드")
    if sorted_groups[0][0] == 3 and sorted_groups[1][0] >= 2:
        trip = sorted_groups[0][1]; pair = sorted_groups[1][1]
        return (6, [trip, pair], f"{r_str(trip)} 하우스")
    if is_flush:
        flush_ranks = sorted([RANKS.index(c[0]) for c in hand if c[1] == flush_suit], reverse=True)[:5]
        return (5, flush_ranks, f"{r_str(flush_ranks[0])} 플러시")
    if is_straight: return (4, [straight_high], f"{r_str(straight_high)} 스트레이트")
    if sorted_groups[0][0] == 3:
        trip = sorted_groups[0][1]
        kickers = sorted([r for r in ranks if r != trip], reverse=True)[:2]
        return (3, [trip] + kickers, f"{r_str(trip)} 트리플")
    if sorted_groups[0][0] == 2 and sorted_groups[1][0] == 2:
        p1 = sorted_groups[0][1]; p2 = sorted_groups[1][1]
        kicker = sorted([r for r in ranks if r != p1 and r != p2], reverse=True)[0]
        return (2, [p1, p2, kicker], f"{r_str(p1)} & {r_str(p2)} 투페어")
    if sorted_groups[0][0] == 2:
        pair = sorted_groups[0][1]
        kickers = sorted([r for r in ranks if r != pair], reverse=True)[:3]
        return (1, [pair] + kickers, f"{r_str(pair)} 원페어")
    return (0, ranks[:5], f"{r_str(ranks[0])} 하이카드")

# ==========================================
# [Advanced AI Logic]
# ==========================================
def get_preflop_tier(hand):
    r1 = RANKS.index(hand[0][0])
    r2 = RANKS.index(hand[1][0])
    if r1 < r2: r1, r2 = r2, r1 # r1 >= r2
    suited = (hand[0][1] == hand[1][1])
    if r1 == r2 and r1 >= 9: return 1 # JJ+
    if r1 == 12 and r2 >= 10: return 1 # AK, AQ
    if r1 == r2 and r1 >= 6: return 2 # 88+
    if r1 >= 10 and r2 >= 9: return 2 # Broadways
    if suited and r1 == 12 and r2 >= 8: return 2 # A8s+
    if r1 == r2: return 3 # 22-77
    if suited and r1 - r2 == 1 and r1 >= 5: return 3 # 54s+
    if suited and r1 == 12: return 3 # Any Ax suited
    if r1 >= 10 and r2 >= 8: return 3 # Q9, J8 etc
    return 4

def get_bot_decision(bot, community, current_bet, pot, bb_amt, phase):
    hand = bot['hand']; stack = bot['stack']; to_call = current_bet - bot['bet']
    style = bot.get('style', 'Normal')
    
    # 1. Preflop
    if not community:
        tier = get_preflop_tier(hand)
        if tier == 4:
            if to_call == 0: return "Check", 0
            return "Fold", 0
        if tier == 1:
            if to_call == 0: return "Raise", min(stack, bb_amt * 4)
            # [수정: int() 강제 변환]
            target_raise = min(stack, int(current_bet * 3))
            if target_raise <= current_bet: return "Call", to_call
            return "Raise", target_raise
        if tier == 2:
            if current_bet > bb_amt * 10: return "Fold", 0
            if to_call > 0 and random.random() < 0.3: 
                # [수정: int() 강제 변환]
                target_raise = min(stack, int(current_bet * 2.5))
                if target_raise <= current_bet: return "Call", to_call
                return "Raise", target_raise
            return "Call", to_call
        if tier == 3:
            if to_call > bb_amt * 3: return "Fold", 0
            if to_call > 0: return "Call", to_call
            return "Check", 0
            
    # 2. Postflop
    rank_val, _, _ = get_hand_strength(hand + community)
    if rank_val == 0 and to_call > pot * 0.3:
        all_cards = hand + community
        suits = [c[1] for c in all_cards]
        ranks_list = sorted(list(set([RANKS.index(c[0]) for c in all_cards])))
        is_fd = any(count == 4 for count in {s: suits.count(s) for s in set(suits)}.values())
        is_sd = any(ranks_list[i+3] - ranks_list[i] == 3 for i in range(len(ranks_list)-3))
        if not is_fd and not is_sd: return "Fold", 0

    equity = 0.1
    if rank_val >= 2: equity = 0.9 
    elif rank_val == 1: equity = 0.6 
    elif rank_val == 0:
         all_cards = hand + community
         suits = [c[1] for c in all_cards]
         ranks_list = sorted(list(set([RANKS.index(c[0]) for c in all_cards])))
         is_fd = any(count == 4 for count in {s: suits.count(s) for s in set(suits)}.values())
         is_sd = any(ranks_list[i+3] - ranks_list[i] == 3 for i in range(len(ranks_list)-3))
         if is_fd or is_sd: equity = 0.35
    
    pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0
    if style == 'Aggressive': equity += 0.05
    if style == 'Tight': equity -= 0.05
    
    if to_call == 0:
        if equity > 0.7: return ("Raise", min(stack, int(pot * 0.6))) if random.random() > 0.3 else ("Check", 0)
        return "Check", 0
    
    if equity >= pot_odds:
        if equity > 0.85: 
            # [수정: int() 강제 변환]
            target_raise = min(stack, int(current_bet * 3))
            if target_raise <= current_bet: return "Call", to_call
            return "Raise", target_raise
        return "Call", to_call
    
    return "Fold", 0

# ==========================================
# 3. 게임 엔진
# ==========================================
def reset_bets_for_new_street():
    st.session_state['current_bet'] = 0
    for p in st.session_state['players']:
        p['bet'] = 0; p['has_acted'] = False; 
        if p['status'] == 'alive': p['action'] = '' 

def determine_winner():
    players = st.session_state['players']
    active_bets = [p['total_bet_hand'] for p in players if p['status'] != 'folded' and p['total_bet_hand'] > 0]
    
    if not active_bets: 
        st.session_state['phase'] = 'GAME_OVER'; 
        st.session_state['wait_for_next_hand'] = True; return

    unique_bets = sorted(list(set(active_bets)))
    pots = [] 
    last_bet = 0
    
    for bet_level in unique_bets:
        step_contribution = bet_level - last_bet
        current_pot = {'amount': 0, 'eligible': []}
        for p in players:
            if p['total_bet_hand'] > last_bet:
                contribution = min(p['total_bet_hand'] - last_bet, step_contribution)
                current_pot['amount'] += contribution
                if p['total_bet_hand'] >= bet_level and p['status'] != 'folded':
                    current_pot['eligible'].append(p)
        if current_pot['amount'] > 0: pots.append(current_pot)
        last_bet = bet_level

    messages = []
    for i, pot_obj in enumerate(pots):
        if pot_obj['amount'] == 0: continue
        if not pot_obj['eligible']: continue 

        best_strength = (-1, [])
        winners = []
        best_desc = ""

        for p in pot_obj['eligible']:
            strength_tuple = get_hand_strength(p['hand'] + st.session_state['community'])
            rank_score = (strength_tuple[0], strength_tuple[1])
            if rank_score > best_strength:
                best_strength = rank_score; winners = [p]; best_desc = strength_tuple[2]
            elif rank_score == best_strength:
                winners.append(p)

        win_amount = pot_obj['amount'] // len(winners)
        winner_names = []
        for w in winners:
            w['stack'] += win_amount; winner_names.append(w['name'])
        rem = pot_obj['amount'] % len(winners)
        if rem > 0: winners[0]['stack'] += rem

        pot_name = "Main Pot" if i == 0 else f"Side Pot {i}"
        messages.append(f"{pot_name} ({pot_obj['amount']:,}): {', '.join(winner_names)} ({best_desc})")

    st.session_state['message'] = " / ".join(messages)
    st.session_state['phase'] = 'GAME_OVER'
    st.session_state['wait_for_next_hand'] = True 
    
    hero = players[4]
    if hero['status'] == 'alive':
        st.session_state['showdown_phase'] = True
        st.session_state['hero_show_flags'] = [False, False]
    else:
        st.session_state['showdown_phase'] = False

def run_auto_showdown():
    deck = st.session_state['deck']; community = st.session_state['community']
    needed = 5 - len(community)
    for _ in range(needed):
        if deck: community.append(deck.pop())
    st.session_state['phase'] = 'GAME_OVER'
    determine_winner()

def proceed_to_next_street():
    phase = st.session_state['phase']; deck = st.session_state['deck']
    if phase == 'PREFLOP':
        st.session_state['phase'] = 'FLOP'; st.session_state['community'] = [deck.pop() for _ in range(3)]
    elif phase == 'FLOP':
        st.session_state['phase'] = 'TURN'; st.session_state['community'].append(deck.pop())
    elif phase == 'TURN':
        st.session_state['phase'] = 'RIVER'; st.session_state['community'].append(deck.pop())
    elif phase == 'RIVER':
        determine_winner(); return
    reset_bets_for_new_street()
    
    active_with_chips = [p for p in st.session_state['players'] if p['status'] == 'alive' and p['stack'] > 0]
    if len(active_with_chips) <= 1: run_auto_showdown(); return

    dealer = st.session_state['dealer_idx']
    players = st.session_state['players']
    def find_next_alive_from(start_idx):
        idx = start_idx
        for _ in range(9):
            idx = (idx + 1) % 9
            if players[idx]['status'] == 'alive' and players[idx]['stack'] > 0: return idx
        return -1
    next_act = find_next_alive_from(dealer)
    if next_act == -1: run_auto_showdown()
    else: st.session_state['turn_idx'] = next_act

def next_turn():
    players = st.session_state['players']
    active = [p for p in players if p['status'] == 'alive']
    if len(active) == 1:
        winner = active[0]; winner['stack'] += st.session_state['pot']
        st.session_state['message'] = f"🏆 {winner['name']} 승리! (All Fold)"
        st.session_state['phase'] = 'GAME_OVER'
        st.session_state['wait_for_next_hand'] = True; return

    active_with_chips = [p for p in active if p['stack'] > 0]
    current_street_bet = st.session_state['current_bet']
    pending_players = [p for p in active_with_chips if not p['has_acted']]
    unmatched_players = [p for p in active_with_chips if p['bet'] < current_street_bet]
    
    if not pending_players and not unmatched_players: proceed_to_next_street(); return

    curr_idx = st.session_state['turn_idx']; found_next = False
    for _ in range(9):
        curr_idx = (curr_idx + 1) % 9; p = players[curr_idx]
        if p['status'] == 'alive' and p['stack'] > 0:
            st.session_state['turn_idx'] = curr_idx; found_next = True; break
    if not found_next: run_auto_showdown(); return

def handle_rebuy_and_elimination(players):
    for p in players:
        if p['stack'] <= 0 and p['status'] != 'spectator':
            if p['buyin_count'] < 3:
                p['buyin_count'] += 1
                if p['buyin_count'] == 2: new_stack = 60000
                else: new_stack = 70000 
                p['stack'] = new_stack; p['status'] = 'alive'
            else: p['status'] = 'spectator'; p['stack'] = 0

def start_new_hand():
    st.session_state['deck'] = new_deck(); st.session_state['community'] = []
    st.session_state['pot'] = 0; st.session_state['phase'] = 'PREFLOP'
    st.session_state['message'] = ""; st.session_state['hero_turn_start'] = 0
    st.session_state['showdown_phase'] = False; st.session_state['hero_show_flags'] = [False, False]
    st.session_state['wait_for_next_hand'] = False 

    sb, bb, ante, lvl, _, _ = get_current_info()
    st.session_state['sb_amount'] = sb; st.session_state['bb_amount'] = bb
    st.session_state['ante_amount'] = ante; st.session_state['level'] = lvl
    st.session_state['current_bet'] = bb
    
    players = st.session_state['players']
    handle_rebuy_and_elimination(players)
    
    next_dealer = (st.session_state['dealer_idx'] + 1) % 9
    while players[next_dealer]['status'] == 'spectator': 
        next_dealer = (next_dealer + 1) % 9
    st.session_state['dealer_idx'] = next_dealer; dealer = next_dealer

    def find_next_participant(start_idx):
        idx = start_idx
        for _ in range(9):
            idx = (idx + 1) % 9
            if players[idx]['status'] != 'spectator': return idx
        return start_idx

    sb_pos = find_next_participant(dealer); bb_pos = find_next_participant(sb_pos); utg_pos = find_next_participant(bb_pos)
    st.session_state['pot'] = 0
    for p in players:
        p['role'] = ''; p['bet'] = 0; p['action'] = ''; p['has_acted'] = False; p['hand'] = []; p['total_bet_hand'] = 0

    players[dealer]['role'] = 'D'; players[sb_pos]['role'] = 'SB'; players[bb_pos]['role'] = 'BB'

    for i, p in enumerate(players):
        if p['status'] == 'spectator': continue
        if p['stack'] > 0: p['status'] = 'alive'
        if p['status'] == 'alive' and len(st.session_state['deck']) > 2:
            p['hand'] = [st.session_state['deck'].pop(), st.session_state['deck'].pop()]
        if i == sb_pos: 
            amt = min(p['stack'], sb); p['stack']-=amt; p['bet']=amt; p['total_bet_hand']+=amt; st.session_state['pot']+=amt; p['action']=f"SB {amt}"; p['has_acted'] = True 
        if i == bb_pos: 
            if ante > 0 and p['stack'] > 0:
                ante_pay = min(p['stack'], ante); p['stack'] -= ante_pay; p['total_bet_hand']+=ante_pay; st.session_state['pot'] += ante_pay
            if p['stack'] > 0:
                blind_pay = min(p['stack'], bb); p['stack'] -= blind_pay; p['bet'] = blind_pay; p['total_bet_hand']+=blind_pay; st.session_state['pot'] += blind_pay; p['action'] = f"BB {blind_pay}"
            p['has_acted'] = False 
            
    st.session_state['turn_idx'] = utg_pos; st.session_state['game_round'] = 1

# ==========================================
# 4. UI 렌더링
# ==========================================
sb, bb, ante, lvl, timer_str, avg_stack = get_current_info()

st.markdown("""<style>
.stApp {background-color:#121212;}
.top-hud {
    display: flex; justify-content: space-around; align-items: center;
    background: #333; padding: 10px; border-radius: 10px; margin-bottom: 5px;
    border: 1px solid #555; color: white; font-weight: bold; font-size: 16px;
}
.hud-time { color: #ffeb3b; font-size: 20px; }
.game-board-container {
    position:relative; width:100%; height:650px;
    margin:0 auto; background-color:#1e1e1e; border-radius:30px; border:4px solid #333;
    overflow: hidden; 
}
.poker-table {
    position:absolute; top:45%; left:50%; transform:translate(-50%,-50%);
    width: 90%; height: 460px;
    background: radial-gradient(#5d4037, #3e2723);
    border: 20px solid #281915; border-radius: 250px;
    box-shadow: inset 0 0 50px rgba(0,0,0,0.8), 0 10px 30px rgba(0,0,0,0.5);
}
.seat {
    position:absolute; width:140px; height:160px;
    background:#2c2c2c; border:3px solid #666;
    border-radius:15px;
    color:white; text-align:center; font-size:12px;
    display:flex; flex-direction:column; justify-content:flex-start;
    padding-top: 10px; align-items:center; z-index:10;
    box-shadow: 3px 3px 15px rgba(0,0,0,0.6);
    overflow: visible !important;
}
.card-container { display: flex; justify-content: center; align-items: center; gap: 4px; margin-top: 5px; }
.hero-folded { filter: grayscale(100%) brightness(40%); opacity: 0.7; }
.seat-num { font-size: 10px; color: #aaa; margin-bottom: 2px; }
.bet-chip {color:#42a5f5; font-weight:bold; font-size:13px; text-shadow: 1px 1px 2px black;}
.buyin-badge {color:#ffcc80; font-size:10px; margin-bottom: 2px;}
.pos-0 {top:30px; right:25%;} .pos-1 {top:110px; right:5%;} .pos-2 {bottom:110px; right:5%;} .pos-3 {bottom:30px; right:25%;} .pos-4 {bottom:30px; left:50%; transform:translateX(-50%);} .pos-5 {bottom:30px; left:25%;} .pos-6 {bottom:110px; left:5%;} .pos-7 {top:110px; left:5%;} .pos-8 {top:30px; left:25%;}
.hero-seat { border:4px solid #ffd700; background:#3a3a3a; box-shadow:0 0 25px #ffd700; transform: translateX(-50%) scale(1.3); z-index: 20; }
.action-badge {
    position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%);
    background:#ffeb3b; color:black; font-weight:bold; padding:2px 8px; border-radius:4px;
    z-index: 100; white-space: nowrap; box-shadow: 1px 1px 3px rgba(0,0,0,0.5); border: 1px solid #000; font-size: 11px;
}
.role-badge {
    position: absolute; top: -10px; left: -10px; width: 24px; height: 24px; border-radius: 50%;
    background: white; color: black; font-weight: bold; line-height: 22px; border: 2px solid #333; z-index: 100; box-shadow: 1px 1px 2px black;
}
.role-D { background: #ffeb3b; } .role-SB { background: #90caf9; } .role-BB { background: #ef9a9a; } 
.center-hud {position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;width:100%;color:#ddd; text-shadow: 1px 1px 3px black;}
.card-span {background:white;padding:2px 6px;border-radius:4px;margin:1px;font-weight:bold;font-size:28px;border:1px solid #ccc; line-height: 1.0;}
.control-title { font-size: 18px; font-weight: bold; color: #ddd; margin-bottom: 20px; text-align: center; }
@media screen and (max-width: 1000px) {
    .seat { width: 85px; height: 110px; font-size: 9px; padding-top: 5px; }
    .card-span { font-size: 16px; padding: 1px 3px; }
    .bet-chip { font-size: 10px; }
    .buyin-badge { font-size: 8px; }
    .seat-num { font-size: 8px; }
    .poker-table { height: 350px; border-width: 10px; }
    .game-board-container { height: 500px; }
    .hero-seat { transform: translateX(-50%) scale(1.1); }
    .pos-0 { right: 15%; } .pos-3 { right: 15%; } .pos-5 { left: 15%; } .pos-8 { left: 15%; }
    .top-hud { font-size: 12px; }
}
</style>""", unsafe_allow_html=True)

st.markdown(f"""<div class="top-hud"><div>LEVEL {lvl}</div><div class="hud-time">⏱️ {timer_str}</div><div>🟡 {sb}/{bb} (A{ante})</div><div>📊 Avg: {avg_stack:,}</div></div>""", unsafe_allow_html=True)

col_table, col_controls = st.columns([3, 1])

with col_table:
    if st.button("🔄 화면 새로고침", use_container_width=True): st.rerun()
    players = st.session_state['players']; turn = st.session_state['turn_idx']
    if st.session_state['show_bb']: pot_display = f"{st.session_state['pot']/bb:.1f} BB"
    else: pot_display = f"{st.session_state['pot']:,}"

    comm = st.session_state['community']
    comm_str = "".join([make_card(c) for c in comm]) if comm else "<span style='color:#999; font-size:24px;'>Waiting...</span>"
    html_code = '<div class="game-board-container">'
    html_code += f'<div class="poker-table"><div class="center-hud"><div style="font-size:22px;color:#a5d6a7;font-weight:bold;margin-bottom:10px;">Pot: {pot_display}</div><div style="margin:20px 0;">{comm_str}</div><div style="font-size:14px;color:#aaa;">{st.session_state["phase"]}</div><div style="color:#ffcc80; font-weight:bold; font-size:16px; margin-top:5px;">{st.session_state["message"]}</div></div></div>'

    for i, p in enumerate(players):
        seat_cls = f"pos-{i}"; extra_cls = ""
        if i == 4: extra_cls += " hero-seat"
        if i == turn and st.session_state['phase'] != 'GAME_OVER': extra_cls += " active-turn"
        status_txt = "<div style='color:red; font-size:10px; font-weight:bold;'>SPECTATOR</div>" if p['status'] == 'spectator' else ""
        if p['status'] != 'alive' and p['status'] != 'spectator': extra_cls += " dead-seat"
        role_html = f"<div class='role-badge role-{p['role']}'>{p['role']}</div>" if p['role'] else ""
        act_badge = f"<div class='action-badge'>{p['action']}</div>" if p['action'] else ""
        if st.session_state['show_bb']:
            bet_val = f"{p['bet']/bb:.1f} BB"; stack_val = f"{p['stack']/bb:.1f} BB"
        else:
            bet_val = f"{p['bet']:,}"; stack_val = f"{p['stack']:,}"
        bet_display = f"<div class='bet-chip'>Bet: {bet_val}</div>" if p['bet'] > 0 else "<div class='bet-chip' style='visibility:hidden;'>-</div>"
        buyin_info = f"<div class='buyin-badge'>Entry: {p['buyin_count']}/3</div>" if p['status'] != 'spectator' else ""
        seat_num_display = f"<div class='seat-num'>SEAT {p['seat']}</div>" 

        cards_html = ""
        if p['status'] == 'folded':
            if i == 4 and p['hand']: cards_html = f"<div class='card-container hero-folded'>{make_card(p['hand'][0])}{make_card(p['hand'][1])}</div>"
            else: cards_html = "<div class='card-container' style='color:#777; font-size:12px;'>❌ Folded</div>"
        elif p['status'] == 'alive':
            cards_html = f"<div class='card-container' style='font-size:24px;'>🂠 🂠</div>"
            if p['hand']:
                if i == 4 and st.session_state['phase'] == 'GAME_OVER' and st.session_state['showdown_phase']:
                    c1 = make_card(p['hand'][0]) if st.session_state['hero_show_flags'][0] else "🂠"
                    c2 = make_card(p['hand'][1]) if st.session_state['hero_show_flags'][1] else "🂠"
                    cards_html = f"<div class='card-container'>{c1}{c2}</div>"
                elif i == 4: cards_html = f"<div class='card-container'>{make_card(p['hand'][0])}{make_card(p['hand'][1])}</div>"
                elif st.session_state['phase'] == 'GAME_OVER': cards_html = f"<div class='card-container'>{make_card(p['hand'][0])}{make_card(p['hand'][1])}</div>"

        html_code += f'<div class="seat {seat_cls} {extra_cls}">{role_html}{seat_num_display}<div style="font-size:12px;"><strong>{p["name"]}</strong></div>{buyin_info}<div style="font-size:12px;">🪙{stack_val}</div>{cards_html}{bet_display}{status_txt}{act_badge}</div>'
    html_code += '</div>'
    st.markdown(html_code, unsafe_allow_html=True)

with col_controls:
    st.markdown('<div class="control-title">🎮 Control Panel</div>', unsafe_allow_html=True)
    if st.button("🔄 칩 / BB 변환", use_container_width=True):
        st.session_state['show_bb'] = not st.session_state['show_bb']; st.rerun()

    players = st.session_state['players']; turn = st.session_state['turn_idx']; hero = players[4]

    if st.session_state['phase'] == 'GAME_OVER':
        st.success(f"🎉 {st.session_state['message']}")
        if st.session_state['wait_for_next_hand']:
            if st.session_state['showdown_phase'] and players[4]['status'] == 'alive':
                 c1, c2 = players[4]['hand']
                 col_show1, col_show2 = st.columns(2)
                 with col_show1: 
                     if st.button(f"👉 {c1} 오픈", use_container_width=True): st.session_state['hero_show_flags'][0] = not st.session_state['hero_show_flags'][0]; st.rerun()
                 with col_show2:
                     if st.button(f"👈 {c2} 오픈", use_container_width=True): st.session_state['hero_show_flags'][1] = not st.session_state['hero_show_flags'][1]; st.rerun()
                 if st.button("👐 모두 오픈", use_container_width=True): st.session_state['hero_show_flags'] = [True, True]; st.rerun()
            st.markdown("---")
            if st.button("▶️ 다음 판 진행 (Next Hand)", type="primary", use_container_width=True):
                start_new_hand(); st.rerun()
        else:
             if st.session_state['game_round'] == 0:
                if st.button("🚀 게임 시작", type="primary", use_container_width=True): start_new_hand(); st.rerun()

    elif turn == 4 and players[4]['status'] == 'alive' and players[4]['stack'] > 0:
        if st.session_state['hero_turn_start'] == 0: st.session_state['hero_turn_start'] = time.time()
        time_left = 30 - int(time.time() - st.session_state['hero_turn_start'])
        if time_left <= 0:
            hero['status'] = 'folded'; hero['action'] = "Fold (Time)"; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
        else:
            st.error(f"⚡ 남은 시간: {time_left}초")
            current_bet = st.session_state['current_bet']; to_call = current_bet - hero['bet']
            min_raise = current_bet * 2 if current_bet > 0 else st.session_state['bb_amount'] * 2
            
            # [최종 수정] 형님 재산과 배팅액을 전부 정수(int)로 강제 변환
            max_possible = int(hero['stack'] + hero['bet'])
            safe_min = int(min(min_raise, max_possible))
            
            if to_call == 0:
                if st.button("체크 (Check)", use_container_width=True):
                    hero['action'] = "Check"; hero['has_acted'] = True; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
            else:
                call_cost = min(to_call, hero['stack'])
                if st.button(f"콜 (Call {call_cost:,})", use_container_width=True):
                    hero['stack'] -= call_cost; hero['bet'] += call_cost; hero['total_bet_hand'] += call_cost
                    st.session_state['pot'] += call_cost
                    hero['action'] = "Call"; hero['has_acted'] = True; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
            
            if safe_min >= max_possible:
                st.warning(f"⚠️ 칩 부족: 올인 ({max_possible:,})만 가능합니다.")
                if st.button("올인 (All-in)", use_container_width=True):
                    amt = hero['stack']; hero['stack'] = 0; hero['bet'] += amt; hero['total_bet_hand'] += amt
                    st.session_state['pot'] += amt
                    if hero['bet'] > st.session_state['current_bet']:
                        st.session_state['current_bet'] = hero['bet']
                        for p in players:
                            if p != hero and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                    hero['action'] = "All-in"; hero['has_acted'] = True; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
            else:
                # [수정] value, min_value, max_value 전부 int로 박아넣음
                raise_input = st.number_input("Raise Amount", min_value=safe_min, max_value=max_possible, value=safe_min, step=100)
                
                if st.button(f"레이즈 (Raise)", use_container_width=True):
                    if raise_input <= current_bet:
                         call_cost = min(to_call, hero['stack'])
                         hero['stack'] -= call_cost; hero['bet'] += call_cost; hero['total_bet_hand'] += call_cost
                         st.session_state['pot'] += call_cost
                         hero['action'] = "Call"; hero['has_acted'] = True
                    else:
                        total = raise_input; added = total - hero['bet']
                        if added > hero['stack']: added = hero['stack']; total = hero['bet'] + added
                        hero['stack'] -= added; hero['bet'] = total; hero['total_bet_hand'] += added
                        st.session_state['pot'] += added
                        st.session_state['current_bet'] = max(st.session_state['current_bet'], total)
                        hero['action'] = f"Raise {total}"; hero['has_acted'] = True
                        for p in players:
                            if p != hero and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                    st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
                
                if st.button("올인 (All-in)", use_container_width=True):
                    amt = hero['stack']; hero['stack'] = 0; hero['bet'] += amt; hero['total_bet_hand'] += amt
                    st.session_state['pot'] += amt
                    if hero['bet'] > st.session_state['current_bet']:
                        st.session_state['current_bet'] = hero['bet']
                        for p in players:
                            if p != hero and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                    hero['action'] = "All-in"; hero['has_acted'] = True; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
                
            st.markdown("---")
            if st.button("폴드 (Fold)", type="primary", use_container_width=True):
                hero['status'] = 'folded'; hero['action'] = "Fold"; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
            time.sleep(1); st.rerun()

    else:
        st.info("⏳ 봇 플레이 중...")
        if st.session_state['game_round'] > 0:
            current_player = players[turn]
            if current_player['status'] != 'alive' or current_player['stack'] <= 0: next_turn(); st.rerun()
            else:
                st.session_state['hero_turn_start'] = 0; bot = players[turn]; time.sleep(0.6)
                action, amount = get_bot_decision(bot, st.session_state['community'], st.session_state['current_bet'], st.session_state['pot'], st.session_state['bb_amount'], st.session_state['phase'])
                if action == "Fold": bot['status'] = 'folded'; bot['action'] = "Fold"
                elif action == "Check": bot['action'] = "Check"; bot['has_acted'] = True
                elif action == "Call":
                    call_amt = st.session_state['current_bet'] - bot['bet']
                    added = min(call_amt, bot['stack'])
                    bot['stack'] -= added; bot['bet'] += added; bot['total_bet_hand'] += added
                    st.session_state['pot'] += added
                    bot['action'] = "All-in" if bot['stack'] == 0 else "Call"
                    bot['has_acted'] = True
                elif action == "Raise":
                    if amount <= st.session_state['current_bet']:
                         call_amt = st.session_state['current_bet'] - bot['bet']
                         added = min(call_amt, bot['stack'])
                         bot['stack'] -= added; bot['bet'] += added; bot['total_bet_hand'] += added
                         st.session_state['pot'] += added
                         bot['action'] = "All-in" if bot['stack'] == 0 else "Call"
                         bot['has_acted'] = True
                    else:
                        raise_amt = amount; actual_add = raise_amt - bot['bet']
                        if actual_add > bot['stack']: actual_add = bot['stack']; raise_amt = bot['bet'] + actual_add
                        bot['stack'] -= actual_add; bot['bet'] = raise_amt; bot['total_bet_hand'] += actual_add
                        st.session_state['pot'] += actual_add
                        st.session_state['current_bet'] = max(st.session_state['current_bet'], raise_amt)
                        bot['action'] = f"Raise {raise_amt}"; bot['has_acted'] = True
                        for p in players:
                            if p != bot and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                elif action == "All-in":
                    all_in_amt = bot['stack']; bot['stack'] = 0; bot['bet'] += all_in_amt; bot['total_bet_hand'] += all_in_amt
                    st.session_state['pot'] += all_in_amt
                    if bot['bet'] > st.session_state['current_bet']:
                        st.session_state['current_bet'] = bot['bet']
                        for p in players:
                            if p != bot and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                    bot['action'] = "All-in"; bot['has_acted'] = True
                next_turn(); st.rerun()
        else:
             if st.button("🚀 게임 시작", type="primary", use_container_width=True): start_new_hand(); st.rerun()
