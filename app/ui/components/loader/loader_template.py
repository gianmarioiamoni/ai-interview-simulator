# app/ui/components/loader/loader_template.py

LOADER_HTML = """ 
<div class="loader-overlay">

  <div class="loader-box">

    <div style="
        height: 6px;
        background: rgba(255,255,255,0.15);
        border-radius: 6px;
        overflow: hidden;
        margin-top: 10px;
    ">
        <div style="
            width: {progress}%;
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            transition: width 0.4s ease;
        "></div>
    </div>

    <div style="font-size: 12px; opacity: 0.7; margin-top: 6px;">
        {progress}%
    </div>

    <div class="loader-text">
        {message}
    </div>

    <div class="loader-dots">
        <span>.</span><span>.</span><span>.</span>
    </div>

  </div>
</div>
 """
