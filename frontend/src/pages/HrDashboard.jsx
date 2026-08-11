import React from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { Home, Briefcase, ClipboardList, User, Settings } from 'lucide-react';
import Sidebar from '../components/hr/Sidebar';
import TopNavbar from '../components/hr/TopNavbar';
import HrDashboardHome from '../components/hr/HrDashboardHome';
import HrJobs from '../components/hr/HrJobs';
import HrApplications from '../components/hr/HrApplications';
import HrProfile from '../components/hr/HrProfile';
import HrSettings from '../components/hr/HrSettings';
import CandidateDetailsPage from '../components/hr/CandidateDetailsPage';
import hrBg from '../assets/hr/hr-bg.png';

export default function HrDashboard() {
  return (
    <div className="relative min-h-screen w-full bg-[#FAFAF7] font-sans flex overflow-hidden">
      {/* Dashboard Full-screen Background Illustration */}
      <img
        src={hrBg}
        alt="HR Dashboard Background"
        className="absolute inset-0 w-full h-full object-cover object-center z-0 select-none pointer-events-none opacity-90"
      />

      {/* Main Page Layout Wrapper */}
      <div className="relative z-10 w-full min-h-screen flex p-2 sm:p-4 md:p-6 lg:p-8 gap-4 lg:gap-6 overflow-x-hidden pb-20 md:pb-6">
        
        {/* Reused HR Left Sidebar Component */}
        <Sidebar />

        {/* Workspace Content Container */}
        <div className="flex-grow flex flex-col gap-6 overflow-x-hidden">
          
          {/* Reused HR Top Navbar Component */}
          <TopNavbar />

          {/* Sub-routing workspace rendering */}
          <div className="flex-grow flex flex-col justify-between overflow-x-hidden">
            <Routes>
              <Route path="/" element={<HrDashboardHome />} />
              <Route path="/jobs" element={<HrJobs />} />
              <Route path="/applications" element={<HrApplications />} />
              <Route path="/applications/:id" element={<CandidateDetailsPage />} />
              <Route path="/profile" element={<HrProfile />} />
              <Route path="/settings" element={<HrSettings />} />
              <Route path="/*" element={<HrDashboardHome />} />
            </Routes>
          </div>

          {/* Spacing footer balance */}
          <div className="h-4 w-full"></div>
        </div>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-[#84A43C] h-16 z-50 flex items-center justify-around px-4 shadow-lg border-t border-white/10 select-none">
        <NavLink to="/hr-dashboard" end className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <Home className="w-5 h-5" />
          <span className="text-[9px]">Home</span>
        </NavLink>
        <NavLink to="/hr-dashboard/jobs" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <Briefcase className="w-5 h-5" />
          <span className="text-[9px]">Jobs</span>
        </NavLink>
        <NavLink to="/hr-dashboard/applications" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <ClipboardList className="w-5 h-5" />
          <span className="text-[9px]">Apps</span>
        </NavLink>
        <NavLink to="/hr-dashboard/profile" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <User className="w-5 h-5" />
          <span className="text-[9px]">Profile</span>
        </NavLink>
        <NavLink to="/hr-dashboard/settings" className={({ isActive }) => `flex flex-col items-center justify-center gap-1 ${isActive ? 'text-white scale-110 font-bold' : 'text-white/60'}`}>
          <Settings className="w-5 h-5" />
          <span className="text-[9px]">Settings</span>
        </NavLink>
      </div>

    </div>
  );
}
