# app/ui/layout/assets/css.py

CODE_BLOCK_STYLE = """
<style>
pre code {
    background-color: #0d1117;
    color: #c9d1d9;
    padding: 16px;
    border-radius: 8px;
    display: block;
    overflow-x: auto;
    font-size: 14px;
    line-height: 1.5;
}
</style>
"""

FEEDBACK_BOX_STYLE = """
<style>
#feedback-box {
    padding: 16px;
    border-radius: 10px;
    background-color: #111;
    margin-bottom: 16px;
}
</style>
"""

LOADER_STYLE = """
<style>

/* GLOBAL LOADER FIX */
#global-loader {
    position: fixed;
    bottom: 20px;
    left: 20px;

    width: 260px;             
    overflow: hidden;          
    isolation: isolate;        

    background-color: #111;
    padding: 12px 16px;
    border-radius: 8px;
    z-index: 9999;
}
/* LOADER CONTENT */
.loader-container {
    display: block;
}

.loader-bar {
    height: 4px; 
    width: 100%; 
    max-width: 100%;

    background: linear-gradient(90deg, #4f46e5, #06b6d4);
    background-size: 200% 100%;
    animation: loading 1.5s infinite linear;
    border-radius: 4px;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.loader-text {
    font-size: 14px;
    color: #aaa;
}

</style>
"""
