import React from 'react';

export default function CandidateHeader() {
  return (
    <div className="py-2 text-left select-none animate-in fade-in slide-in-from-top-4 duration-300">
      <h1 className="text-3xl sm:text-4xl font-extrabold text-[#E29D29] tracking-tight mb-1">
        Hello!
      </h1>
      <p className="text-sm font-medium text-slate-500">
        Welcome back to your TN Jobz candidate workspace portal.
      </p>
    </div>
  );
}
