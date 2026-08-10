import { Outlet } from 'react-router-dom';

import './App.css';

/**
 * Application shell: a persistent header and a routed content area. Individual
 * features (registration, dashboard) render into the <Outlet />.
 */
export function App() {
  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>
      <header className="app-header">
        <div className="app-header__inner">
          <span className="app-logo" aria-hidden="true">
            🚀
          </span>
          <h1 className="app-title">Employee Onboarding Assistant</h1>
        </div>
      </header>
      <main id="main" className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        <p>Secure onboarding · powered by Azure &amp; your AI assistant</p>
      </footer>
    </div>
  );
}
