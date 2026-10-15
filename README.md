# Enterprise RAG Application

## Run with Docker Compose

1. Create a root `.env` file containing the required provider, Qdrant, and Neon
   variables. The existing local `.env` is used automatically and is never copied
   into the image.
2. Start the API and UI:

   ```bash
   docker compose up --build
   ```

3. Open the Streamlit UI at `http://localhost:8501` and the FastAPI health check
   at `http://localhost:8000/health`.

The Compose network sets `BACKEND_URL=http://api:8000` for the UI container, so
the UI reaches the API by its service name rather than `localhost`.
