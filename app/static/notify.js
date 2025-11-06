// Live notifications: poll server and update bell and approvals bubble
(function(){
  const lastMKey = 'tm_last_msgs';
  const lastAKey = 'tm_last_appr';
  let lastMessages = 0;
  let lastApprovals = 0;

  // Initialize last known counts from server-rendered values on first load
  try {
    const initM = typeof window!== 'undefined' && typeof window.TM_NOTIF_MESSAGES !== 'undefined' ? Number(window.TM_NOTIF_MESSAGES||0) : 0;
    const initA = typeof window!== 'undefined' && typeof window.TM_NOTIF_APPROVALS !== 'undefined' ? Number(window.TM_NOTIF_APPROVALS||0) : 0;
    if (localStorage.getItem(lastMKey) === null) localStorage.setItem(lastMKey, String(initM));
    if (localStorage.getItem(lastAKey) === null) localStorage.setItem(lastAKey, String(initA));
    lastMessages = initM;
    lastApprovals = initA;
  } catch (e) {}

  let audioCtx;
  function ensureAudio(){
    if (!audioCtx){ try { audioCtx = new (window.AudioContext||window.webkitAudioContext)(); } catch(e){} }
    if (audioCtx && audioCtx.state==='suspended') { audioCtx.resume().catch(()=>{}); }
    return audioCtx;
  }
  function beep(pattern=[[880,120],[0,60],[660,160]]){
    const ctx = ensureAudio(); if (!ctx) return;
    const now = ctx.currentTime; let t = now;
    const osc = ctx.createOscillator(); const gain = ctx.createGain();
    osc.type='sine'; osc.connect(gain).connect(ctx.destination); osc.start(now);
    for (const [f,d] of pattern){ osc.frequency.setValueAtTime(f||440,t); gain.gain.setValueAtTime(f?0.15:0.0,t); t += (d||120)/1000; }
    osc.stop(t);
  }

  function updateHeader(messages, approvals){
    const bell = document.querySelector('.navbar .btn.bell');
    if (bell){
      if (messages > 0) bell.classList.add('bell-alert'); else bell.classList.remove('bell-alert');
      let b = bell.querySelector('.bubble');
      if (messages > 0){ if (!b){ b = document.createElement('span'); b.className='bubble'; bell.appendChild(b);} b.textContent = String(messages); }
      else if (b){ b.remove(); }
    }
    const appr = document.getElementById('approvals-link');
    if (appr){
      let ab = appr.querySelector('.bubble');
      if (approvals > 0){ if (!ab){ ab = document.createElement('span'); ab.className='bubble'; appr.appendChild(ab);} ab.textContent = String(approvals); }
      else if (ab){ ab.remove(); }
    }
  }

  function updateCards(pendingIds){
    const set = new Set(pendingIds || []);
    document.querySelectorAll('.card .btn.bell').forEach((el)=>{
      const idAttr = el.getAttribute('data-task-id');
      const id = idAttr ? Number(idAttr) : null;
      const shouldAlert = (id !== null) && set.has(id);
      if (shouldAlert){ el.classList.add('bell-alert'); } else { el.classList.remove('bell-alert'); }
      // Always mirror the header unread count on card bells when > 0
      let b = el.querySelector('.bubble');
      if (lastMessages > 0){
        if (!b){ b = document.createElement('span'); b.className='bubble'; el.appendChild(b); }
        b.textContent = String(lastMessages);
      } else if (b){ b.remove(); }
    });
  }

  // On first load, render numeric bubble on card bells (do not change alert classes)
  function initCardBubbles(){
    document.querySelectorAll('.card .btn.bell').forEach((el)=>{
      let b = el.querySelector('.bubble');
      if (lastMessages > 0){
        if (!b){ b = document.createElement('span'); b.className='bubble'; el.appendChild(b); }
        b.textContent = String(lastMessages);
      } else if (b){ b.remove(); }
    });
  }

  function poll(){
    fetch('/notifications/poll', {credentials:'same-origin'})
      .then(r=> r.ok ? r.json() : Promise.reject())
      .then(({messages, approvals, pending_task_ids})=>{
        const lm = Number(localStorage.getItem(lastMKey)||'0');
        const la = Number(localStorage.getItem(lastAKey)||'0');
        const hasApprovalsLink = !!document.getElementById('approvals-link');
        if (messages>lm || (hasApprovalsLink && approvals>la)) setTimeout(()=>beep(), 200);
        localStorage.setItem(lastMKey, String(messages||0));
        localStorage.setItem(lastAKey, String(approvals||0));
        lastMessages = Number(messages||0);
        lastApprovals = Number(approvals||0);
        updateHeader(messages||0, approvals||0);
        updateCards(pending_task_ids||[]);
      })
      .catch(()=>{});
  }

  // Initial refresh then poll every 7s
  initCardBubbles();
  setTimeout(poll, 500);
  setInterval(poll, 7000);
})();

