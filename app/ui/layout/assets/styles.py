# app/ui/layout/assets/styles.py

LOADER_STYLE = """
<style>
#global-loader {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: rgba(0, 0, 0, 0.6);
    z-index: 9999;

    display: none;
    align-items: center;
    justify-content: center;

    backdrop-filter: blur(4px);
}

/* attivazione via Gradio */
#global-loader[style*="display: block"] {
    display: flex !important;
}

/* contenuto */
.loader-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;

    color: white;
    font-size: 18px;
}

/* spinner */
.loader-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255,255,255,0.2);
    border-top: 4px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

/* animazione */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

</style>
"""
