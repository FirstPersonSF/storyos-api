"""
Debug API Routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os
import glob

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/llm-responses")
def get_llm_responses(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the most recent LLM response debug files

    Args:
        limit: Maximum number of responses to return (default 10)

    Returns:
        List of debug file contents with timestamps
    """
    debug_dir = '/Users/drewf/Desktop/Python/storyos_protoype/llm_debug'

    if not os.path.exists(debug_dir):
        return []

    # Get all debug files
    files = glob.glob(f"{debug_dir}/response_*.json")

    # Sort by modification time (most recent first)
    files.sort(key=os.path.getmtime, reverse=True)

    # Limit results
    files = files[:limit]

    responses = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Extract timestamp from filename
            filename = os.path.basename(file_path)
            timestamp = filename.replace('response_', '').replace('.json', '')

            responses.append({
                'timestamp': timestamp,
                'filename': filename,
                'content': content
            })
        except Exception as e:
            responses.append({
                'timestamp': 'unknown',
                'filename': os.path.basename(file_path),
                'error': str(e)
            })

    return responses


@router.delete("/llm-responses")
def clear_llm_responses() -> Dict[str, Any]:
    """
    Clear all LLM response debug files

    Returns:
        Status message with count of deleted files
    """
    debug_dir = '/Users/drewf/Desktop/Python/storyos_protoype/llm_debug'

    if not os.path.exists(debug_dir):
        return {'message': 'Debug directory does not exist', 'deleted': 0}

    # Get all debug files
    files = glob.glob(f"{debug_dir}/response_*.json")

    deleted = 0
    for file_path in files:
        try:
            os.remove(file_path)
            deleted += 1
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

    return {'message': f'Deleted {deleted} debug files', 'deleted': deleted}
