import sys
import os

# Make the project root importable from inside api/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator_agent import problem_agent, options_agent, risks_agent, recommendation_agent

app = FastAPI(title="ORQ Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


@app.post("/analyze")
async def analyze(request: QueryRequest):
    query = request.query

    async def event_stream():
        try:
            yield f"data: {json.dumps({'event': 'stage_start', 'stage': 'problem'})}\n\n"
            problem = await asyncio.to_thread(problem_agent, query)
            yield f"data: {json.dumps({'event': 'stage_complete', 'stage': 'problem', 'content': problem})}\n\n"

            yield f"data: {json.dumps({'event': 'stage_start', 'stage': 'options'})}\n\n"
            options = await asyncio.to_thread(options_agent, query, problem)
            yield f"data: {json.dumps({'event': 'stage_complete', 'stage': 'options', 'content': options})}\n\n"

            yield f"data: {json.dumps({'event': 'stage_start', 'stage': 'risks'})}\n\n"
            risks = await asyncio.to_thread(risks_agent, query, problem, options)
            yield f"data: {json.dumps({'event': 'stage_complete', 'stage': 'risks', 'content': risks})}\n\n"

            yield f"data: {json.dumps({'event': 'stage_start', 'stage': 'recommendation'})}\n\n"
            recommendation = await asyncio.to_thread(recommendation_agent, query, problem, options, risks)
            yield f"data: {json.dumps({'event': 'stage_complete', 'stage': 'recommendation', 'content': recommendation})}\n\n"

            yield f"data: {json.dumps({'event': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# Vercel picks this up as the ASGI handler
handler = app
