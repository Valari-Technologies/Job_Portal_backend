import React, { useState } from 'react';
import { MapPin, Calendar, ChevronRight } from 'lucide-react';

export default function Applications() {
  const [activeTab, setActiveTab] = useState('All');
  const [selectedAppId, setSelectedAppId] = useState(1);
  const [activeSubTab, setActiveSubTab] = useState('Timeline'); // 'Overview' | 'Timeline' | 'Documents' | 'Notes'

  // Standard applications dataset representing the Figma design precisely
  const applications = [
    {
      id: 1,
      title: 'UI/UX Designer',
      company: 'Microsoft',
      appliedDate: '12 Jul 2026',
      appId: 'MSFT12678',
      status: 'Interview',
      nextStep: 'Technical Interview',
      progressStep: 4, // 4 out of 6 steps filled
      logoText: 'M',
      logoBg: 'bg-red-500/10 text-red-600',
      timeline: [
        { name: 'Applied', date: '12 Jul 2026, 10:30 AM', status: 'completed' },
        { name: 'Screening', date: '13 Jul 2026, 02:15 PM', status: 'completed' },
        { name: 'Assessment', date: '15 Jul 2026, 11:00 AM', status: 'active' },
        { name: 'Interview', date: '18 Jul 2026, 03:00 PM', status: 'upcoming', badge: 'Upcoming' },
        { name: 'HR Discussion', date: '-', status: 'pending' },
        { name: 'Offer', date: '-', status: 'pending' },
        { name: 'Joined', date: '-', status: 'pending' }
      ]
    },
    {
      id: 2,
      title: 'Frontend Developer',
      company: 'TCS',
      appliedDate: '08 Jul 2026',
      appId: 'TCS84729',
      status: 'Under Review',
      nextStep: 'HR Discussion',
      progressStep: 3,
      logoText: 'T',
      logoBg: 'bg-blue-600/10 text-blue-600',
      timeline: [
        { name: 'Applied', date: '08 Jul 2026, 09:15 AM', status: 'completed' },
        { name: 'Screening', date: '10 Jul 2026, 11:00 AM', status: 'active' },
        { name: 'Assessment', date: '12 Jul 2026, 02:00 PM', status: 'upcoming', badge: 'Active' },
        { name: 'Interview', date: '-', status: 'pending' },
        { name: 'HR Discussion', date: '-', status: 'pending' },
        { name: 'Offer', date: '-', status: 'pending' },
        { name: 'Joined', date: '-', status: 'pending' }
      ]
    },
    {
      id: 3,
      title: 'Product Designer',
      company: 'Infosys',
      appliedDate: '05 Jul 2026',
      appId: 'INFY38201',
      status: 'Assessment',
      nextStep: 'Design Assessment',
      progressStep: 2,
      logoText: 'I',
      logoBg: 'bg-indigo-600/10 text-indigo-600',
      timeline: [
        { name: 'Applied', date: '05 Jul 2026, 10:00 AM', status: 'active' },
        { name: 'Screening', date: '07 Jul 2026, 03:30 PM', status: 'upcoming', badge: 'Active' },
        { name: 'Assessment', date: '-', status: 'pending' },
        { name: 'Interview', date: '-', status: 'pending' },
        { name: 'HR Discussion', date: '-', status: 'pending' },
        { name: 'Offer', date: '-', status: 'pending' },
        { name: 'Joined', date: '-', status: 'pending' }
      ]
    },
    {
      id: 4,
      title: 'UX Researcher',
      company: 'Amazon',
      appliedDate: '30 Jun 2026',
      appId: 'AMZN58291',
      status: 'Offer',
      nextStep: 'Offer Letter',
      progressStep: 5,
      logoText: 'A',
      logoBg: 'bg-amber-500/10 text-amber-600',
      timeline: [
        { name: 'Applied', date: '30 Jun 2026, 09:00 AM', status: 'completed' },
        { name: 'Screening', date: '02 Jul 2026, 11:30 AM', status: 'completed' },
        { name: 'Assessment', date: '05 Jul 2026, 04:00 PM', status: 'completed' },
        { name: 'Interview', date: '08 Jul 2026, 02:00 PM', status: 'active' },
        { name: 'HR Discussion', date: '12 Jul 2026, 10:00 AM', status: 'upcoming', badge: 'Upcoming' },
        { name: 'Offer', date: '-', status: 'pending' },
        { name: 'Joined', date: '-', status: 'pending' }
      ]
    }
  ];

  // Filter criteria logic
  const getFilteredApps = () => {
    if (activeTab === 'All') return applications;
    return applications.filter(app => app.status === activeTab);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Interview':
        return 'bg-blue-50 text-blue-600 border-blue-100';
      case 'Under Review':
        return 'bg-amber-50 text-[#E29D29] border-amber-100';
      case 'Assessment':
        return 'bg-purple-50 text-purple-600 border-purple-100';
      case 'Offer':
        return 'bg-emerald-50 text-emerald-600 border-emerald-100';
      default:
        return 'bg-slate-50 text-slate-600';
    }
  };

  const selectedApp = applications.find(app => app.id === selectedAppId) || applications[0];

  return (
    <div className="px-2 sm:px-6 md:px-8 mt-4 flex-grow space-y-6 animate-in fade-in duration-300 select-none text-left font-sans w-full">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-[#84A43C] tracking-tight">Applications</h1>
        <p className="text-sm font-semibold text-slate-400 mt-1">Track your job applications</p>
      </div>

      {/* Tabs list row */}
      <div className="bg-white rounded-[24px] border border-slate-100 shadow-xs p-2 flex items-center gap-4 sm:gap-6 overflow-x-auto w-full">
        {['All', 'Applied', 'Under Review', 'Interview', 'Assessment', 'Offer'].map((tab) => {
          const isActive = activeTab === tab;
          const count = tab === 'All' ? applications.length : applications.filter(app => app.status === tab).length;
          return (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-2.5 px-4 py-2 text-xs sm:text-sm font-bold rounded-[14px] transition-all shrink-0 cursor-pointer focus:outline-none ${
                isActive
                  ? 'bg-[#F4F8F0] border border-[#84A43C]/30 text-[#84A43C]'
                  : 'border border-transparent text-[#E29D29] hover:bg-slate-50/50'
              }`}
            >
              <span>{tab}</span>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-black shrink-0 transition-all ${
                isActive
                  ? 'bg-[#84A43C] text-white shadow-xs'
                  : 'bg-white text-[#E29D29] shadow-[0_2px_8px_rgba(0,0,0,0.06)]'
              }`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Split dashboard grid - using flex/items-stretch to stretch content vertically to the bottom */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch w-full">
        
        {/* Left Column: Applications List (Cards) */}
        <div className="lg:col-span-5 space-y-4 w-full flex flex-col justify-start">
          {getFilteredApps().map((app) => {
            const isSelected = selectedAppId === app.id;
            return (
              <div
                key={app.id}
                onClick={() => setSelectedAppId(app.id)}
                className={`bg-white rounded-3xl p-5 border shadow-xs transition-all cursor-pointer flex flex-col justify-between min-h-[170px] ${
                  isSelected 
                    ? 'border-[#84A43C] ring-1 ring-[#84A43C]/20 shadow-md' 
                    : 'border-slate-100 hover:shadow-md'
                }`}
              >
                <div>
                  {/* Top Row: Logo + Info + Badge */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-11 h-11 rounded-xl ${app.logoBg} font-black text-lg flex items-center justify-center`}>
                        {app.logoText}
                      </div>
                      <div className="text-left">
                        <h4 className="text-sm font-semibold text-slate-400">{app.company}</h4>
                        <h3 className="text-base font-extrabold text-slate-800 leading-snug">{app.title}</h3>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-[10px] sm:text-xs font-bold border ${getStatusColor(app.status)}`}>
                      {app.status}
                    </span>
                  </div>

                  <p className="text-[11px] font-semibold text-slate-400 mt-2 text-left">Applied on {app.appliedDate}</p>

                  {/* Horizontal timeline bar */}
                  <div className="relative flex items-center justify-between mt-4 mb-2">
                    {/* Background track line */}
                    <div className="absolute left-0 right-0 h-1 bg-slate-100 -z-0 rounded-full" />
                    {/* Active track line */}
                    <div 
                      className="absolute left-0 h-1 bg-[#84A43C] -z-0 rounded-full" 
                      style={{ width: `${((app.progressStep - 1) / 5) * 100}%` }}
                    />
                    
                    {/* Circles */}
                    {[1, 2, 3, 4, 5, 6].map((step) => {
                      const isCompleted = step < app.progressStep;
                      const isCurrent = step === app.progressStep;
                      return (
                        <div
                          key={step}
                          className={`w-3.5 h-3.5 rounded-full border-2 z-10 transition-colors ${
                            isCompleted
                              ? 'bg-[#84A43C] border-[#84A43C]'
                              : isCurrent
                              ? 'bg-[#3562D6] border-[#3562D6]'
                              : 'bg-white border-slate-200'
                          }`}
                        />
                      );
                    })}
                  </div>
                </div>

                {/* Footer details row */}
                <div className="flex items-center justify-between border-t border-slate-50 pt-3 mt-2 text-xs">
                  <div className="text-left">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Next Step</p>
                    <p className="font-extrabold text-slate-700">{app.nextStep}</p>
                  </div>
                  <button
                    type="button"
                    className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-[#84A43C] font-bold rounded-xl transition-all cursor-pointer"
                  >
                    View Details
                  </button>
                </div>

              </div>
            );
          })}
        </div>

        {/* Right Column: Application Detail Pane (Active Tracking Timeline) - h-full stretches to bottom */}
        <div className="lg:col-span-7 bg-white rounded-[32px] border border-slate-100 p-6 shadow-xs w-full h-full flex flex-col justify-between">
          
          <div className="flex flex-col h-full flex-grow">
            {/* Active Job Header details */}
            <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 rounded-2xl ${selectedApp.logoBg} font-black text-2xl flex items-center justify-center`}>
                  {selectedApp.logoText}
                </div>
                <div className="text-left">
                  <h2 className="text-2xl font-black text-slate-800 tracking-tight leading-tight">{selectedApp.title}</h2>
                  <div className="flex items-center gap-3 mt-1.5 flex-wrap text-xs sm:text-sm font-semibold text-slate-400">
                    <span>{selectedApp.company}</span>
                    <span>•</span>
                    <span>Applied on {selectedApp.appliedDate}</span>
                    <span>•</span>
                    <span>ID: {selectedApp.appId}</span>
                  </div>
                </div>
              </div>
              
              <span className={`px-4 py-1.5 rounded-full text-xs sm:text-sm font-extrabold border shrink-0 ${getStatusColor(selectedApp.status)}`}>
                {selectedApp.status}
              </span>
            </div>

            {/* Sub Navigation tabs */}
            <div className="flex border-b border-slate-100 gap-6 text-sm font-extrabold mt-6 overflow-x-auto pb-px">
              {['Overview', 'Timeline', 'Documents', 'Notes'].map((subTab) => (
                <button
                  key={subTab}
                  type="button"
                  onClick={() => setActiveSubTab(subTab)}
                  className={`pb-2.5 transition-all border-b-2 cursor-pointer ${
                    activeSubTab === subTab
                      ? 'border-[#84A43C] text-[#84A43C]'
                      : 'border-transparent text-slate-400 hover:text-slate-600'
                  }`}
                >
                  {subTab}
                </button>
              ))}
            </div>

            {/* Tab Content Panels - flex-grow handles expanding vertical heights */}
            <div className="pt-6 flex-grow flex flex-col">
              {activeSubTab === 'Timeline' ? (
                // Vertical timeline list using justify-between to stretch nodes across the height
                <div className="relative flex flex-col justify-between flex-grow text-left pl-6 min-h-[460px] lg:min-h-[500px] pb-4">
                  
                  {/* Connecting track line passing through the center of 24px circles (left-[11px]) */}
                  <div className="absolute left-[11px] top-3 bottom-6 w-0.5 bg-slate-100/80 -z-0" />
                  
                  {selectedApp.timeline.map((step, idx) => {
                    const isDone = step.status === 'completed';
                    const isActiveStage = step.status === 'active';
                    const isCurrent = step.status === 'upcoming';
                    
                    return (
                      <div key={idx} className="relative flex gap-4 items-start py-1">
                        
                        {/* Concentric Circle Timeline Node centered with the vertical track line */}
                        <div className={`w-[24px] h-[24px] rounded-full border-2 flex items-center justify-center shrink-0 z-10 bg-white transition-all ${
                          isDone 
                            ? 'border-[#84A43C] text-[#84A43C]'
                            : isActiveStage
                            ? 'border-[#3562D6] text-[#3562D6]'
                            : isCurrent
                            ? 'border-purple-500 text-purple-500'
                            : 'border-slate-200'
                        }`}>
                          {(isDone || isActiveStage) && (
                            <div className={`w-[10px] h-[10px] rounded-full ${
                              isDone ? 'bg-[#84A43C]' : 'bg-[#3562D6]'
                            }`} />
                          )}
                        </div>

                        {/* Detail row text column */}
                        <div className="space-y-0.5 min-w-0">
                          <div className="flex items-center gap-3">
                            <h4 className={`text-base font-extrabold ${isDone || isActiveStage ? 'text-slate-800' : 'text-slate-400'}`}>
                              {step.name}
                            </h4>
                            {step.badge && (
                              <span className="px-2.5 py-0.5 bg-purple-50 text-purple-600 border border-purple-100 rounded-md text-[10px] font-black uppercase tracking-wide">
                                {step.badge}
                              </span>
                            )}
                          </div>
                          <p className="text-xs font-semibold text-slate-400">{step.date}</p>
                        </div>

                      </div>
                    );
                  })}
                </div>
              ) : (
                // Standard stub for other tabs
                <div className="text-slate-400 text-sm font-semibold py-8 text-center bg-slate-50 rounded-2xl border border-slate-100 flex-grow flex items-center justify-center">
                  Details for {activeSubTab} section are being updated.
                </div>
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
