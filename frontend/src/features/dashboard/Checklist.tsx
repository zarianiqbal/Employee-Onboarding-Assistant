import { useMemo } from 'react';

import { ProgressBar } from '../../components/ProgressBar';
import type { Checklist as ChecklistData, EmployeeTask } from '../../api/types';
import './Checklist.css';

interface ChecklistProps {
  data: ChecklistData;
  onToggle: (task: EmployeeTask) => void;
  pendingIds: Set<number>;
}

const PHASE_ORDER = ['Pre-boarding', 'Day 1', 'Week 1', 'Week 2', 'Month 1'];

/** Interactive onboarding checklist grouped by phase, with a progress bar. */
export function Checklist({ data, onToggle, pendingIds }: ChecklistProps) {
  const byPhase = useMemo(() => {
    const groups = new Map<string, EmployeeTask[]>();
    for (const task of data.tasks) {
      const list = groups.get(task.phase) ?? [];
      list.push(task);
      groups.set(task.phase, list);
    }
    return PHASE_ORDER.filter((p) => groups.has(p)).map((p) => [p, groups.get(p)!] as const);
  }, [data.tasks]);

  return (
    <section className="card" aria-labelledby="checklist-title">
      <h2 id="checklist-title">Onboarding checklist</h2>
      <ProgressBar
        value={data.completion_percentage}
        label={`${data.completed} of ${data.total} tasks complete`}
      />

      <div className="checklist">
        {byPhase.map(([phase, tasks]) => (
          <div key={phase} className="checklist__phase">
            <h3 className="checklist__phase-title">{phase}</h3>
            <ul className="checklist__list">
              {tasks.map((task) => {
                const done = task.status === 'Completed';
                const busy = pendingIds.has(task.employee_task_id);
                return (
                  <li key={task.employee_task_id} className="checklist__item">
                    <label className={`checklist__label ${done ? 'is-done' : ''}`}>
                      <input
                        type="checkbox"
                        checked={done}
                        disabled={busy}
                        onChange={() => onToggle(task)}
                      />
                      <span className="checklist__text">
                        <span className="checklist__task-title">
                          {task.title}
                          {task.is_required && (
                            <span className="checklist__required" aria-label="required">
                              {' '}
                              *
                            </span>
                          )}
                        </span>
                        {task.description && (
                          <span className="checklist__desc">{task.description}</span>
                        )}
                        {task.due_date && (
                          <span className="checklist__due">Due {task.due_date}</span>
                        )}
                      </span>
                      {done ? (
                        <span className="badge badge-success">Done</span>
                      ) : (
                        <span className="badge badge-muted">{task.category ?? 'Task'}</span>
                      )}
                    </label>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
