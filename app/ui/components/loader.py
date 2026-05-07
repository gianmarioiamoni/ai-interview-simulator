# app/ui/components/loader.py


def build_loader_html(message: str) -> str:
    
    return f"""
    <div class="loader-container">
        <div class="loader-bar"></div>
        <div class="loader-text">{message}</div>
    </div>
    """
