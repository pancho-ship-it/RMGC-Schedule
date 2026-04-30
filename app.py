from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os, json, requests as req

app = Flask(__name__)
app.secret_key = 'rmgc-schedule-secret-2026'

USERS = {
    'greens':   {'password': 'LB2026',      'role': 'edit'},
    'admin':    {'password': 'rmgc2026',    'role': 'read'},
    'manager':  {'password': 'gm2026',      'role': 'read'},
    'chairman': {'password': '3putt2026',   'role': 'read'},
    'deputy':   {'password': 'JP2026',      'role': 'read'},
}

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

def sb_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

def sb_get(key):
    if not SUPABASE_URL:
        return None
    try:
        r = req.get(f'{SUPABASE_URL}/rest/v1/rmgc_data?id=eq.{key}&select=payload',
                    headers=sb_headers(), timeout=5)
        data = r.json()
        if data:
            return data[0]['payload']
    except:
        pass
    return None

def sb_set(key, payload):
    if not SUPABASE_URL:
        return False
    try:
        # upsert
        r = req.post(
            f'{SUPABASE_URL}/rest/v1/rmgc_data',
            headers={**sb_headers(), 'Prefer': 'resolution=merge-duplicates,return=representation'},
            json={'id': key, 'payload': payload},
            timeout=5
        )
        return r.status_code in (200, 201)
    except:
        return False

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html',
                           username=session['user'],
                           role=session['role'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        u = request.form.get('username', '').strip().lower()
        p = request.form.get('password', '').strip()
        if u in USERS and USERS[u]['password'] == p:
            session['user'] = u
            session['role'] = USERS[u]['role']
            return redirect(url_for('index'))
        error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── API: ticks ───────────────────────────────────────────────────────────────

@app.route('/api/ticks', methods=['GET'])
def get_ticks():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 401
    data = sb_get('ticks') or {}
    return jsonify(data)

@app.route('/api/ticks', methods=['POST'])
def save_ticks():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 401
    if session.get('role') != 'edit':
        return jsonify({'error': 'read-only'}), 403
    body = request.get_json()
    sb_set('ticks', body)
    return jsonify({'ok': True})

# ── API: notes ───────────────────────────────────────────────────────────────

@app.route('/api/notes', methods=['GET'])
def get_notes():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 401
    data = sb_get('notes') or {}
    return jsonify(data)

@app.route('/api/notes', methods=['POST'])
def save_notes():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 401
    if session.get('role') != 'edit':
        return jsonify({'error': 'read-only'}), 403
    body = request.get_json()
    sb_set('notes', body)
    return jsonify({'ok': True})

@app.route('/api/debug')
def debug():
    ok = False
    msg = 'No Supabase configured'
    if SUPABASE_URL:
        try:
            r = req.get(f'{SUPABASE_URL}/rest/v1/rmgc_data?select=id&limit=1',
                        headers=sb_headers(), timeout=5)
            ok = r.status_code == 200
            msg = f'Connected — {len(r.json())} row(s)' if ok else r.text
        except Exception as e:
            msg = str(e)
    return jsonify({'supabase_ok': ok, 'supabase_msg': msg})

if __name__ == '__main__':
    app.run(debug=True)
