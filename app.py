import os
import json
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from orchestrator_agent import problem_agent, options_agent, risks_agent, recommendation_agent

load_dotenv()

app = FastAPI(title="ORQ Agent")
app.mount("/static", StaticFiles(directory="public"), name="static")


@app.get("/")
async def root():
    return FileResponse("public/index.html")


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
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
