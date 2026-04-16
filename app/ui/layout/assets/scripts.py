# app/ui/layout/assets/scripts.py

FOCUS_EDITOR_SCRIPT = """
<script>
    function focusEditor() {
        setTimeout(() => {
            const editor = document.querySelector('#code-editor textarea');
            if (editor) {
                editor.focus();
            }
        }, 100);
    }
    window.addEventListener('load', focusEditor);
</script>
"""

SCROLL_TOP_SCRIPT = """
<script>
    function scrollToTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    const observerScroll = new MutationObserver(() => {
        scrollToTop();
    });

    observerScroll.observe(document.body, { childList: true, subtree: true });
</script>
"""

FOCUS_OBSERVER_SCRIPT = """
<script>
    const observer = new MutationObserver(() => {
        focusEditor();
    });
    observer.observe(document.body, {childList: true, subtree: true});
</script>
"""
