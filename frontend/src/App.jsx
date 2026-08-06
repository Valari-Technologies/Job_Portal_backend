import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/login/LoginPage';
import RegisterPage from './components/register/RegisterPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirect empty root path to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* Render separate pages using clean route mapping */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
    </BrowserRouter>
  );
}
