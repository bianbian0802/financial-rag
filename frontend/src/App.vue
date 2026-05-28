<script setup lang="ts">
import { computed, nextTick, ref } from "vue";

import { requestChat, requestChatStream } from "./lib/chat-client";
import type { ChatHistoryMessage, UiMessage } from "./types/chat";

const messageInput = ref("请结合金融知识库场景，简洁解释一下 RAG 的价值。");
const systemPrompt = ref("你是一名严谨、清晰的金融 AI 助手。");
const useStreaming = ref(true);
const isSending = ref(false);
const statusText = ref("等待发送");
const statusKind = ref<"idle" | "success" | "error">("idle");
const messages = ref<UiMessage[]>([]);
const debugLogs = ref<string[]>(["等待请求..."]);
const messageViewport = ref<HTMLElement | null>(null);
const nextMessageId = ref(0);

/**
 * Build the history payload expected by the backend from rendered UI messages.
 */
function buildHistory(): ChatHistoryMessage[] {
  return messages.value
    .filter((message) => message.state !== "error")
    .map((message) => ({
      role: message.role,
      content: message.content,
    }));
}

/**
 * Generate a stable local id for a new message bubble.
 */
function createMessageId(): string {
  nextMessageId.value += 1;
  return `message-${nextMessageId.value}`;
}

/**
 * Append a new line into the log area and keep the latest event visible.
 */
function appendLog(line: string): void {
  if (debugLogs.value.length === 1 && debugLogs.value[0] === "等待请求...") {
    debugLogs.value = [];
  }
  debugLogs.value.push(line);
}

/**
 * Update the status pill shown in the top-right corner.
 */
function setStatus(text: string, kind: "idle" | "success" | "error" = "idle"): void {
  statusText.value = text;
  statusKind.value = kind;
}

/**
 * Scroll the message viewport to the latest message after DOM updates.
 */
async function scrollMessagesToBottom(): Promise<void> {
  await nextTick();
  if (messageViewport.value) {
    messageViewport.value.scrollTop = messageViewport.value.scrollHeight;
  }
}

/**
 * Clear the debug panel back to its default placeholder text.
 */
function resetLogs(): void {
  debugLogs.value = ["等待请求..."];
}

/**
 * Clear the current chat transcript and keep the current prompt settings.
 */
function clearConversation(): void {
  if (isSending.value) {
    return;
  }
  messages.value = [];
  resetLogs();
  setStatus("等待发送");
}

/**
 * Clear only the current composer text.
 */
function clearInput(): void {
  if (isSending.value) {
    return;
  }
  messageInput.value = "";
}

/**
 * Create and append a message bubble to the current transcript.
 */
function pushMessage(role: "user" | "assistant", content: string, state: UiMessage["state"] = "done"): UiMessage {
  const createdMessage: UiMessage = {
    id: createMessageId(),
    role,
    content,
    state,
  };
  messages.value.push(createdMessage);
  return messages.value[messages.value.length - 1] as UiMessage;
}

/**
 * Yield control to the browser so the latest chunk can be painted.
 */
async function allowBrowserPaint(): Promise<void> {
  await nextTick();
  await new Promise<void>((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}

/**
 * Handle a streaming assistant reply by mutating the placeholder bubble in place.
 */
async function runStreamingReply(assistantMessage: UiMessage, latestMessage: string): Promise<void> {
  await requestChatStream(
    {
      message: latestMessage,
      stream: true,
      system_prompt: systemPrompt.value.trim() || undefined,
      history: buildHistory().slice(0, -1),
    },
    async (eventPayload) => {
      appendLog(`SSE -> ${eventPayload}`);
    },
    async (chunk) => {
      assistantMessage.content += chunk;
      await allowBrowserPaint();
      await scrollMessagesToBottom();
    },
  );
}

/**
 * Handle a non-streaming assistant reply and update the placeholder bubble once.
 */
async function runStandardReply(assistantMessage: UiMessage, latestMessage: string): Promise<void> {
  const responsePayload = await requestChat({
    message: latestMessage,
    stream: false,
    system_prompt: systemPrompt.value.trim() || undefined,
    history: buildHistory().slice(0, -1),
  });
  appendLog(`JSON -> ${JSON.stringify(responsePayload, null, 2)}`);
  assistantMessage.content = responsePayload.reply || "模型没有返回内容。";
}

/**
 * Submit the current user input to the backend and render the assistant response.
 */
async function sendMessage(): Promise<void> {
  if (isSending.value) {
    return;
  }

  const latestMessage = messageInput.value.trim();
  if (!latestMessage) {
    setStatus("请先输入问题", "error");
    return;
  }

  isSending.value = true;
  appendLog(`POST /api/v1/chat`);
  appendLog(`stream = ${useStreaming.value}`);
  appendLog(`history_count = ${messages.value.length}`);
  setStatus(useStreaming.value ? "请求中，等待首段流..." : "请求中，等待完整回答...");

  pushMessage("user", latestMessage, "done");
  const assistantMessage = pushMessage("assistant", "", "streaming");
  messageInput.value = "";
  await scrollMessagesToBottom();

  try {
    if (useStreaming.value) {
      await runStreamingReply(assistantMessage, latestMessage);
      assistantMessage.state = "done";
      if (!assistantMessage.content) {
        assistantMessage.content = "模型没有返回内容。";
      }
      setStatus("流式回复完成", "success");
      return;
    }

    await runStandardReply(assistantMessage, latestMessage);
    assistantMessage.state = "done";
    setStatus("普通回复完成", "success");
  } catch (error) {
    const messageText = error instanceof Error ? error.message : "未知错误";
    assistantMessage.content = `请求失败：${messageText}`;
    assistantMessage.state = "error";
    appendLog(`ERROR -> ${messageText}`);
    setStatus("请求失败", "error");
  } finally {
    isSending.value = false;
    await scrollMessagesToBottom();
  }
}

/**
 * Map the current message state to a user-facing label.
 */
function buildAssistantStateLabel(message: UiMessage): string {
  if (message.state === "streaming") {
    return "助手 / 流式返回中";
  }
  if (message.state === "error") {
    return "助手 / 失败";
  }
  return "助手";
}

/**
 * Handle Enter to send and Shift+Enter to insert a newline.
 */
function handleComposerKeydown(event: KeyboardEvent): void {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    void sendMessage();
  }
}

const hasMessages = computed(() => messages.value.length > 0);
const joinedLogs = computed(() => debugLogs.value.join("\n"));
</script>

<template>
  <main class="app-shell">
    <section class="chat-layout">
      <header class="hero-bar">
        <div class="hero-copy">
          <span class="eyebrow">VUE STREAM CHAT</span>
          <h1>Financial RAG 对话前端</h1>
          <p>
            这个前端基于 Vue 3 + Vite + TypeScript，实现了居中的聊天窗口、流式回复和基础多轮对话。
          </p>
        </div>

        <div class="hero-actions">
          <span class="status-pill" :class="`status-pill--${statusKind}`">状态：{{ statusText }}</span>
          <button class="ghost-button" type="button" :disabled="isSending" @click="clearConversation">
            清空会话
          </button>
        </div>
      </header>

      <section class="controls-panel">
        <label class="toggle-card">
          <input v-model="useStreaming" type="checkbox" :disabled="isSending" />
          <span>流式返回</span>
        </label>

        <label class="prompt-field">
          <span>系统提示词</span>
          <input
            v-model="systemPrompt"
            type="text"
            :disabled="isSending"
            placeholder="例如：你是一名严谨、清晰的金融 AI 助手。"
          />
        </label>
      </section>

      <section class="content-panel">
        <div ref="messageViewport" class="messages-panel">
          <div v-if="!hasMessages" class="empty-state">
            <h2>开始你的第一轮对话</h2>
            <p>
              发送消息后，用户问题会先落在聊天区，助手回复会根据你的勾选状态，走普通返回或流式增量更新。
            </p>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="message-row"
            :class="`message-row--${message.role}`"
          >
            <div class="message-card">
              <span
                class="message-meta"
                :class="{ 'message-meta--streaming': message.state === 'streaming' }"
              >
                {{ message.role === "user" ? "你" : buildAssistantStateLabel(message) }}
              </span>
              <div
                class="message-bubble"
                :class="[
                  `message-bubble--${message.role}`,
                  { 'message-bubble--error': message.state === 'error' },
                  { 'message-bubble--streaming': message.state === 'streaming' },
                ]"
              >
                {{ message.content }}
              </div>
            </div>
          </article>
        </div>
      </section>

      <footer class="composer-panel">
        <textarea
          v-model="messageInput"
          :disabled="isSending"
          placeholder="输入你的问题。Enter 发送，Shift + Enter 换行。"
          @keydown="handleComposerKeydown"
        />

        <div class="composer-panel__bottom">
          <span class="composer-hint">开发环境下默认通过 Vite 代理请求 `http://127.0.0.1:8000/api`。</span>

          <div class="composer-actions">
            <button class="ghost-button" type="button" :disabled="isSending" @click="clearInput">
              清空输入
            </button>
            <button class="primary-button" type="button" :disabled="isSending" @click="sendMessage">
              {{ isSending ? "发送中..." : "发送消息" }}
            </button>
          </div>
        </div>
      </footer>
    </section>
  </main>
</template>
