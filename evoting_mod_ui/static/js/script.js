function setMessage(id, text, ok = true) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.classList.remove('error');
  if (!ok) el.classList.add('error');
}

function digitsOnly(id, maxLen) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('input', () => {
    el.value = el.value.replace(/\D/g, '').slice(0, maxLen);
  });
}

['reg_aadhaar','reg_mobile','reg_pincode','reg_otp','login_unique_id','login_mobile','login_otp','vote_unique_id','vote_otp']
  .forEach(id => digitsOnly(id, id.includes('aadhaar') ? 12 : id.includes('pincode') ? 6 : id.includes('unique_id') ? 9 : id.includes('mobile') ? 10 : 6));

function regPayload() {
  return {
    full_name: document.getElementById('reg_full_name')?.value.trim(),
    dob: document.getElementById('reg_dob')?.value,
    aadhaar: document.getElementById('reg_aadhaar')?.value.trim(),
    mobile: document.getElementById('reg_mobile')?.value.trim(),
    father_name: document.getElementById('reg_father_name')?.value.trim(),
    state: document.getElementById('reg_state')?.value.trim(),
    district: document.getElementById('reg_district')?.value.trim(),
    mandal: document.getElementById('reg_mandal')?.value.trim(),
    pincode: document.getElementById('reg_pincode')?.value.trim(),
    assembly_code: document.getElementById('reg_assembly_code')?.value.trim(),
    village_name: document.getElementById('reg_village_name')?.value.trim()
  };
}

function validateRegClient() {
  const data = regPayload();
  if (!/^\d{12}$/.test(data.aadhaar) || data.aadhaar === '000000000000') return 'Enter a valid 12-digit Aadhaar number';
  if (!/^\d{10}$/.test(data.mobile) || data.mobile === '0000000000') return 'Enter a valid 10-digit mobile number';
  if (!/^\d{6}$/.test(data.pincode)) return 'Enter a valid 6-digit pincode';
  return '';
}

async function postJson(url, payload) {
  const res = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const data = await res.json();
  return {res, data};
}

const sendRegOtpBtn = document.getElementById('sendRegOtpBtn');
if (sendRegOtpBtn) sendRegOtpBtn.addEventListener('click', async () => {
  const error = validateRegClient();
  if (error) return setMessage('registerMessage', error, false);
  try {
    const {res, data} = await postJson('/api/register/send-otp', regPayload());
    setMessage('registerMessage', data.message || 'OTP sent', res.ok && data.success);
  } catch {
    setMessage('registerMessage', 'Server connection failed', false);
  }
});

const resendRegOtpBtn = document.getElementById('resendRegOtpBtn');
if (resendRegOtpBtn) resendRegOtpBtn.addEventListener('click', async () => {
  try {
    const {res, data} = await postJson('/api/register/resend-otp', {});
    setMessage('registerMessage', data.message || 'OTP resent', res.ok && data.success);
  } catch {
    setMessage('registerMessage', 'Server connection failed', false);
  }
});

const completeRegBtn = document.getElementById('completeRegBtn');
if (completeRegBtn) completeRegBtn.addEventListener('click', async () => {
  const otp = document.getElementById('reg_otp').value.trim();
  if (!/^\d{6}$/.test(otp)) return setMessage('registerMessage', 'Enter valid 6-digit OTP', false);
  try {
    const {res, data} = await postJson('/api/register/complete', {otp});
    setMessage('registerMessage', data.message || 'Completed', res.ok && data.success);
    if (res.ok && data.success && data.redirect) window.location.href = data.redirect;
  } catch {
    setMessage('registerMessage', 'Server connection failed', false);
  }
});

const sendLoginOtpBtn = document.getElementById('sendLoginOtpBtn');
if (sendLoginOtpBtn) sendLoginOtpBtn.addEventListener('click', async () => {
  const unique_id = document.getElementById('login_unique_id').value.trim();
  const mobile = document.getElementById('login_mobile').value.trim();
  if (!/^\d{9}$/.test(unique_id)) return setMessage('loginMessage', 'Enter valid 9-digit voter ID', false);
  if (!/^\d{10}$/.test(mobile) || mobile === '0000000000') return setMessage('loginMessage', 'Enter valid mobile number', false);
  try {
    const {res, data} = await postJson('/api/login/send-otp', {unique_id, mobile});
    setMessage('loginMessage', data.message || 'OTP sent', res.ok && data.success);
  } catch {
    setMessage('loginMessage', 'Server connection failed', false);
  }
});

const resendLoginOtpBtn = document.getElementById('resendLoginOtpBtn');
if (resendLoginOtpBtn) resendLoginOtpBtn.addEventListener('click', async () => {
  try {
    const {res, data} = await postJson('/api/login/resend-otp', {});
    setMessage('loginMessage', data.message || 'OTP resent', res.ok && data.success);
  } catch {
    setMessage('loginMessage', 'Server connection failed', false);
  }
});

const verifyLoginBtn = document.getElementById('verifyLoginBtn');
if (verifyLoginBtn) verifyLoginBtn.addEventListener('click', async () => {
  const otp = document.getElementById('login_otp').value.trim();
  if (!/^\d{6}$/.test(otp)) return setMessage('loginMessage', 'Enter valid 6-digit OTP', false);
  try {
    const {res, data} = await postJson('/api/login/verify', {otp});
    setMessage('loginMessage', data.message || 'Login verified', res.ok && data.success);
    if (res.ok && data.success && data.redirect) window.location.href = data.redirect;
  } catch {
    setMessage('loginMessage', 'Server connection failed', false);
  }
});

const sendVoteOtpBtn = document.getElementById('sendVoteOtpBtn');
if (sendVoteOtpBtn) sendVoteOtpBtn.addEventListener('click', async () => {
  try {
    const {res, data} = await postJson('/api/vote/send-otp', {});
    setMessage('voteVerifyMessage', data.message || 'OTP sent', res.ok && data.success);
  } catch {
    setMessage('voteVerifyMessage', 'Server connection failed', false);
  }
});

const verifyVoteOtpBtn = document.getElementById('verifyVoteOtpBtn');
if (verifyVoteOtpBtn) verifyVoteOtpBtn.addEventListener('click', async () => {
  const unique_id = document.getElementById('vote_unique_id').value.trim();
  const otp = document.getElementById('vote_otp').value.trim();
  if (!/^\d{9}$/.test(unique_id)) return setMessage('voteVerifyMessage', 'Enter valid 9-digit voter ID', false);
  if (!/^\d{6}$/.test(otp)) return setMessage('voteVerifyMessage', 'Enter valid 6-digit OTP', false);
  try {
    const {res, data} = await postJson('/api/vote/verify', {unique_id, otp});
    setMessage('voteVerifyMessage', data.message || 'Verified', res.ok && data.success);
    if (res.ok && data.success && data.redirect) window.location.href = data.redirect;
  } catch {
    setMessage('voteVerifyMessage', 'Server connection failed', false);
  }
});

let selectedParty = '';
const selectedPartyText = document.getElementById('selectedPartyText');
document.querySelectorAll('.candidate-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.candidate-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    selectedParty = card.dataset.party;
    if (selectedPartyText) selectedPartyText.textContent = `Selected party: ${selectedParty}`;
  });
});

const confirmModal = document.getElementById('confirmModal');
const confirmText = document.getElementById('confirmText');
const submitVoteBtn = document.getElementById('submitVoteBtn');
if (submitVoteBtn) submitVoteBtn.addEventListener('click', () => {
  if (!selectedParty) return setMessage('voteMessage', 'Please select a candidate or party first', false);
  confirmText.textContent = `Are you sure you want to submit your vote for ${selectedParty}?`;
  confirmModal.classList.remove('hidden');
});

document.getElementById('cancelVoteBtn')?.addEventListener('click', () => confirmModal.classList.add('hidden'));
document.getElementById('confirmVoteBtn')?.addEventListener('click', async () => {
  try {
    const {res, data} = await postJson('/api/vote', {party:selectedParty});
    if (!res.ok || !data.success) return setMessage('voteMessage', data.error || 'Vote failed', false);
    window.location.href = data.redirect;
  } catch {
    setMessage('voteMessage', 'Server connection failed', false);
  } finally {
    confirmModal.classList.add('hidden');
  }
});
