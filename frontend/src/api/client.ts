/** Thin typed API client for the onboarding backend. */
import type {
  Checklist,
  ChatMessage,
  ChatResponse,
  DocumentRecord,
  Employee,
  EmployeeCreate,
  EmployeeTask,
  SasTokenResponse,
  TaskStatus,
} from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(resp.status, detail);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  // --- Employees ---
  createEmployee: (payload: EmployeeCreate) =>
    request<Employee>('/api/v1/employees', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getEmployee: (id: number) => request<Employee>(`/api/v1/employees/${id}`),

  updateEmployee: (id: number, changes: Partial<Employee>) =>
    request<Employee>(`/api/v1/employees/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(changes),
    }),

  // --- Checklist / tasks ---
  getChecklist: (id: number) => request<Checklist>(`/api/v1/employees/${id}/tasks`),

  updateTask: (employeeTaskId: number, status: TaskStatus) =>
    request<EmployeeTask>(`/api/v1/tasks/${employeeTaskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  // --- Documents ---
  requestSasToken: (
    employeeId: number,
    fileName: string,
    contentType: string,
    documentType: string,
  ) =>
    request<SasTokenResponse>(`/api/v1/employees/${employeeId}/documents/sas`, {
      method: 'POST',
      body: JSON.stringify({
        file_name: fileName,
        content_type: contentType,
        document_type: documentType,
      }),
    }),

  commitDocument: (
    employeeId: number,
    payload: {
      blob_name: string;
      original_file_name: string;
      document_type: string;
      content_type?: string;
      size_bytes?: number;
    },
  ) =>
    request<DocumentRecord>(`/api/v1/employees/${employeeId}/documents`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listDocuments: (employeeId: number) =>
    request<DocumentRecord[]>(`/api/v1/employees/${employeeId}/documents`),

  // --- Chat ---
  chat: (employeeId: number, message: string, history: ChatMessage[] = []) =>
    request<ChatResponse>('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ employee_id: employeeId, message, history }),
    }),

  /** Streamed chat: yields text deltas, then citations via callback. */
  chatStream: async (
    employeeId: number,
    message: string,
    history: ChatMessage[],
    onDelta: (text: string) => void,
    onCitations?: (citations: ChatResponse['citations']) => void,
  ): Promise<void> => {
    const resp = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_id: employeeId, message, history }),
    });
    if (!resp.ok || !resp.body) {
      throw new ApiError(resp.status, 'Chat stream failed');
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    // Parse Server-Sent Events: events are separated by a blank line, and each
    // carries a `data:` JSON payload with either a delta or citations.
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() ?? '';
      for (const event of events) {
        const line = event.split('\n').find((l) => l.startsWith('data:'));
        if (!line) continue;
        try {
          const payload = JSON.parse(line.slice(5).trim());
          if (typeof payload.delta === 'string') onDelta(payload.delta);
          if (payload.citations && onCitations) onCitations(payload.citations);
        } catch {
          /* ignore keep-alive / non-JSON frames */
        }
      }
    }
  },
};
