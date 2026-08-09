import React, { useState, useEffect, useRef } from 'react';
import { Bell, ChevronDown, User, Settings, LogOut, CheckCircle, Eye, Briefcase, FileText } from 'lucide-react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';

export default function TopNavbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname.endsWith('/') && location.pathname.length > 1
    ? location.pathname.slice(0, -1)
    : location.pathname;
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Profile Synchronization State (syncs in real-time with Profile.jsx via window event)
  const [fullName, setFullName] = useState('Riya Mohan');
  const [profileImage, setProfileImage] = useState(null);

  // Notifications State
  const [notifications, setNotifications] = useState([
    { id: 1, text: 'New job matching your profile', read: false, type: 'job' },
    { id: 2, text: 'Application viewed by recruiter', read: false, type: 'view' },
    { id: 3, text: 'Interview scheduled', read: false, type: 'interview' },
    { id: 4, text: 'Resume downloaded', read: false, type: 'download' }
  ]);

  const notifRef = useRef(null);
  const profileRef = useRef(null);

  // Load profile sync values and setup custom event listener
  const syncProfile = () => {
    const savedImage = localStorage.getItem('profileImage');
    if (savedImage) setProfileImage(savedImage);

    const savedInfo = localStorage.getItem('personalInfo');
    if (savedInfo) {
      const parsed = JSON.parse(savedInfo);
      if (parsed.fullName) setFullName(parsed.fullName);
    }
  };

  useEffect(() => {
    syncProfile();

    const handleProfileUpdate = () => {
      syncProfile();
    };

    window.addEventListener('profileUpdate', handleProfileUpdate);
    return () => {
      window.removeEventListener('profileUpdate', handleProfileUpdate);
    };
  }, []);

  // Load notifications read/unread state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('header_notifications');
    if (saved) {
      setNotifications(JSON.parse(saved));
    }
  }, []);

  // Save to localStorage whenever notifications change
  const saveNotifications = (newNotifs) => {
    setNotifications(newNotifs);
    localStorage.setItem('header_notifications', JSON.stringify(newNotifs));
  };

  // Close dropdowns on clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setIsNotifOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleNotifClick = (id) => {
    const updated = notifications.map((n) => (n.id === id ? { ...n, read: true } : n));
    saveNotifications(updated);
  };

  const markAllAsRead = () => {
    const updated = notifications.map((n) => ({ ...n, read: true }));
    saveNotifications(updated);
  };

  const hasUnread = notifications.some((n) => !n.read);

  const getNotifIcon = (type) => {
    if (type === 'job') return <Briefcase className="w-4 h-4 text-emerald-500" />;
    if (type === 'view') return <Eye className="w-4 h-4 text-blue-500" />;
    if (type === 'interview') return <CheckCircle className="w-4 h-4 text-amber-500" />;
    return <FileText className="w-4 h-4 text-rose-500" />;
  };

  return (
    <header className="w-full flex items-center justify-between py-4 px-2 sm:px-6 md:px-8 select-none z-30 relative">
      {/* Middle Top Navigation Tab bar */}
      <nav className="flex items-center gap-1 sm:gap-2 md:gap-4 bg-white/50 backdrop-blur-xs p-1.5 rounded-full border border-white/40 shadow-xs">
        <NavLink
          to="/dashboard"
          className={
            `px-3 sm:px-5 py-2 text-xs sm:text-sm font-extrabold rounded-full transition-all duration-200 cursor-pointer ${
              currentPath === '/dashboard'
                ? 'bg-[#84A43C] text-white shadow-md shadow-[#84A43C]/20' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/40'
            }`
          }
        >
          Home
        </NavLink>
        <NavLink
          to="/dashboard/jobs"
          className={({ isActive }) =>
            `px-3 sm:px-5 py-2 text-xs sm:text-sm font-extrabold rounded-full transition-all duration-200 cursor-pointer ${
              isActive 
                ? 'bg-[#84A43C] text-white shadow-md shadow-[#84A43C]/20' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/40'
            }`
          }
        >
          Jobs
        </NavLink>
        <NavLink
          to="/dashboard/applications"
          className={({ isActive }) =>
            `px-3 sm:px-5 py-2 text-xs sm:text-sm font-extrabold rounded-full transition-all duration-200 cursor-pointer ${
              isActive 
                ? 'bg-[#84A43C] text-white shadow-md shadow-[#84A43C]/20' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/40'
            }`
          }
        >
          Applications
        </NavLink>
        <NavLink
          to="/dashboard/profile"
          className={({ isActive }) =>
            `px-3 sm:px-5 py-2 text-xs sm:text-sm font-extrabold rounded-full transition-all duration-200 cursor-pointer ${
              isActive 
                ? 'bg-[#84A43C] text-white shadow-md shadow-[#84A43C]/20' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/40'
            }`
          }
        >
          Profile
        </NavLink>
        <NavLink
          to="/dashboard/settings"
          className={({ isActive }) =>
            `px-3 sm:px-5 py-2 text-xs sm:text-sm font-extrabold rounded-full transition-all duration-200 cursor-pointer ${
              isActive 
                ? 'bg-[#84A43C] text-white shadow-md shadow-[#84A43C]/20' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/40'
            }`
          }
        >
          Settings
        </NavLink>
      </nav>

      {/* Right Side: Notifications & User Card */}
      <div className="flex items-center gap-3 sm:gap-6 relative">
        
        {/* Notification Bell Dropdown wrapper */}
        <div className="relative" ref={notifRef}>
          <button 
            type="button" 
            onClick={() => setIsNotifOpen(!isNotifOpen)}
            className="relative p-2.5 rounded-full bg-white hover:bg-slate-50 transition-colors shadow-xs border border-slate-100 cursor-pointer text-slate-500 hover:text-slate-800 focus:outline-none"
          >
            <Bell className="w-5 h-5" />
            {hasUnread && (
              <span className="absolute top-1.5 right-1.5 w-2.2 h-2.2 rounded-full bg-rose-500 ring-2 ring-white" />
            )}
          </button>

          {/* Notifications List Panel */}
          {isNotifOpen && (
            <div className="absolute right-0 mt-2.5 w-80 bg-white rounded-2xl border border-slate-100 shadow-xl py-3 z-50 animate-in fade-in slide-in-from-top-3 duration-200 text-left">
              <div className="flex items-center justify-between px-4 pb-2.5 border-b border-slate-50">
                <span className="text-sm font-extrabold text-slate-800">Notifications</span>
                {hasUnread && (
                  <button 
                    type="button" 
                    onClick={markAllAsRead} 
                    className="text-[11px] font-bold text-[#84A43C] hover:underline cursor-pointer"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-60 overflow-y-auto divide-y divide-slate-50">
                {notifications.map((notif) => (
                  <div 
                    key={notif.id} 
                    onClick={() => handleNotifClick(notif.id)}
                    className={`flex items-start gap-3 p-3 cursor-pointer hover:bg-slate-50/70 transition-colors ${
                      !notif.read ? 'bg-slate-50/30' : ''
                    }`}
                  >
                    <div className="mt-0.5 shrink-0">
                      {getNotifIcon(notif.type)}
                    </div>
                    <div className="flex-grow min-w-0">
                      <p className={`text-xs ${!notif.read ? 'font-bold text-slate-800' : 'font-medium text-slate-500'}`}>
                        {notif.text}
                      </p>
                    </div>
                    {!notif.read && (
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0 self-center" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Card Dropdown wrapper */}
        <div className="relative" ref={profileRef}>
          <div 
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-3 bg-white/60 p-1 pr-3 rounded-full border border-white/50 shadow-xs cursor-pointer hover:bg-white/80 transition-colors"
          >
            {/* Avatar representation matching the UI */}
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full overflow-hidden border-2 border-white shadow-sm shrink-0 bg-[#84A43C]/10 flex items-center justify-center">
              {profileImage ? (
                <img src={profileImage} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              )}
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-xs sm:text-sm font-extrabold text-slate-800 leading-tight">{fullName}</p>
              <p className="text-[10px] sm:text-xs font-semibold text-slate-400">Candidate</p>
            </div>
            <ChevronDown className={`w-4 h-4 text-slate-400 hidden sm:block transition-transform duration-200 ${
              isProfileOpen ? 'rotate-180' : ''
            }`} />
          </div>

          {/* Profile Menu Dropdown */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2.5 w-48 bg-white rounded-2xl border border-slate-100 shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-3 duration-200 text-left">
              <button
                type="button"
                onClick={() => { setIsProfileOpen(false); navigate('/dashboard/profile'); }}
                className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-slate-50 text-slate-600 hover:text-slate-800 font-bold text-xs sm:text-sm transition-colors text-left cursor-pointer"
              >
                <User className="w-4 h-4 text-slate-400" />
                <span>View Profile</span>
              </button>
              <button
                type="button"
                onClick={() => { setIsProfileOpen(false); navigate('/dashboard/profile'); }}
                className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-slate-50 text-slate-600 hover:text-slate-800 font-bold text-xs sm:text-sm transition-colors text-left cursor-pointer"
              >
                <User className="w-4 h-4 text-slate-400" />
                <span>Edit Profile</span>
              </button>
              <button
                type="button"
                onClick={() => { setIsProfileOpen(false); navigate('/dashboard/settings'); }}
                className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-slate-50 text-slate-600 hover:text-slate-800 font-bold text-xs sm:text-sm transition-colors text-left cursor-pointer"
              >
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Settings</span>
              </button>
              <div className="border-t border-slate-100 my-1.5" />
              <button
                type="button"
                onClick={() => { setIsProfileOpen(false); navigate('/login'); }}
                className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-rose-50 text-rose-600 font-bold text-xs sm:text-sm transition-colors text-left cursor-pointer"
              >
                <LogOut className="w-4 h-4 text-rose-400" />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
