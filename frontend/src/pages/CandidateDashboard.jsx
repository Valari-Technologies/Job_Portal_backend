import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from '../components/candidate/Sidebar';
import TopNavbar from '../components/candidate/TopNavbar';
import DashboardHome from '../components/candidate/DashboardHome';
import Jobs from './Jobs';
import Applications from './Applications';
import Profile from './Profile';
import Settings from './Settings';
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
      <div className="relative z-10 w-full min-h-screen flex p-3 sm:p-5 md:p-6 lg:p-8 gap-4 lg:gap-6 overflow-x-hidden">
        
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
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </div>

          {/* Spacing footer balance */}
          <div className="h-4 w-full"></div>
        </div>

      </div>
    </div>
  );
}
