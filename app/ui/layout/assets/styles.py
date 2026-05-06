# app/ui/layout/assets/styles.py

LOADER_STYLE = """
<style>
#global-loader {
    display: none;  

    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: rgba(0, 0, 0, 0.6);
    z-index: 9999;

    align-items: center;
    justify-content: center;

    font-size: 24px;
    color: white;

    backdrop-filter: blur(4px);
}

#global-loader span {
    background: rgba(0,0,0,0.7);
    padding: 16px 24px;
    border-radius: 8px;
}

/* VISIBILITY CONTROL */
.loader-hidden {
    display: none !important;
}

.loader-visible {
    display: flex !important;
}
</style>
"""
