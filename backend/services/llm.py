import json
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from openai import OpenAI
import models, crud, schemas
from services import scheduler, memory, calendar_integration

# Initialize OpenAI client
# Expects OPENAI_API_KEY in environment variables
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Tool Definitions
TOOLS = [
    # --- Task Tools ---
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new study task. IMPORTANT: After creating a task, you MUST call plan_task with the returned task_id to actually schedule it into time slots.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title (e.g. 'Analitik Geometri - Chapter 3')"},
                    "total_required_time": {"type": "integer", "description": "Total minutes needed"},
                    "deadline": {"type": "string", "description": "ISO format datetime string (YYYY-MM-DDTHH:MM:SS). If not provided, defaults to end of today."},
                    "priority": {"type": "string", "enum": ["normal", "high"], "default": "normal"},
                    "course_tag": {"type": "string", "description": "Course code or subject tag"}
                },
                "required": ["title", "total_required_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Modify an existing task's properties.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID of the task to update"},
                    "title": {"type": "string"},
                    "total_required_time": {"type": "integer"},
                    "deadline": {"type": "string"},
                    "priority": {"type": "string", "enum": ["normal", "high"]},
                    "status": {"type": "string", "enum": ["pending", "scheduled", "completed"]}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks filtered by status or course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "scheduled", "completed"]},
                    "course_tag": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task and its scheduled study blocks from the database and Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "delete_blocks": {"type": "boolean", "description": "Also remove scheduled study sessions?", "default": True}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": "Delete an event directly from Google Calendar by its event ID. Use get_schedule first to find event IDs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The Google Calendar event ID to delete"}
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_events_by_title",
            "description": "Delete events from Google Calendar that match a title (partial match). Useful for deleting study sessions by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title_contains": {"type": "string", "description": "Delete events whose title contains this text"},
                    "date": {"type": "string", "description": "YYYY-MM-DD - only delete events on this date (optional)"}
                },
                "required": ["title_contains"]
            }
        }
    },

    # --- Planning Tools ---
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Create an event directly on Google Calendar at a SPECIFIC time. Use this when the user explicitly requests a specific time slot like 'schedule study from 10:00 to 13:30'. For STUDY sessions, ALWAYS set split_into_blocks=true to divide into focused 50-min blocks with 10-min breaks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title (e.g. 'Study: Math Chapter 5')"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_time": {"type": "string", "description": "HH:MM (24-hour format, e.g. '10:00')"},
                    "end_time": {"type": "string", "description": "HH:MM (24-hour format, e.g. '13:30')"},
                    "split_into_blocks": {"type": "boolean", "description": "If true, splits into 50-min study blocks with 10-min breaks. ALWAYS use true for study sessions!", "default": True},
                    "description": {"type": "string", "description": "Optional event description", "default": ""}
                },
                "required": ["title", "date", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plan_task",
            "description": "Automatically schedule a task into the FIRST available time slots before its deadline. Use this for tasks WITHOUT a specific time preference. If the user wants a SPECIFIC time slot, use create_calendar_event instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The task_id returned from create_task"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": "Get events and study blocks for a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "days": {"type": "integer", "default": 1}
                },
                "required": ["start_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_today_overview",
            "description": "Get a briefing of today's events and tasks.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },

    # --- Conflict & Rescheduling Tools ---
    {
        "type": "function",
        "function": {
            "name": "update_study_session",
            "description": "Move a specific study session (block) to a new time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "block_id": {"type": "integer", "description": "ID of the study block to move"},
                    "new_start_time": {"type": "string", "description": "ISO format datetime (YYYY-MM-DDTHH:MM:SS)"}
                },
                "required": ["block_id", "new_start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_conflicts",
            "description": "Check for overlapping study blocks and events.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "replan_conflicts",
            "description": "Reschedule conflicted study blocks to new free times.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },

    # --- Free Time / Gap Analysis Tools ---
    {
        "type": "function",
        "function": {
            "name": "find_free_slots",
            "description": "Find available free time slots between a start and end date. Use this BEFORE suggesting times to the user or scheduling tasks. Returns a list of available gaps with their duration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"},
                    "min_duration_mins": {"type": "integer", "description": "Minimum gap duration in minutes to include (default: 30)", "default": 30}
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_study_time",
            "description": "Given a required duration (in minutes), find the best available time slot(s) within a date range. Returns concrete time suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_mins": {"type": "integer", "description": "How many minutes are needed"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD (default: same as start_date)"},
                    "preferred_time": {"type": "string", "enum": ["morning", "afternoon", "evening", "any"], "default": "any"}
                },
                "required": ["duration_mins", "start_date"]
            }
        }
    },

    # --- Preferences Tools ---
    {
        "type": "function",
        "function": {
            "name": "get_preferences",
            "description": "Read current user preferences (wake/sleep time, etc).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_preferences",
            "description": "Update user preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "wake_time": {"type": "string", "description": "HH:MM"},
                    "sleep_time": {"type": "string", "description": "HH:MM"},
                    "study_block_length": {"type": "integer"},
                    "max_study_minutes_per_day": {"type": "integer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_daily_override",
            "description": "Set a temporary schedule adjustment for a specific date. Use this when user wants to leave early, skip commute, skip dinner, or wake up at a different time for ONE day. Types: 'departure_time' (HH:MM when leaving home), 'skip_commute' ('true' to remove commute blocks), 'skip_dinner' ('true' to remove dinner block), 'custom_wake' (HH:MM wake time for that day only).",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "override_type": {"type": "string", "enum": ["departure_time", "skip_commute", "skip_dinner", "custom_wake"], "description": "Type of override"},
                    "value": {"type": "string", "description": "The value - time in HH:MM format or 'true' for skip options"},
                    "note": {"type": "string", "description": "Optional note explaining the override"}
                },
                "required": ["date", "override_type", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_overrides",
            "description": "Get the temporary schedule adjustments for a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format (optional, returns all if not specified)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_daily_override",
            "description": "Remove a daily override, reverting to normal schedule for that date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "override_type": {"type": "string", "enum": ["departure_time", "skip_commute", "skip_dinner", "custom_wake", "all"], "description": "Type to clear, or 'all' to clear everything for that date"}
                },
                "required": ["date", "override_type"]
            }
        }
    }
]

SYSTEM_PROMPT = """
You are Ultron (Mark II), an advanced academic copilot and scheduling assistant.
Your goal is to help the user manage their time, study efficiently, and stay organized.
You have access to a deterministic scheduling engine (Timekeeper) and a memory of past conversations.

Style:
- Concise, efficient, and slightly robotic but helpful (Detroit: Become Human vibe).
- When presenting schedules or available times, use bullet points and clear time formats.

**SCHEDULING TOOLS - WHEN TO USE WHICH** (CRITICAL):

1. **create_calendar_event** - Use when user specifies EXACT times:
   - "Schedule study from 10:00 to 13:30" → use create_calendar_event
   - "Add meeting at 14:00-15:00 tomorrow" → use create_calendar_event  
   - "Block 09:00-12:00 for exam prep" → use create_calendar_event
   - This creates the event EXACTLY at the requested time, no automatic placement.

2. **create_task + plan_task** - Use when user wants AUTO-scheduling:
   - "I need 3 hours of study time this week" → create_task + plan_task
   - "Schedule math homework before Friday" → create_task + plan_task
   - This finds the FIRST available slots and fills them automatically.

**PLANNING WORKFLOW** (When using auto-scheduling):
1. FIRST: ALWAYS call `find_free_slots` or `suggest_study_time` - DO NOT assume availability!
2. THEN: Present the options to the user clearly with times and durations.
3. WAIT: For user confirmation before creating tasks or scheduling.
4. If user confirms, THEN use `create_task` + `plan_task`.

**DAILY OVERRIDES** (FLEXIBLE SCHEDULE):
Users can adjust their schedule for specific days without changing permanent settings:
- "I'm leaving early tomorrow at 10:00" → use `set_daily_override` with type="departure_time", value="10:00"
- "Skip commute tomorrow, I'm staying home" → use `set_daily_override` with type="skip_commute", value="true"
- "No dinner block on Friday" → use `set_daily_override` with type="skip_dinner", value="true"  
- "I'll wake up at 6am tomorrow" → use `set_daily_override` with type="custom_wake", value="06:00"

After setting an override, re-check `find_free_slots` to show the updated availability!

**EXPLAINING SLOT AVAILABILITY** (CRITICAL - READ THIS):
When `find_free_slots` returns data:
- `free_slots`: These are the AVAILABLE time windows
- `blocked_by`: These are the EVENTS that are taking up time
- `awake_hours`: The user's wake/sleep schedule

When user asks "why can't I schedule at X time?":
1. Look at `blocked_by` to find what event is at that time
2. Tell them: "The slot from X to Y is blocked by [EVENT NAME]"
3. NEVER blame "sleep time" unless the time is actually outside awake_hours!
4. If commute is blocking, offer to adjust it: "Commute is blocking that time. Would you like me to adjust your departure time for that day?"

**DO NOT MAKE UP REASONS**. Only cite:
- A specific event from `blocked_by`
- The awake_hours constraint (only if time is before wake_time or after sleep_time)

**TIME UNDERSTANDING** (CRITICAL):
- "Today" means the current calendar date (e.g., if it's 00:30 on Sunday, "today" = Sunday)
- If current time is between 00:00-07:59, the ENTIRE day (08:00-23:00) is still ahead!
- NEVER assume "no slots available" - ALWAYS call the tool first to check

**TIME SUGGESTION RULES**:
- Study/work hours are between user's wake_time and sleep_time
- Prefer afternoon (14:00-18:00) and evening (18:00-21:00) for study sessions
- Always round suggested start times to nice intervals (e.g., 09:00, 10:30, 14:00)

Capabilities:
- You can create tasks, view the schedule, and trigger the scheduler.
- You can adjust daily schedules (commute, dinner, wake time) for specific dates.
- You remember user preferences and past context.

CRITICAL INSTRUCTIONS:
1. **MEMORY WARNING**: The "Relevant Context from Memory" section contains PAST conversations. It is for context only. 
   - If the User's LATEST message contradicts the Memory, **OBEY THE LATEST MESSAGE**.

2. **REAL-TIME DATA**: 
   - Do NOT rely on memory for current calendar events. 
   - ALWAYS use `get_today_overview` or `get_schedule` to check the REAL-TIME schedule.

3. **TOOL USAGE**:
   - If you say you are "Executing" or "Scheduling", you **MUST** emit a tool call in the same turn.
   - Do not say "Executing now" without actually calling the function.
"""

async def process_user_message(user_message: str, db: Session, user_id: int = 1):
    # 0. Get or Create Session (Short Term Memory Context)
    sessions = crud.get_chat_sessions(db, user_id, limit=1)
    if sessions:
        session = sessions[0]
    else:
        session = crud.create_chat_session(db, user_id, title="New Conversation")
    session_id = session.id

    # Save User Message to SQL History
    crud.add_chat_message(db, session_id, "user", user_message)

    # 1. Retrieve Context from Vector Memory (Long Term)
    context = memory.MemoryService.retrieve_context(user_message)
    
    # 2. Retrieve Recent History from SQL (Short Term)
    # Get all messages for this session (ordered by timestamp asc)
    all_msgs = crud.get_chat_messages(db, session_id)
    # Take the last 10 messages to keep context window manageable
    recent_msgs = all_msgs[-10:]
    
    # Current Time Context
    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    
    # 3. Prepare Messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Current Date and Time: {now_str}"},
        {"role": "system", "content": f"Long-Term Memory Context (Use if relevant):\n{context}"}
    ]
    
    # Append Short-Term History (includes the user message we just added)
    for msg in recent_msgs:
        messages.append({"role": msg.role, "content": msg.content})
    
    # 4. Call OpenAI
    try:
        # Using gpt-4o-mini as gpt-5.1-mini is not a valid model identifier
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        final_reply = ""

        # 5. Handle Tool Calls
        if tool_calls:
            messages.append(response_message) # Add the assistant's decision to history
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                tool_output = execute_tool(function_name, function_args, db, user_id)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_output)
                })
            
            # 6. Get Final Response after Tool Execution
            second_response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=messages
            )
            final_reply = second_response.choices[0].message.content
        else:
            final_reply = response_message.content
            
        # 7. Store Interaction in Memory (Vector + SQL)
        memory.MemoryService.store_message("user", user_message) # Vector
        memory.MemoryService.store_message("assistant", final_reply) # Vector
        
        crud.add_chat_message(db, session_id, "assistant", final_reply) # SQL
        
        return final_reply
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return f"System Malfunction: {str(e)}"

def execute_tool(name, args, db: Session, user_id: int):
    print(f"Executing Tool: {name} with {args}")
    
    try:
        # --- Task Tools ---
        if name == "create_task":
            # Parse deadline or default to end of today
            if "deadline" in args and args["deadline"]:
                deadline = datetime.fromisoformat(args["deadline"])
            else:
                # Default: end of today (23:59)
                now = datetime.now()
                deadline = now.replace(hour=23, minute=59, second=59)
            
            # Handle priority input (int or string)
            raw_priority = args.get("priority", "normal")
            if isinstance(raw_priority, int):
                priority = "high" if raw_priority == 1 else "normal"
            else:
                priority = raw_priority

            task = crud.create_task(db, schemas.TaskCreate(
                title=args["title"],
                total_required_time=args["total_required_time"],
                deadline=deadline,
                priority=priority,
                course_tag=args.get("course_tag", "General")
            ), user_id)
            return {"status": "success", "task_id": task.id, "message": f"Directive '{task.title}' initialized."}
            
        elif name == "update_task":
            task_id = args["task_id"]
            # Build update object
            update_data = {}
            if "title" in args: update_data["title"] = args["title"]
            if "total_required_time" in args: update_data["total_required_time"] = args["total_required_time"]
            if "deadline" in args: update_data["deadline"] = datetime.fromisoformat(args["deadline"])
            
            if "priority" in args: 
                raw_p = args["priority"]
                if isinstance(raw_p, int):
                    update_data["priority"] = "high" if raw_p == 1 else "normal"
                else:
                    update_data["priority"] = raw_p
                    
            if "status" in args: update_data["status"] = args["status"]
            
            task = crud.update_task(db, task_id, schemas.TaskUpdate(**update_data))
            if task:
                return {"status": "success", "message": f"Task {task_id} updated."}
            return {"error": "Task not found"}

        elif name == "list_tasks":
            tasks = crud.get_tasks(db, user_id)
            
            # Filter
            if "status" in args:
                tasks = [t for t in tasks if t.status == args["status"]]
            if "course_tag" in args:
                tasks = [t for t in tasks if t.course_tag == args["course_tag"]]
                
            return [{"id": t.id, "title": t.title, "status": t.status, "deadline": str(t.deadline), "scheduled": t.scheduled_minutes, "total": t.total_required_time} for t in tasks]

        elif name == "delete_task":
            task = crud.get_task(db, args["task_id"])
            if not task:
                return {"error": "Task not found"}
            
            # Delete associated Google Calendar events
            user = crud.get_user(db, user_id)
            deleted_events = 0
            if user.google_token and task.study_blocks:
                for block in task.study_blocks:
                    if block.google_event_id:
                        try:
                            calendar_integration.delete_event(user.google_token, block.google_event_id)
                            deleted_events += 1
                        except Exception as e:
                            print(f"Failed to delete calendar event {block.google_event_id}: {e}")
            
            # Now delete the task (cascade deletes study blocks)
            crud.delete_task(db, args["task_id"])
            return {"status": "success", "message": f"Task '{task.title}' deleted. {deleted_events} calendar events removed."}

        elif name == "delete_calendar_event":
            user = crud.get_user(db, user_id)
            if not user.google_token:
                return {"error": "Google Calendar not connected"}
            
            try:
                calendar_integration.delete_event(user.google_token, args["event_id"])
                return {"status": "success", "message": f"Event {args['event_id']} deleted from Google Calendar."}
            except Exception as e:
                return {"error": f"Failed to delete event: {str(e)}"}

        elif name == "delete_calendar_events_by_title":
            user = crud.get_user(db, user_id)
            if not user.google_token:
                return {"error": "Google Calendar not connected"}
            
            title_filter = args["title_contains"].lower()
            target_date = args.get("date")
            
            # Get events to find matching ones
            now = datetime.now().astimezone()
            if target_date:
                start_dt = datetime.fromisoformat(target_date + "T00:00:00").replace(tzinfo=now.tzinfo)
                end_dt = datetime.fromisoformat(target_date + "T23:59:59").replace(tzinfo=now.tzinfo)
            else:
                # Search next 30 days
                start_dt = now
                end_dt = now + timedelta(days=30)
            
            try:
                events = calendar_integration.list_events(
                    user.google_token, 
                    time_min=start_dt.isoformat(), 
                    time_max=end_dt.isoformat()
                )
                
                deleted = 0
                for event in events:
                    event_title = event.get('summary', '').lower()
                    if title_filter in event_title:
                        try:
                            calendar_integration.delete_event(user.google_token, event['id'])
                            deleted += 1
                        except Exception as e:
                            print(f"Failed to delete event {event['id']}: {e}")
                
                return {"status": "success", "message": f"Deleted {deleted} events matching '{args['title_contains']}'."}
            except Exception as e:
                return {"error": f"Failed to search/delete events: {str(e)}"}

        elif name == "update_study_session":
            try:
                new_start = datetime.fromisoformat(args["new_start_time"])
                block = scheduler.reschedule_block(db, args["block_id"], new_start)
                return {"status": "success", "message": f"Study session moved to {block.start_time}."}
            except Exception as e:
                return {"error": f"Rescheduling failed: {str(e)}"}

        # --- Planning Tools ---
        elif name == "create_calendar_event":
            # Direct calendar event creation at specific time
            user = crud.get_user(db, user_id)
            if user:
                db.refresh(user)  # Ensure we have the latest data
            if not user:
                return {"error": f"User {user_id} not found in database."}
            if not user.google_token:
                return {"error": "Google Calendar not connected. Please connect it in Settings."}
            
            try:
                # Parse date and times
                event_date = args["date"]
                start_time_str = args["start_time"]
                end_time_str = args["end_time"]
                split_into_blocks = args.get("split_into_blocks", True)  # Default to splitting
                
                # Build full datetime strings
                tz = datetime.now().astimezone().tzinfo
                start_dt = datetime.fromisoformat(f"{event_date}T{start_time_str}:00").replace(tzinfo=tz)
                end_dt = datetime.fromisoformat(f"{event_date}T{end_time_str}:00").replace(tzinfo=tz)
                
                # Validate end is after start
                if end_dt <= start_dt:
                    return {"error": "End time must be after start time."}
                
                title = args["title"]
                description = "Scheduled by Ultron"  # Always use this description
                
                # Get user preferences for block length
                prefs = crud.get_preferences(db, user_id)
                block_length = prefs.study_block_length if prefs else 50  # Default 50 mins
                break_length = 10  # 10 min breaks between blocks
                
                total_duration_mins = int((end_dt - start_dt).total_seconds() / 60)
                created_events = []
                
                if split_into_blocks and total_duration_mins > block_length:
                    # Split into multiple blocks with breaks
                    current_start = start_dt
                    block_num = 1
                    total_study_mins = 0
                    
                    while current_start < end_dt:
                        # Calculate block end (either block_length or remaining time)
                        remaining = int((end_dt - current_start).total_seconds() / 60)
                        this_block_length = min(block_length, remaining)
                        
                        if this_block_length < 15:  # Skip very short blocks
                            break
                            
                        block_end = current_start + timedelta(minutes=this_block_length)
                        
                        # Create this block
                        block_title = f"{title} (Block {block_num})"
                        g_event = calendar_integration.create_event(
                            user.google_token,
                            summary=block_title,
                            start_time=current_start,
                            end_time=block_end,
                            description=description
                        )
                        created_events.append({
                            "block": block_num,
                            "time": f"{current_start.strftime('%H:%M')}-{block_end.strftime('%H:%M')}",
                            "google_event_id": g_event.get("id")
                        })
                        
                        total_study_mins += this_block_length
                        block_num += 1
                        
                        # Move to next block (add break time)
                        current_start = block_end + timedelta(minutes=break_length)
                    
                    return {
                        "status": "success",
                        "message": f"Created {len(created_events)} study blocks ({block_length} mins each with {break_length} min breaks) from {start_time_str} to {end_time_str}.",
                        "blocks": created_events,
                        "total_study_mins": total_study_mins,
                        "total_blocks": len(created_events)
                    }
                else:
                    # Single event (meetings, short sessions, or split_into_blocks=false)
                    g_event = calendar_integration.create_event(
                        user.google_token,
                        summary=title,
                        start_time=start_dt,
                        end_time=end_dt,
                        description=description
                    )
                    
                    return {
                        "status": "success",
                        "message": f"Event '{title}' created on {event_date} from {start_time_str} to {end_time_str}.",
                        "google_event_id": g_event.get("id"),
                        "duration_mins": total_duration_mins
                    }
            except Exception as e:
                return {"error": f"Failed to create calendar event: {str(e)}"}

        elif name == "plan_task":
            # Trigger the scheduler for this task
            try:
                result = scheduler.schedule_task(db, args["task_id"])
                return {"status": "success", "details": result}
            except Exception as e:
                return {"error": f"Scheduling failed: {str(e)}"}

        elif name == "get_schedule":
            start_date = datetime.fromisoformat(args["start_date"])
            # Ensure timezone awareness for Google Calendar API
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
                
            days = args.get("days", 1)
            end_date = start_date + timedelta(days=days)
            
            user = crud.get_user(db, user_id)
            events = scheduler.get_events_for_range(user, start_date, end_date, db=db)
            
            # Format for LLM - include event IDs for Google Calendar events
            formatted_events = []
            for event in events:
                event_info = {
                    "time": f"{event['start'].strftime('%Y-%m-%d %H:%M')} - {event['end'].strftime('%H:%M')}",
                    "title": event['title'],
                    "source": event.get('source', 'local')
                }
                if event.get('google_event_id'):
                    event_info["google_event_id"] = event['google_event_id']
                formatted_events.append(event_info)
                
            return {"events": formatted_events}

        elif name == "get_today_overview":
            now = datetime.now().astimezone()
            # Start of day (00:00:00) to End of day (23:59:59)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            user = crud.get_user(db, user_id)
            # Fetch events for the WHOLE day, not just from 'now' onwards
            events = scheduler.get_events_for_range(user, start_of_day, end_of_day, db=db)
            
            tasks = crud.get_tasks(db, user_id)
            pending_tasks = [t for t in tasks if t.status == "pending"]
            
            return {
                "date": now.strftime("%Y-%m-%d"),
                "events_count": len(events),
                "pending_tasks_count": len(pending_tasks),
                "events_summary": [f"{e['start'].strftime('%H:%M')}-{e['end'].strftime('%H:%M')} {e['title']}" for e in events],
                "top_priority_tasks": [{"id": t.id, "title": t.title} for t in sorted(pending_tasks, key=lambda x: x.priority)[:3]]
            }

        # --- Conflict & Preferences ---
        elif name == "get_conflicts":
            # Placeholder
            return {"message": "Conflict detection module is online but currently returns no conflicts (Prototype)."}

        elif name == "replan_conflicts":
            return {"message": "Conflict resolution module is online. No conflicts to resolve."}

        elif name == "find_free_slots":
            # Parse dates
            start_str = args["start_date"]
            end_str = args["end_date"]
            min_duration = args.get("min_duration_mins", 30)
            
            # Handle both date-only and datetime formats
            try:
                if "T" in start_str:
                    start_dt = datetime.fromisoformat(start_str)
                else:
                    start_dt = datetime.fromisoformat(start_str + "T00:00:00")
                    
                if "T" in end_str:
                    end_dt = datetime.fromisoformat(end_str)
                else:
                    end_dt = datetime.fromisoformat(end_str + "T23:59:59")
            except:
                return {"error": "Invalid date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"}
            
            # Ensure timezone awareness
            tz = datetime.now().astimezone().tzinfo
            now = datetime.now().astimezone()
            
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=tz)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=tz)
            
            # IMPORTANT: If querying for today, start from NOW (not midnight)
            if start_dt.date() == now.date() and start_dt < now:
                start_dt = now
                
            user = crud.get_user(db, user_id)
            prefs = crud.get_preferences(db, user_id)
            
            if not prefs:
                return {"error": "User preferences not configured."}
            
            # Get existing events (Google Calendar errors are handled gracefully inside)
            events = scheduler.get_events_for_range(user, start_dt, end_dt, db=db)
            
            # Format existing events for context (so LLM knows what's blocking)
            blocking_events = []
            for ev in events:
                blocking_events.append({
                    "title": ev.get("title", "Busy"),
                    "start": ev["start"].strftime("%H:%M"),
                    "end": ev["end"].strftime("%H:%M")
                })
            
            # Calculate gaps
            gaps = scheduler.calculate_free_gaps(start_dt, end_dt, events, prefs)
            
            # Filter by minimum duration and format
            result = []
            for gap_start, gap_end in gaps:
                duration_mins = int((gap_end - gap_start).total_seconds() / 60)
                if duration_mins >= min_duration:
                    result.append({
                        "start": gap_start.strftime("%Y-%m-%d %H:%M"),
                        "end": gap_end.strftime("%H:%M"),
                        "duration_mins": duration_mins,
                        "duration_human": f"{duration_mins // 60}h {duration_mins % 60}m" if duration_mins >= 60 else f"{duration_mins}m"
                    })
            
            # Build clear explanation
            response = {
                "free_slots": result,
                "total_free_minutes": sum(s["duration_mins"] for s in result) if result else 0,
                "blocked_by": blocking_events,
                "awake_hours": f"{prefs.wake_time} to {prefs.sleep_time}",
                "explanation": f"Scheduling window: {prefs.wake_time} - {prefs.sleep_time}. Slots are gaps between existing events."
            }
            
            if not result:
                response["message"] = "No free slots found in the requested time range."
                
            return response

        elif name == "suggest_study_time":
            duration_mins = args["duration_mins"]
            start_str = args["start_date"]
            end_str = args.get("end_date", start_str)
            preferred_time = args.get("preferred_time", "any")
            
            # Parse dates (same logic as find_free_slots)
            tz = datetime.now().astimezone().tzinfo
            now = datetime.now().astimezone()
            start_dt = datetime.fromisoformat(start_str + "T00:00:00").replace(tzinfo=tz)
            end_dt = datetime.fromisoformat(end_str + "T23:59:59").replace(tzinfo=tz)
            
            # IMPORTANT: If querying for today, start from NOW
            if start_dt.date() == now.date() and start_dt < now:
                start_dt = now
            
            user = crud.get_user(db, user_id)
            prefs = crud.get_preferences(db, user_id)
            
            if not prefs:
                return {"error": "User preferences not configured."}
            
            events = scheduler.get_events_for_range(user, start_dt, end_dt, db=db)
            gaps = scheduler.calculate_free_gaps(start_dt, end_dt, events, prefs)
            
            # Filter gaps that can fit the duration
            suitable_gaps = []
            for gap_start, gap_end in gaps:
                gap_mins = int((gap_end - gap_start).total_seconds() / 60)
                if gap_mins >= duration_mins:
                    # Score by preference
                    hour = gap_start.hour
                    score = 0
                    if preferred_time == "morning" and 6 <= hour < 12:
                        score = 10
                    elif preferred_time == "afternoon" and 12 <= hour < 17:
                        score = 10
                    elif preferred_time == "evening" and 17 <= hour < 22:
                        score = 10
                    elif preferred_time == "any":
                        score = 5
                    
                    suitable_gaps.append({
                        "start": gap_start.strftime("%Y-%m-%d %H:%M"),
                        "end": (gap_start + timedelta(minutes=duration_mins)).strftime("%H:%M"),
                        "score": score
                    })
            
            # Sort by score (descending) then by start time
            suitable_gaps.sort(key=lambda x: (-x["score"], x["start"]))
            
            if not suitable_gaps:
                return {"message": f"No {duration_mins}-minute slots available in the given range.", "suggestions": []}
            
            # Return top 3 suggestions
            return {"suggestions": suitable_gaps[:3]}

        elif name == "get_preferences":
            pref = crud.get_preferences(db, user_id)
            if pref:
                return {
                    "wake_time": str(pref.wake_time),
                    "sleep_time": str(pref.sleep_time),
                    "study_block_length": pref.study_block_length,
                    "max_study_minutes_per_day": pref.max_study_minutes_per_day
                }
            return {"error": "Preferences not found"}

        elif name == "update_preferences":
            update_data = {}
            if "wake_time" in args: update_data["wake_time"] = args["wake_time"]
            if "sleep_time" in args: update_data["sleep_time"] = args["sleep_time"]
            if "study_block_length" in args: update_data["study_block_length"] = args["study_block_length"]
            if "max_study_minutes_per_day" in args: update_data["max_study_minutes_per_day"] = args["max_study_minutes_per_day"]
            
            pref = crud.update_preferences(db, user_id, schemas.PreferenceCreate(**update_data))
            return {"status": "success", "message": "Preferences updated."}

        # --- Daily Overrides ---
        elif name == "set_daily_override":
            date = args["date"]
            override_type = args["override_type"]
            value = args["value"]
            note = args.get("note")
            
            override = crud.set_daily_override(db, user_id, date, override_type, value, note)
            
            type_descriptions = {
                "departure_time": f"departure time set to {value}",
                "skip_commute": "commute blocks removed",
                "skip_dinner": "dinner block removed", 
                "custom_wake": f"wake time set to {value}"
            }
            
            return {
                "status": "success",
                "message": f"Override set for {date}: {type_descriptions.get(override_type, override_type)}",
                "override": {
                    "id": override.id,
                    "date": override.date,
                    "type": override.override_type,
                    "value": override.value
                }
            }

        elif name == "get_daily_overrides":
            date = args.get("date")
            overrides = crud.get_daily_overrides(db, user_id, date)
            
            return {
                "overrides": [
                    {
                        "id": o.id,
                        "date": o.date,
                        "type": o.override_type,
                        "value": o.value,
                        "note": o.note
                    } for o in overrides
                ]
            }

        elif name == "clear_daily_override":
            date = args["date"]
            override_type = args["override_type"]
            
            if override_type == "all":
                crud.clear_daily_overrides_for_date(db, user_id, date)
                return {"status": "success", "message": f"All overrides cleared for {date}"}
            else:
                # Find and delete specific override
                overrides = crud.get_daily_overrides(db, user_id, date)
                for o in overrides:
                    if o.override_type == override_type:
                        crud.delete_daily_override(db, o.id)
                        return {"status": "success", "message": f"Override '{override_type}' cleared for {date}"}
                return {"status": "not_found", "message": f"No override of type '{override_type}' found for {date}"}

        return {"error": f"Tool '{name}' not implemented"}
        
    except Exception as e:
        print(f"Tool Execution Error: {e}")
        return {"error": f"Execution failed: {str(e)}"}

def process_user_message_streaming(user_message: str, db: Session, user_id: int = 1, session_id: int = None):
    """
    Generator function that streams LLM responses.
    Note: This is a regular generator (not async) for compatibility with StreamingResponse.
    """
    # 0. Get or Create Session (Short Term Memory Context)
    if session_id:
        # Verify session exists
        session = crud.get_chat_session(db, session_id)
        if not session:
             # Fallback if invalid ID passed
             session = crud.create_chat_session(db, user_id, title=user_message[:30])
             session_id = session.id
    else:
        # Create NEW session if no ID provided
        session = crud.create_chat_session(db, user_id, title=user_message[:30])
        session_id = session.id

    # Save User Message to SQL History
    crud.add_chat_message(db, session_id, "user", user_message)

    # 1. Retrieve Context from Vector Memory (Long Term)
    context = memory.MemoryService.retrieve_context(user_message)
    
    # 2. Retrieve Recent History from SQL (Short Term)
    all_msgs = crud.get_chat_messages(db, session_id)
    recent_msgs = all_msgs[-10:]
    
    # Current Time Context
    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    
    # 3. Prepare Messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Current Date and Time: {now_str}"},
        {"role": "system", "content": f"Long-Term Memory Context (Use if relevant):\n{context}"}
    ]
    
    for msg in recent_msgs:
        messages.append({"role": msg.role, "content": msg.content})
    
    # 4. Call OpenAI with Streaming
    try:
        stream = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            stream=True
        )
        
        tool_calls_buffer = []
        final_content = ""
        
        for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle Tool Calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if len(tool_calls_buffer) <= tc.index:
                        tool_calls_buffer.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                    
                    tc_buffer = tool_calls_buffer[tc.index]
                    if tc.id: tc_buffer["id"] += tc.id
                    if tc.function.name: tc_buffer["function"]["name"] += tc.function.name
                    if tc.function.arguments: tc_buffer["function"]["arguments"] += tc.function.arguments
            
            # Handle Content
            if delta.content:
                final_content += delta.content
                yield delta.content

        # 5. Handle Tool Execution with support for MULTIPLE ROUNDS of tool calls
        max_tool_rounds = 3  # Prevent infinite loops
        tool_round = 0
        
        while tool_calls_buffer and tool_round < max_tool_rounds:
            tool_round += 1
            print(f"Tool execution round {tool_round}...")
            
            # Reconstruct the assistant message for history
            assistant_msg = {
                "role": "assistant",
                "content": final_content if final_content else None,
                "tool_calls": tool_calls_buffer
            }
            messages.append(assistant_msg)
            
            # Execute Tools
            for tc in tool_calls_buffer:
                function_name = tc["function"]["name"]
                try:
                    function_args = json.loads(tc["function"]["arguments"])
                    tool_output = execute_tool(function_name, function_args, db, user_id)
                    print(f"Tool Output: {tool_output}")
                except json.JSONDecodeError:
                    tool_output = {"error": "Invalid JSON arguments"}
                except Exception as e:
                    print(f"Tool execution exception: {e}")
                    tool_output = {"error": str(e)}
                
                messages.append({
                    "tool_call_id": tc["id"],
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_output)
                })
            
            # Clear buffer for next round
            tool_calls_buffer = []
            
            # 6. Get Response (with tools available for follow-up calls!)
            print(f"Getting response after tool round {tool_round}...")
            follow_up_stream = client.chat.completions.create(
                model="gpt-5-mini",
                messages=messages,
                tools=TOOLS,  # Allow follow-up tool calls!
                tool_choice="auto",
                stream=True
            )
            
            round_content = ""
            for chunk in follow_up_stream:
                delta = chunk.choices[0].delta
                
                # Check for more tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if len(tool_calls_buffer) <= tc.index:
                            tool_calls_buffer.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                        
                        tc_buffer = tool_calls_buffer[tc.index]
                        if tc.id: tc_buffer["id"] += tc.id
                        if tc.function.name: tc_buffer["function"]["name"] += tc.function.name
                        if tc.function.arguments: tc_buffer["function"]["arguments"] += tc.function.arguments
                
                if delta.content:
                    round_content += delta.content
                    final_content += delta.content
                    yield delta.content
            
            print(f"Round {tool_round} content: {round_content[:100] if round_content else 'EMPTY'}...")
            # Loop continues if tool_calls_buffer was populated again

        # 7. Store Interaction in Memory
        memory.MemoryService.store_message("user", user_message)
        memory.MemoryService.store_message("assistant", final_content)
        crud.add_chat_message(db, session_id, "assistant", final_content)
        
    except Exception as e:
        print(f"LLM Stream Error: {e}")
        yield f"System Malfunction: {str(e)}"
