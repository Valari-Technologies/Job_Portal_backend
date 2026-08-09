import React, { useState, useEffect } from 'react';

export default function ProfileCompletion() {
  const [percentage, setPercentage] = useState(0);
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  useEffect(() => {
    let score = 0;
    
    // Personal Info (default contains name)
    const savedInfo = localStorage.getItem('personalInfo');
    if (savedInfo) {
      const parsed = JSON.parse(savedInfo);
      if (parsed.fullName && parsed.fullName.trim() !== '') score += 25;
    } else {
      score += 25;
    }
    
    // Experience (default contains experience)
    const savedExp = localStorage.getItem('experienceList');
    if (savedExp) {
      const parsed = JSON.parse(savedExp);
      if (parsed.length > 0) score += 20;
    } else {
      score += 20;
    }
    
    // Skills (default contains skills)
    const savedSkills = localStorage.getItem('skillsList');
    if (savedSkills) {
      const parsed = JSON.parse(savedSkills);
      if (parsed.length > 0) score += 20;
    } else {
      score += 20;
    }
    
    // Resume (check if resumeData is saved and is not dummy)
    const savedResumeData = localStorage.getItem('resumeData');
    if (savedResumeData && savedResumeData !== 'dummy') {
      score += 20;
    }
    
    // Certifications
    const savedCerts = localStorage.getItem('certifications');
    if (savedCerts) {
      const parsed = JSON.parse(savedCerts);
      if (parsed.length > 0) score += 15;
    }

    setPercentage(score);
  }, []);

  return (
    <div className="bg-white rounded-[32px] p-6 shadow-xs border border-slate-100 flex flex-col items-center justify-between min-h-[340px] select-none text-center hover:shadow-md transition-shadow">
      
      {/* Title */}
      <div className="w-full text-left">
        <h2 className="text-xl font-bold text-[#84A43C] tracking-tight">Profile Completion</h2>
        <p className="text-xs font-semibold text-slate-400 mt-0.5">Almost there!</p>
      </div>

      {/* Circular Progress Ring - Starts at top center, moves counter-clockwise (left side first) */}
      <div className="relative my-4 flex items-center justify-center">
        <svg 
          className="w-44 h-44" 
          style={{ transform: 'scaleX(-1) rotate(-90deg)', transformOrigin: 'center' }} 
          viewBox="0 0 160 160"
        >
          <defs>
            <linearGradient id="profileGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#EF4444" />   {/* Red */}
              <stop offset="50%" stopColor="#E29D29" />  {/* Yellow/Orange */}
              <stop offset="100%" stopColor="#84A43C" /> {/* Green */}
            </linearGradient>
          </defs>
          
          {/* Background circle */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            className="text-slate-100"
            strokeWidth="10"
            stroke="currentColor"
            fill="transparent"
          />
          
          {/* Progress circle using the custom gradient */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="url(#profileGradient)"
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-500 ease-out"
          />
        </svg>

        {/* Text Inside Circle */}
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-4xl font-extrabold text-slate-800 tracking-tighter">
            {percentage}%
          </span>
        </div>
      </div>

      {/* Footer link/label */}
      <button 
        type="button" 
        className="text-[#84A43C] hover:text-[#73922f] font-bold text-sm tracking-wide transition-colors cursor-pointer focus:outline-none"
      >
        Complete your profile
      </button>

    </div>
  );
}
