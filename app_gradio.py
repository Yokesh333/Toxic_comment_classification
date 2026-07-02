import os
import time
import gradio as gr

# Model Directory Check
MODEL_DIR = "./best_model"

# Custom Premium CSS Styling for Glassmorphism & High-end Dark Theme aesthetics
custom_css = """
body {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
}

#header-container {
    text-align: center;
    margin-bottom: 2rem;
}

#header-title {
    background: linear-gradient(135deg, #FF4B4B, #FF8F6B, #8F6BFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    margin-bottom: 0.1rem;
    letter-spacing: -0.03em;
}

#header-subtitle {
    color: #6B7280;
    font-size: 1.1rem;
}

.warning-container {
    background: rgba(239, 68, 68, 0.05);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    color: #F87171;
    margin-bottom: 1.5rem;
}

.status-card-safe {
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    color: #4ADE80;
    font-weight: 600;
    text-align: center;
}

.status-card-toxic {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    color: #F87171;
    font-weight: 600;
    text-align: center;
}
"""

classifier = None
model_missing = False

try:
    from model import ToxicClassifier
    classifier = ToxicClassifier(model_dir=MODEL_DIR)
    # Don't load yet, wait for prediction or start so it starts up fast
except Exception as e:
    model_missing = True

def predict_toxicity(text, threshold):
    if model_missing or not os.path.exists(MODEL_DIR):
        return (
            "⚠️ Model directory 'best_model' not found. Please follow instructions to download it first.",
            {},
            "N/A"
        )
    
    if text.strip() == "":
        return "Awaiting Input...", {}, "0.0 ms"
        
    try:
        start_time = time.time()
        results = classifier.predict(text, threshold=threshold)
        latency_ms = (time.time() - start_time) * 1000
        
        # Format label predictions for Gradio Label component
        probs_dict = {label: res["probability"] for label, res in results.items()}
        
        # Identify flagged labels
        flagged = [label.replace("_", " ").upper() for label, res in results.items() if res["flagged"]]
        
        if len(flagged) == 0:
            status_html = '<div class="status-card-safe">🟢 Comment Safe — No toxic dimensions flagged</div>'
        else:
            labels_str = ", ".join(flagged)
            status_html = f'<div class="status-card-toxic">🚨 Flagged Toxic: {labels_str}</div>'
            
        latency_str = f"{latency_ms:.1f} ms"
        return status_html, probs_dict, latency_str
        
    except Exception as e:
        return f"Error during model inference: {str(e)}", {}, "N/A"

# Build Interface
with gr.Blocks(theme=gr.themes.Soft(primary_hue="rose", secondary_hue="indigo"), css=custom_css) as demo:
    
    # Custom Header
    gr.HTML(
        """
        <div id="header-container">
            <div id="header-title">GuardianAI</div>
            <div id="header-subtitle">BERT-Based Multi-Label Toxicity Analysis Engine</div>
        </div>
        """
    )
    
    # Model Missing Alert
    if not os.path.exists(MODEL_DIR):
        gr.HTML(
            """
            <div class="warning-container">
                <h3 style="margin-top: 0; color: #F87171;">⚠️ Local Model Files Not Found</h3>
                <p>The interactive dashboard requires the trained model weights. Please download and extract them:</p>
                <ol style="padding-left: 1.5rem; line-height: 1.6;">
                    <li>Train and download model weights as <code>best_model.zip</code> via <b>colab_instructions.md</b>.</li>
                    <li>Extract the ZIP into a folder named <code>best_model</code> in this directory.</li>
                </ol>
            </div>
            """
        )
        
    with gr.Row():
        with gr.Column(scale=1):
            # Input Text Area
            input_text = gr.Textbox(
                label="Enter Comment Text",
                placeholder="Type your comment here to analyze toxicity scores...",
                lines=8,
                max_lines=15
            )
            
            # Threshold slider
            threshold_slider = gr.Slider(
                minimum=0.1,
                maximum=0.9,
                value=0.4,
                step=0.05,
                label="Flagging Confidence Threshold"
            )
            
            # Predict Button
            predict_btn = gr.Button("⚡ Analyze Comment", variant="primary")
            
        with gr.Column(scale=1):
            # Output HTML Box for Toxicity status
            status_output = gr.HTML(
                value='<div style="text-align: center; color: gray; padding: 2rem;">Awaiting Analysis</div>'
            )
            
            # Toxicity label probabilities
            label_output = gr.Label(
                num_top_classes=6,
                label="Toxicity Probabilities"
            )
            
            # Latency display
            latency_output = gr.Textbox(
                label="Inference Latency",
                interactive=False
            )
            
    # Examples section
    gr.Examples(
        examples=[
            ["This is a wonderful and incredibly informative blog post. Thank you!", 0.4],
            ["Shut up you idiot, no one wants to hear your stupid thoughts here.", 0.4],
            ["I will search for your home and hurt you, you better watch your back.", 0.4],
            ["This piece of code is trash. Stop uploading absolute garbage to this repo.", 0.4]
        ],
        inputs=[input_text, threshold_slider],
        outputs=[status_output, label_output, latency_output],
        fn=predict_toxicity,
        cache_examples=False
    )
    
    # Event Handlers
    predict_btn.click(
        fn=predict_toxicity,
        inputs=[input_text, threshold_slider],
        outputs=[status_output, label_output, latency_output]
    )
    
    input_text.submit(
        fn=predict_toxicity,
        inputs=[input_text, threshold_slider],
        outputs=[status_output, label_output, latency_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
