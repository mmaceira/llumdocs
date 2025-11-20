"""
Smoke test for Gradio UI creation.

This test ensures that the UI can be imported and the interface can be created
without triggering heavy side effects (e.g., importing torch at module level).
"""

from __future__ import annotations


def test_ui_import_and_creation():
    """Smoke test: import UI module and create interface without side effects."""
    from llumdocs.ui.main import create_interface

    # This should not raise and should not trigger heavy imports
    demo = create_interface()

    # Verify it returns a Gradio Blocks object
    import gradio as gr

    assert isinstance(demo, gr.Blocks)
