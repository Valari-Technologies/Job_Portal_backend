import React, { useState, useEffect, useRef } from 'react';
import { Bell, ChevronDown, User, Settings, Info, LogOut, Check, X, ShieldAlert, BookOpen, MessageSquare, Briefcase, CalendarCheck } from 'lucide-react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';

const DEFAULT_NOTIFICATIONS = [
  { id: 1, text: 'New application received for Senior Frontend Developer', type: 'info', unread: true, time: '2 mins ago' },
  { id: 2, text: 'Candidate Sarah Connor shortlisted', type: 'success', unread: true, time: '1 hour ago' },
  { id: 3, text: 'Interview scheduled with John Doe', type: 'interview', unread: true, time: '3 hours ago' },
  { id: 4, text: 'QA Engineer job listing is about to expire', type: 'warning', unread: false, time: '1 day ago' },
  { id: 5, text: 'Team member Sandra updated Backend Developer listing', type: 'team', unread: false, time: '2 days ago' }
];

export default function TopNavbar() {
  const location = useLocation();
  const navigate = useNavigate();

  // Profile state from localStorage
  const [profile, setProfile] = useState({
    fullName: 'HR Manager',
    designation: 'HR Manager',
    image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150'
  });

  // Dropdown States
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Modal States
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);

  // Notifications State
  const [notifications, setNotifications] = useState([]);

  // Refs for outside click detection
  const notifRef = useRef(null);
  const profileRef = useRef(null);

  // Synchronize profile data
  useEffect(() => {
    const loadProfile = () => {
      const stored = localStorage.getItem('hrProfile');
      if (stored) {
        const parsed = JSON.parse(stored);
        setProfile({
          ...parsed,
          designation: parsed.designation || 'HR Manager'
        });
      }
    };
    loadProfile();
    window.addEventListener('hr_profile_updated', loadProfile);
    return () => window.removeEventListener('hr_profile_updated', loadProfile);
  }, []);

  // Synchronize notifications list
  useEffect(() => {
    const storedNotifs = localStorage.getItem('hr_notifications');
    if (storedNotifs) {
      setNotifications(JSON.parse(storedNotifs));
    } else {
      localStorage.setItem('hr_notifications', JSON.stringify(DEFAULT_NOTIFICATIONS));
      setNotifications(DEFAULT_NOTIFICATIONS);
    }
  }, []);

  // Handle outside click to close dropdowns
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setIsNotifOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  // Close dropdowns on ESC key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsNotifOpen(false);
        setIsProfileOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const markAsRead = (id) => {
    const updated = notifications.map(n => n.id === id ? { ...n, unread: false } : n);
    setNotifications(updated);
    localStorage.setItem('hr_notifications', JSON.stringify(updated));
  };

  const markAllAsRead = () => {
    const updated = notifications.map(n => ({ ...n, unread: false }));
    setNotifications(updated);
    localStorage.setItem('hr_notifications', JSON.stringify(updated));
  };

  const hasUnread = notifications.some(n => n.unread);

  const isTabActive = (path, end = false) => {
    const current = location.pathname.endsWith('/') && location.pathname.length > 1
      ? location.pathname.slice(0, -1)
      : location.pathname;
    const target = path.endsWith('/') && path.length > 1
      ? path.slice(0, -1)
      : path;
    if (end) {
      return current === target;
    }
    return current.startsWith(target);
  };

  const tabs = [
    { label: 'Dashboard', to: '/hr-dashboard', end: true },
    { label: 'Jobs', to: '/hr-dashboard/jobs', end: false },
    { label: 'Applications', to: '/hr-dashboard/applications', end: false },
    { label: 'Profile', to: '/hr-dashboard/profile', end: false },
    { label: 'Settings', to: '/hr-dashboard/settings', end: false }
  ];

  return (
    <header className="w-full flex items-center justify-between py-2.5 z-30 relative select-none">
      {/* Navigation menu tabs */}
      <nav className="flex items-center gap-1 sm:gap-2 bg-white/50 backdrop-blur-xs p-1.5 rounded-full border border-white/40 shadow-xs overflow-x-auto max-w-[200px] min-[375px]:max-w-[240px] min-[425px]:max-w-[280px] sm:max-w-md md:max-w-none whitespace-nowrap scrollbar-none">
        {tabs.map((tab) => {
          const active = isTabActive(tab.to, tab.end);
          return (
            <NavLink
              key={tab.label}
              to={tab.to}
              end={tab.end}
              className={`px-4 sm:px-5 py-2 text-base font-extrabold rounded-full transition-all duration-200 cursor-pointer ${
                active 
                  ? 'bg-[#84A43C] text-white shadow-md shadow-[#84A43C]/20' 
                  : 'text-slate-500 hover:text-slate-800 hover:bg-white/40'
              }`}
            >
              {tab.label}
            </NavLink>
          );
        })}
      </nav>

      {/* Right Side Icons & Avatar */}
      <div className="flex items-center gap-4">
        
        {/* NOTIFICATION BELL CONTAINER */}
        <div className="relative" ref={notifRef}>
          <button 
            onClick={() => { setIsNotifOpen(!isNotifOpen); setIsProfileOpen(false); }}
            className={`relative w-10 h-10 rounded-full bg-white flex items-center justify-center border border-slate-100 hover:bg-slate-50 transition-colors shadow-xs shrink-0 cursor-pointer ${
              isNotifOpen ? 'ring-2 ring-[#8CC63F]/40' : ''
            }`}
          >
            <Bell className="w-5 h-5 text-slate-600" />
            {hasUnread && (
              <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-rose-500 rounded-full border border-white animate-pulse" />
            )}
          </button>

          {/* Notifications Dropdown Panel */}
          {isNotifOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-100 rounded-2xl shadow-xl py-3 z-30 animate-scaleUp text-left">
              <div className="px-4 pb-2 border-b border-slate-50 flex items-center justify-between">
                <h3 className="text-xs font-black text-slate-800">HR Notifications</h3>
                {hasUnread && (
                  <button 
                    onClick={markAllAsRead}
                    className="text-[10px] font-black text-[#8CC63F] hover:underline cursor-pointer"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-slate-50">
                {notifications.map((n) => (
                  <div 
                    key={n.id} 
                    onClick={() => { markAsRead(n.id); }}
                    className={`p-3 text-[11px] leading-snug cursor-pointer transition-colors flex gap-2.5 items-start ${
                      n.unread ? 'bg-[#8CC63F]/5 font-black text-slate-800' : 'text-slate-500 hover:bg-slate-50'
                    }`}
                  >
                    <div className="mt-0.5">
                      {n.unread && <span className="w-1.5 h-1.5 bg-[#8CC63F] rounded-full inline-block mr-1.5" />}
                    </div>
                    <div className="flex-grow">
                      <p>{n.text}</p>
                      <span className="text-[9px] text-slate-400 font-bold block mt-1">{n.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* PROFILE SECTION CONTAINER */}
        <div className="relative" ref={profileRef}>
          <div 
            onClick={() => { setIsProfileOpen(!isProfileOpen); setIsNotifOpen(false); }}
            className={`flex items-center gap-3 bg-white pl-2.5 pr-4 py-1.5 rounded-full border border-slate-100 shadow-xs cursor-pointer hover:bg-slate-50 transition-colors select-none ${
              isProfileOpen ? 'ring-2 ring-[#8CC63F]/40' : ''
            }`}
          >
            <img 
              src={profile.image} 
              alt="User Admin Avatar" 
              className="w-8 h-8 rounded-full object-cover border border-slate-100" 
            />
            <div className="text-left leading-tight hidden sm:block">
              <p className="text-sm sm:text-base font-black text-slate-800">{profile.fullName}</p>
              <p className="text-xs sm:text-sm font-bold text-slate-400">{profile.designation}</p>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400 hidden sm:block" />
          </div>

          {/* Profile Dropdown Menu */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-100 rounded-2xl shadow-xl py-2 z-30 animate-scaleUp text-left text-xs font-bold text-slate-600">
              <button 
                onClick={() => { navigate('/hr-dashboard/profile'); setIsProfileOpen(false); }}
                className="w-full px-4 py-2.5 hover:bg-slate-50 flex items-center gap-2.5 transition-colors text-left"
              >
                <User className="w-4 h-4 text-slate-400" />
                <span>View Profile</span>
              </button>
              <button 
                onClick={() => { 
                  navigate('/hr-dashboard/profile'); 
                  setIsProfileOpen(false);
                  setTimeout(() => {
                    // dispatch edit notification to Profile page
                    window.dispatchEvent(new Event('hr_profile_trigger_edit'));
                  }, 100);
                }}
                className="w-full px-4 py-2.5 hover:bg-slate-50 flex items-center gap-2.5 transition-colors text-left"
              >
                <User className="w-4 h-4 text-[#8CC63F]" />
                <span>Edit Profile</span>
              </button>
              <button 
                onClick={() => { 
                  navigate('/hr-dashboard/profile'); 
                  setIsProfileOpen(false);
                  setTimeout(() => {
                    // dispatch tab change to Profile page
                    window.dispatchEvent(new CustomEvent('hr_profile_change_tab', { detail: 'Organization' }));
                  }, 100);
                }}
                className="w-full px-4 py-2.5 hover:bg-slate-50 flex items-center gap-2.5 transition-colors text-left"
              >
                <Briefcase className="w-4 h-4 text-slate-400" />
                <span>Organization Profile</span>
              </button>
              <button 
                onClick={() => { navigate('/hr-dashboard/settings'); setIsProfileOpen(false); }}
                className="w-full px-4 py-2.5 hover:bg-slate-50 flex items-center gap-2.5 transition-colors text-left"
              >
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Settings</span>
              </button>
              <div className="border-t border-slate-50 my-1"></div>
              <button 
                onClick={() => { setIsLogoutModalOpen(true); setIsProfileOpen(false); }}
                className="w-full px-4 py-2.5 hover:bg-rose-50 text-rose-600 flex items-center gap-2.5 transition-colors text-left"
              >
                <LogOut className="w-4 h-4 text-rose-500" />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>

      </div>

      {/* HELP & SUPPORT MODAL */}
      {isHelpModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white w-full max-w-sm rounded-[28px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col animate-scaleUp">
            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-base font-black text-slate-800">Help & Support</h3>
              <button onClick={() => setIsHelpModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 flex flex-col gap-4 text-xs font-bold text-slate-500 text-left">
              <div className="flex items-start gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                <BookOpen className="w-5 h-5 text-[#8CC63F] mt-0.5 shrink-0" />
                <div>
                  <p className="text-slate-700 font-black">HR Documentation</p>
                  <p className="text-[10px] text-slate-400 font-bold mt-0.5">Read quick walkthrough guidelines on managing candidate pipelines.</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                <MessageSquare className="w-5 h-5 text-[#8CC63F] mt-0.5 shrink-0" />
                <div>
                  <p className="text-slate-700 font-black">Support Hotline</p>
                  <p className="text-[10px] text-slate-400 font-bold mt-0.5">Contact us at support@tnjobz.com or call +91 44 9876 5432.</p>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end">
              <button 
                onClick={() => setIsHelpModalOpen(false)}
                className="px-6 py-2 bg-[#8CC63F] hover:bg-[#80b835] text-white text-xs font-black rounded-xl cursor-pointer"
              >
                Close Support
              </button>
            </div>
          </div>
        </div>
      )}

      {/* LOGOUT CONFIRMATION MODAL */}
      {isLogoutModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white w-full max-w-xs rounded-[28px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col animate-scaleUp">
            <div className="p-6 text-center flex flex-col items-center gap-4">
              <div className="w-12 h-12 bg-rose-50 rounded-full flex items-center justify-center text-rose-600">
                <LogOut className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-black text-slate-800">Confirm Sign Out</h3>
                <p className="text-xs font-bold text-slate-400 mt-1 font-sans">Are you sure you want to end your current session?</p>
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button 
                onClick={() => setIsLogoutModalOpen(false)}
                className="px-4 py-2 text-slate-500 hover:bg-slate-100 text-xs font-black rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  setIsLogoutModalOpen(false);
                  navigate('/login');
                }}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-black rounded-xl cursor-pointer shadow-xs"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

    </header>
  );
}
