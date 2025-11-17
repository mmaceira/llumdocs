"""
Gradio web interface example using LiteLLM with Ollama (llama3.1:8b) and OpenAI.

Make sure you have:
1. Ollama installed and running locally
2. llama3.1:8b model pulled: `ollama pull llama3.1:8b`
3. OpenAI API key set in environment variable: OPENAI_API_KEY (optional)

Run with: python example_litellm_gradio.py
"""

import os

import gradio as gr
from litellm import completion


def get_available_models():
    """Get list of available models based on environment setup"""
    models = []

    # Always add Ollama
    models.append(("Ollama (llama3.1:8b)", "ollama/llama3.1:8b"))

    # Add OpenAI if key is available
    if os.getenv("OPENAI_API_KEY"):
        models.append(("OpenAI (gpt-3.5-turbo)", "gpt-3.5-turbo"))
        models.append(("OpenAI (gpt-4)", "gpt-4"))

    return models


def chat_with_llm(model_choice, user_message, history):
    """
    Chat function that works with LiteLLM and different providers.

    Args:
        model_choice: Selected model string (e.g., "ollama/llama3.1:8b")
        user_message: User's input message
        history: Chat history (list of [user, assistant] pairs)

    Returns:
        Updated history and empty message box
    """
    if not user_message.strip():
        return history, ""

    # Determine if this is an Ollama model
    is_ollama = model_choice.startswith("ollama/")

    try:
        # Prepare completion arguments
        kwargs = {"model": model_choice, "messages": [{"role": "user", "content": user_message}]}

        # Add API base for Ollama
        if is_ollama:
            kwargs["api_base"] = "http://localhost:11434"

        # Get response from LiteLLM
        response = completion(**kwargs)
        assistant_message = response.choices[0].message.content

        # Update history
        history.append([user_message, assistant_message])

        return history, ""

    except Exception as e:
        error_message = f"Error: {str(e)}"
        if is_ollama:
            error_message += "\n\nMake sure Ollama is running: `ollama serve`"
            error_message += "\nAnd the model is pulled: `ollama pull llama3.1:8b`"
        else:
            error_message += "\n\nMake sure OPENAI_API_KEY is set in your environment."

        history.append([user_message, error_message])
        return history, ""


def create_gradio_interface():
    """Create and launch the Gradio interface"""

    available_models = get_available_models()

    # If no models available, show error
    if not available_models:
        print("Error: No models available. Please set up Ollama or OpenAI API key.")
        return

    # Extract model identifiers for the dropdown
    model_choices = [model[0] for model in available_models]
    model_map = {model[0]: model[1] for model in available_models}

    with gr.Blocks(title="LiteLLM Chat Interface", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🤖 LiteLLM Chat Interface

            Chat with different LLM providers using a unified interface:
            - **Ollama** (llama3.1:8b) - Local model
            - **OpenAI** (gpt-3.5-turbo, gpt-4) - Cloud API (if API key is set)

            Select a model and start chatting!
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=model_choices,
                    value=model_choices[0],
                    label="Select Model",
                    info="Choose which LLM provider to use",
                )

                gr.Markdown("### Instructions")
                gr.Markdown(
                    """
                    - **Ollama**: Make sure Ollama is running locally
                    - **OpenAI**: Requires OPENAI_API_KEY environment variable
                    """
                )

            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Chat", height=500, show_copy_button=True)

                with gr.Row():
                    msg = gr.Textbox(
                        label="Your Message",
                        placeholder="Type your message here...",
                        scale=4,
                        container=False,
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)

                clear_btn = gr.Button("Clear Chat", variant="secondary")

        # Store the selected model identifier
        model_state = gr.State(value=model_map[model_choices[0]])

        # Update model state when dropdown changes
        def update_model_state(choice):
            return model_map[choice]

        model_dropdown.change(fn=update_model_state, inputs=model_dropdown, outputs=model_state)

        # Chat function wrapper
        def chat_wrapper(message, history, model_state_value):
            return chat_with_llm(model_state_value, message, history)

        # Submit actions
        msg.submit(fn=chat_wrapper, inputs=[msg, chatbot, model_state], outputs=[chatbot, msg])
        submit_btn.click(
            fn=chat_wrapper, inputs=[msg, chatbot, model_state], outputs=[chatbot, msg]
        )

        # Clear chat
        clear_btn.click(fn=lambda: ([], ""), outputs=[chatbot, msg])

    return demo


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("LiteLLM Gradio Interface")
    print("=" * 50)
    print("\nStarting web interface...")
    print("Available models:")

    models = get_available_models()
    for name, model_id in models:
        print(f"  - {name} ({model_id})")

    if not models:
        print("\n⚠️  Warning: No models available!")
        print("Please set up at least one of:")
        print("  1. Ollama: `ollama serve` and `ollama pull llama3.1:8b`")
        print("  2. OpenAI: Set OPENAI_API_KEY environment variable")

    print("\n" + "=" * 50)
    print("Opening web interface...")
    print("=" * 50 + "\n")

    demo = create_gradio_interface()
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
