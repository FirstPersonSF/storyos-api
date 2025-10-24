"""
StoryOS API - Main Application

FastAPI application for the StoryOS prototype
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import unf, voices, story_models, templates, deliverables, debug

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="StoryOS API",
    description="""
StoryOS is a content management system for enterprise storytelling.

## Features

* **UNF (Unified Narrative Framework)** - Manage reusable narrative content
* **Brand Voices** - Define and apply tonal filters
* **Story Models** - Structural templates (PAS, Inverted Pyramid, etc.)
* **Deliverable Templates** - Assemble content using story models
* **Deliverables** - Final outputs with version tracking and impact alerts

## Key Concepts

- **Elements**: Reusable content blocks (e.g., "Vision Statement", "Problem")
- **Version Tracking**: Elements link via `prev_element_id` to track changes
- **Impact Alerts**: Deliverables detect when source Elements are updated
- **Brand Voice**: Applied at render time (non-destructive)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(unf.router)
app.include_router(voices.router)
app.include_router(story_models.router)
app.include_router(templates.router)
app.include_router(deliverables.router)
app.include_router(debug.router)


@app.get("/")
def root():
    """Root endpoint - API info"""
    return {
        "name": "StoryOS API",
        "version": "1.0.0",
        "description": "Content management system for enterprise storytelling",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "unf": "/unf",
            "voices": "/voices",
            "story_models": "/story-models",
            "templates": "/templates",
            "deliverables": "/deliverables"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
