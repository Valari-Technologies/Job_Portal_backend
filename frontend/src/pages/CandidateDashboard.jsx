import React from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { Home, Briefcase, FileText, User, Settings } from 'lucide-react';
import Sidebar from '../components/candidate/Sidebar';
import TopNavbar from '../components/candidate/TopNavbar';
import DashboardHome from '../components/candidate/DashboardHome';
import Jobs from './Jobs';
import Applications from './Applications';
import Profile from './Profile';
import SettingsPage from './Settings';
import bgImage from '../assets/canditate/canditate-bg.png';

export default function CandidateDashboard() {
  return (
    <div className="relative min-h-screen w-full bg-[#FAFAFA] font-sans flex overflow-hidden">
      {/* Dashboard Full-screen Background Illustration */}
      <img
        src={bgImage}
        alt="Dashboard Background"
        className="absolute inset-0 w-full h-full object-cover object-center z-0 select-none pointer-events-none opacity-90"
      />

      {/* Main Page Layout Wrapper */}
      <div className="relative z-10 w-full min-h-screen flex p-2 sm:p-4 md:p-6 lg:p-8 gap-4 lg:gap-6 overflow-x-hidden pb-20 md:pb-6">
        
        {/* Fixed Left Navigation Sidebar */}
        <Sidebar />

        {/* Workspace Content Container */}
        <div className="flex-grow flex flex-col justify-between overflow-x-hidden">
          {/* Top Bar Navigation */}
          <TopNavbar />

          {/* Sub-routing workspace rendering */}
          <div className="flex-grow flex flex-col justify-between overflow-x-hidden mt-4">
            <Routes>
              <Route path="/" element={<DashboardHome />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/applications" element={<Applications />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </div>

          {/* Spacing footer balance */}
          <div className="h-4 w-full"></div>
        </div>

      </div>

      {/* Mobile Bottom Navigation Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-[#84A43C] h-16 z-50 flex items-center justify-around px-4 shadow-lg border-t border-white/10 select-none">
        <NavLink to="/dashboard" end className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <Home className="w-5 h-5" />
          <span className="text-[9px]">Home</span>
        </NavLink>
        <NavLink to="/dashboard/jobs" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <Briefcase className="w-5 h-5" />
          <span className="text-[9px]">Jobs</span>
        </NavLink>
        <NavLink to="/dashboard/applications" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <FileText className="w-5 h-5" />
          <span className="text-[9px]">Apps</span>
        </NavLink>
        <NavLink to="/dashboard/profile" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <User className="w-5 h-5" />
          <span className="text-[9px]">Profile</span>
        </NavLink>
        <NavLink to="/dashboard/settings" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <Settings className="w-5 h-5" />
          <span className="text-[9px]">Settings</span>
        </NavLink>
      </div>

    </div>
  );
}
