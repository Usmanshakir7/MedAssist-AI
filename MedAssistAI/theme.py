import streamlit as st


def get_css():
    return r'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#07171d;--surface:#0d252d;--accent:#35e0c1;--accent2:#159d8e;--text:#edf9f6;--muted:#91aaa7;--warn:#ffc261;--ok:#39d99b;--border:rgba(53,224,193,.16)}
html,body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 50% -10%,#12414b 0,#07171d 52%);color:var(--text);font-family:'DM Sans',sans-serif;scroll-behavior:smooth}
.block-container{max-width:1180px;padding-top:1.5rem;padding-bottom:6rem}h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important}.muted{color:var(--muted)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#081d24,#061319);border-right:1px solid var(--border)}.sidebar-brand{font-family:'Space Grotesk';font-size:1.35rem;font-weight:700;margin-bottom:18px}.sidebar-brand span{color:var(--accent)}.sidebar-user{padding:10px 12px;border:1px solid var(--border);border-radius:12px;color:var(--muted);margin-bottom:18px}.side-links a{display:block;color:var(--muted);text-decoration:none;padding:11px 12px;border-radius:10px;margin:3px 0}.side-links a:hover{background:rgba(53,224,193,.1);color:var(--accent)}.sidebar-tip{margin-top:20px;padding:12px;border:1px solid var(--border);border-radius:12px;color:var(--muted);font-size:.82rem}
.app-header{display:flex;align-items:center;gap:10px}.logo-mark{font-size:2rem}.app-wordmark{font-family:'Space Grotesk';font-size:1.55rem;font-weight:700;margin:0}.app-wordmark span{color:var(--accent)}.auth-tagline{text-align:center;color:var(--muted);margin:8px 0 20px}.auth-card,.empty-card,.guide-card,.insight-card,.recommend-card{background:rgba(13,37,45,.88);border:1px solid var(--border);border-radius:18px;box-shadow:0 15px 45px rgba(0,0,0,.2)}.auth-card{padding:4px}.empty-card{padding:28px;text-align:center;color:var(--muted)}
.hero{display:flex;justify-content:space-between;align-items:center;min-height:300px;padding:42px;border-radius:28px;border:1px solid var(--border);background:linear-gradient(135deg,rgba(53,224,193,.14),rgba(13,37,45,.8));overflow:hidden}.hero h1{font-size:clamp(2.2rem,5vw,4rem);margin:5px 0}.hero p{max-width:650px;color:var(--muted);font-size:1.05rem}.hero-orbit{font-size:6rem;animation:float 3s ease-in-out infinite}.eyebrow{font-size:.72rem;letter-spacing:.14em;color:var(--accent);font-weight:700}.guide-card{display:flex;gap:18px;padding:22px;margin:20px 0}.guide-card>b{font-size:2rem;color:var(--accent)}.guide-card p{color:var(--muted)}.scroll-cue{text-align:center;color:var(--accent);margin:22px 0;animation:bounce 1.8s infinite}.anchor-offset{scroll-margin-top:25px;height:1px}
.stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:20px 0}.stat-card{background:rgba(13,37,45,.85);border:1px solid var(--border);border-radius:16px;padding:18px}.stat-label{color:var(--muted);font-size:.76rem;text-transform:uppercase;letter-spacing:.08em}.stat-value{font-size:1.8rem;font-weight:700;margin-top:5px}.stat-accent{color:var(--accent)}.stat-warn{color:var(--warn)}
.insight-card,.recommend-card{padding:26px;margin:12px 0}.insight-card{border-top:3px solid var(--accent)}.recommend-card{border-top:3px solid var(--ok)}.insight-card p,.recommend-card p{line-height:1.75;color:#c9dcda}.stButton>button,.stDownloadButton>button{border-radius:12px;font-weight:700;min-height:42px}.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#04201d;border:0}[data-testid="stFileUploader"]{border:1px dashed rgba(53,224,193,.35);border-radius:16px;padding:10px;background:rgba(53,224,193,.04)}
@keyframes float{50%{transform:translateY(-10px)}}@keyframes bounce{50%{transform:translateY(5px)}}@media(max-width:700px){.block-container{padding:1rem .75rem 4rem}.hero{padding:25px;min-height:260px}.hero-orbit{display:none}.hero h1{font-size:2.2rem}.stat-grid{grid-template-columns:1fr}.guide-card{padding:16px}}
</style>'''


def inject():
    st.markdown(get_css(), unsafe_allow_html=True)


def app_header(show_border=True):
    st.markdown('<div class="app-header"><div class="logo-mark">🩺</div><p class="app-wordmark">Med<span>Assist</span> AI</p></div>', unsafe_allow_html=True)


def sidebar_brand():
    st.markdown('<div class="sidebar-brand">🩺 Med<span>Assist</span> AI</div>', unsafe_allow_html=True)


def stat_card_html(label, value, accent=""):
    cls = f"stat-{accent}" if accent else ""
    return f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value {cls}">{value}</div></div>'


def page_header(title, subtitle=""):
    st.markdown(f'<h2>{title}</h2><p class="muted">{subtitle}</p>', unsafe_allow_html=True)


def status_badge_html(status):
    return status


def range_bar_html(*args, **kwargs):
    return ""
