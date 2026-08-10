import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { ApiError, api } from '../../api/client';
import type { Checklist as ChecklistData, Employee, EmployeeTask } from '../../api/types';
import { ChatDrawer } from '../chat/ChatDrawer';
import { DocumentUpload } from '../documents/DocumentUpload';
import { Checklist } from './Checklist';

/** The onboarding dashboard: profile summary, checklist, uploads, and chat. */
export function DashboardPage() {
  const { employeeId } = useParams();
  const id = Number(employeeId);

  const [employee, setEmployee] = useState<Employee | null>(null);
  const [checklist, setChecklist] = useState<ChecklistData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingIds, setPendingIds] = useState<Set<number>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [emp, list] = await Promise.all([api.getEmployee(id), api.getChecklist(id)]);
      setEmployee(emp);
      setChecklist(list);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 404
          ? 'We could not find that employee.'
          : 'Failed to load the dashboard. Please try again.',
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!Number.isNaN(id)) void load();
  }, [id, load]);

  const onToggle = useCallback(
    async (task: EmployeeTask) => {
      const nextStatus = task.status === 'Completed' ? 'Pending' : 'Completed';

      // Optimistically update the UI, then persist. Roll back on failure.
      setChecklist((prev) => prev && applyStatus(prev, task.employee_task_id, nextStatus));
      setPendingIds((prev) => new Set(prev).add(task.employee_task_id));

      try {
        await api.updateTask(task.employee_task_id, nextStatus);
      } catch {
        setChecklist((prev) => prev && applyStatus(prev, task.employee_task_id, task.status));
      } finally {
        setPendingIds((prev) => {
          const next = new Set(prev);
          next.delete(task.employee_task_id);
          return next;
        });
      }
    },
    [],
  );

  if (Number.isNaN(id)) {
    return <ErrorState message="Invalid employee id." />;
  }
  if (loading) {
    return (
      <div className="card" aria-busy="true">
        Loading your onboarding dashboard…
      </div>
    );
  }
  if (error || !employee || !checklist) {
    return <ErrorState message={error ?? 'Something went wrong.'} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      <section className="card" aria-labelledby="welcome">
        <h2 id="welcome">Welcome, {employee.first_name}! 👋</h2>
        <p style={{ marginBottom: 0, color: 'var(--color-text-muted)' }}>
          {employee.job_title ? `${employee.job_title} · ` : ''}
          {employee.department ?? 'Onboarding in progress'}
          {' · '}
          <span className="badge badge-muted">{employee.invitation_status}</span>
        </p>
      </section>

      <Checklist data={checklist} onToggle={onToggle} pendingIds={pendingIds} />
      <DocumentUpload employeeId={id} />

      <p>
        <Link to="/register">← Register another new hire</Link>
      </p>

      <ChatDrawer employeeId={id} />
    </div>
  );
}

/** Return a new checklist with one task's status changed and progress recomputed. */
function applyStatus(
  checklist: ChecklistData,
  employeeTaskId: number,
  status: EmployeeTask['status'],
): ChecklistData {
  const tasks = checklist.tasks.map((t) =>
    t.employee_task_id === employeeTaskId
      ? { ...t, status, completed_at: status === 'Completed' ? new Date().toISOString() : null }
      : t,
  );
  const completed = tasks.filter((t) => t.status === 'Completed').length;
  const pct = tasks.length ? Math.round((completed / tasks.length) * 1000) / 10 : 0;
  return { ...checklist, tasks, completed, completion_percentage: pct };
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="card">
      <div className="toast toast-error" role="alert">
        {message}
      </div>
      <Link to="/register">← Back to registration</Link>
    </div>
  );
}
