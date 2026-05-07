# app/ui/components/loader/loader_template.py

LOADER_HTML = """
<div style="
    position: fixed;
    top:0; left:0; right:0; bottom:0;
    background: rgba(0,0,0,0.65);
    display:flex;
    align-items:center;
    justify-content:center;
    backdrop-filter: blur(6px);
    z-index:9999;
">

    <div style="
        background: rgba(0,0,0,0.85);
        padding: 28px 36px;
        border-radius: 12px;
        color: white;
        font-size: 16px;
        text-align: center;
        min-width: 280px;
    ">

        <!-- Spinner -->
        <div style="
            border: 4px solid rgba(255,255,255,0.2);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px auto;
        "></div>

        <!-- Message -->
        <div style="margin-bottom: 10px;">
            {message}
        </div>

        <!-- Progress bar -->
        <div style="
            height: 6px;
            background: rgba(255,255,255,0.15);
            border-radius: 6px;
            overflow: hidden;
        ">
            <div style="
                width: {progress}%;
                height: 100%;
                background: linear-gradient(90deg, #4facfe, #00f2fe);
                transition: width 0.3s ease;
            "></div>
        </div>

        <!-- Percentage -->
        <div style="
            margin-top: 8px;
            font-size: 12px;
            opacity: 0.7;
        ">
            {progress}%
        </div>

    </div>
</div>
"""
