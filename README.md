# Personal Portfolio — Ezz Eldin Ahmed

A custom-built personal website showcasing my projects, skills, and tools as a statistics major and aspiring machine learning engineer. Built from the ground up to go beyond static portfolios — this site integrates custom apps, interpretable analytics, and a real-time chatbot.

## Tech Stack

**Frontend:**
- HTML, CSS, JavaScript
- Bootstrap-based responsive design
- Fully customized dark/light mode styling

**Backend:**
- Django (site structure and routing)
- Streamlit (embedded apps via iframe)
- Supabase (user/session backend for research tools)

**Interactive Tools:**
- Logistic, Linear, and Time Series Modeling apps
- AI-powered chatbot with OpenRouter + Pollinations fallback
- Image generation module (Flux/GPTImage-style)
- Voice generation via Pollinations TTS
- File parsing (PDF, CSV, plain text)

## Projects Included

- **XANE Chatbot**: Conversational AI that also handles uploaded files and voice responses.
- **Auto Statistical Models**: Logistic regression, linear regression, and time series with diagnostic reporting and visuals.
- **OCR Tool**: Parses text from uploaded images.
- **Custom Image Generator**: Prompt-based art and AI concept generation using free APIs.
- **Scholarship + Research Center Tools**: Login system, role-based dashboard, and student tools.

## Hosting

- Main website hosted on **Vercel**
- Streamlit apps deployed separately and embedded via iframe
- Pollinations and OpenRouter APIs used for model interactions

## Purpose

This portfolio is a living collection of everything I’ve built — replacing the need for generic dashboards or templates. Each tool solves a specific real-world problem I encountered during my academic or extracurricular work.

## How to Run Locally

```bash
# Main Django app
git clone https://github.com/yourusername/portfolio-website.git
cd portfolio-website
pip install -r requirements.txt
python manage.py runserver

# Streamlit apps (in separate folders or repos)
streamlit run chatbot.py
streamlit run regression_logistic.py
streamlit run regression_linear.py
streamlit run tsa_model.py
