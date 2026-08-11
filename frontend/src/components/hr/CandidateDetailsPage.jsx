import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Mail, 
  Phone, 
  Briefcase, 
  Calendar, 
  FileText, 
  Download, 
  ExternalLink, 
  Copy, 
  Check, 
  X, 
  Clock, 
  ChevronDown,
  UserCheck,
  Send,
  CalendarCheck
} from 'lucide-react';

const DEFAULT_CANDIDATES = [
  {
    id: 1,
    name: 'Riya Sharma',
    email: 'riya.sharma@email.com',
    phone: '+91 98765 43210',
    role: 'UI/UX Designer',
    exp: '3+ years',
    appliedJob: 'UI/UX Designer',
    appliedDate: 'May 24, 2025',
    status: 'Under Review',
    img: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=250',
    about: 'Creative and detail-oriented UI/UX Designer with 3+ years of experience in designing user-centered digital experiences.',
    education: {
      degree: 'B.Tech in Computer Science',
      school: 'Delhi Technological University',
      year: '2017 - 2021',
      cgpa: '8.4'
    },
    experience: {
      role: 'UI/UX Designer - ABC Tech',
      duration: 'Jan 2022 - Present (1+ years)',
      highlights: [
        'Designed 20+ web and mobile applications.',
        'Improved user engagement by 30%.'
      ]
    },
    skills: ['UI/UX Design', 'Figma', 'Adobe XD', 'HTML', 'CSS', 'JavaScript', 'Prototyping', 'User Research'],
    coverLetter: 'Dear Hiring Team,\n\nI am writing to express my strong interest in the UI/UX Designer position. With over 3 years of experience creating user-centric mobile and web designs, I am confident in my ability to contribute value to your design team.\n\nSincerely,\nRiya Sharma',
    timeline: [
      { stage: 'Applied', date: 'May 24, 2025', time: '10:00 AM', completed: true },
      { stage: 'Under Review', date: 'May 24, 2025', time: '02:30 PM', completed: true },
      { stage: 'Shortlisted', date: '', time: '', completed: false },
      { stage: 'Interview', date: '', time: '', completed: false },
      { stage: 'Selected', date: '', time: '', completed: false }
    ]
  },
  {
    id: 2,
    name: 'Arjun Singh',
    email: 'arjun.s@example.com',
    phone: '+91 98765 11111',
    role: 'Frontend Developer',
    exp: '4+ years',
    appliedJob: 'Frontend Developer',
    appliedDate: 'May 24, 2025',
    status: 'Shortlisted',
    img: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=250',
    about: 'Passionate Frontend Developer focused on building accessible, high-performance web applications using modern React and CSS.',
    education: {
      degree: 'B.E. in Information Technology',
      school: 'Mumbai University',
      year: '2016 - 2020',
      cgpa: '7.9'
    },
    experience: {
      role: 'Frontend Developer - Webify',
      duration: 'Jul 2020 - Present (3+ years)',
      highlights: [
        'Built dynamic responsive pages using React.',
        'Collaborated with designers to deliver premium pixel-perfect dashboards.'
      ]
    },
    skills: ['React', 'JavaScript', 'HTML', 'CSS', 'Tailwind CSS', 'Git', 'Webpack'],
    coverLetter: 'Hello Team,\n\nI am excited to submit my application for the Frontend Developer position. I have been building clean React applications for 4 years now and look forward to joining you.\n\nBest,\nArjun Singh',
    timeline: [
      { stage: 'Applied', date: 'May 24, 2025', time: '09:00 AM', completed: true },
      { stage: 'Under Review', date: 'May 24, 2025', time: '11:00 AM', completed: true },
      { stage: 'Shortlisted', date: 'May 24, 2025', time: '04:00 PM', completed: true },
      { stage: 'Interview', date: '', time: '', completed: false },
      { stage: 'Selected', date: '', time: '', completed: false }
    ]
  }
];

export default function CandidateDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [candidate, setCandidate] = useState(null);
  const [activeTab, setActiveTab] = useState('Overview');
  const [isActionsDropdownOpen, setIsActionsDropdownOpen] = useState(false);

  // Modal States
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const [isInterviewModalOpen, setIsInterviewModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [isSelectModalOpen, setIsSelectModalOpen] = useState(false);

  // Contact form state
  const [contactSubject, setContactSubject] = useState('');
  const [contactMessage, setContactMessage] = useState('');

  // Interview form state
  const [interviewDate, setInterviewDate] = useState('');
  const [interviewTime, setInterviewTime] = useState('');
  const [interviewMode, setInterviewMode] = useState('Online');
  const [interviewer, setInterviewer] = useState('');
  const [interviewNotes, setInterviewNotes] = useState('');

  // Reject form state
  const [rejectReason, setRejectReason] = useState('Qualifications mismatch');

  useEffect(() => {
    const stored = localStorage.getItem('hr_candidates');
    if (stored) {
      const parsed = JSON.parse(stored);
      setCandidates(parsed);
      const found = parsed.find(c => c.id.toString() === id);
      setCandidate(found || parsed[0]);
    } else {
      localStorage.setItem('hr_candidates', JSON.stringify(DEFAULT_CANDIDATES));
      setCandidates(DEFAULT_CANDIDATES);
      const found = DEFAULT_CANDIDATES.find(c => c.id.toString() === id);
      setCandidate(found || DEFAULT_CANDIDATES[0]);
    }
  }, [id]);

  const updateCandidateInStorage = (updated) => {
    const updatedList = candidates.map(c => c.id === updated.id ? updated : c);
    setCandidates(updatedList);
    setCandidate(updated);
    localStorage.setItem('hr_candidates', JSON.stringify(updatedList));
  };

  const handleStatusChange = (newStatus) => {
    if (!candidate) return;
    
    // Update timeline stages based on new status
    const updatedTimeline = candidate.timeline.map(t => {
      if (t.stage.toLowerCase() === newStatus.toLowerCase()) {
        return { ...t, completed: true, date: 'May 24, 2025', time: '05:00 PM' };
      }
      return t;
    });

    const updated = {
      ...candidate,
      status: newStatus,
      timeline: updatedTimeline
    };
    updateCandidateInStorage(updated);
    setIsActionsDropdownOpen(false);
  };

  if (!candidate) {
    return (
      <div className="p-8 text-center text-slate-500 font-bold">
        Loading candidate details...
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full text-left relative">
      
      {/* Back button header navigation bar */}
      <div className="flex items-center justify-between">
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-xs font-black text-slate-500 hover:text-slate-700 transition-colors cursor-pointer bg-white px-4 py-2 rounded-xl border border-slate-100 shadow-2xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Applications</span>
        </button>

        <h2 className="text-5xl font-black text-slate-800 tracking-tight">Candidate Details</h2>

        {/* Top Right Actions Dropdown */}
        <div className="relative">
          <button 
            onClick={() => setIsActionsDropdownOpen(!isActionsDropdownOpen)}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-base font-black text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer shadow-2xs"
          >
            <span>Actions</span>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </button>
          {isActionsDropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-100 rounded-xl shadow-lg py-2 z-30 animate-scaleUp">
              <button 
                onClick={() => handleStatusChange('Under Review')}
                className="w-full text-left px-4 py-2.5 text-base font-bold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Under Review
              </button>
              <button 
                onClick={() => handleStatusChange('Shortlisted')}
                className="w-full text-left px-4 py-2.5 text-base font-bold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Shortlist
              </button>
              <button 
                onClick={() => handleStatusChange('Interviewing')}
                className="w-full text-left px-4 py-2.5 text-base font-bold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Schedule Interview
              </button>
              <button 
                onClick={() => setIsRejectModalOpen(true)}
                className="w-full text-left px-4 py-2.5 text-base font-bold text-rose-600 hover:bg-rose-50 transition-colors"
              >
                Reject Candidate
              </button>
              <button 
                onClick={() => setIsSelectModalOpen(true)}
                className="w-full text-left px-4 py-2.5 text-base font-bold text-slate-700 hover:bg-emerald-50 hover:text-emerald-600 transition-colors"
              >
                Select Candidate
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT PROFILE CARD - 4 cols */}
        <div className="lg:col-span-4 bg-white rounded-[32px] border border-slate-100 p-6 shadow-xs flex flex-col items-center">
          <div className="w-24 h-24 rounded-full overflow-hidden border-2 border-[#8CC63F]/30 shadow-xs mb-4">
            <img src={candidate.img} alt={candidate.name} className="w-full h-full object-cover" />
          </div>

          <h3 className="text-3xl font-black text-slate-800">{candidate.name}</h3>
          
          <span className={`mt-2 px-3 py-1 rounded-full text-sm font-black uppercase ${
            candidate.status === 'Shortlisted' ? 'bg-amber-50 text-amber-600' :
            candidate.status === 'Interviewing' ? 'bg-violet-50 text-violet-600' :
            candidate.status === 'Selected' ? 'bg-emerald-50 text-emerald-600' :
            candidate.status === 'Rejected' ? 'bg-rose-50 text-rose-600' :
            'bg-blue-50 text-blue-600'
          }`}>
            {candidate.status}
          </span>

          <div className="w-full border-t border-slate-50 my-5"></div>

          {/* Contact Details Items */}
          <div className="w-full flex flex-col gap-3.5 text-base font-bold text-slate-500 mb-6">
            <div className="flex items-center gap-3">
              <Mail className="w-4 h-4 text-slate-400" />
              <span>{candidate.email}</span>
            </div>
            <div className="flex items-center gap-3">
              <Phone className="w-4 h-4 text-slate-400" />
              <span>{candidate.phone}</span>
            </div>
            <div className="flex items-center gap-3">
              <Briefcase className="w-4 h-4 text-slate-400" />
              <span>{candidate.role}</span>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span>{candidate.exp} experience</span>
            </div>
          </div>

          {/* Core Action buttons */}
          <div className="w-full flex flex-col gap-2">
            <button 
              onClick={() => setIsContactModalOpen(true)}
              className="w-full py-2.5 bg-[#8CC63F] hover:bg-[#80b835] text-white text-base font-black rounded-xl transition-all shadow-xs cursor-pointer text-center"
            >
              Contact Candidate
            </button>
            <button 
              onClick={() => alert(`Downloading resume for ${candidate.name}`)}
              className="w-full py-2.5 bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 text-base font-black rounded-xl transition-all cursor-pointer text-center"
            >
              Download Resume
            </button>
          </div>

          <div className="w-full border-t border-slate-50 my-5"></div>

          {/* Additional Info Cards */}
          <div className="w-full text-left flex flex-col gap-4">
            <div>
              <p className="text-sm font-black text-slate-400 uppercase tracking-wider">APPLIED JOB</p>
              <p className="text-base font-black text-slate-700 mt-0.5">{candidate.appliedJob}</p>
            </div>
            <div>
              <p className="text-sm font-black text-slate-400 uppercase tracking-wider">APPLIED DATE</p>
              <p className="text-base font-black text-slate-700 mt-0.5">{candidate.appliedDate}</p>
            </div>
          </div>
        </div>

        {/* RIGHT DETAILS WORKSPACE - 8 cols */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          {/* Tabs row */}
          <div className="bg-white rounded-[24px] p-2 border border-slate-100 shadow-xs flex items-center overflow-x-auto scrollbar-none w-full">
            <div className="flex items-center gap-2 w-full">
              {['Overview', 'Resume', 'Cover Letter', 'Timeline'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-2.5 text-base font-black rounded-xl transition-all cursor-pointer whitespace-nowrap ${
                    activeTab === tab 
                      ? 'bg-[#8CC63F] text-white shadow-xs' 
                      : 'text-slate-400 hover:text-slate-600'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {/* Active Tab Workspace Panel */}
          <div className="bg-white rounded-[32px] border border-slate-100 p-6 md:p-8 shadow-xs min-h-[400px]">
            {activeTab === 'Overview' && (
              <div className="flex flex-col gap-6">
                {/* About */}
                <div className="flex flex-col gap-2">
                  <h4 className="text-xl font-black text-slate-800 uppercase tracking-wider">About</h4>
                  <p className="text-base font-bold text-slate-500 leading-relaxed">{candidate.about}</p>
                </div>

                <div className="border-t border-slate-50 my-2"></div>

                {/* Education */}
                <div className="flex flex-col gap-2">
                  <h4 className="text-xl font-black text-slate-800 uppercase tracking-wider">Education</h4>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-base font-black text-slate-700">{candidate.education.degree}</p>
                      <p className="text-base font-bold text-slate-400 mt-0.5">{candidate.education.school}</p>
                      <p className="text-sm font-bold text-slate-400 mt-1">CGPA: {candidate.education.cgpa}</p>
                    </div>
                    <span className="text-sm font-black text-slate-400">{candidate.education.year}</span>
                  </div>
                </div>

                <div className="border-t border-slate-50 my-2"></div>

                {/* Experience */}
                <div className="flex flex-col gap-2">
                  <h4 className="text-xl font-black text-slate-800 uppercase tracking-wider">Experience</h4>
                  <div className="flex flex-col gap-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-base font-black text-slate-700">{candidate.experience.role}</p>
                        <ul className="list-disc pl-4 mt-2 text-base font-bold text-slate-500 flex flex-col gap-1.5">
                          {candidate.experience.highlights.map((h, i) => (
                            <li key={i}>{h}</li>
                          ))}
                        </ul>
                      </div>
                      <span className="text-sm font-black text-[#8CC63F] whitespace-nowrap">{candidate.experience.duration}</span>
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-50 my-2"></div>

                {/* Skills */}
                <div className="flex flex-col gap-2">
                  <h4 className="text-xl font-black text-slate-800 uppercase tracking-wider">Skills</h4>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {candidate.skills.map((skill, i) => (
                      <span key={i} className="px-3 py-1 bg-slate-50 text-slate-500 rounded-full text-base font-bold border border-slate-100 shadow-2xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'Resume' && (
              <div className="flex flex-col items-center justify-center py-10 gap-4">
                <FileText className="w-16 h-16 text-slate-300" />
                <div className="text-center">
                  <h4 className="text-base font-black text-slate-700">{candidate.name}_resume.pdf</h4>
                  <p className="text-sm font-bold text-slate-400 mt-1">Ready for review</p>
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <button 
                    onClick={() => alert('Downloading resume file...')}
                    className="flex items-center gap-1.5 px-4 py-2 bg-[#8CC63F] hover:bg-[#80b835] text-white text-base font-black rounded-xl transition-all shadow-xs cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </button>
                  <button 
                    onClick={() => window.open('#', '_blank')}
                    className="flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 text-base font-black rounded-xl transition-all cursor-pointer"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Open in New Tab</span>
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'Cover Letter' && (
              <div className="flex flex-col gap-4 text-left">
                <div className="flex items-center justify-between border-b border-slate-50 pb-3 mb-2">
                  <h4 className="text-xl font-black text-slate-800 uppercase tracking-wider">Cover Letter</h4>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(candidate.coverLetter);
                      alert('Cover letter copied to clipboard!');
                    }}
                    className="flex items-center gap-1.5 text-base font-bold text-[#8CC63F] hover:underline cursor-pointer"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Letter</span>
                  </button>
                </div>
                <div className="bg-slate-50/50 p-6 rounded-2xl border border-slate-100/50 text-base font-bold text-slate-500 whitespace-pre-line leading-relaxed">
                  {candidate.coverLetter}
                </div>
              </div>
            )}

            {activeTab === 'Timeline' && (
              <div className="flex flex-col gap-6 text-left max-w-md mx-auto py-4">
                <h4 className="text-xl font-black text-slate-800 uppercase tracking-wider mb-2">Application Progress</h4>
                
                <div className="relative border-l border-slate-200 ml-3 pl-6 flex flex-col gap-8">
                  {candidate.timeline.map((step, idx) => {
                    const isCompleted = step.completed;
                    const isCurrent = candidate.status.toLowerCase() === step.stage.toLowerCase() || 
                                      (candidate.status === 'Under Review' && step.stage === 'Under Review');

                    return (
                      <div key={idx} className="relative flex flex-col gap-1">
                        {/* Circle Indicator */}
                        <div className={`absolute -left-[31px] top-0.5 w-4 h-4 rounded-full flex items-center justify-center ${
                          isCompleted ? 'bg-[#8CC63F]' : 
                          isCurrent ? 'bg-blue-600 animate-pulse' : 'bg-slate-200'
                        }`}>
                          {isCompleted && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>

                        <div className="flex justify-between items-start">
                          <p className={`text-xs font-black ${
                            isCompleted ? 'text-slate-800' : 
                            isCurrent ? 'text-blue-600 font-extrabold' : 'text-slate-400'
                          }`}>{step.stage}</p>
                          {isCompleted && (
                            <span className="text-[9px] font-bold text-slate-400">{step.date} • {step.time}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

          </div>
        </div>

      </div>

      {/* CONTACT CANDIDATE MODAL */}
      {isContactModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-[28px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col animate-scaleUp">
            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-base font-black text-slate-800">Contact Candidate</h3>
              <button onClick={() => setIsContactModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-black text-slate-500 uppercase tracking-wide">To</label>
                <input 
                  type="text" 
                  disabled 
                  value={`${candidate.name} (${candidate.email})`}
                  className="px-4 py-2.5 text-xs font-bold text-slate-500 bg-slate-50 border border-slate-100 rounded-xl"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-black text-slate-500 uppercase tracking-wide">Subject</label>
                <input 
                  type="text" 
                  value={contactSubject}
                  onChange={(e) => setContactSubject(e.target.value)}
                  placeholder="Interview schedule follow-up"
                  className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-black text-slate-500 uppercase tracking-wide">Message</label>
                <textarea 
                  rows="4" 
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  placeholder="Write your email draft here..."
                  className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl"
                />
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button 
                onClick={() => setIsContactModalOpen(false)}
                className="px-4 py-2 text-xs font-bold text-slate-500 hover:bg-slate-100 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  alert(`Email sent successfully to ${candidate.email}!`);
                  setIsContactModalOpen(false);
                  setContactSubject('');
                  setContactMessage('');
                }}
                className="px-4 py-2 bg-[#8CC63F] hover:bg-[#80b835] text-white text-xs font-black rounded-xl flex items-center gap-1.5 cursor-pointer shadow-xs"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send Message</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SCHEDULE INTERVIEW MODAL */}
      {isInterviewModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-[28px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col animate-scaleUp">
            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-base font-black text-slate-800">Schedule Interview</h3>
              <button onClick={() => setIsInterviewModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-black text-slate-500 uppercase tracking-wide">Date</label>
                  <input 
                    type="date" 
                    value={interviewDate}
                    onChange={(e) => setInterviewDate(e.target.value)}
                    className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-black text-slate-500 uppercase tracking-wide">Time</label>
                  <input 
                    type="time" 
                    value={interviewTime}
                    onChange={(e) => setInterviewTime(e.target.value)}
                    className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-black text-slate-500 uppercase tracking-wide">Mode</label>
                <select 
                  value={interviewMode}
                  onChange={(e) => setInterviewMode(e.target.value)}
                  className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl cursor-pointer"
                >
                  <option value="Online">Online (Video Call)</option>
                  <option value="Offline">Offline (Office)</option>
                  <option value="Hybrid">Hybrid</option>
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-black text-slate-500 uppercase tracking-wide">Interviewer Name</label>
                <input 
                  type="text" 
                  value={interviewer}
                  onChange={(e) => setInterviewer(e.target.value)}
                  placeholder="e.g. Sandra Bullock"
                  className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-black text-slate-500 uppercase tracking-wide">Notes</label>
                <textarea 
                  rows="3" 
                  value={interviewNotes}
                  onChange={(e) => setInterviewNotes(e.target.value)}
                  placeholder="Share details or preparation guidelines..."
                  className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl"
                />
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button 
                onClick={() => setIsInterviewModalOpen(false)}
                className="px-4 py-2 text-xs font-bold text-slate-500 hover:bg-slate-100 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  alert(`Interview scheduled successfully for ${candidate.name}!`);
                  handleStatusChange('Interviewing');
                  setIsInterviewModalOpen(false);
                }}
                className="px-4 py-2 bg-[#8CC63F] hover:bg-[#80b835] text-white text-xs font-black rounded-xl flex items-center gap-1.5 cursor-pointer shadow-xs"
              >
                <CalendarCheck className="w-3.5 h-3.5" />
                <span>Confirm & Schedule</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REJECT CANDIDATE CONFIRMATION MODAL */}
      {isRejectModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white w-full max-w-sm rounded-[28px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col animate-scaleUp">
            <div className="p-6 text-center flex flex-col items-center gap-4">
              <div className="w-12 h-12 bg-rose-50 rounded-full flex items-center justify-center text-rose-600">
                <X className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-black text-slate-800">Reject Candidate?</h3>
                <p className="text-xs font-bold text-slate-400 mt-1">This action will mark the candidate status as Rejected.</p>
              </div>
              <div className="w-full flex flex-col gap-1.5 text-left">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-wide">Reason for Rejection</label>
                <select 
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 focus:border-[#8CC63F] focus:outline-none rounded-xl cursor-pointer"
                >
                  <option value="Qualifications mismatch">Qualifications mismatch</option>
                  <option value="Failed coding round">Failed coding round</option>
                  <option value="Salary expectation gap">Salary expectation gap</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button 
                onClick={() => setIsRejectModalOpen(false)}
                className="px-4 py-2 text-xs font-bold text-slate-500 hover:bg-slate-100 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  handleStatusChange('Rejected');
                  setIsRejectModalOpen(false);
                  alert(`${candidate.name} status updated to Rejected.`);
                }}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-black rounded-xl cursor-pointer shadow-xs"
              >
                Reject Candidate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SELECT CANDIDATE CONFIRMATION MODAL */}
      {isSelectModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-white w-full max-w-sm rounded-[28px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col animate-scaleUp">
            <div className="p-6 text-center flex flex-col items-center gap-4">
              <div className="w-12 h-12 bg-emerald-50 rounded-full flex items-center justify-center text-emerald-600">
                <UserCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-black text-slate-800">Select Candidate?</h3>
                <p className="text-xs font-bold text-slate-400 mt-1">This will update status to Selected and complete the review process.</p>
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button 
                onClick={() => setIsSelectModalOpen(false)}
                className="px-4 py-2 text-xs font-bold text-slate-500 hover:bg-slate-100 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  handleStatusChange('Selected');
                  setIsSelectModalOpen(false);
                  alert(`${candidate.name} status updated to Selected!`);
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black rounded-xl cursor-pointer shadow-xs"
              >
                Confirm Selection
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
