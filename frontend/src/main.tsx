import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider, createBrowserRouter, Navigate } from 'react-router-dom';

import { App } from './App';
import { RegistrationPage } from './features/registration/RegistrationPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import './styles/global.css';

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/register" replace /> },
      { path: 'register', element: <RegistrationPage /> },
      { path: 'employees/:employeeId', element: <DashboardPage /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
