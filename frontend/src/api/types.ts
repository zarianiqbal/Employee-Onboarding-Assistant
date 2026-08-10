/** Shared API types mirroring the backend Pydantic schemas. */

export type InvitationStatus = 'PendingAcceptance' | 'Accepted' | 'Revoked';

export interface Employee {
  employee_id: number;
  first_name: string;
  last_name: string;
  personal_email: string;
  job_title: string | null;
  department: string | null;
  region: string | null;
  clearance_level: string | null;
  start_date: string | null;
  date_of_birth: string | null;
  phone_number: string | null;
  home_address: string | null;
  invitation_status: InvitationStatus;
  created_at: string;
  updated_at: string;
}

export interface EmployeeCreate {
  first_name: string;
  last_name: string;
  personal_email: string;
  job_title?: string;
  department?: string;
  region?: string;
  start_date?: string;
}

export type TaskStatus = 'Pending' | 'InProgress' | 'Completed' | 'Skipped';

export interface EmployeeTask {
  employee_task_id: number;
  task_id: number;
  title: string;
  description: string | null;
  phase: string;
  category: string | null;
  status: TaskStatus;
  due_date: string | null;
  completed_at: string | null;
  is_required: boolean;
}

export interface Checklist {
  employee_id: number;
  total: number;
  completed: number;
  completion_percentage: number;
  tasks: EmployeeTask[];
}

export interface SasTokenResponse {
  upload_url: string;
  blob_name: string;
  container: string;
  expires_at: string;
  required_headers: Record<string, string>;
}

export interface DocumentRecord {
  document_id: number;
  employee_id: number;
  document_type: string;
  original_file_name: string;
  container_name: string;
  blob_uri: string;
  content_type: string | null;
  size_bytes: number | null;
  uploaded_at: string;
}

export interface Citation {
  title: string;
  source: string;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
