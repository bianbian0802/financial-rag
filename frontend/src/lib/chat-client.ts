import type {
  ChatRequestPayload,
  ChatResponsePayload,
  ChatStreamChunk,
} from "../types/chat";

const chatEndpoint = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api/v1/chat`;

/**
 * Build a readable error string from a failed backend response.
 */
export async function buildErrorMessage(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const payload = (await response.json()) as { message?: string; error_code?: string };
    return payload.message ?? payload.error_code ?? "请求失败。";
  }
  return (await response.text()) || "请求失败。";
}

/**
 * Send a non-streaming chat request and return the normalized JSON payload.
 */
export async function requestChat(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
  const response = await fetch(chatEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await buildErrorMessage(response));
  }

  return (await response.json()) as ChatResponsePayload;
}

/**
 * Send a streaming chat request and emit each parsed SSE payload to the caller.
 */
export async function requestChatStream(
  payload: ChatRequestPayload,
  onEvent: (eventPayload: string) => void | Promise<void>,
  onChunk: (chunk: string) => void | Promise<void>,
): Promise<void> {
  const response = await fetch(chatEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await buildErrorMessage(response));
  }

  if (!response.body) {
    throw new Error("浏览器没有返回可读流。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const eventBlock of events) {
      const dataLines = eventBlock
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim());

      if (!dataLines.length) {
        continue;
      }

      const eventPayload = dataLines.join("\n");
      await onEvent(eventPayload);

      if (eventPayload === "[DONE]") {
        return;
      }

      const parsedChunk = JSON.parse(eventPayload) as ChatStreamChunk;
      if (parsedChunk.error?.message) {
        throw new Error(parsedChunk.error.message);
      }

      const chunkText = parsedChunk.choices?.[0]?.delta?.content ?? "";
      if (chunkText) {
        await onChunk(chunkText);
      }
    }
  }
}
