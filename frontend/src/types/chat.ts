export type ChatRole = "user" | "assistant";

export interface ChatHistoryMessage {
  role: ChatRole;
  content: string;
}

export interface ChatRequestPayload {
  message: string;
  stream: boolean;
  system_prompt?: string;
  history: ChatHistoryMessage[];
}

export interface ChatResponsePayload {
  reply: string;
  model: string;
  provider: string;
}

export interface ChatStreamChunk {
  choices?: Array<{
    delta?: {
      content?: string;
    };
  }>;
  error?: {
    message?: string;
  };
}

export interface UiMessage {
  id: string;
  role: ChatRole;
  content: string;
  state?: "done" | "streaming" | "error";
}
