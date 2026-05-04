# app/ui/layout/assets/css.py

LOADER_STYLE = """
<style>

#global-loader {
    margin-top: 10px;
    margin-bottom: 10px;
}

/* container */
.loader-container {
    display: block;
}

/* SINGLE BAR (NO BUG) */
.loader-bar {
    height: 4px;
    width: 100%;
    background: linear-gradient(90deg, #4f46e5, #06b6d4);
    background-size: 200% 100%;
    animation: loading 1.5s infinite linear;
    border-radius: 4px;
}

/* animation */
@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* text */
.loader-text {
    font-size: 14px;
    color: #aaa;
    margin-top: 6px;
}

</style>
"""
