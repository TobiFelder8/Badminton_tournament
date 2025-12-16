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
    <title>Matchmaking - Spieler</title>
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
        <h3>🏸 Badminton Matchmaker</h3>
        <p class="hint">Trage die Namen der Spieler ein (einer pro Zeile)</p>
        <form method=post action="{{ url_for('schedule') }}">
            <textarea name=players placeholder="Max Mustermann&#10;Erika Musterfrau&#10;...">{{ example }}</textarea>
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
                            <th>Spieler</th>
                            <th>Punkte</th>
                            <th>Spiele</th>
                            <th>Tore+</th>
                            <th>Tore-</th>
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
                <h2>📅 Spielplan ({{ rounds | length }} Runden)</h2>
                {% for r_idx, rnd in enumerate(rounds) %}
                    <div class="round-section">
                        <div class="round-header">
                            <span class="round-badge">Runde {{ r_idx + 1 }}</span>
                        </div>
                        <div class="match-list">
                        {% for m_idx, match in enumerate(rnd) %}
                            {% set a, b = match %}
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
                                        <input type="number" name="score_{{ r_idx }}_{{ m_idx }}_a" min=0 placeholder="0" value="{{ scores.get(key(r_idx,m_idx,'a'), '') }}">
                                        <span>:</span>
                                        <input type="number" name="score_{{ r_idx }}_{{ m_idx }}_b" min=0 placeholder="0" value="{{ scores.get(key(r_idx,m_idx,'b'), '') }}">
                                    </div>
                                {% endif %}
                            </div>
                        {% endfor %}
                        </div>
                    </div>
                {% endfor %}
            </div>
            
            <div class="save-bar">
                <a href="{{ url_for('index') }}" class="back-link">← Zurück zum Start</a>
                <button type="submit" class="save-btn">Ergebnisse speichern</button>
            </div>
        </form>
    </div>
</body>
</html>
"""

def normalize_input(text):
    parts = []
    for line in text.splitlines():
        for sub in line.split(','):
            name = sub.strip()
            if name:
                parts.append(name)
    return parts

def round_robin(players):
    n = len(players)
    if n % 2 == 1:
        players = players + ['Freilos']
        n += 1
    half = n // 2
    players_list = list(players)
    rounds = []
    for r in range(n - 1):
        pairings = []
        for i in range(half):
            a = players_list[i]
            b = players_list[n - 1 - i]
            pairings.append((a, b))
        rounds.append(pairings)
        players_list = [players_list[0]] + players_list[-1:] + players_list[1:-1]
    return rounds

def make_double_round_robin(players):
    base_rounds = round_robin(players)
    mirrored = []
    for rnd in base_rounds:
        mirrored.append([(b,a) for (a,b) in rnd])
    combined = []
    for a, b in zip(base_rounds, mirrored):
        combined.append(a)
        combined.append(b)
    # shuffle blocks to reduce repeats
    blocks = [combined[i:i+2] for i in range(0, len(combined), 2)]
    random.shuffle(blocks)
    new_rounds = []
    for block in blocks:
        for rnd in block:
            new_rounds.append(rnd)
    return new_rounds

def init_state(players):
    session['players'] = players
    session['rounds'] = make_double_round_robin(players)
    # scores: dict key "r_m_side" -> integer (e.g., "0_1_a")
    session['scores'] = {}
    # stats for leaderboard
    session['stats'] = {p: {'points':0, 'played':0, 'gf':0, 'ga':0} for p in players}

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

def apply_scores_to_stats():
    # reset stats and recompute from scratch from session['scores']
    players = session.get('players', [])
    rounds = session.get('rounds', [])
    scores = session.get('scores', {})
    stats = {p: {'points':0, 'played':0, 'gf':0, 'ga':0} for p in players}
    for r_idx, rnd in enumerate(rounds):
        for m_idx, match in enumerate(rnd):
            a, b = match
            if b == 'Freilos':
                # Freilos: keine Änderung ausser ev. give 3 points? We'll give 3 points to bye
                stats[a]['points'] += 3
                continue
            ka = key(r_idx, m_idx, 'a')
            kb = key(r_idx, m_idx, 'b')
            if ka in scores and kb in scores:
                try:
                    sa = int(scores[ka])
                    sb = int(scores[kb])
                except ValueError:
                    continue
                # update gf/ga/played
                stats[a]['gf'] += sa
                stats[a]['ga'] += sb
                stats[b]['gf'] += sb
                stats[b]['ga'] += sa
                stats[a]['played'] += 1
                stats[b]['played'] += 1
                # assign points: win 3, draw 2, loss 1
                if sa > sb:
                    stats[a]['points'] += 3
                    stats[b]['points'] += 1
                elif sa == sb:
                    stats[a]['points'] += 2
                    stats[b]['points'] += 2
                else:
                    stats[a]['points'] += 1
                    stats[b]['points'] += 3
    session['stats'] = stats

@app.route('/')
def index():
    example = "Anna\nBenedikt\nCarla\nDaniel\nEva\nFelix"
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
                <h3>⚠️ Zu wenige Spieler</h3>
                <p>Es werden mindestens 2 unterschiedliche Spieler benötigt, um ein Turnier zu starten.</p>
                <p><a href='/'>Zurück zur Eingabe</a></p>
            </div>
        </body>
        </html>
        """
    init_state(uniq)
    return redirect(url_for('show_schedule'))

@app.route('/schedule_view')
def show_schedule():
    rounds = session.get('rounds', [])
    scores = session.get('scores', {})
    apply_scores_to_stats()
    leaderboard = compute_leaderboard()
    # helper for template to fetch keys
    return render_template_string(TEMPLATE_SCHEDULE, rounds=rounds, scores=scores, leaderboard=leaderboard, key=key, enumerate=enumerate)

@app.route('/submit_scores', methods=['POST'])
def submit_scores():
    rounds = session.get('rounds', [])
    scores = session.get('scores', {})
    # read all numeric inputs and store
    for r_idx, rnd in enumerate(rounds):
        for m_idx, match in enumerate(rnd):
            a, b = match
            if b == 'Freilos':
                continue
            ka = key(r_idx, m_idx, 'a')
            kb = key(r_idx, m_idx, 'b')
            va = request.form.get(f"score_{r_idx}_{m_idx}_a", "").strip()
            vb = request.form.get(f"score_{r_idx}_{m_idx}_b", "").strip()
            if va != "":
                scores[ka] = va
            if vb != "":
                scores[kb] = vb
    session['scores'] = scores
    apply_scores_to_stats()
    return redirect(url_for('show_schedule'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
