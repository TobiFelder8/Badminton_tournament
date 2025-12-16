from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
from flask_session import Session
import random

app = Flask(__name__)
# einfache Server-Session (Datei-basiert). Für Demo ok.
app.config['SECRET_KEY'] = 'change_this_in_prod'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

TEMPLATE_INDEX = """
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Matchmaking - Teams</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f3f4f6;
            color: #1f2937;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 600px;
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            height: fit-content;
        }
        h3 {
            color: #111827;
            margin-top: 0;
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        textarea {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            font-family: inherit;
            font-size: 1rem;
            box-sizing: border-box;
            resize: vertical;
            min-height: 200px;
            transition: border-color 0.2s;
        }
        textarea:focus {
            outline: none;
            border-color: #3b82f6;
        }
        button {
            background-color: #2563eb;
            color: white;
            padding: 1rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
        }
        button:hover {
            background-color: #1d4ed8;
        }
        button:active {
            transform: scale(0.98);
        }
        .hint {
            color: #6b7280;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h3>🏸 Badminton Matchmaker (Doppel)</h3>
        <p class="hint">Trage die Teams ein (ein Team pro Zeile, z.B. "Anna & Bert")</p>
        <form method=post action="{{ url_for('schedule') }}">
            <textarea name=players placeholder="Team A (Max & Moritz)&#10;Team B (Susi & Strolch)&#10;...">{{ example }}</textarea>
            <button type=submit>Turnier starten</button>
        </form>
    </div>
</body>
</html>
"""

TEMPLATE_SCHEDULE = """
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Spielplan & Live-Rangliste</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f3f4f6;
            color: #1f2937;
            margin: 0;
            padding: 20px;
            line-height: 1.5;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding-bottom: 80px; /* Space for sticky footer */
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            padding: 2rem;
            margin-bottom: 2rem;
        }
        h2, h3, h4 { color: #111827; margin-top: 0; }
        h2 { border-bottom: 2px solid #e5e7eb; padding-bottom: 1rem; margin-bottom: 1.5rem; }
        
        /* Table Styles */
        .table-container { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; white-space: nowrap; }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background-color: #f9fafb; font-weight: 600; color: #4b5563; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background-color: #f9fafb; }
        
        /* Match Styles */
        .round-header {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #4b5563;
            font-weight: 600;
            margin-top: 1.5rem;
        }
        .round-header:first-child { margin-top: 0; }
        
        .round-badge {
            background: #e0e7ff;
            color: #4338ca;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            margin-right: 0.75rem;
        }
        .match-list { list-style: none; padding: 0; margin: 0; }
        .match-item {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .match-players {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex: 1;
            font-weight: 500;
            min-width: 200px;
        }
        .vs { color: #9ca3af; font-size: 0.875rem; margin: 0 0.5rem; }
        .score-inputs { display: flex; align-items: center; gap: 0.5rem; }
        input[type="number"] {
            width: 60px;
            padding: 0.5rem;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            text-align: center;
            font-size: 1rem;
            font-weight: 600;
        }
        input[type="number"]:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
        
        .freilos { color: #6b7280; font-style: italic; width: 100%; }
        
        /* Floating Action Button or Sticky Footer for Save */
        .save-bar {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 860px;
            background: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #e5e7eb;
            z-index: 100;
        }
        button.save-btn {
            background-color: #10b981;
            color: white;
            padding: 0.75rem 2rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
            transition: all 0.2s;
        }
        button.save-btn:hover { background-color: #059669; transform: translateY(-1px); }
        
        .back-link { color: #6b7280; text-decoration: none; font-size: 0.875rem; display: flex; align-items: center; font-weight: 500; }
        .back-link:hover { color: #111827; }
        
        @media (max-width: 600px) {
            .match-item { flex-direction: column; align-items: stretch; text-align: center; }
            .match-players { justify-content: center; margin-bottom: 0.5rem; }
            .score-inputs { justify-content: center; }
            .save-bar { flex-direction: column; gap: 1rem; bottom: 10px; width: calc(100% - 40px); }
            .save-btn { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>🏆 Live-Rangliste</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Team</th>
                            <th>Punkte</th>
                            <th>Spiele</th>
                            <th>Spielpunkte+</th>
                            <th>Spielpunkte-</th>
                            <th>Diff</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for i, row in enumerate(leaderboard, start=1) %}
                        <tr>
                            <td><strong>{{ i }}</strong></td>
                            <td>{{ row.name }}</td>
                            <td><strong>{{ row.points }}</strong></td>
                            <td>{{ row.played }}</td>
                            <td>{{ row.gf }}</td>
                            <td>{{ row.ga }}</td>
                            <td style="color: {{ 'green' if (row.gf - row.ga) > 0 else 'red' if (row.gf - row.ga) < 0 else 'inherit' }}">{{ row.gf - row.ga }}</td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <form method="post" action="{{ url_for('submit_scores') }}">
            <div class="card">
                <h2>📅 Aktuelle Runde (Runde {{ completed_rounds | length + 1 }})</h2>
                <div class="round-section">
                    <div class="match-list">
                    {% for m_idx, match in enumerate(current_round) %}
                        {% set a, b = match %}
                        {% set r_idx = completed_rounds | length %}
                        <div class="match-item">
                            {% if b == 'Freilos' %}
                                <div class="freilos"><strong>{{ a }}</strong> hat spielfrei</div>
                            {% else %}
                                <div class="match-players">
                                    <span>{{ a }}</span>
                                    <span class="vs">vs</span>
                                    <span>{{ b }}</span>
                                </div>
                                <div class="score-inputs">
                                    <input type="number" name="score_{{ r_idx }}_{{ m_idx }}_a" min=0 placeholder="0" value="{{ scores.get(key(r_idx,m_idx,'a'), '') }}" required>
                                    <span>:</span>
                                    <input type="number" name="score_{{ r_idx }}_{{ m_idx }}_b" min=0 placeholder="0" value="{{ scores.get(key(r_idx,m_idx,'b'), '') }}" required>
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                    </div>
                </div>
            </div>
            
            {% if completed_rounds %}
            <div class="card">
                <h2>📜 Vergangene Runden</h2>
                {% for r_idx, rnd in enumerate(completed_rounds) %}
                    <div class="round-section">
                        <div class="round-header">
                            <span class="round-badge">Runde {{ r_idx + 1 }}</span>
                        </div>
                        <div class="match-list">
                        {% for m_idx, match in enumerate(rnd) %}
                            {% set a, b = match %}
                            <div class="match-item" style="opacity: 0.8;">
                                {% if b == 'Freilos' %}
                                    <div class="freilos"><strong>{{ a }}</strong> hatte spielfrei</div>
                                {% else %}
                                    <div class="match-players">
                                        <span>{{ a }}</span>
                                        <span class="vs">vs</span>
                                        <span>{{ b }}</span>
                                    </div>
                                    <div class="score-inputs">
                                        <span style="font-weight: bold; font-size: 1.1rem;">{{ scores.get(key(r_idx,m_idx,'a'), '-') }}</span>
                                        <span>:</span>
                                        <span style="font-weight: bold; font-size: 1.1rem;">{{ scores.get(key(r_idx,m_idx,'b'), '-') }}</span>
                                    </div>
                                {% endif %}
                            </div>
                        {% endfor %}
                        </div>
                    </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="save-bar">
                <a href="{{ url_for('index') }}" class="back-link">← Neustart</a>
                <button type="submit" class="save-btn">Runde beenden & Nächste Runde</button>
            </div>
        </form>
    </div>
</body>
</html>
"""

def normalize_input(text):
    parts = []
    for line in text.splitlines():
        name = line.strip()
        if name:
            parts.append(name)
    return parts

def generate_next_round(players, past_pairings, stats):
    # Swiss System pairing
    # 1. Sort players by points (desc), then goal diff, then goals for
    sorted_players = sorted(players, key=lambda p: (
        -stats[p]['points'], 
        -(stats[p]['gf'] - stats[p]['ga']), 
        -stats[p]['gf'],
        random.random() # shuffle equals
    ))
    
    pairings = []
    used = set()
    
    # Handle odd number of players with a Bye (Freilos)
    # Give bye to the lowest ranked player who hasn't had one yet
    # For simplicity in this version, we just give it to the last one if odd
    if len(sorted_players) % 2 == 1:
        # Find lowest ranked player for bye
        bye_player = sorted_players.pop()
        pairings.append((bye_player, 'Freilos'))
        used.add(bye_player)

    while len(sorted_players) >= 2:
        p1 = sorted_players.pop(0)
        if p1 in used: continue
        
        # Find best opponent
        opponent = None
        for i, p2 in enumerate(sorted_players):
            # Check if they played before
            pair = tuple(sorted((p1, p2)))
            if pair not in past_pairings:
                opponent = p2
                sorted_players.pop(i)
                break
        
        if opponent is None:
            # Fallback: if everyone played everyone, just take the next best
            # This might happen in small tournaments with many rounds
            opponent = sorted_players.pop(0)
            
        pairings.append((p1, opponent))
        used.add(p1)
        used.add(opponent)
        
    return pairings

def init_state(players):
    session['players'] = players
    session['completed_rounds'] = [] # List of rounds (which are lists of matches)
    session['current_round'] = []    # The active round
    session['past_pairings'] = []    # List of tuples (a, b) sorted
    session['scores'] = {}           # Global scores dict
    session['stats'] = {p: {'points':0, 'played':0, 'gf':0, 'ga':0} for p in players}
    
    # Generate first round (Random)
    random.shuffle(players)
    first_round = []
    if len(players) % 2 == 1:
        bye = players.pop()
        first_round.append((bye, 'Freilos'))
    
    for i in range(0, len(players), 2):
        first_round.append((players[i], players[i+1]))
        
    session['current_round'] = first_round

def compute_leaderboard():
    stats = session.get('stats', {})
    # convert to list and sort: points desc, goal diff desc, gf desc, name asc
    lb = []
    for name, s in stats.items():
        lb.append({
            'name': name,
            'points': s['points'],
            'played': s['played'],
            'gf': s['gf'],
            'ga': s['ga']
        })
    lb.sort(key=lambda x: (-x['points'], -(x['gf'] - x['ga']), -x['gf'], x['name']))
    return lb

def key(r, m, side):
    return f"{r}_{m}_{side}"

def update_stats_with_round(round_idx, round_matches, scores):
    stats = session.get('stats')
    players = session.get('players')
    
    for m_idx, match in enumerate(round_matches):
        a, b = match
        if b == 'Freilos':
            stats[a]['points'] += 3
            stats[a]['played'] += 1
            continue
            
        ka = key(round_idx, m_idx, 'a')
        kb = key(round_idx, m_idx, 'b')
        
        if ka in scores and kb in scores:
            try:
                sa = int(scores[ka])
                sb = int(scores[kb])
                
                stats[a]['gf'] += sa
                stats[a]['ga'] += sb
                stats[b]['gf'] += sb
                stats[b]['ga'] += sa
                stats[a]['played'] += 1
                stats[b]['played'] += 1
                
                if sa > sb:
                    stats[a]['points'] += 3
                    stats[b]['points'] += 1
                elif sa == sb:
                    stats[a]['points'] += 2
                    stats[b]['points'] += 2
                else:
                    stats[a]['points'] += 1
                    stats[b]['points'] += 3
            except ValueError:
                pass
    session['stats'] = stats

@app.route('/')
def index():
    example = "Team A (Anna & Ben)\nTeam B (Carla & Dan)\nTeam C (Eva & Flo)"
    return render_template_string(TEMPLATE_INDEX, example=example)

@app.route('/schedule', methods=['POST'])
def schedule():
    text = request.form.get('players', '')
    players = normalize_input(text)
    seen = set()
    uniq = []
    for p in players:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    if len(uniq) < 2:
        return """
        <!doctype html>
        <html lang="de">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Fehler</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; color: #1f2937; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center; max-width: 400px; }
                h3 { color: #ef4444; margin-top: 0; }
                a { color: #2563eb; text-decoration: none; font-weight: 600; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="card">
                <h3>⚠️ Zu wenige Teams</h3>
                <p>Es werden mindestens 2 unterschiedliche Teams benötigt, um ein Turnier zu starten.</p>
                <p><a href='/'>Zurück zur Eingabe</a></p>
            </div>
        </body>
        </html>
        """
    init_state(uniq)
    return redirect(url_for('show_schedule'))

@app.route('/schedule_view')
def show_schedule():
    if 'players' not in session:
        return redirect(url_for('index'))
        
    completed_rounds = session.get('completed_rounds', [])
    current_round = session.get('current_round', [])
    scores = session.get('scores', {})
    leaderboard = compute_leaderboard()
    
    return render_template_string(
        TEMPLATE_SCHEDULE, 
        completed_rounds=completed_rounds, 
        current_round=current_round, 
        scores=scores, 
        leaderboard=leaderboard, 
        key=key, 
        enumerate=enumerate
    )

@app.route('/submit_scores', methods=['POST'])
def submit_scores():
    current_round = session.get('current_round', [])
    completed_rounds = session.get('completed_rounds', [])
    scores = session.get('scores', {})
    
    # Determine the index for the current round (it's the next one after completed ones)
    current_round_idx = len(completed_rounds)
    
    # Read scores for current round
    all_scores_entered = True
    for m_idx, match in enumerate(current_round):
        a, b = match
        if b == 'Freilos':
            continue
            
        ka = key(current_round_idx, m_idx, 'a')
        kb = key(current_round_idx, m_idx, 'b')
        
        va = request.form.get(f"score_{current_round_idx}_{m_idx}_a", "").strip()
        vb = request.form.get(f"score_{current_round_idx}_{m_idx}_b", "").strip()
        
        if va == "" or vb == "":
            all_scores_entered = False
        else:
            scores[ka] = va
            scores[kb] = vb
            
    session['scores'] = scores
    
    if not all_scores_entered:
        # Just save partial scores, don't advance
        return redirect(url_for('show_schedule'))
        
    # If all scores entered, finalize round
    update_stats_with_round(current_round_idx, current_round, scores)
    
    # Archive current round
    completed_rounds.append(current_round)
    session['completed_rounds'] = completed_rounds
    
    # Update past pairings
    past_pairings = session.get('past_pairings', [])
    for a, b in current_round:
        if b != 'Freilos':
            past_pairings.append(tuple(sorted((a, b))))
    session['past_pairings'] = past_pairings
    
    # Generate next round
    players = session.get('players')
    stats = session.get('stats')
    next_round = generate_next_round(list(players), set(past_pairings), stats)
    session['current_round'] = next_round
    
    return redirect(url_for('show_schedule'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
