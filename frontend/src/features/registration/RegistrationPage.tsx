import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiError, api } from '../../api/client';
import type { EmployeeCreate } from '../../api/types';

const DEPARTMENTS = [
  'Engineering',
  'Sales',
  'Marketing',
  'Finance',
  'People Ops',
  'Customer Success',
  'Legal',
  'IT',
];
const REGIONS = ['US', 'UK', 'EU', 'APAC', 'LATAM'];

type Errors = Partial<Record<keyof EmployeeCreate, string>>;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** New-hire registration form with client-side validation. */
export function RegistrationPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<EmployeeCreate>({
    first_name: '',
    last_name: '',
    personal_email: '',
    job_title: '',
    department: '',
    region: '',
    start_date: '',
  });
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const update = (field: keyof EmployeeCreate, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
    setErrors((e) => ({ ...e, [field]: undefined }));
  };

  const validate = (): boolean => {
    const next: Errors = {};
    if (!form.first_name.trim()) next.first_name = 'First name is required.';
    if (!form.last_name.trim()) next.last_name = 'Last name is required.';
    if (!form.personal_email.trim()) next.personal_email = 'Email is required.';
    else if (!EMAIL_RE.test(form.personal_email))
      next.personal_email = 'Enter a valid email address.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setServerError(null);
    if (!validate()) return;

    setSubmitting(true);
    try {
      // Omit empty optional fields so the backend keeps them null (progressive
      // profiling fills them in later).
      const payload: EmployeeCreate = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        personal_email: form.personal_email.trim(),
      };
      if (form.job_title) payload.job_title = form.job_title;
      if (form.department) payload.department = form.department;
      if (form.region) payload.region = form.region;
      if (form.start_date) payload.start_date = form.start_date;

      const created = await api.createEmployee(payload);
      navigate(`/employees/${created.employee_id}`);
    } catch (err) {
      setServerError(
        err instanceof ApiError ? err.message : 'Something went wrong. Please try again.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="card" aria-labelledby="reg-title">
      <h2 id="reg-title">Register a new hire</h2>
      <p style={{ color: 'var(--color-text-muted)', marginTop: 0 }}>
        Enter the new hire&apos;s details to start onboarding. Only name and email are required —
        everything else can be added later.
      </p>

      {serverError && (
        <div className="toast toast-error" role="alert">
          {serverError}
        </div>
      )}

      <form onSubmit={onSubmit} noValidate>
        <div className="field">
          <label htmlFor="first_name">First name *</label>
          <input
            id="first_name"
            value={form.first_name}
            onChange={(e) => update('first_name', e.target.value)}
            aria-invalid={!!errors.first_name}
            aria-describedby={errors.first_name ? 'err-first_name' : undefined}
            required
          />
          {errors.first_name && (
            <span className="error" id="err-first_name">
              {errors.first_name}
            </span>
          )}
        </div>

        <div className="field">
          <label htmlFor="last_name">Last name *</label>
          <input
            id="last_name"
            value={form.last_name}
            onChange={(e) => update('last_name', e.target.value)}
            aria-invalid={!!errors.last_name}
            aria-describedby={errors.last_name ? 'err-last_name' : undefined}
            required
          />
          {errors.last_name && (
            <span className="error" id="err-last_name">
              {errors.last_name}
            </span>
          )}
        </div>

        <div className="field">
          <label htmlFor="personal_email">Personal email *</label>
          <input
            id="personal_email"
            type="email"
            value={form.personal_email}
            onChange={(e) => update('personal_email', e.target.value)}
            aria-invalid={!!errors.personal_email}
            aria-describedby={errors.personal_email ? 'err-personal_email' : undefined}
            required
          />
          {errors.personal_email && (
            <span className="error" id="err-personal_email">
              {errors.personal_email}
            </span>
          )}
        </div>

        <div className="field">
          <label htmlFor="job_title">Job title</label>
          <input
            id="job_title"
            value={form.job_title}
            onChange={(e) => update('job_title', e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="department">Department</label>
          <select
            id="department"
            value={form.department}
            onChange={(e) => update('department', e.target.value)}
          >
            <option value="">Select a department…</option>
            {DEPARTMENTS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="region">Region</label>
          <select
            id="region"
            value={form.region}
            onChange={(e) => update('region', e.target.value)}
          >
            <option value="">Select a region…</option>
            {REGIONS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="start_date">Start date</label>
          <input
            id="start_date"
            type="date"
            value={form.start_date}
            onChange={(e) => update('start_date', e.target.value)}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Registering…' : 'Register & start onboarding'}
        </button>
      </form>
    </section>
  );
}
