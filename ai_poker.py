import streamlit as st
import random
import time

# ==========================================
# 1. 설정 및 초기화
# ==========================================
st.set_page_config(layout="wide", page_title="AI 몬스터 토너먼트", page_icon="🦁")

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
    
    st.session_state['players'] = [
        {'name': 'Bot 1', 'seat': 1, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': 'Bot 2', 'seat': 2, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': 'Bot 3', 'seat': 3, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': 'Bot 4', 'seat': 4, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': '👑 형님', 'seat': 5, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': 'Bot 5', 'seat': 6, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': 'Bot 6', 'seat': 7, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': 'Bot 7', 'seat': 8, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
        {'name': 'Bot 8', 'seat': 9, 'stack': 30000, 'hand': [], 'status': 'alive', 'bet': 0, 'action': '', 'role': '', 'has_acted': False, 'buyin_count': 1},
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

def get_hand_rank(hand):
    if not hand: return 0, "", ""
    ranks = sorted([RANKS.index(c[0]) for c in hand], reverse=True)
    suits = [c[1] for c in hand]
    suit_counts = {s: suits.count(s) for s in set(suits)}
    flush_suit = next((s for s, c in suit_counts.items() if c >= 5), None)
    is_flush = (flush_suit is not None)
    unique_ranks = sorted(list(set(ranks)), reverse=True)
    is_straight = False; straight_high = -1
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i] - unique_ranks[i+4] == 4: is_straight = True; straight_high = unique_ranks[i]; break
    if not is_straight and set([12, 3, 2, 1, 0]).issubset(set(ranks)): is_straight = True; straight_high = 3
    counts = {r: ranks.count(r) for r in ranks}
    sorted_counts = sorted(counts.values(), reverse=True)

    if is_flush and is_straight:
        flush_cards = sorted([RANKS.index(c[0]) for c in hand if c[1] == flush_suit], reverse=True)
        is_sf = False; sf_high = -1
        for i in range(len(flush_cards) - 4):
            if flush_cards[i] - flush_cards[i+4] == 4: is_sf = True; sf_high = flush_cards[i]; break
        if not is_sf and set([12, 3, 2, 1, 0]).issubset(set(flush_cards)): is_sf = True; sf_high = 3
        if is_sf:
            if sf_high == 12: return 999, "로얄 스트레이트 플러시", "로얄 스트레이트 플러시"
            return 900 + sf_high, "스티플", f"{r_str(sf_high)} 스트레이트 플러시"
    if 4 in sorted_counts:
        quad = next(r for r, c in counts.items() if c == 4)
        return 800 + quad, "포카드", f"{r_str(quad)} 포카드"
    if 3 in sorted_counts and 2 in sorted_counts:
        trip = next(r for r, c in counts.items() if c == 3)
        pair = next(r for r, c in counts.items() if c == 2)
        return 700 + trip, "풀하우스", f"{r_str(trip)} 하우스 ({r_str(pair)} 페어)"
    if is_flush:
        f_ranks = sorted([RANKS.index(c[0]) for c in hand if c[1] == flush_suit], reverse=True)
        return 600 + f_ranks[0], "플러시", f"{r_str(f_ranks[0])} 하이 플러시"
    if is_straight: return 500 + straight_high, "스트레이트", f"{r_str(straight_high)} 하이 스트레이트"
    if 3 in sorted_counts:
        trip = next(r for r, c in counts.items() if c == 3)
        return 400 + trip, "트리플", f"{r_str(trip)} 트리플"
    if sorted_counts.count(2) >= 2:
        pairs = sorted([r for r, c in counts.items() if c == 2], reverse=True)
        return 300 + pairs[0], "투페어", f"{r_str(pairs[0])} & {r_str(pairs[1])} 투페어"
    if 2 in sorted_counts:
        pair = next(r for r, c in counts.items() if c == 2)
        return 200 + pair, "원페어", f"{r_str(pair)} 원페어"
    return 100 + ranks[0], "하이카드", f"{r_str(ranks[0])} 하이카드"

# ==========================================
# [AI Logic]
# ==========================================
def is_trash_hand(hand):
    r1 = RANKS.index(hand[0][0]); r2 = RANKS.index(hand[1][0])
    is_pair = (r1 == r2); is_suited = (hand[0][1] == hand[1][1])
    if is_pair: return False
    if is_suited and r1 >= 8 and r2 >= 8: return False 
    if r1 >= 11 or r2 >= 11: return False 
    if abs(r1 - r2) <= 2: return False
    return True

def calculate_approx_equity(hand, community):
    if not community:
        r1 = RANKS.index(hand[0][0]); r2 = RANKS.index(hand[1][0])
        is_pair = (r1 == r2); is_suited = (hand[0][1] == hand[1][1])
        if is_pair and r1 >= 10: return 0.85
        if is_pair and r1 >= 7: return 0.70
        if is_pair: return 0.55
        if r1 >= 11 and r2 >= 10: return 0.65 
        if is_suited and r1 >= 10: return 0.55
        return 0.35
    else:
        current_score, _, _ = get_hand_rank(hand + community)
        if current_score >= 400: return 0.95 
        if current_score >= 300: return 0.85 
        if current_score >= 200: return 0.75 if current_score >= 210 else 0.60
        all_cards = hand + community
        suits = [c[1] for c in all_cards]
        is_flush_draw = any(count == 4 for count in {s: suits.count(s) for s in set(suits)}.values())
        ranks = sorted(list(set([RANKS.index(c[0]) for c in all_cards])))
        consecutive = 0
        for i in range(len(ranks)-1):
            if ranks[i+1] - ranks[i] == 1: consecutive += 1
            else: consecutive = 0
        is_straight_draw = (consecutive >= 3)
        draw_bonus = 0.0
        if is_flush_draw: draw_bonus += 0.20
        if is_straight_draw: draw_bonus += 0.10
        return min(0.90, 0.1 + draw_bonus) 

def get_bot_decision(bot, community, current_bet, pot, bb_amt, phase):
    hand = bot['hand']; stack = bot['stack']; to_call = current_bet - bot['bet']
    equity = calculate_approx_equity(hand, community)
    
    if not community:
        if is_trash_hand(hand) and to_call > bb_amt: return "Fold", 0

    if phase == 'RIVER':
        current_score, _, _ = get_hand_rank(hand + community)
        if current_score < 200 and to_call > 0: return "Fold", 0

    if to_call == 0:
        if equity > 0.8: return "Raise", min(stack, int(pot * 0.6))
        if equity < 0.3 and random.random() > 0.95: return "Raise", min(stack, bb_amt * 2) 
        return "Check", 0
    else:
        total_pot = pot + to_call
        pot_odds = to_call / total_pot if total_pot > 0 else 0
        if equity >= (pot_odds + 0.1): 
            if equity > 0.85 and random.random() > 0.3: return "Raise", min(stack, current_bet * 3)
            return "Call", to_call
        else:
            if to_call <= bb_amt: return "Call", to_call 
            return "Fold", 0

# ==========================================
# 3. 게임 엔진
# ==========================================
def reset_bets_for_new_street():
    st.session_state['current_bet'] = 0
    for p in st.session_state['players']:
        p['bet'] = 0; p['has_acted'] = False; 
        if p['status'] == 'alive': p['action'] = '' 

# [핵심] 초과 배팅액 반환 함수
def return_uncalled_chips():
    bettors = [p for p in st.session_state['players'] if p['bet'] > 0 and p['status'] != 'folded']
    if len(bettors) < 2: return 

    bettors.sort(key=lambda x: x['bet'], reverse=True)
    highest = bettors[0]
    second = bettors[1]
    
    diff = highest['bet'] - second['bet']
    if diff > 0:
        highest['stack'] += diff
        highest['bet'] -= diff
        st.session_state['pot'] -= diff
        st.toast(f"💰 {highest['name']}에게 초과 배팅 {diff:,}칩 반환됨")

def determine_winner():
    # [수정] 여기서도 한번 더 체크 (안전장치)
    return_uncalled_chips()

    players = st.session_state['players']
    best_score = -1; winner = None; best_desc = ""
    active = [p for p in players if p['status'] == 'alive']
    
    for p in active:
        sc, _, desc = get_hand_rank(p['hand'] + st.session_state['community'])
        if sc > best_score:
            best_score = sc; winner = p; best_desc = desc
            
    if winner:
        winner['stack'] += st.session_state['pot']
        st.session_state['message'] = f"🏆 승자: {winner['name']} ({best_desc})"
    st.session_state['phase'] = 'GAME_OVER'
    
    hero = players[4]
    if winner == hero and hero['status'] == 'alive':
        st.session_state['showdown_phase'] = True
        st.session_state['hero_show_flags'] = [False, False]
    else:
        st.session_state['showdown_phase'] = False

def run_auto_showdown():
    # [핵심 수정] 팟 계산 전에 '무조건' 초과 금액부터 돌려주고 시작
    return_uncalled_chips()
    
    deck = st.session_state['deck']; community = st.session_state['community']
    needed = 5 - len(community)
    for _ in range(needed):
        if deck: community.append(deck.pop())
        
    st.session_state['phase'] = 'GAME_OVER'
    determine_winner()

def proceed_to_next_street():
    # [핵심 수정] 라운드 넘어가기 전에 '무조건' 초과 금액부터 정리
    return_uncalled_chips()

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
    if len(active_with_chips) <= 1:
        run_auto_showdown(); return

    dealer = st.session_state['dealer_idx']
    players = st.session_state['players']
    def find_next_alive_from(start_idx):
        idx = start_idx
        for _ in range(9):
            idx = (idx + 1) % 9
            if players[idx]['status'] == 'alive' and players[idx]['stack'] > 0:
                return idx
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
        st.session_state['phase'] = 'GAME_OVER'; return

    active_with_chips = [p for p in active if p['stack'] > 0]
    is_bet_matched = all(p['bet'] == st.session_state['current_bet'] for p in active_with_chips)
    have_all_acted = all(p['has_acted'] for p in active_with_chips)
    
    if is_bet_matched and have_all_acted: 
        proceed_to_next_street(); return

    curr_idx = st.session_state['turn_idx']; found_next = False
    for _ in range(9):
        curr_idx = (curr_idx + 1) % 9; p = players[curr_idx]
        if p['status'] == 'alive' and p['stack'] > 0:
            st.session_state['turn_idx'] = curr_idx; found_next = True; break
            
    if not found_next: 
        run_auto_showdown(); return

def handle_rebuy_and_elimination(players):
    for p in players:
        if p['stack'] <= 0 and p['status'] != 'spectator':
            if p['buyin_count'] < 3:
                p['buyin_count'] += 1; new_stack = 40000 if p['buyin_count'] == 2 else 50000
                p['stack'] = new_stack; p['status'] = 'alive'
            else: p['status'] = 'spectator'; p['stack'] = 0

def start_new_hand():
    st.session_state['deck'] = new_deck(); st.session_state['community'] = []
    st.session_state['pot'] = 0; st.session_state['phase'] = 'PREFLOP'
    st.session_state['message'] = ""; st.session_state['hero_turn_start'] = 0
    st.session_state['showdown_phase'] = False; st.session_state['hero_show_flags'] = [False, False]

    sb, bb, ante, lvl, _, _ = get_current_info()
    st.session_state['sb_amount'] = sb; st.session_state['bb_amount'] = bb
    st.session_state['ante_amount'] = ante; st.session_state['level'] = lvl
    st.session_state['current_bet'] = bb
    players = st.session_state['players']; handle_rebuy_and_elimination(players)
    
    next_dealer = (st.session_state['dealer_idx'] + 1) % 9
    while players[next_dealer]['status'] == 'spectator': 
        next_dealer = (next_dealer + 1) % 9
    st.session_state['dealer_idx'] = next_dealer; dealer = next_dealer

    def find_next_participant(start_idx):
        idx = start_idx
        for _ in range(9):
            idx = (idx + 1) % 9
            if players[idx]['status'] != 'spectator':
                return idx
        return start_idx

    sb_pos = find_next_participant(dealer)
    bb_pos = find_next_participant(sb_pos)
    utg_pos = find_next_participant(bb_pos)

    st.session_state['pot'] = 0
    for p in players: p['role'] = ''
    players[dealer]['role'] = 'D'
    players[sb_pos]['role'] = 'SB'
    players[bb_pos]['role'] = 'BB'

    for i, p in enumerate(players):
        p['bet'] = 0; p['action'] = ''; p['has_acted'] = False; p['hand'] = []
        if p['status'] == 'spectator': continue
        if p['stack'] > 0: p['status'] = 'alive'
        if p['status'] == 'alive' and len(st.session_state['deck']) > 2:
            p['hand'] = [st.session_state['deck'].pop(), st.session_state['deck'].pop()]
        
        if i == sb_pos: 
            amt = min(p['stack'], sb); p['stack']-=amt; p['bet']=amt; st.session_state['pot']+=amt; p['action']=f"SB {amt}"; p['has_acted'] = True 
        if i == bb_pos: 
            if ante > 0 and p['stack'] > 0:
                ante_pay = min(p['stack'], ante); p['stack'] -= ante_pay; st.session_state['pot'] += ante_pay
            if p['stack'] > 0:
                blind_pay = min(p['stack'], bb); p['stack'] -= blind_pay; p['bet'] = blind_pay; st.session_state['pot'] += blind_pay; p['action'] = f"BB {blind_pay}"
            p['has_acted'] = False 
            
    st.session_state['turn_idx'] = utg_pos
    st.session_state['game_round'] = 1

# ==========================================
# 4. UI 렌더링
# ==========================================
st.title("🦁 AI 몬스터 토너먼트 (9-Max)")
sb, bb, ante, lvl, timer_str, avg_stack = get_current_info()

st.markdown("""<style>
.stApp {background-color:#121212;}
.top-hud {
    display: flex; justify-content: space-around; align-items: center;
    background: #333; padding: 10px; border-radius: 10px; margin-bottom: 5px;
    border: 1px solid #555; color: white; font-weight: bold;
}
.hud-item { font-size: 16px; }
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

.pos-0 {top:30px; right:25%;}
.pos-1 {top:110px; right:5%;}
.pos-2 {bottom:110px; right:5%;}
.pos-3 {bottom:30px; right:25%;}
.pos-4 {bottom:30px; left:50%; transform:translateX(-50%);} 
.pos-5 {bottom:30px; left:25%;}
.pos-6 {bottom:110px; left:5%;}
.pos-7 {top:110px; left:5%;}
.pos-8 {top:30px; left:25%;}

.hero-seat {
    border:4px solid #ffd700; background:#3a3a3a; box-shadow:0 0 25px #ffd700;
    transform: translateX(-50%) scale(1.3); z-index: 20; 
}
.action-badge {
    position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%);
    background:#ffeb3b; color:black; font-weight:bold; padding:2px 8px; border-radius:4px;
    z-index: 100; white-space: nowrap; box-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    border: 1px solid #000; font-size: 11px;
}
.role-badge {
    position: absolute; top: -10px; left: -10px;
    width: 24px; height: 24px; border-radius: 50%;
    background: white; color: black; font-weight: bold; line-height: 22px;
    border: 2px solid #333; z-index: 100; box-shadow: 1px 1px 2px black;
}
.role-D { background: #ffeb3b; } .role-SB { background: #90caf9; } .role-BB { background: #ef9a9a; } 
.center-hud {position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;width:100%;color:#ddd; text-shadow: 1px 1px 3px black;}
.card-span {background:white;padding:2px 6px;border-radius:4px;margin:1px;font-weight:bold;font-size:28px;border:1px solid #ccc; line-height: 1.0;}
.control-title { font-size: 18px; font-weight: bold; color: #ddd; margin-bottom: 20px; text-align: center; }
</style>""", unsafe_allow_html=True)

col_table, col_controls = st.columns([3, 1])

# [좌측] 게임 테이블
with col_table:
    if st.button("🔄 화면 새로고침", use_container_width=True): st.rerun()
    players = st.session_state['players']; turn = st.session_state['turn_idx']
    html_code = '<div class="game-board-container">'
    comm = st.session_state['community']
    comm_str = "".join([make_card(c) for c in comm]) if comm else "<span style='color:#999; font-size:24px;'>Waiting...</span>"
    html_code += f'<div class="poker-table"><div class="center-hud"><div style="font-size:22px;color:#a5d6a7;font-weight:bold;margin-bottom:10px;">Pot: {st.session_state["pot"]:,}</div><div style="margin:20px 0;">{comm_str}</div><div style="font-size:14px;color:#aaa;">{st.session_state["phase"]}</div><div style="color:#ffcc80; font-weight:bold; font-size:16px; margin-top:5px;">{st.session_state["message"]}</div></div></div>'

    for i, p in enumerate(players):
        seat_cls = f"pos-{i}"; extra_cls = ""
        if i == 4: extra_cls += " hero-seat"
        if i == turn and st.session_state['phase'] != 'GAME_OVER': extra_cls += " active-turn"
        status_txt = "<div style='color:red; font-size:10px; font-weight:bold;'>SPECTATOR</div>" if p['status'] == 'spectator' else ""
        if p['status'] != 'alive' and p['status'] != 'spectator': extra_cls += " dead-seat"
        role_html = f"<div class='role-badge role-{p['role']}'>{p['role']}</div>" if p['role'] else ""
        act_badge = f"<div class='action-badge'>{p['action']}</div>" if p['action'] else ""
        bet_display = f"<div class='bet-chip'>Bet: {p['bet']:,}</div>" if p['bet'] > 0 else "<div class='bet-chip' style='visibility:hidden;'>-</div>"
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

        html_code += f'<div class="seat {seat_cls} {extra_cls}">{role_html}{seat_num_display}<div style="font-size:12px;"><strong>{p["name"]}</strong></div>{buyin_info}<div style="font-size:12px;">🪙{p["stack"]:,}</div>{cards_html}{bet_display}{status_txt}{act_badge}</div>'
    html_code += '</div>'
    st.markdown(html_code, unsafe_allow_html=True)

# [우측] 컨트롤 패널
with col_controls:
    st.markdown('<div class="control-title">🎮 Control Panel</div>', unsafe_allow_html=True)
    players = st.session_state['players']; turn = st.session_state['turn_idx']; hero = players[4]

    if st.session_state['phase'] == 'GAME_OVER':
        st.success(f"🎉 {st.session_state['message']}")
        if st.session_state['showdown_phase'] and players[4]['status'] == 'alive':
            c1, c2 = players[4]['hand']
            if st.button(f"👉 {c1} 오픈", use_container_width=True): st.session_state['hero_show_flags'][0] = not st.session_state['hero_show_flags'][0]; st.rerun()
            if st.button(f"👈 {c2} 오픈", use_container_width=True): st.session_state['hero_show_flags'][1] = not st.session_state['hero_show_flags'][1]; st.rerun()
            if st.button("👐 모두 오픈", use_container_width=True): st.session_state['hero_show_flags'] = [True, True]; st.rerun()
            st.markdown("---")
            if st.button("🙈 먹(Muck) & 다음 판", type="primary", use_container_width=True): start_new_hand(); st.rerun()
        elif st.session_state['game_round'] == 0:
            if st.button("🚀 게임 시작", type="primary", use_container_width=True): start_new_hand(); st.rerun()
        else:
            with st.spinner("3초 후 다음 판이 시작됩니다..."): time.sleep(3)
            start_new_hand(); st.rerun()

    elif turn == 4 and players[4]['status'] == 'alive' and players[4]['stack'] > 0:
        if st.session_state['hero_turn_start'] == 0: st.session_state['hero_turn_start'] = time.time()
        time_left = 30 - int(time.time() - st.session_state['hero_turn_start'])
        if time_left <= 0:
            hero['status'] = 'folded'; hero['action'] = "Fold (Time)"; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
        else:
            st.error(f"⚡ 남은 시간: {time_left}초")
            current_bet = st.session_state['current_bet']; to_call = current_bet - hero['bet']
            min_raise = current_bet * 2 if current_bet > 0 else st.session_state['bb_amount'] * 2
            max_possible = hero['stack'] + hero['bet']
            safe_min = min(int(min_raise), max_possible)
            raise_input = st.number_input("Raise Amount", min_value=safe_min, max_value=max_possible, value=safe_min, step=100)
            
            if to_call == 0:
                if st.button("체크 (Check)", use_container_width=True):
                    hero['action'] = "Check"; hero['has_acted'] = True; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
            else:
                call_cost = min(to_call, hero['stack'])
                if st.button(f"콜 (Call {call_cost:,})", use_container_width=True):
                    hero['stack'] -= call_cost; hero['bet'] += call_cost; st.session_state['pot'] += call_cost
                    hero['action'] = "Call"; hero['has_acted'] = True; st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
            
            if st.button(f"레이즈 (Raise)", use_container_width=True):
                total = raise_input; added = total - hero['bet']
                if added > hero['stack']: added = hero['stack']; total = hero['bet'] + added
                hero['stack'] -= added; hero['bet'] = total; st.session_state['pot'] += added
                st.session_state['current_bet'] = total; hero['action'] = f"Raise {total}"; hero['has_acted'] = True
                for p in players:
                    if p != hero and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                st.session_state['hero_turn_start'] = 0; next_turn(); st.rerun()
            
            if st.button("올인 (All-in)", use_container_width=True):
                amt = hero['stack']; hero['stack'] = 0; hero['bet'] += amt; st.session_state['pot'] += amt
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
                    bot['stack'] -= added; bot['bet'] += added; st.session_state['pot'] += added
                    bot['action'] = "All-in" if bot['stack'] == 0 else "Call"
                    bot['has_acted'] = True
                elif action == "Raise":
                    raise_amt = amount; actual_add = raise_amt - bot['bet']
                    if actual_add > bot['stack']: actual_add = bot['stack']; raise_amt = bot['bet'] + actual_add
                    bot['stack'] -= actual_add; bot['bet'] = raise_amt; st.session_state['pot'] += actual_add
                    st.session_state['current_bet'] = raise_amt; bot['action'] = f"Raise {raise_amt}"; bot['has_acted'] = True
                    for p in players:
                        if p != bot and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                elif action == "All-in":
                    all_in_amt = bot['stack']; bot['stack'] = 0; bot['bet'] += all_in_amt; st.session_state['pot'] += all_in_amt
                    if bot['bet'] > st.session_state['current_bet']:
                        st.session_state['current_bet'] = bot['bet']
                        for p in players:
                            if p != bot and p['status'] == 'alive' and p['stack'] > 0: p['has_acted'] = False
                    bot['action'] = "All-in"; bot['has_acted'] = True
                next_turn(); st.rerun()
        else:
             if st.button("🚀 게임 시작", type="primary", use_container_width=True): start_new_hand(); st.rerun()