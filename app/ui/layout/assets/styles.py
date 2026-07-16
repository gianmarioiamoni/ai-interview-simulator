# app/ui/layout/assets/styles.py

LOADER_STYLE = """
<style>
.loader-box {
    background: rgba(0,0,0,0.75);
    padding: 20px 30px;
    border-radius: 10px;
    color: white;
    font-size: 18px;
    text-align: center;
}

.spinner {
    border: 4px solid rgba(255,255,255,0.2);
    border-top: 4px solid white;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    animation: spin 1s linear infinite;
    margin: 0 auto 10px auto;
}

.loader-dots span {
    animation: blink 1.4s infinite;
    opacity: 0;
}

.loader-dots span:nth-child(1) { animation-delay: 0s; }
.loader-dots span:nth-child(2) { animation-delay: 0.2s; }
.loader-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
    0%, 80%, 100% { opacity: 0; }
    40% { opacity: 1; }
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

</style>
"""

# EPIC-04 Phase 5 — Replay responsive layout (EPIC-04-DATA-MODEL §6.3 / §6.4).
# Breakpoints: mobile < 640px; tablet 640–1024px; desktop > 1024px.
REPLAY_LAYOUT_STYLE = """
<style>
#replay-view .replay-layout {
    display: grid;
    gap: 1rem;
    width: 100%;
}

#replay-view .replay-col-nav,
#replay-view .replay-col-question,
#replay-view .replay-col-sidebar {
    min-width: 0;
}

#replay-view .replay-error {
    text-align: center;
    width: 100%;
}

/* Mobile: < 640px — single column stack */
@media (max-width: 639px) {
    #replay-view .replay-layout {
        grid-template-columns: 1fr;
        grid-template-areas:
            "nav"
            "question"
            "sidebar";
    }
    #replay-view .replay-col-nav { grid-area: nav; }
    #replay-view .replay-col-question { grid-area: question; }
    #replay-view .replay-col-sidebar { grid-area: sidebar; }
}

/* Tablet: 640px – 1024px — two columns */
@media (min-width: 640px) and (max-width: 1024px) {
    #replay-view .replay-layout {
        grid-template-columns: 1fr 1fr;
        grid-template-areas:
            "nav sidebar"
            "question sidebar";
    }
    #replay-view .replay-col-nav { grid-area: nav; }
    #replay-view .replay-col-question { grid-area: question; }
    #replay-view .replay-col-sidebar { grid-area: sidebar; }
}

/* Desktop: > 1024px — three columns */
@media (min-width: 1025px) {
    #replay-view .replay-layout {
        grid-template-columns: minmax(160px, 1fr) minmax(0, 2fr) minmax(220px, 1fr);
        grid-template-areas: "nav question sidebar";
    }
    #replay-view .replay-col-nav { grid-area: nav; }
    #replay-view .replay-col-question { grid-area: question; }
    #replay-view .replay-col-sidebar { grid-area: sidebar; }
}
</style>
"""
