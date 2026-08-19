from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from pathlib import Path
from uuid import uuid4
from werkzeug.utils import secure_filename

from database import (
    get_db,
    init_db,
    is_voting_enabled,
    set_setting,
    fetch_parties,
    save_party,
    toggle_party_status,
    save_complaint,
    fetch_complaints,
    update_complaint_status,
)
from blockchain import Blockchain
from utils import (
    hash_text,
    is_valid_aadhaar,
    is_valid_mobile,
    is_valid_unique_id,
    is_18_plus,
    generate_unique_id,
    normalize_mobile,
    utc_now_str,
)
from otp_service import create_otp, verify_otp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-me-for-production')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
UPLOAD_DIR = Path(__file__).resolve().parent / 'static' / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_UPLOADS = {'.png', '.jpg', '.jpeg', '.webp'}

blockchain = None


def active_parties():
    return [dict(r) for r in fetch_parties(active_only=True)]


def all_parties():
    return [dict(r) for r in fetch_parties(active_only=False)]


@app.before_request
def setup_once():
    global blockchain
    if blockchain is None:
        init_db()
        blockchain = Blockchain()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/candidate-info')
def candidate_info_page():
    voter = session.get('verified_voter')
    if not voter:
        return redirect(url_for('login_page'))
    return render_template('candidate_info.html', parties=active_parties())


@app.route('/complaints', methods=['GET', 'POST'])
def complaint_page():
    voter = session.get('verified_voter')
    if not voter:
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if not subject or not message:
            return render_template('complaint.html', success_message='', error='Please fill subject and message')
        save_complaint(voter['unique_id'], voter['full_name'], voter['mobile'], subject, message, utc_now_str())
        return render_template('complaint.html', success_message='Complaint sent successfully to admin panel', error='')

    return render_template('complaint.html', success_message='', error='')


@app.route('/dashboard')
def dashboard_page():
    voter = session.get('verified_voter')
    if not voter:
        return redirect(url_for('login_page'))

    db = get_db()
    vote_count = db.execute('SELECT COUNT(*) AS c FROM votes WHERE unique_id=?', (voter['unique_id'],)).fetchone()['c']
    total_votes = db.execute('SELECT COUNT(*) AS c FROM votes').fetchone()['c']
    db.close()
    return render_template(
        'dashboard.html',
        voter=voter,
        vote_count=vote_count,
        total_votes=total_votes,
        parties=active_parties(),
        voting_enabled=is_voting_enabled(),
        status_message=request.args.get('msg', ''),
    )


@app.route('/vote-verify')
def vote_verify_page():
    voter = session.get('verified_voter')
    if not voter:
        return redirect(url_for('login_page'))
    if not is_voting_enabled():
        return redirect(url_for('dashboard_page', msg='Voting is currently stopped by admin'))
    return render_template('vote_verify.html', voter=voter)


@app.route('/vote-portal')
def vote_portal_page():
    voter = session.get('verified_voter')
    if not voter or not session.get('vote_gate_passed'):
        return redirect(url_for('vote_verify_page'))
    if not is_voting_enabled():
        session.pop('vote_gate_passed', None)
        return redirect(url_for('dashboard_page', msg='Voting is currently stopped by admin'))

    db = get_db()
    already = db.execute('SELECT 1 FROM votes WHERE unique_id=?', (voter['unique_id'],)).fetchone()
    db.close()
    if already:
        session.pop('vote_gate_passed', None)
        return redirect(url_for('dashboard_page', msg='You have already voted'))
    return render_template('vote_portal.html', voter=voter, parties=active_parties())


@app.route('/success')
def success_page():
    return render_template('success.html', registration=session.pop('registration_success', None), vote_success=session.pop('vote_success', None))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/api/register/send-otp', methods=['POST'])
def register_send_otp():
    data = request.get_json(force=True)
    required_fields = ['full_name', 'dob', 'mobile', 'aadhaar', 'father_name', 'state', 'district', 'mandal', 'pincode', 'assembly_code', 'village_name']
    for field in required_fields:
        if not str(data.get(field, '')).strip():
            return jsonify(success=False, message=f'Missing field: {field}'), 400

    full_name = str(data['full_name']).strip()
    dob = str(data['dob']).strip()
    mobile = normalize_mobile(str(data['mobile']).strip())
    aadhaar = str(data['aadhaar']).strip()
    father_name = str(data['father_name']).strip()
    state = str(data['state']).strip()
    district = str(data['district']).strip()
    mandal = str(data['mandal']).strip()
    pincode = str(data['pincode']).strip()
    assembly_code = str(data['assembly_code']).strip().upper()
    village_name = str(data['village_name']).strip()

    if not is_valid_mobile(mobile):
        return jsonify(success=False, message='Enter a valid 10-digit mobile number'), 400
    if not is_valid_aadhaar(aadhaar):
        return jsonify(success=False, message='Enter a valid 12-digit Aadhaar number'), 400
    if not (pincode.isdigit() and len(pincode) == 6):
        return jsonify(success=False, message='Enter a valid 6-digit pincode'), 400
    try:
        if not is_18_plus(dob):
            return jsonify(success=False, message='User must be 18 years or older'), 400
    except Exception:
        return jsonify(success=False, message='Date of birth format is invalid'), 400

    aadhaar_hash = hash_text(aadhaar)
    db = get_db()
    exists = db.execute('SELECT 1 FROM registrations WHERE aadhaar_hash=?', (aadhaar_hash,)).fetchone()
    db.close()
    if exists:
        return jsonify(success=False, message='This Aadhaar is already registered'), 400

    otp_result = create_otp(mobile)
    session['register_data'] = {
        'full_name': full_name,
        'dob': dob,
        'mobile': mobile,
        'aadhaar': aadhaar,
        'father_name': father_name,
        'state': state,
        'district': district,
        'mandal': mandal,
        'pincode': pincode,
        'assembly_code': assembly_code,
        'village_name': village_name,
    }
    return jsonify(success=True, message=otp_result['message'])


@app.route('/api/register/resend-otp', methods=['POST'])
def register_resend_otp():
    reg_data = session.get('register_data')
    if not reg_data:
        return jsonify(success=False, message='Please fill the form first'), 400
    otp_result = create_otp(reg_data['mobile'])
    return jsonify(success=True, message=otp_result['message'])


@app.route('/api/register/complete', methods=['POST'])
def register_complete():
    data = request.get_json(force=True)
    otp = str(data.get('otp', '')).strip()
    reg_data = session.get('register_data')
    if not reg_data:
        return jsonify(success=False, message='Registration session expired'), 400
    if not verify_otp(reg_data['mobile'], otp):
        return jsonify(success=False, message='Invalid OTP'), 400

    db = get_db()
    cur = db.cursor()

    def checker(candidate):
        return cur.execute('SELECT 1 FROM registrations WHERE unique_id=?', (candidate,)).fetchone() is None

    unique_id = generate_unique_id(checker)
    try:
        cur.execute(
            '''
            INSERT INTO registrations (
                unique_id, aadhaar_hash, full_name, dob, mobile, father_name,
                state, district, mandal, pincode, assembly_code, village_name, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                unique_id,
                hash_text(reg_data['aadhaar']),
                reg_data['full_name'],
                reg_data['dob'],
                reg_data['mobile'],
                reg_data['father_name'],
                reg_data['state'],
                reg_data['district'],
                reg_data['mandal'],
                reg_data['pincode'],
                reg_data['assembly_code'],
                reg_data['village_name'],
                utc_now_str(),
            )
        )
        db.commit()
    except Exception as e:
        db.close()
        return jsonify(success=False, message=f'Registration failed: {e}'), 500
    db.close()

    session.pop('register_data', None)
    session['registration_success'] = {
        'full_name': reg_data['full_name'],
        'unique_id': unique_id,
        'state': reg_data['state'],
        'district': reg_data['district'],
        'assembly_code': reg_data['assembly_code'],
        'village_name': reg_data['village_name'],
    }
    return jsonify(success=True, message='Registration completed successfully', unique_id=unique_id, redirect=url_for('success_page'))


@app.route('/api/login/send-otp', methods=['POST'])
def login_send_otp():
    data = request.get_json(force=True)
    unique_id = str(data.get('unique_id', '')).strip()
    mobile = normalize_mobile(str(data.get('mobile', '')).strip())

    if not is_valid_unique_id(unique_id):
        return jsonify(success=False, message='Enter valid 9-digit voter ID'), 400
    if not is_valid_mobile(mobile):
        return jsonify(success=False, message='Enter valid mobile number'), 400

    db = get_db()
    voter = db.execute('SELECT * FROM registrations WHERE unique_id=? AND mobile=?', (unique_id, mobile)).fetchone()
    db.close()
    if not voter:
        return jsonify(success=False, message='Invalid voter ID or mobile number'), 400

    otp_result = create_otp(mobile)
    session['login_mobile'] = mobile
    session['login_candidate'] = dict(voter)
    return jsonify(success=True, message=otp_result['message'])


@app.route('/api/login/resend-otp', methods=['POST'])
def login_resend_otp():
    mobile = session.get('login_mobile')
    if not mobile:
        return jsonify(success=False, message='Please start login first'), 400
    otp_result = create_otp(mobile)
    return jsonify(success=True, message=otp_result['message'])


@app.route('/api/login/verify', methods=['POST'])
def login_verify():
    data = request.get_json(force=True)
    otp = str(data.get('otp', '')).strip()
    mobile = session.get('login_mobile')
    candidate = session.get('login_candidate')
    if not mobile or not candidate:
        return jsonify(success=False, message='Login session expired'), 400
    if not verify_otp(mobile, otp):
        return jsonify(success=False, message='Invalid OTP'), 400
    session['verified_voter'] = candidate
    return jsonify(success=True, message='Login verified successfully', redirect=url_for('dashboard_page'))


@app.route('/api/vote/send-otp', methods=['POST'])
def vote_send_otp():
    voter = session.get('verified_voter')
    if not voter:
        return jsonify(success=False, message='Unauthorized'), 401
    if not is_voting_enabled():
        return jsonify(success=False, message='Voting is currently stopped by admin'), 403
    otp_result = create_otp(voter['mobile'])
    return jsonify(success=True, message=otp_result['message'])


@app.route('/api/vote/verify', methods=['POST'])
def vote_verify():
    voter = session.get('verified_voter')
    if not voter:
        return jsonify(success=False, message='Unauthorized'), 401

    data = request.get_json(force=True)
    unique_id = str(data.get('unique_id', '')).strip()
    otp = str(data.get('otp', '')).strip()
    if unique_id != voter['unique_id']:
        return jsonify(success=False, message='Voter ID does not match your profile'), 400
    if not verify_otp(voter['mobile'], otp):
        return jsonify(success=False, message='Invalid OTP'), 400
    session['vote_gate_passed'] = True
    return jsonify(success=True, message='Verification completed', redirect=url_for('vote_portal_page'))


@app.route('/api/vote', methods=['POST'])
def submit_vote():
    voter = session.get('verified_voter')
    if not voter or not session.get('vote_gate_passed'):
        return jsonify(success=False, error='Unauthorized'), 401
    if not is_voting_enabled():
        return jsonify(success=False, error='Voting is currently stopped by admin'), 403

    data = request.get_json(force=True)
    party = str(data.get('party', '')).strip().upper()
    chosen = next((p for p in active_parties() if p['party'] == party), None)
    if not chosen:
        return jsonify(success=False, error='Invalid or locked party selection'), 400

    db = get_db()
    already = db.execute('SELECT 1 FROM votes WHERE unique_id=?', (voter['unique_id'],)).fetchone()
    if already:
        db.close()
        return jsonify(success=False, error='Already voted'), 400

    block_hash = blockchain.add_vote_block({
        'unique_id': voter['unique_id'],
        'party': chosen['party'],
        'candidate_name': chosen['candidate'],
        'assembly_code': voter['assembly_code'],
        'area': {
            'state': voter['state'],
            'district': voter['district'],
            'mandal': voter['mandal'],
            'village_name': voter['village_name'],
        }
    })

    db.execute(
        '''
        INSERT INTO votes (
            unique_id, aadhaar_hash, state, district, mandal, village_name,
            assembly_code, party, candidate_name, voted_at, block_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            voter['unique_id'], voter['aadhaar_hash'], voter['state'], voter['district'],
            voter['mandal'], voter['village_name'], voter['assembly_code'], chosen['party'],
            chosen['candidate'], utc_now_str(), block_hash,
        )
    )
    db.commit()
    db.close()

    session['vote_success'] = {
        'full_name': voter['full_name'],
        'unique_id': voter['unique_id'],
        'party': chosen['party'],
        'candidate_name': chosen['candidate'],
        'assembly_code': voter['assembly_code'],
        'block_hash': block_hash,
    }
    session.pop('vote_gate_passed', None)
    session.pop('verified_voter', None)
    session.pop('login_mobile', None)
    session.pop('login_candidate', None)
    return jsonify(success=True, message='Vote submitted successfully', redirect=url_for('login_page'))


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_ok'] = True
            return redirect(url_for('admin_page'))
        return render_template('admin_login.html', error='Invalid username or password')
    return render_template('admin_login.html', error=None)


@app.route('/admin')
def admin_page():
    if not session.get('admin_ok'):
        return redirect(url_for('admin_login_page'))

    db = get_db()
    results = db.execute('SELECT party, COUNT(*) AS count FROM votes GROUP BY party ORDER BY count DESC, party ASC').fetchall()
    total_registrations = db.execute('SELECT COUNT(*) AS count FROM registrations').fetchone()['count']
    total_votes = db.execute('SELECT COUNT(*) AS count FROM votes').fetchone()['count']
    assembly_summary = db.execute('SELECT assembly_code, COUNT(*) AS count FROM votes GROUP BY assembly_code ORDER BY assembly_code ASC').fetchall()
    registrations = db.execute('SELECT unique_id, full_name, state, district, assembly_code, mandal, village_name, created_at FROM registrations ORDER BY created_at DESC').fetchall()
    votes = db.execute('SELECT unique_id, party, candidate_name, assembly_code, state, district, mandal, village_name, voted_at FROM votes ORDER BY id DESC').fetchall()
    db.close()
    return render_template(
        'admin.html',
        total_registrations=total_registrations,
        total_votes=total_votes,
        results=results,
        assembly_summary=assembly_summary,
        registrations=registrations,
        votes=votes,
        voting_enabled=is_voting_enabled(),
        parties=all_parties(),
        complaints=fetch_complaints(),
    )


@app.route('/admin/toggle-voting', methods=['POST'])
def admin_toggle_voting():
    if not session.get('admin_ok'):
        return redirect(url_for('admin_login_page'))
    action = request.form.get('action', '').strip().lower()
    if action == 'start':
        set_setting('voting_enabled', '1')
    elif action == 'stop':
        set_setting('voting_enabled', '0')
    return redirect(url_for('admin_page'))


@app.route('/admin/party/save', methods=['POST'])
def admin_save_party():
    if not session.get('admin_ok'):
        return redirect(url_for('admin_login_page'))

    party = request.form.get('party', '').strip().upper()
    candidate = request.form.get('candidate', '').strip()
    symbol = request.form.get('symbol', '').strip() or '•'
    photo = request.form.get('photo', '').strip()[:4].upper() or candidate[:2].upper() or 'NA'
    is_active = 1 if request.form.get('is_active') == 'on' else 0
    photo_path = None

    upload = request.files.get('party_image')
    if upload and upload.filename:
        suffix = Path(upload.filename).suffix.lower()
        if suffix in ALLOWED_UPLOADS:
            safe_name = secure_filename(f"{party.lower()}_{uuid4().hex[:8]}{suffix}")
            target = UPLOAD_DIR / safe_name
            upload.save(target)
            photo_path = f"uploads/{safe_name}"

    if party and candidate:
        save_party(party, candidate, symbol, photo, photo_path, is_active)
    return redirect(url_for('admin_page'))


@app.route('/admin/party/toggle/<int:party_id>', methods=['POST'])
def admin_toggle_party(party_id: int):
    if not session.get('admin_ok'):
        return redirect(url_for('admin_login_page'))
    toggle_party_status(party_id)
    return redirect(url_for('admin_page'))


@app.route('/admin/complaint/<int:complaint_id>/status', methods=['POST'])
def admin_complaint_status(complaint_id: int):
    if not session.get('admin_ok'):
        return redirect(url_for('admin_login_page'))
    status = request.form.get('status', 'Resolved').strip() or 'Resolved'
    update_complaint_status(complaint_id, status)
    return redirect(url_for('admin_page'))


@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_ok', None)
    return redirect(url_for('admin_login_page'))


if __name__ == '__main__':
    app.run(debug=True)
