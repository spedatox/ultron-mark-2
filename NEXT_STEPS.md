# Ultron Mark II - Development Status

## Completed (Session: Nov 20, 2025)
- **Scheduler Logic:** 
  - Fixed commute times (Uni/Work treated as "Campus" block).
  - Enforced Dinner constraints (19:00-20:00).
- **Memory System:** 
  - Implemented Hybrid Architecture (SQL for short-term context, ChromaDB for long-term).
  - Fixed "Amnesia" bug where immediate context was lost.
- **UI Enhancements:**
  - Added Markdown rendering (`react-markdown`) for rich text responses.
- **Real-Time Streaming:**
  - Implemented `StreamingResponse` in Backend (`/chat/stream`).
  - Implemented `ReadableStream` consumer in Frontend (`api.ts`, `page.tsx`).
- **Session Management:**
  - Fixed bug where "New Sequence" merged into the previous chat.
  - Backend now correctly handles `session_id` to split conversations.

## Next Steps / Pending
- **UI Polish:**
  - Improve auto-scrolling during streaming.
  - Add "Stop Generation" button.
  - Better visual feedback for file uploads.
- **Testing:**
  - Verify complex scheduling scenarios.
  - Test long-term memory retrieval accuracy.
