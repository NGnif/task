// Notification sound and counters
(function(){
  const SOUND_KEY = 'tm_sound';
  const lastMKey = 'tm_last_msgs';
  const lastAKey = 'tm_last_appr';

  // Insert toggle button in navbar
  const navRight = document.querySelector('.nav-right');
  if (navRight){
    const snd = document.createElement('a');
    snd.className = 'btn';
    snd.href = 'javascript:void(0)';
    const label = ()=> (localStorage.getItem(SOUND_KEY)==='off' ? '🔕' : '🔔');
    snd.textContent = label();
    snd.title = 'Toggle notification sound';
    snd.addEventListener('click', ()=>{
      const v = (localStorage.getItem(SOUND_KEY)==='off')?'on':'off';
      localStorage.setItem(SOUND_KEY, v);
      snd.textContent = label();
    });
    navRight.prepend(snd);
  }

  let audioCtx;
  function ensureAudio(){
    if (!audioCtx){ try { audioCtx = new (window.AudioContext||window.webkitAudioContext)(); } catch(e){} }
    if (audioCtx && audioCtx.state==='suspended') { audioCtx.resume().catch(()=>{}); }
    return audioCtx;
  }
  function beep(pattern=[[880,120],[0,60],[660,160]]){
    if (localStorage.getItem(SOUND_KEY)==='off') return;
    const ctx = ensureAudio(); if (!ctx) return;
    const now = ctx.currentTime; let t = now;
    const osc = ctx.createOscillator(); const gain = ctx.createGain();
    osc.type='sine';
    osc.connect(gain).connect(ctx.destination);
    osc.start(now);
    for (const [f,d] of pattern){
      osc.frequency.setValueAtTime(f||440,t);
      gain.gain.setValueAtTime(f?0.15:0.0,t);
      t += (d||120)/1000;
    }
    osc.stop(t);
  }

  const m = Number(window.TM_NOTIF_MESSAGES||0);
  const a = Number(window.TM_NOTIF_APPROVALS||0);
  const lm = Number(localStorage.getItem(lastMKey)||'0');
  const la = Number(localStorage.getItem(lastAKey)||'0');
  if (m>lm || a>la) { setTimeout(()=>beep(), 300); }
  localStorage.setItem(lastMKey, String(m));
  localStorage.setItem(lastAKey, String(a));
})();

