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
<title>Matchmaking - Spieler</title>
<h3>Spieler eintragen</h3>
<form method=post action="{{ url_for('schedule') }}">
  <textarea name=players rows=12 cols=40 placeholder="Ein Name pro Zeile oder durch Komma getrennt">{{ example }}</textarea><br>
  <button type=submit>Weiter</button>
</form>
"""

TEMPLATE_SCHEDULE = """
<!doctype html>
<title>Spielplan & Live-Rangliste</title>
<h2>Live-Rangliste</h2>
<table border=1 cellpadding=4>
  <tr><th>Rang</th><th>Spieler</th><th>Punkte</th><th>Spiele</th><th>Tore+</th><th>Tore-</th><th>Diff</th></tr>
  {% for i, row in enumerate(leaderboard, start=1) %}
    <tr>
      <td>{{ i }}</td>
      <td>{{ row.name }}</td>
      <td>{{ row.points }}</td>
      <td>{{ row.played }}</td>
      <td>{{ row.gf }}</td>
      <td>{{ row.ga }}</td>
      <td>{{ row.gf - row.ga }}</td>
    </tr>
  {% endfor %}
</table>

<hr>
<h3>Spielplan ({{ rounds | length }} Runden)</h3>
<form method="post" action="{{ url_for('submit_scores') }}">
{% for r_idx, rnd in enumerate(rounds) %}
  <h4>Runde {{ r_idx + 1 }}</h4>
  <ul>
  {% for m_idx, match in enumerate(rnd) %}
    {% set a, b = match %}
    <li>
      {% if b == 'Freilos' %}
        <strong>{{ a }}</strong> hat ein Freilos
      {% else %}
        {{ a }} <input type="number" name="score_{{ r_idx }}_{{ m_idx }}_a" min=0 value="{{ scores.get(key(r_idx,m_idx,'a'), '') }}"> :
        <input type="number" name="score_{{ r_idx }}_{{ m_idx }}_b" min=0 value="{{ scores.get(key(r_idx,m_idx,'b'), '') }}"> {{ b }}
        <small> (Id: {{ r_idx }}-{{ m_idx }})</small>
      {% endif %}
    </li>
  {% endfor %}
  </ul>
{% endfor %}
  <button type="submit">Punkte speichern</button>
</form>

<p><a href="{{ url_for('index') }}">Zurück</a></p>
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
        return "<p>Mindestens 2 unterschiedliche Spieler nötig. <a href='/'>Zurück</a></p>"
    init_state(uniq)
    return redirect(url_for('show_schedule'))

@app.route('/schedule_view')
def show_schedule():
    rounds = session.get('rounds', [])
    scores = session.get('scores', {})
    apply_scores_to_stats()
    leaderboard = compute_leaderboard()
    # helper for template to fetch keys
    return render_template_string(TEMPLATE_SCHEDULE, rounds=rounds, scores=scores, leaderboard=leaderboard, key=key)

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
