// Minimal SSE-over-fetch client for the streaming audit endpoint.
// Native EventSource can't do POST bodies, so we read the streamed
// response body directly and split it into SSE frames ourselves.

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://ai-compliance-auditor.onrender.com";

export interface StreamEvent {
  event: string;
  data: any;
}

export async function streamAudit(
  policy: string,
  config: string,
  onEvent: (evt: StreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/audit/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ policy, config }),
    signal,
  });

  if (!response.ok || !response.body) {
    let detail = response.statusText;
    try {
      const err = await response.json();
      detail = err.detail || detail;
    } catch {
      /* body wasn't JSON, fall back to statusText */
    }
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      if (!frame.trim()) continue;
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data = line.slice(6);
      }
      try {
        onEvent({ event, data: JSON.parse(data) });
      } catch {
        onEvent({ event, data });
      }
    }
  }
}
