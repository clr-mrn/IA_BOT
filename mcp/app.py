from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl, Field

from mcp.tools import scrape_category, scrape_place, scrape_events


app = FastAPI(title="MCP Tools", version="0.1.0")

class CategoryArgs(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=20)

class PlaceArgs(BaseModel):
    url: HttpUrl

class EventsArgs(BaseModel):
    limit: int = Field(default=10, ge=1, le=20)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tools/scrape_category")
def tool_category(args: CategoryArgs):
    return scrape_category(args.query, limit=args.limit)

@app.post("/tools/scrape_place")
def tool_place(args: PlaceArgs):
    return scrape_place(str(args.url))

@app.post("/tools/scrape_events")
def tool_events(args: EventsArgs):
    return scrape_events(limit=args.limit)
