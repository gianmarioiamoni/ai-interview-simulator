app/ui/layout/assets/styles.py

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

</style>
"""
