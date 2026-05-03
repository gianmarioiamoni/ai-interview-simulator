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
.loader-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 16px;
}

.loader-bar {
    height: 4px;
    width: 100%;
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
