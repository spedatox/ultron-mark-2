const API_URL = "http://127.0.0.1:8000";

export async function fetchTasks() {
  const res = await fetch(`${API_URL}/tasks/`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function createTask(task: any) {
  const res = await fetch(`${API_URL}/tasks/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(task),
  });
  if (!res.ok) throw new Error("Failed to create task");
  return res.json();
}

export async function fetchPreferences() {
  const res = await fetch(`${API_URL}/preferences/`);
  if (!res.ok) throw new Error("Failed to fetch preferences");
  return res.json();
}

export async function updatePreferences(preferences: any) {
  const res = await fetch(`${API_URL}/preferences/`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(preferences),
  });
  if (!res.ok) throw new Error("Failed to update preferences");
  return res.json();
}

export async function getAuthUrl() {
  const res = await fetch(`${API_URL}/auth/google/url`);
  if (!res.ok) throw new Error("Failed to get auth url");
  return res.json();
}

export async function getAuthStatus() {
  const res = await fetch(`${API_URL}/auth/status`);
  if (!res.ok) throw new Error("Failed to get auth status");
  return res.json();
}

export async function scheduleTask(taskId: number) {
  const res = await fetch(`${API_URL}/schedule/task/${taskId}`, {
    method: "POST",
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to schedule task");
  }
  return res.json();
}

export async function fetchEvents(start: string, end: string) {
  const params = new URLSearchParams({ start, end });
  const res = await fetch(`${API_URL}/schedule/events?${params}`);
  if (!res.ok) throw new Error("Failed to fetch events");
  return res.json();
}

export async function fetchConflicts() {
  const res = await fetch(`${API_URL}/schedule/conflicts`);
  if (!res.ok) throw new Error("Failed to fetch conflicts");
  return res.json();
}

export async function sendChatMessage(message: string, sessionId?: number) {
  const res = await fetch(`${API_URL}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${API_URL}/chat/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function fetchSessionMessages(sessionId: number) {
  const res = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  
  const res = await fetch(`${API_URL}/chat/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload file");
  return res.json();
}

export async function fetchFixedSchedules() {
  const res = await fetch(`${API_URL}/schedule/fixed`);
  if (!res.ok) throw new Error("Failed to fetch fixed schedules");
  return res.json();
}

export async function createFixedSchedule(schedule: any) {
  const res = await fetch(`${API_URL}/schedule/fixed`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(schedule),
  });
  if (!res.ok) throw new Error("Failed to create fixed schedule");
  return res.json();
}

export async function deleteFixedSchedule(id: number) {
  const res = await fetch(`${API_URL}/schedule/fixed/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete fixed schedule");
  return res.json();
}

export async function streamChat(message: string, sessionId?: number, signal?: AbortSignal) {
  const res = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!res.ok) throw new Error("Failed to start stream");
  return res;
}

export async function clearAllChatHistory() {
  const res = await fetch(`${API_URL}/chat/sessions/all`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to clear chat history");
  return res.json();
}
