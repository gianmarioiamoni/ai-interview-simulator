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

    display: flex;
    align-items: center;
    justify-content: center;

    backdrop-filter: blur(4px);
}

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

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
"""
