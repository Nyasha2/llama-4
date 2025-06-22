# AI Literary Game

## Description

This project is an AI-powered conversational game that uses the Llama 4 API to generate an interactive story based on the universe of a book. Players can make choices that influence the narrative, creating a dynamic and immersive experience.

## Setup

1.  Clone the repository.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate the virtual environment: `source venv/bin/activate` (on macOS/Linux) or `.\venv\Scripts\activate` (on Windows).
4.  Install the dependencies: `pip install -r requirements.txt`
5.  Create a `.env` file in the root directory and add your Llama 4 API key and endpoint. See `.env.example` for the format.

## Usage

Run the Flask application:
`flask run`

Then, open your web browser and navigate to `http://127.0.0.1:5000`.
