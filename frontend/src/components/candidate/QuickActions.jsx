import React from 'react';
import { Search, UserCheck, FileUp } from 'lucide-react';

export default function QuickActions() {
  return (
    <div className="bg-white rounded-[32px] p-6 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[300px] select-none hover:shadow-md transition-shadow">
      
      {/* Title */}
      <div className="mb-5 text-left">
        <h2 className="text-xl font-black text-slate-800 tracking-tight">Quick Actions</h2>
      </div>

      {/* Action Buttons List */}
      <div className="space-y-4">
        {/* Action 1: Browse Jobs */}
        <button
          type="button"
          className="flex items-center gap-3.5 w-full p-4 bg-[#EADFC9]/30 hover:bg-[#EADFC9]/50 active:scale-[0.99] rounded-2xl border border-[#EADFC9]/40 text-left transition-all duration-200 cursor-pointer focus:outline-none"
        >
          <div className="w-9 h-9 rounded-xl bg-[#84A43C]/10 text-[#84A43C] flex items-center justify-center border border-[#84A43C]/20 shadow-xs shrink-0">
            <Search className="w-4.5 h-4.5" />
          </div>
          <span className="text-sm font-extrabold text-slate-800">Browse Jobs</span>
        </button>

        {/* Action 2: Update Profile */}
        <button
          type="button"
          className="flex items-center gap-3.5 w-full p-4 bg-slate-100/60 hover:bg-slate-100/90 active:scale-[0.99] rounded-2xl border border-slate-200/40 text-left transition-all duration-200 cursor-pointer focus:outline-none"
        >
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center border border-amber-500/20 shadow-xs shrink-0">
            <UserCheck className="w-4.5 h-4.5" />
          </div>
          <span className="text-sm font-extrabold text-slate-800">Update Profile</span>
        </button>

        {/* Action 3: Upload Resume */}
        <button
          type="button"
          className="flex items-center gap-3.5 w-full p-4 bg-orange-50/70 hover:bg-orange-100/70 active:scale-[0.99] rounded-2xl border border-orange-100/60 text-left transition-all duration-200 cursor-pointer focus:outline-none"
        >
          <div className="w-9 h-9 rounded-xl bg-orange-500/10 text-orange-600 flex items-center justify-center border border-orange-500/20 shadow-xs shrink-0">
            <FileUp className="w-4.5 h-4.5" />
          </div>
          <span className="text-sm font-extrabold text-slate-800">Upload Resume</span>
        </button>
      </div>

    </div>
  );
}
