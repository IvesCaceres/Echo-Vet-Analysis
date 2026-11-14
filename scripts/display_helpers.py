"""Use rich notebook display when installed; headless execution is also supported."""
try:
    from IPython.display import display, Markdown
except ImportError:
    def display(*objects, **kwargs):
        return None

    def Markdown(text):
        return text
